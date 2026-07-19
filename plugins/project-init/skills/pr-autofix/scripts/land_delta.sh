#!/usr/bin/env bash
# land_delta.sh — stage-gated worktree landing pipeline for the pr-autofix skill.
#
# Why a script: the skill's guards were prose-embedded bash for 20+ review rounds and
# every round found real defects — shell state does not survive across host tool calls,
# and prose promises drift from code. Here every stage persists its state in RUN_DIR,
# enforces its predecessor's sentinel, and is unit-tested (tests/structure/).
#
# Stages (each is one host tool call):
#   setup                          create RUN_DIR + implementer/reference worktrees, pin state
#   capture <run>                  integrity gates + immutable full.N.patch generation
#   approve <run>                  freeze approved.patch (host edits it BEFORE calling this)
#   check-plan-paths <run>         validate plan paths from stdin (relative, no .., in-worktree)
#   land <run> [--allow-exec-surface]   denylist+cleanliness gates, apply, baseline snapshots
#   verify <run> --build-ok 0|1    containment + equality vs reference, writes ok.build
#   commit <run> <msg> --approved-sha <sha>   final guards + hooks/config integrity + pathspec commit
#   push <run>                     idempotent push (separate stage — retryable)
#   rollback <run>                 revert landed paths, preserving user edits
#   cleanup <run> [--keep]         remove worktrees (+ artifacts unless --keep)
set -euo pipefail

die() { echo "STOP: $*" >&2; exit 1; }
_canon() { (cd "$1" 2>/dev/null && pwd -P); }   # portable dir canonicalization (realpath -e is GNU-only)
_verify_self() { # $1 = script sha the HOST recorded in its notes at 4b — a tampered script
                 # computes valid-looking signatures for everything else, so every
                 # destructive/final stage re-verifies itself against the host-held value
  [ -n "${1:-}" ] || die "missing --script-sha (value the host recorded at setup)"
  [ "$(SHAPIPE < "$0" | cut -d' ' -f1)" = "$1" ] || die "land_delta.sh does not match the setup-recorded hash — script tampered"
}
SHAPIPE() { if command -v sha256sum >/dev/null 2>&1; then sha256sum; else shasum -a 256; fi; }

# Execution-surface denylist: files the host executes during build/commit. Edits to these
# require --allow-exec-surface (user-granted). Hook dirs are included — a hook that execs
# a tracked file runs landed code at commit time.
# Class-based, not filename-enumerated: anything plausibly executed during build/verify/
# commit. Broad on purpose — a false positive costs one --allow-exec-surface approval,
# a false negative is arbitrary code execution on the host.
EXEC_SURFACE_RE='(^|/)(\.github|\.husky|\.git[a-z]*|\.ci|ci|\.circleci|bin|scripts?|tests?|hooks?)/|(^|/)(package\.json|package-lock\.json|Makefile|makefile|GNUmakefile|CMakeLists\.txt|build\.rs|pyproject\.toml|setup\.(py|cfg)|conftest\.py|noxfile\.py|tox\.ini|Cargo\.toml|pom\.xml|build\.xml|Rakefile|Gemfile|justfile|Justfile|Taskfile\.ya?ml|\.gitlab-ci\.ya?ml|Jenkinsfile[^/]*|azure-pipelines\.ya?ml|bitbucket-pipelines\.ya?ml|gradlew(\.bat)?|mvnw(\.cmd)?|configure|autogen\.sh|BUILD(\.bazel)?|WORKSPACE|Dockerfile[^/]*|\.envrc|sitecustomize\.py|\.gitattributes|\.gitmodules|\.pre-commit-config\.ya?ml|\.?lefthook(-local)?\.ya?ml|\.huskyrc[^/]*|gulpfile\.[a-z]+|Gruntfile\.[a-z]+|\.eslintrc[^/]*|\.babelrc[^/]*|composer\.json|meson\.build|SConstruct|SConscript|docker-compose[^/]*\.ya?ml|compose\.ya?ml|\.mcp\.json|pytest\.ini|\.yarnrc\.ya?ml|manage\.py|configure\.ac|.*\.cmake|.*\.pth)$|(^|/)\.yarn/|(^|/)\.claude/settings[^/]*\.json$|\.(gradle|gradle\.kts|sh|bash|zsh|ps1|psm1)$|(^|/)\.[a-z0-9_-]+rc\.(js|cjs|mjs|ts)$|(^|/)[^/]*\.config\.(js|cjs|mjs|ts)$'

state() { # state <run> get KEY | state <run> set KEY VALUE
  local run=$1 op=$2 key=$3
  case "$op" in
    get) sed -n "s/^$key=//p" "$run/state" | tail -1 ;;   # last write wins — state appends
    set) printf '%s=%s\n' "$key" "${4:?}" >> "$run/state" ;;
  esac
}

