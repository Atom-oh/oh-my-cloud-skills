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
#   commit <run> <message>         final guards + hooks integrity + pathspec commit + push
#   rollback <run>                 revert landed paths, preserving user edits
#   cleanup <run> [--keep]         remove worktrees (+ artifacts unless --keep)
set -euo pipefail

die() { echo "STOP: $*" >&2; exit 1; }
SHAPIPE() { if command -v sha256sum >/dev/null 2>&1; then sha256sum; else shasum -a 256; fi; }

# Execution-surface denylist: files the host executes during build/commit. Edits to these
# require --allow-exec-surface (user-granted). Hook dirs are included — a hook that execs
# a tracked file runs landed code at commit time.
EXEC_SURFACE_RE='^(\.github/|\.husky/|\.git)|(^|/)(package\.json|Makefile|makefile|GNUmakefile|CMakeLists\.txt|build\.rs|pyproject\.toml|Cargo\.toml|.*\.gradle)$'

state() { # state <run> get KEY | state <run> set KEY VALUE
  local run=$1 op=$2 key=$3
  case "$op" in
    get) sed -n "s/^$key=//p" "$run/state" | head -1 ;;
    set) printf '%s=%s\n' "$key" "${4:?}" >> "$run/state" ;;
  esac
}

hooks_snap() { # hooks_snap <host_root>
  local dir
  dir=$(git -C "$1" rev-parse --path-format=absolute --git-path hooks)
  [ -n "$dir" ] || die "cannot resolve hooks dir"
  if [ -d "$dir" ]; then
    ( cd "$dir" && { find . \( -type f -o -type l \) -print0 | sort -z | xargs -0 ls -ld 2>/dev/null
                     find . \( -type f -o -type l \) -print0 | sort -z | xargs -0 cat 2>/dev/null
                   } | SHAPIPE | cut -d' ' -f1 )
  else echo absent; fi
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

GITH() { local run=$1; shift; git -C "$(state "$run" get HOST_ROOT)" -c core.hooksPath=/dev/null --literal-pathspecs "$@"; }
GITWT() { local run=$1; shift; git -C "$(state "$run" get IMPL_WT)" -c core.hooksPath=/dev/null --literal-pathspecs "$@"; }
GITREF() { local run=$1; shift; git -C "$(state "$run" get REF_WT)" -c core.hooksPath=/dev/null --literal-pathspecs "$@"; }

cmd_setup() {
  local run wtd refd host base ref
  host=$(git rev-parse --show-toplevel) || die "not in a git repo"
  base=$(git -C "$host" rev-parse HEAD)
  ref=$(git -C "$host" symbolic-ref -q HEAD || echo detached)
  run=$(mktemp -d "${TMPDIR:-/tmp}/pr-autofix.XXXXXX")
  wtd=$(mktemp -d "${TMPDIR:-/tmp}/pr-autofix-wt.XXXXXX")
  refd=$(mktemp -d "${TMPDIR:-/tmp}/pr-autofix-ref.XXXXXX")
  : > "$run/state"
  state "$run" set HOST_ROOT "$host"; state "$run" set BASE_SHA "$base"; state "$run" set BASE_REF "$ref"
  state "$run" set WT_DIR "$wtd";    state "$run" set REF_DIR "$refd"
  state "$run" set IMPL_WT "$wtd/wt"; state "$run" set REF_WT "$refd/wt"
  state "$run" set HOOKS_SNAP "$(hooks_snap "$host")"
  git -C "$host" -c core.hooksPath=/dev/null worktree add --detach "$wtd/wt" "$base" >/dev/null
  git -C "$host" -c core.hooksPath=/dev/null worktree add --detach "$refd/wt" "$base" >/dev/null
  symlink_scan "$wtd/wt"           # pre-implementer: branch-committed symlinks would leak reads DURING the run
  : > "$run/ok.setup"
  echo "$run"                       # host records this ONE path; everything else lives in state
}

cmd_capture() {
  local run=$1 n
  [ -f "$run/ok.setup" ] || die "setup stage missing"
  gitwt_verify "$run"; symlink_scan "$(state "$run" get IMPL_WT)"
  GITWT "$run" add -N .
  n=1; while [ -e "$run/full.$n.patch" ]; do n=$((n+1)); done   # generations are immutable — re-runs append
  GITWT "$run" diff --binary --no-ext-diff --no-textconv "$(state "$run" get BASE_SHA)" > "$run/full.$n.patch"
  [ -s "$run/full.$n.patch" ] || die "empty capture — implementer produced no delta"
  state "$run" set LATEST_FULL "full.$n.patch"
  : > "$run/ok.captured"
  echo "$run/full.$n.patch"
}

cmd_approve() { # host has already copied+edited approved.patch from the latest generation
  local run=$1
  [ -f "$run/ok.captured" ] || die "capture stage missing"
  [ -s "$run/approved.patch" ] || die "approved.patch missing/empty — copy it from $(state "$run" get LATEST_FULL) and strip unplanned hunks first"
  grep -q '^diff --git' "$run/approved.patch" || die "approved.patch is not a git patch"
  grep -qE '^new file mode 120000|^old mode|^new mode' "$run/approved.patch" \
    && die "approved.patch contains symlink/mode-change hunks — always unplanned unless the user explicitly approved"
  : > "$run/ok.approved"
}

cmd_check_plan_paths() { # paths on stdin, one per line — pre-spawn gate
  local run=$1 p
  while IFS= read -r p || [ -n "$p" ]; do
    case "$p" in
      /*) die "plan path is absolute: $p" ;;
      *..*) die "plan path traverses: $p" ;;
    esac
  done
  echo ok
}

cmd_land() {
  local run=$1 allow=${2:-} host f
  [ -f "$run/ok.approved" ] || die "approve stage missing"
  host=$(state "$run" get HOST_ROOT)
  [ "$(git -C "$host" rev-parse HEAD)" = "$(state "$run" get BASE_SHA)" ] || die "base moved"
  [ "$(git -C "$host" symbolic-ref -q HEAD || echo detached)" = "$(state "$run" get BASE_REF)" ] || die "branch switched"
  GITH "$run" apply --numstat "$run/approved.patch" | cut -f3- > "$run/landed.files"
  [ -s "$run/landed.files" ] || die "approved patch names no files"
  grep -qE '^"|=>' "$run/landed.files" && die "exotic/renamed path in patch — refuse"
  # Execution-surface gate — CODE, not prose (build/commit execute these files):
  if grep -qE "$EXEC_SURFACE_RE" "$run/landed.files" && [ "$allow" != "--allow-exec-surface" ]; then
    die "execution-surface files in the landing set (user approval + --allow-exec-surface required): $(grep -E "$EXEC_SURFACE_RE" "$run/landed.files" | tr '\n' ' ')"
  fi
  while IFS= read -r f || [ -n "$f" ]; do
    [ -z "$(GITH "$run" status --porcelain -- "$f")" ] || die "target file locally modified: $f"
  done < "$run/landed.files"
  GITH "$run" status --porcelain > "$run/host.status.before"
  GITH "$run" apply --check "$run/approved.patch"
  GITH "$run" apply "$run/approved.patch"
  GITH "$run" add -N --pathspec-from-file="$run/landed.files"
  GITREF "$run" apply "$run/approved.patch"       # reference worktree tracks the approved state (rollback + equality baseline)
  GITREF "$run" add -N .
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
  local run=$1 buildok=${3:?usage: verify <run> --build-ok 0|1} changed bad
  [ "$2" = "--build-ok" ] || die "usage: verify <run> --build-ok 0|1"
  [ -f "$run/ok.landed" ] || die "land stage missing"
  [ "$buildok" = 1 ] || die "build failed — run rollback"
  GITH "$run" status --porcelain > "$run/host.status.after"
  changed=$(diff "$run/host.status.before" "$run/host.status.after" | grep '^[<>]' || true)
  if [ -n "$changed" ]; then
    bad=$(printf '%s\n' "$changed" | sed 's/^[<>] ...//' | grep -vFxf "$run/landed.files" || true)
    [ -z "$bad" ] || die "build touched files outside the landed set: $(printf '%s ' $bad)"
  fi
  _equality "$run" "$run/host.final.diff" "$run/ref.final.diff" || die "drift from approved delta"
  : > "$run/ok.build"
}

cmd_commit() {
  local run=$1 msg=$2 host flags=""
  [ -f "$run/ok.build" ] || die "verify stage missing"
  host=$(state "$run" get HOST_ROOT)
  [ "$(git -C "$host" rev-parse HEAD)" = "$(state "$run" get BASE_SHA)" ] || die "base moved since landing"
  [ "$(git -C "$host" symbolic-ref -q HEAD || echo detached)" = "$(state "$run" get BASE_REF)" ] || die "branch switched"
  [ "$(hooks_snap "$host")" = "$(state "$run" get HOOKS_SNAP)" ] || die "git hooks changed during the run"
  _equality "$run" "$run/host.final2.diff" "$run/ref.final2.diff" || die "landed files changed since verification"
  git -C "$host" config core.hooksPath >/dev/null 2>&1 && flags="-c core.hooksPath=/dev/null"
  # configured hooksPath (husky-style) is PR-influenceable even when untracked (v9 wrappers
  # exec tracked files) — disable unconditionally; default untracked .git/hooks stays active.
  git -C "$host" --literal-pathspecs add --pathspec-from-file="$run/landed.files"
  git -C "$host" --literal-pathspecs $flags commit -m "$msg" --pathspec-from-file="$run/landed.files"
  git -C "$host" $flags push
}

cmd_rollback() {
  local run=$1 host ref base f failed=0
  host=$(state "$run" get HOST_ROOT); ref=$(state "$run" get REF_WT); base=$(state "$run" get BASE_SHA)
  [ -d "$ref" ] || die "no reference worktree — cannot verify safe rollback"
  while IFS= read -r f || [ -n "$f" ]; do
    if [ ! -e "$host/$f" ] && [ ! -e "$ref/$f" ]; then     # approved DELETION — restore the base file
      GITH "$run" checkout "$base" -- "$f" || die "restore failed: $f"
      continue
    fi
    if ! cmp -s -- "$host/$f" "$ref/$f" 2>/dev/null; then
      echo "SKIP (user-modified since landing — left untouched): $f"; failed=1; continue
    fi
    if GITH "$run" cat-file -e "$base:$f" 2>/dev/null; then
      GITH "$run" checkout "$base" -- "$f" || die "restore failed: $f"
    else
      GITH "$run" rm -q --cached -- "$f" 2>/dev/null || true
      rm -f -- "$host/$f" || die "delete failed: $f"
    fi
  done < "$run/landed.files"
  [ "$failed" = 0 ] || die "partial rollback — user-modified files above were preserved"
}

cmd_cleanup() {
  local run=$1 keep=${2:-} host wt refwt
  host=$(state "$run" get HOST_ROOT); wt=$(state "$run" get IMPL_WT); refwt=$(state "$run" get REF_WT)
  [ -n "$run" ] && [ -n "$wt" ] || die "state incomplete — refusing cleanup"
  [ ! -L "$wt" ] || die "worktree is a symlink — implementer deviated; not removing"
  git -C "$host" worktree remove --force "$wt" 2>/dev/null || true
  git -C "$host" worktree remove --force "$refwt" 2>/dev/null || true
  rm -rf -- "$(state "$run" get WT_DIR)" "$(state "$run" get REF_DIR)"
  [ "$keep" = "--keep" ] || rm -rf -- "$run"
}

case "${1:-}" in
  setup) cmd_setup ;;
  capture) cmd_capture "${2:?run dir}" ;;
  approve) cmd_approve "${2:?run dir}" ;;
  check-plan-paths) cmd_check_plan_paths "${2:?run dir}" ;;
  land) cmd_land "${2:?run dir}" "${3:-}" ;;
  verify) cmd_verify "${2:?run dir}" "${3:-}" "${4:-}" ;;
  commit) cmd_commit "${2:?run dir}" "${3:?message}" ;;
  rollback) cmd_rollback "${2:?run dir}" ;;
  cleanup) cmd_cleanup "${2:?run dir}" "${3:-}" ;;
  *) echo "usage: land_delta.sh setup|capture|approve|check-plan-paths|land|verify|commit|rollback|cleanup ..." >&2; exit 2 ;;
esac