_state_sig() { # recompute the setup signature from CURRENT state values — any tamper breaks it
  local run=$1
  printf '%s|%s|%s|%s|%s|%s|%s|%s' \
    "$(state "$run" get WT_DIR)" "$(state "$run" get REF_DIR)" \
    "$(state "$run" get CANON_WT_DIR)" "$(state "$run" get CANON_REF_DIR)" \
    "$(state "$run" get HOST_ROOT)" "$(state "$run" get IMPL_WT)" \
    "$(state "$run" get REF_WT)" "$(state "$run" get BASE_SHA)" | SHAPIPE | cut -d' ' -f1
}

dirty_snap() { # content hash of every dirty/untracked file — the porcelain STRING comparison
               # is blind to an implementer overwriting an ALREADY-dirty user file (same 'M'
               # line); this tripwire hashes what the user actually had
  local host=$1 f
  git -C "$host" --literal-pathspecs status --porcelain --untracked-files=all -z 2>/dev/null \
    | while IFS= read -r -d '' rec; do
        f=${rec:3}
        [ -f "$host/$f" ] && { printf '%s\x01' "$f"; cat "$host/$f" 2>/dev/null || true; printf '\x02'; } || printf '%s\x01absent\x02' "$f"
      done | SHAPIPE | cut -d' ' -f1
}

config_snap() { # a planted core.sshCommand/credential.helper would execute at push — and it
                # can live in ANY scope reachable by the same uid (local, worktree, global).
                # Snapshot the EFFECTIVE config, not just --local, and re-verify before use.
  git -C "$1" config --list 2>/dev/null | sort | SHAPIPE | cut -d' ' -f1
}

hooks_snap() { # hooks_snap <host_root> — portable: no xargs -r / sort -z (both GNU-only;
               # on BSD/macOS the old form failed into 2>/dev/null and the gate silently
               # compared empty hashes on BOTH sides = no-op security)
  local dir list
  dir=$(git -C "$1" rev-parse --path-format=absolute --git-path hooks)
  [ -n "$dir" ] || die "cannot resolve hooks dir"
  [ -d "$dir" ] || { echo absent; return 0; }
  (
    cd "$dir" || exit 1
    list=$(find . \( -type f -o -type l \) | LC_ALL=C sort)
    [ -n "$list" ] || { echo empty; exit 0; }
    {
      printf '%s\n' "$list" | while IFS= read -r f; do ls -ld "$f"; done
      printf '%s\n' "$list" | while IFS= read -r f; do cat "$f" 2>/dev/null || true; done
    } | SHAPIPE | cut -d' ' -f1
  )
}

symlink_scan() { # symlink_scan <worktree> — fail-closed (find status checked explicitly)
  local wt=$1 links rp base
  base=$(cd "$wt" && pwd -P)
  links=$(mktemp); find "$wt" -type l -print > "$links" || die "symlink scan failed"
  while IFS= read -r l || [ -n "$l" ]; do
    rp=$(realpath "$l" 2>/dev/null) || rp=""          # unresolvable/dangling = fail-closed
    case "$rp" in "$base"/*) ;; *) rm -f "$links"; die "symlink escapes worktree (or dangling): $l";; esac
  done < "$links"
  rm -f "$links"
}

gitwt_verify() { # gitwt_verify <run> — worktree gitfile integrity (common dir AND git dir)
  local run=$1 host wt gcd gd
  host=$(state "$run" get HOST_ROOT); wt=$(state "$run" get IMPL_WT)
  gcd=$(git -C "$host" rev-parse --path-format=absolute --git-common-dir)
  [ "$(git -C "$wt" rev-parse --path-format=absolute --git-common-dir)" = "$gcd" ] || die "worktree gitfile tampered (common dir)"
  gd=$(git -C "$wt" rev-parse --path-format=absolute --absolute-git-dir)
  case "$gd" in "$gcd"/worktrees/*) ;; *) die "worktree gitfile tampered (git dir: $gd)";; esac
}

GITH() { local run=$1; shift; git -C "$(state "$run" get HOST_ROOT)" -c core.hooksPath=/dev/null -c core.fsmonitor=false --literal-pathspecs "$@"; }
GITWT() { local run=$1; shift; git -C "$(state "$run" get IMPL_WT)" -c core.hooksPath=/dev/null -c core.fsmonitor=false --literal-pathspecs "$@"; }
GITREF() { local run=$1; shift; git -C "$(state "$run" get REF_WT)" -c core.hooksPath=/dev/null -c core.fsmonitor=false --literal-pathspecs "$@"; }

cmd_setup() {
  local run wtd refd host base ref
  host=$(git rev-parse --show-toplevel) || die "not in a git repo"
  _setup_fail() { # a mid-setup die must not leak worktrees the caller never learned about
    git -C "$host" worktree remove --force "$wtd/wt" 2>/dev/null || true
    git -C "$host" worktree remove --force "$refd/wt" 2>/dev/null || true
    rm -rf -- "${run:-}" "${wtd:-}" "${refd:-}"
  }
  trap _setup_fail EXIT
  base=$(git -C "$host" rev-parse HEAD)
  ref=$(git -C "$host" symbolic-ref -q HEAD || echo detached)
  run=$(mktemp -d "${TMPDIR:-/tmp}/pr-autofix.XXXXXX")
  wtd=$(mktemp -d "${TMPDIR:-/tmp}/pr-autofix-wt.XXXXXX")
  refd=$(mktemp -d "${TMPDIR:-/tmp}/pr-autofix-ref.XXXXXX")
  : > "$run/state"
  state "$run" set HOST_ROOT "$host"; state "$run" set BASE_SHA "$base"; state "$run" set BASE_REF "$ref"
  state "$run" set WT_DIR "$wtd";    state "$run" set REF_DIR "$refd"
  state "$run" set CANON_WT_DIR "$(_canon "$wtd")"; state "$run" set CANON_REF_DIR "$(_canon "$refd")"
  state "$run" set IMPL_WT "$wtd/wt"; state "$run" set REF_WT "$refd/wt"
  HS=$(hooks_snap "$host") || die "hooks snapshot failed";  state "$run" set HOOKS_SNAP "$HS"
  CS=$(config_snap "$host") || die "config snapshot failed"; state "$run" set CONFIG_SNAP "$CS"
  DS=$(dirty_snap "$host")  || die "dirty snapshot failed";  state "$run" set DIRTY_SNAP "$DS"
  SIG=$(printf '%s|%s|%s|%s|%s|%s|%s|%s' "$wtd" "$refd" "$(_canon "$wtd")" "$(_canon "$refd")" "$host" "$wtd/wt" "$refd/wt" "$base" | SHAPIPE | cut -d' ' -f1)
  state "$run" set SETUP_SIG "$SIG"
  git -C "$host" --literal-pathspecs status --porcelain --untracked-files=all > "$run/host.status.setup"
  git -C "$host" -c core.hooksPath=/dev/null worktree add --detach "$wtd/wt" "$base" >/dev/null
  git -C "$host" -c core.hooksPath=/dev/null worktree add --detach "$refd/wt" "$base" >/dev/null
  symlink_scan "$wtd/wt"           # pre-implementer: branch-committed symlinks would leak reads DURING the run
  : > "$run/ok.setup"
  trap - EXIT
  echo "$run $SIG"                  # host records BOTH in its notes: the run path and the
                                    # cleanup signature (its own trust root — see cmd_cleanup)
}

cmd_capture() { # capture <run> --sig <setup-sig>
  local run=$1 n
  [ "${2:-}" = "--sig" ] && [ -n "${3:-}" ] || die "capture requires --sig <value printed by setup>"
  [ "$(_state_sig "$run")" = "$3" ] || die "state signature mismatch — refusing capture"
  [ -f "$run/ok.setup" ] || die "setup stage missing"
  gitwt_verify "$run"; symlink_scan "$(state "$run" get IMPL_WT)"
  [ "$(config_snap "$(state "$run" get HOST_ROOT)")" = "$(state "$run" get CONFIG_SNAP)" ] || die "shared git config changed during implementation"
  [ "$(dirty_snap "$(state "$run" get HOST_ROOT)")" = "$(state "$run" get DIRTY_SNAP)" ] || die "the user's uncommitted files changed during implementation (out-of-worktree write?) — inspect before proceeding"
  GITH "$run" status --porcelain --untracked-files=all > "$run/host.status.capture"
  diff -q "$run/host.status.setup" "$run/host.status.capture" >/dev/null \
    || die "host tree changed during implementation (out-of-worktree writes or concurrent edits) — inspect before proceeding"
  GITWT "$run" add -N .
  n=1; while [ -e "$run/full.$n.patch" ]; do n=$((n+1)); done   # generations are immutable — re-runs append
  GITWT "$run" diff --binary --no-ext-diff --no-textconv "$(state "$run" get BASE_SHA)" > "$run/full.$n.patch"
  [ -s "$run/full.$n.patch" ] || die "empty capture — implementer produced no delta"
  state "$run" set LATEST_FULL "full.$n.patch"
  _hunk_hashes "$run/full.$n.patch" | sort > "$run/full.$n.hunks"   # manifest for approve's subset check
  _opaque_chunks "$run/full.$n.patch" | sort > "$run/full.$n.opaque" # binary/meta-only file sections (whole-chunk unit)
  rm -f "$run/ok.approved" "$run/ok.landed" "$run/ok.build" "$run/ok.committed" "$run/approved.patch"   # a new capture invalidates EVERY downstream stage — INCLUDING a stale approved.patch from an older generation
  : > "$run/ok.captured"
  echo "$run/full.$n.patch"
}

_hunk_hashes() { # one PHYSICAL line per hunk (newlines -> \x01), offsets stripped, then hashed
  awk '
    function flush() { if (inh && hunk != "") print hunk; hunk=""; inh=0 }
    /^diff --git /{ flush(); file=$0; next }
    /^@@/{ flush(); line=$0; sub(/@@[^@]*@@/, "@@ @@", line); hunk=file "\x01" line; inh=1; next }
    inh { hunk = hunk "\x01" $0 }
    END { flush() }
  ' "$1" | while IFS= read -r h; do printf '%s' "$h" | SHAPIPE | cut -d' ' -f1; done
}

_opaque_chunks() { # per-FILE sections with no text hunks (binary patches, empty adds/deletes,
                   # pure meta) — these can't be hunk-subset-checked, so they must match whole
  awk '
    function flush() { if (chunk != "" && !hastext) print chunk; chunk=""; hastext=0 }
    /^diff --git /{ flush(); chunk=$0; next }
    /^@@/{ hastext=1 }
    chunk != "" { chunk = chunk "\x01" $0 }
    END { flush() }
  ' "$1" | while IFS= read -r c; do printf '%s' "$c" | SHAPIPE | cut -d' ' -f1; done
}

cmd_approve() { # host has already copied+edited approved.patch from the latest generation
  local run=$1
  [ -f "$run/ok.captured" ] || die "capture stage missing"
  [ -s "$run/approved.patch" ] || die "approved.patch missing/empty — copy it from $(state "$run" get LATEST_FULL) and strip unplanned hunks first"
  grep -q '^diff --git' "$run/approved.patch" || die "approved.patch is not a git patch"
  grep -qE '^(new file mode 1[02]0[07][0-9][0-9]|old mode|new mode)|^index [0-9a-f]+\.\.[0-9a-f]+ 120000' "$run/approved.patch" \
    && die "approved.patch contains symlink/executable/mode-change hunks (incl. existing-symlink target changes and new +x files) — this pipeline has no approval path for them; apply such changes manually outside the loop"
  # Subset check — every approved hunk must exist verbatim in the latest generation
  # (stripping whole hunks is allowed; editing or adding hunks is not):
  _hunk_hashes "$run/approved.patch" | sort > "$run/approved.hunks"
  MANIFEST="$run/$(state "$run" get LATEST_FULL | sed 's/\.patch$/.hunks/')"
  [ -z "$(comm -23 "$run/approved.hunks" "$MANIFEST")" ] || die "approved.patch contains hunks not present in the latest capture generation"
  [ -f "$run/ok.plan" ] || die "check-plan-paths stage missing — the plan gate is not optional"
  if [ -f "$run/plan.files" ]; then   # plan conformance — approved files must be planned files
    GITH "$run" apply --numstat "$run/approved.patch" | cut -f3- | sort -u > "$run/approved.files.tmp"
    EXTRA=$(comm -23 "$run/approved.files.tmp" "$run/plan.files"); rm -f "$run/approved.files.tmp"
    [ -z "$EXTRA" ] || die "approved.patch touches files the plan never named: $EXTRA"
  fi
  _opaque_chunks "$run/approved.patch" | sort > "$run/approved.opaque"
  OPAQUE="$run/$(state "$run" get LATEST_FULL | sed 's/\.patch$/.opaque/')"
  [ -z "$(comm -23 "$run/approved.opaque" "$OPAQUE")" ] || die "approved.patch contains binary/meta-only file sections not present verbatim in the latest capture"
  APPROVED_SHA=$(SHAPIPE < "$run/approved.patch" | cut -d' ' -f1)
  state "$run" set APPROVED_SHA "$APPROVED_SHA"   # convenience copy — the TRUST copy is the one echoed below
  rm -f "$run/ok.landed" "$run/ok.build" "$run/ok.committed"   # a re-approval invalidates every later stage
  : > "$run/ok.approved"
  echo "$APPROVED_SHA"                            # host records this in its notes (implementer-unwritable)
                                                  # and passes it back to land/commit as --approved-sha
}

cmd_check_plan_paths() { # paths on stdin, one per line — pre-spawn gate
  local run=$1 p
  [ -f "$run/ok.setup" ] || die "setup stage missing"
  : > "$run/plan.files.tmp"                       # truncate — appends must not survive a previous invocation
  local n=0
  while IFS= read -r p || [ -n "$p" ]; do
    n=$((n+1))
    [ -n "$p" ] && [ "$p" != "." ] || die "empty plan path"
    case "/$p/" in
      //*) die "plan path is absolute: $p" ;;
      */../*) die "plan path traverses: $p" ;;   # component-anchored — schema..v2.json is fine
    esac
    printf '%s\n' "$p" >> "$run/plan.files.tmp"
  done
  [ "$n" -gt 0 ] || die "no plan paths on stdin — fail closed"
  sort -u "$run/plan.files.tmp" > "$run/plan.files"; rm -f "$run/plan.files.tmp"
  : > "$run/ok.plan"
  echo ok
}

cmd_land() { # land <run> --sig <s> --approved-sha <a> --script-sha <h> [--allow-exec-surface]
  local run=$1 host f allow="" sigv="" aprv="" ssha=""
  shift
  while [ $# -gt 0 ]; do case "$1" in
    --sig) sigv=${2:-}; shift 2;; --approved-sha) aprv=${2:-}; shift 2;;
    --script-sha) ssha=${2:-}; shift 2;; --allow-exec-surface) allow=--allow-exec-surface; shift;;
    "") shift;; *) die "unknown land arg: $1";; esac; done
  _verify_self "$ssha"
  [ -n "$sigv" ] || die "land requires --sig <value printed by setup>"
  [ "$(_state_sig "$run")" = "$sigv" ] || die "state signature mismatch — refusing land"
  [ -n "$aprv" ] || die "land requires --approved-sha <value printed by approve>"
  [ -f "$run/ok.plan" ] || die "check-plan-paths stage missing — the plan gate is not optional"
  [ -f "$run/ok.approved" ] || die "approve stage missing"
  # verify against the HOST-supplied hash, not state — state and approved.patch live in the
  # same implementer-reachable tmp; the host's notes are the one unwritable place:
  [ "$(SHAPIPE < "$run/approved.patch" | cut -d' ' -f1)" = "$aprv" ] || die "approved.patch does not match the hash approve printed — tampered since approval"
  host=$(state "$run" get HOST_ROOT)
  [ "$(git -C "$host" rev-parse HEAD)" = "$(state "$run" get BASE_SHA)" ] || die "base moved"
  [ "$(git -C "$host" symbolic-ref -q HEAD || echo detached)" = "$(state "$run" get BASE_REF)" ] || die "branch switched"
  GITH "$run" apply --numstat "$run/approved.patch" | cut -f3- > "$run/landed.files"
  [ -s "$run/landed.files" ] || die "approved patch names no files"
  grep -qE '^"|=>' "$run/landed.files" && die "exotic/renamed path in patch — refuse"
  # CI workflow files are denied UNCONDITIONALLY — no flag opens them (the review CI must
  # never be modifiable by the loop it gates):
  ! grep -qE '^\.github/workflows/' "$run/landed.files" || die "refusing to land .github/workflows changes — hard deny, no override"
  # Execution-surface gate — CODE, not prose (build/commit execute these files):
  if grep -qE "$EXEC_SURFACE_RE" "$run/landed.files" && [ "$allow" != "--allow-exec-surface" ]; then
    die "execution-surface files in the landing set (user approval + --allow-exec-surface required): $(grep -E "$EXEC_SURFACE_RE" "$run/landed.files" | tr '\n' ' ')"
  fi
  while IFS= read -r f || [ -n "$f" ]; do
    [ -z "$(GITH "$run" status --porcelain -- "$f")" ] || die "target file locally modified: $f"
    case "$(GITH "$run" ls-tree "$(state "$run" get BASE_SHA)" -- "$f" | awk '{print $1}')" in
      100755|120000) [ "$allow" = "--allow-exec-surface" ] || die "existing executable/symlink at base mode needs --allow-exec-surface: $f";;
    esac
  done < "$run/landed.files"
  while IFS= read -r f || [ -n "$f" ]; do          # PRE-apply: no landed path may already be a symlink
    [ ! -L "$host/$f" ] || die "landed path is a symlink on the host: $f"
  done < "$run/landed.files"
  GITH "$run" apply --check "$run/approved.patch"  # non-mutating pre-flight FIRST — both sides still pristine on failure
  GITREF "$run" apply "$run/approved.patch"        # reference next — disposable
  GITREF "$run" add -N .
  GITREF "$run" status --porcelain --untracked-files=all > "$run/ref.status.before"   # ref-side containment baseline (ref builds)
  GITH "$run" status --porcelain --untracked-files=all > "$run/host.status.before"
  if ! GITH "$run" apply "$run/approved.patch"; then   # host LAST (atomic); if the check→apply race loses,
    GITREF "$run" reset --hard "$(state "$run" get BASE_SHA)" >/dev/null; GITREF "$run" clean -fdx >/dev/null
    die "host apply failed — reference reset, nothing landed"
  fi
  if ! GITH "$run" add -N --pathspec-from-file="$run/landed.files"; then
    # compensation: the cleanliness gate proved these paths were clean — base restore is safe
    while IFS= read -r f || [ -n "$f" ]; do GITH "$run" checkout "$(state "$run" get BASE_SHA)" -- "$f" 2>/dev/null || rm -f -- "$host/$f"; done < "$run/landed.files"
    die "post-apply staging failed — host restored to base"
  fi
  : > "$run/ok.landed"
}

_equality() { # _equality <run> <host.out> <ref.out>
  local run=$1 hostf=$2 reff=$3 f base
  base=$(state "$run" get BASE_SHA)
  : > "$hostf"; : > "$reff"
  while IFS= read -r f || [ -n "$f" ]; do
    GITH "$run" diff --binary --no-ext-diff --no-textconv "$base" -- "$f" >> "$hostf"
    GITREF "$run" diff --binary --no-ext-diff --no-textconv "$base" -- "$f" >> "$reff"
  done < "$run/landed.files"
  diff -q "$hostf" "$reff" >/dev/null
}

cmd_verify() {
  local run=$1 buildok=${3:?usage: verify <run> --build-ok 0|1 [--built-in host|ref]} builtin=host changed bad
  [ "$2" = "--build-ok" ] || die "usage: verify <run> --build-ok 0|1 [--built-in host|ref]"
  case "$buildok" in 0|1) ;; *) die "--build-ok takes 0 or 1, got: $buildok";; esac
  if [ -n "${4:-}" ]; then
    [ "$4" = "--built-in" ] || die "unknown argument: $4"
    case "${5:-}" in host|ref) builtin=$5 ;; *) die "--built-in takes host|ref, got: ${5:-<empty>}";; esac
  fi
  [ -f "$run/ok.landed" ] || die "land stage missing"
  rm -f "$run/ok.build"                            # a failed re-verify must not leave last round's sentinel
  [ "$buildok" = 1 ] || die "build failed — run rollback"
  # A build on a dirty host tree can overwrite the user's pre-existing modified files
  # WITHOUT changing their porcelain status line — containment can't see that. So a
  # dirty tree (beyond the landed set) mandates building in the reference worktree:
  if [ "$builtin" = host ] && sed 's/^...//' "$run/host.status.before" | grep -vFxf "$run/landed.files" | grep -q .; then
    die "host tree has unrelated local changes — build in the reference worktree and pass --built-in ref"
  fi
  GITH "$run" status --porcelain --untracked-files=all > "$run/host.status.after"
  changed=$(diff "$run/host.status.before" "$run/host.status.after" | grep '^[<>]' || true)
  if [ -n "$changed" ]; then
    bad=$(printf '%s\n' "$changed" | sed 's/^[<>] ...//' | grep -vFxf "$run/landed.files" || true)
    [ -z "$bad" ] || die "build touched files outside the landed set: $(printf '%s ' "$bad")"
  fi
  if [ "$builtin" = ref ]; then                    # ref build gets the same containment rule
    GITREF "$run" status --porcelain --untracked-files=all > "$run/ref.status.after"
    changed=$(diff "$run/ref.status.before" "$run/ref.status.after" | grep '^[<>]' || true)
    [ -z "$changed" ] || die "reference-worktree build touched files beyond the approved state: $(printf '%s ' "$changed")"
  fi
  _equality "$run" "$run/host.final.diff" "$run/ref.final.diff" || die "drift from approved delta"
  : > "$run/ok.build"
}

cmd_commit() { # commit <run> <msg> --approved-sha <a> --script-sha <h> [--bypass-hookspath-approved]
  local run=$1 msg=$2 host aprv="" ssha="" bypass=""; local -a flags=()
  shift 2
  while [ $# -gt 0 ]; do case "$1" in
    --approved-sha) aprv=${2:-}; shift 2;; --script-sha) ssha=${2:-}; shift 2;;
    --bypass-hookspath-approved) bypass=yes; shift;; "") shift;; *) die "unknown commit arg: $1";; esac; done
  _verify_self "$ssha"
  [ -f "$run/ok.build" ] || die "verify stage missing"
  host=$(state "$run" get HOST_ROOT)
  [ "$(git -C "$host" rev-parse HEAD)" = "$(state "$run" get BASE_SHA)" ] || die "base moved since landing"
  [ "$(git -C "$host" symbolic-ref -q HEAD || echo detached)" = "$(state "$run" get BASE_REF)" ] || die "branch switched"
  [ "$(hooks_snap "$host")" = "$(state "$run" get HOOKS_SNAP)" ] || die "git hooks changed during the run"
  [ "$(config_snap "$host")" = "$(state "$run" get CONFIG_SNAP)" ] || die "git config/remotes changed during the run"
  [ -n "$aprv" ] || die "commit requires --approved-sha <value printed by approve>"
  [ "$(SHAPIPE < "$run/approved.patch" | cut -d' ' -f1)" = "$aprv" ] || die "approved.patch does not match the approved hash — tampered"
  _equality "$run" "$run/host.final2.diff" "$run/ref.final2.diff" || die "landed files changed since verification"
  if git -C "$host" config core.hooksPath >/dev/null 2>&1; then
    # A configured hooksPath (husky-style) is PR-influenceable — but it may also be the
    # org's legitimate secret-scan/signing hooks. Bypassing is a USER decision, not ours:
    [ "$bypass" = yes ] || die "core.hooksPath is configured — ask the user: bypass it (--bypass-hookspath-approved) or abort"
    flags=(-c core.hooksPath=/dev/null)
  fi
  git -C "$host" --literal-pathspecs ${flags[@]+"${flags[@]}"} add --pathspec-from-file="$run/landed.files"
  git -C "$host" --literal-pathspecs ${flags[@]+"${flags[@]}"} commit -m "$msg" --pathspec-from-file="$run/landed.files"   # ${arr[@]+...}: empty-array expansion aborts under set -u on macOS bash 3.2
  state "$run" set COMMIT_SHA "$(git -C "$host" rev-parse HEAD)"
  # A hook that ran during commit could have mutated content — verify the COMMITTED blobs
  # against the reference worktree before declaring success:
  while IFS= read -r f || [ -n "$f" ]; do
    if [ -e "$(state "$run" get REF_WT)/$f" ]; then
      git -C "$host" show "HEAD:$f" 2>/dev/null | cmp -s - "$(state "$run" get REF_WT)/$f" \
        || die "committed content diverges from the approved state for: $f — a hook modified it; git reset --soft HEAD~1 and investigate"
    fi
  done < "$run/landed.files"
  state "$run" set HOOKS_FLAGS "${flags[*]:-none}"
  : > "$run/ok.committed"
}

cmd_push() { # push <run> --script-sha <h> — separate, idempotent
  local run=$1 host sha flags ssha=""
  [ "${2:-}" = "--script-sha" ] && ssha=${3:-}
  _verify_self "$ssha"
  [ -f "$run/ok.committed" ] || die "commit stage missing"
  host=$(state "$run" get HOST_ROOT); sha=$(state "$run" get COMMIT_SHA)
  [ "$(git -C "$host" rev-parse HEAD)" = "$sha" ] || die "HEAD moved since commit — refusing to push"
  [ "$(git -C "$host" symbolic-ref -q HEAD || echo detached)" = "$(state "$run" get BASE_REF)" ] || die "branch switched since setup — refusing to push"
  [ "$(config_snap "$host")" = "$(state "$run" get CONFIG_SNAP)" ] || die "git config/remotes changed since setup — refusing to push"
  [ "$(hooks_snap "$host")" = "$(state "$run" get HOOKS_SNAP)" ] || die "git hooks changed — refusing to push (pre-push would execute them)"
  local -a pf=(); [ "$(state "$run" get HOOKS_FLAGS)" != none ] && pf=(-c core.hooksPath=/dev/null)
  git -C "$host" ${pf[@]+"${pf[@]}"} push
  : > "$run/ok.pushed"
}

cmd_rollback() { # rollback <run> --sig <s> --script-sha <h> — destructive; same trust roots as cleanup
  local run=$1 host ref base f failed=0 hostmeta refmeta sigv="" ssha=""
  shift
  while [ $# -gt 0 ]; do case "$1" in
    --sig) sigv=${2:-}; shift 2;; --script-sha) ssha=${2:-}; shift 2;; "") shift;; *) die "unknown rollback arg: $1";; esac; done
  _verify_self "$ssha"
  [ -n "$sigv" ] || die "rollback requires --sig <value printed by setup>"
  [ "$(_state_sig "$run")" = "$sigv" ] || die "state signature mismatch — refusing rollback"
  host=$(state "$run" get HOST_ROOT); ref=$(state "$run" get REF_WT); base=$(state "$run" get BASE_SHA)
  if [ "$(git -C "$host" rev-parse HEAD)" != "$base" ]; then
    # One recoverable case: HEAD is OUR commit (recorded sha, parent == base) that
    # post-commit verification rejected — soft-reset it away, then roll back the files.
    if [ "$(git -C "$host" rev-parse HEAD)" = "$(state "$run" get COMMIT_SHA)" ] \
       && [ "$(git -C "$host" rev-parse HEAD~1 2>/dev/null)" = "$base" ]; then
      git -C "$host" -c core.hooksPath=/dev/null reset --soft "$base"
    else
      die "HEAD is not the landing base — a rollback here would target the wrong revision"
    fi
  fi
  [ "$(git -C "$host" symbolic-ref -q HEAD || echo detached)" = "$(state "$run" get BASE_REF)" ] || die "branch switched — refusing rollback"
  [ -d "$ref" ] || die "no reference worktree — cannot verify safe rollback"
  while IFS= read -r f || [ -n "$f" ]; do
    if [ ! -e "$host/$f" ] && [ ! -e "$ref/$f" ]; then     # approved DELETION — restore the base file
      [ ! -L "$host/$f" ] || { echo "SKIP (dangling symlink at path — user artifact, left untouched): $f"; failed=1; continue; }
      GITH "$run" checkout "$base" -- "$f" || die "restore failed: $f"
      continue
    fi
    if ! cmp -s -- "$host/$f" "$ref/$f" 2>/dev/null; then
      echo "SKIP (user-modified since landing — left untouched): $f"; failed=1; continue
    fi
    hostmeta=$([ -L "$host/$f" ] && echo L || ls -ld -- "$host/$f" 2>/dev/null | cut -d' ' -f1)
    refmeta=$([ -L "$ref/$f" ] && echo L || ls -ld -- "$ref/$f" 2>/dev/null | cut -d' ' -f1)
    if [ "$hostmeta" != "$refmeta" ]; then   # same bytes, different type/mode = user chmod/symlink swap
      echo "SKIP (type/mode changed by user — left untouched): $f"; failed=1; continue
    fi
    if GITH "$run" cat-file -e "$base:$f" 2>/dev/null; then
      GITH "$run" checkout "$base" -- "$f" || die "restore failed: $f"
    else
      GITH "$run" rm -q --cached -- "$f" 2>/dev/null || true
      [ ! -L "$host/$f" ] || { echo "SKIP (path became a symlink — left untouched): $f"; failed=1; continue; }
      rm -f -- "$host/$f" || die "delete failed: $f"
    fi
  done < "$run/landed.files"
  # Reset the reference worktree too (it held the approved state) — otherwise the next
  # land()'s GITREF apply hits already-applied content and re-landing is impossible:
  GITREF "$run" reset --hard "$base" >/dev/null
  GITREF "$run" clean -fdx >/dev/null
  rm -f "$run/ref.status.before"
  [ "$failed" = 0 ] || die "partial rollback — user-modified files above were preserved"
}

cmd_cleanup() { # cleanup <run> --sig <setup-sig> [--keep] — sig comes from the HOST's own notes,
                # the one place the implementer cannot write; it re-derives from current state
                # values, so tampering ANY path key breaks it (state self-consistency proves nothing)
  local run=$1 sig="" keep="" host wt refwt
  shift
  local ssha=""
  while [ $# -gt 0 ]; do case "$1" in --sig) sig=$2; shift 2;; --script-sha) ssha=${2:-}; shift 2;; --keep) keep=--keep; shift;; "") shift;; *) die "unknown cleanup arg: $1";; esac; done
  _verify_self "$ssha"
  [ -n "$sig" ] || die "cleanup requires --sig <value printed by setup>"
  [ "$(_state_sig "$run")" = "$sig" ] || die "state signature mismatch — path keys tampered; not removing anything"
  host=$(state "$run" get HOST_ROOT); wt=$(state "$run" get IMPL_WT); refwt=$(state "$run" get REF_WT)
  [ -n "$run" ] && [ -n "$wt" ] || die "state incomplete — refusing cleanup"
  # Exact canonical-path equality, not glob (case '*' matches '/' and '..' — a tampered
  # state value like prefix/../../home would pass a prefix glob):
  [ "$(_canon "$(state "$run" get WT_DIR)")" = "$(state "$run" get CANON_WT_DIR)" ] || die "WT_DIR does not match setup-recorded path — state tampered; not removing"
  [ "$(_canon "$(state "$run" get REF_DIR)")" = "$(state "$run" get CANON_REF_DIR)" ] || die "REF_DIR does not match setup-recorded path — state tampered; not removing"
  [ ! -L "$wt" ] || die "worktree is a symlink — implementer deviated; not removing"
  git -C "$host" worktree remove --force "$wt" 2>/dev/null || true
  git -C "$host" worktree remove --force "$refwt" 2>/dev/null || true
  rm -rf -- "$(state "$run" get WT_DIR)" "$(state "$run" get REF_DIR)"
  [ "$keep" = "--keep" ] || rm -rf -- "$run"
}

case "${1:-}" in
  setup) cmd_setup ;;
  capture) cmd_capture "${2:?run dir}" "${3:-}" "${4:-}" ;;
  approve) cmd_approve "${2:?run dir}" ;;
  check-plan-paths) cmd_check_plan_paths "${2:?run dir}" ;;
  land) cmd_land "${2:?run dir}" "${@:3}" ;;
  verify) cmd_verify "${2:?run dir}" "${3:-}" "${4:-}" "${5:-}" "${6:-}" ;;
  commit) cmd_commit "${2:?run dir}" "${3:?message}" "${@:4}" ;;
  push) cmd_push "${2:?run dir}" "${3:-}" "${4:-}" ;;
  rollback) cmd_rollback "${2:?run dir}" "${@:3}" ;;
  cleanup) cmd_cleanup "${2:?run dir}" "${@:3}" ;;
  *) echo "usage: land_delta.sh setup|capture|approve|check-plan-paths|land|verify|commit|push|rollback|cleanup ..." >&2; exit 2 ;;
esac
