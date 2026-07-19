#!/usr/bin/env bash
# Unit tests for the pr-autofix landing pipeline (land_delta.sh).
# Sourced by tests/run-all.sh — uses its assert_* helpers; never calls exit.

LD="plugins/project-init/skills/pr-autofix/scripts/land_delta.sh"
LD_ABS="$(pwd)/$LD"

assert_file_executable "$LD" "land_delta.sh is executable"
LDSHA=$( (sha256sum "$LD_ABS" 2>/dev/null || shasum -a 256 "$LD_ABS") | cut -d' ' -f1 )

_ld_fixture() {  # creates a throwaway repo with one commit; echoes its path
  local d; d=$(mktemp -d "${TMPDIR:-/tmp}/ld-fix.XXXXXX")
  ( cd "$d" && git init -q && git config user.email t@t && git config user.name t \
    && echo hello > a.txt && mkdir -p src && echo 'x=1' > src/app.py \
    && git add -A && git commit -qm init ) >/dev/null
  echo "$d"
}

# --- happy path: setup -> implementer edit -> capture -> approve -> land -> verify -> commit ---
FIX=$(_ld_fixture)
read -r RUN SIG <<<"$( cd "$FIX" && bash "$LD_ABS" setup )" || true
assert_file_exists "$RUN/ok.setup" "setup writes its sentinel"
IMPL_WT=$(sed -n 's/^IMPL_WT=//p' "$RUN/state" | head -1)
echo 'x=2' > "$IMPL_WT/src/app.py"                       # implementer edit (worktree only)
OUT=$( cd "$FIX" && bash "$LD_ABS" capture "$RUN" --sig "$SIG" ) || true
assert_file_exists "$RUN/full.1.patch" "capture writes generation 1"
( cd "$FIX" && git -C . diff --name-only >/dev/null ); printf '%s\n' src/app.py a.txt package.json build.gradle.kts installer .github/workflows/ci.yml | ( cd "$FIX" && bash "$LD_ABS" check-plan-paths "$RUN" ) >/dev/null 2>&1 || true
cp "$RUN/full.1.patch" "$RUN/approved.patch"
APPR=$( cd "$FIX" && bash "$LD_ABS" approve "$RUN" 2>/dev/null ) || true
assert_file_exists "$RUN/ok.approved" "approve writes its sentinel"
( cd "$FIX" && bash "$LD_ABS" land "$RUN" --script-sha "$LDSHA" --sig "$SIG" --approved-sha "$APPR" ) >/dev/null 2>&1 || true
assert_file_exists "$RUN/ok.landed" "land writes its sentinel"
assert_eq "x=2" "$(cat "$FIX/src/app.py")" "approved edit landed on the host"
( cd "$FIX" && bash "$LD_ABS" verify "$RUN" --build-ok 1 ) >/dev/null 2>&1 || true
assert_file_exists "$RUN/ok.build" "verify writes ok.build"
RC=0; ( cd "$FIX" && bash "$LD_ABS" commit "$RUN" "test: landed" --script-sha "$LDSHA" --approved-sha "$APPR" ) >/dev/null 2>&1 || RC=$?
assert_eq "0" "$RC" "commit stage succeeds without pushing"
assert_file_exists "$RUN/ok.committed" "commit writes its sentinel"
assert_eq "test: landed" "$(cd "$FIX" && git log -1 --format=%s)" "pathspec commit landed"
RC=0; ( cd "$FIX" && bash "$LD_ABS" push "$RUN" --script-sha "$LDSHA" ) >/dev/null 2>&1 || RC=$?
[ "$RC" -ne 0 ] && PUSH_FAILED=yes || PUSH_FAILED=no
assert_eq "yes" "$PUSH_FAILED" "push stage fails with no remote (commit preserved, retryable)"
assert_eq "test: landed" "$(cd "$FIX" && git log -1 --format=%s)" "commit survives the failed push"
( cd "$FIX" && bash "$LD_ABS" cleanup "$RUN" --script-sha "$LDSHA" --sig "$SIG" ) >/dev/null 2>&1 || true
rm -rf "$FIX"

# --- stage gating: land without approve must fail ---
FIX=$(_ld_fixture)
read -r RUN SIG <<<"$( cd "$FIX" && bash "$LD_ABS" setup )"
RC=0; ( cd "$FIX" && bash "$LD_ABS" land "$RUN" --script-sha "$LDSHA" --sig "$SIG" --approved-sha "$APPR" ) >/dev/null 2>&1 || RC=$?
assert_eq "1" "$RC" "land without approve stage is blocked"
( cd "$FIX" && bash "$LD_ABS" cleanup "$RUN" --script-sha "$LDSHA" --sig "$SIG" ) >/dev/null 2>&1 || true; rm -rf "$FIX"

# --- cleanliness gate: dirty target file blocks landing ---
FIX=$(_ld_fixture)
read -r RUN SIG <<<"$( cd "$FIX" && bash "$LD_ABS" setup )"
IMPL_WT=$(sed -n 's/^IMPL_WT=//p' "$RUN/state" | head -1)
echo 'x=2' > "$IMPL_WT/src/app.py"
( cd "$FIX" && bash "$LD_ABS" capture "$RUN" --sig "$SIG" ) >/dev/null || true
printf '%s\n' src/app.py a.txt package.json build.gradle.kts installer .github/workflows/ci.yml | ( cd "$FIX" && bash "$LD_ABS" check-plan-paths "$RUN" ) >/dev/null 2>&1 || true
cp "$RUN/full.1.patch" "$RUN/approved.patch"; APPR=$( cd "$FIX" && bash "$LD_ABS" approve "$RUN" 2>/dev/null ) || true
echo 'user-edit' >> "$FIX/src/app.py"                    # user's uncommitted edit on the target
RC=0; ERR=$( cd "$FIX" && bash "$LD_ABS" land "$RUN" --script-sha "$LDSHA" --sig "$SIG" --approved-sha "$APPR" 2>&1 ) || RC=$?
assert_eq "1" "$RC" "dirty target file blocks landing"
assert_contains "$ERR" "locally modified" "cleanliness gate names the reason"
( cd "$FIX" && bash "$LD_ABS" cleanup "$RUN" --script-sha "$LDSHA" --sig "$SIG" ) >/dev/null 2>&1 || true; rm -rf "$FIX"

# --- execution-surface denylist gate ---
FIX=$(_ld_fixture)
( cd "$FIX" && echo '{}' > package.json && git add -A && git commit -qm pkg ) >/dev/null
read -r RUN SIG <<<"$( cd "$FIX" && bash "$LD_ABS" setup )"
IMPL_WT=$(sed -n 's/^IMPL_WT=//p' "$RUN/state" | head -1)
echo '{"scripts":{"build":"evil"}}' > "$IMPL_WT/package.json"
( cd "$FIX" && bash "$LD_ABS" capture "$RUN" --sig "$SIG" ) >/dev/null || true
printf '%s\n' src/app.py a.txt package.json build.gradle.kts installer .github/workflows/ci.yml | ( cd "$FIX" && bash "$LD_ABS" check-plan-paths "$RUN" ) >/dev/null 2>&1 || true
cp "$RUN/full.1.patch" "$RUN/approved.patch"; APPR=$( cd "$FIX" && bash "$LD_ABS" approve "$RUN" 2>/dev/null ) || true
RC=0; ERR=$( cd "$FIX" && bash "$LD_ABS" land "$RUN" --script-sha "$LDSHA" --sig "$SIG" --approved-sha "$APPR" 2>&1 ) || RC=$?
assert_eq "1" "$RC" "execution-surface edit blocked without approval flag"
assert_contains "$ERR" "execution-surface" "denylist gate names the class"
RC=0; ( cd "$FIX" && bash "$LD_ABS" land "$RUN" --script-sha "$LDSHA" --sig "$SIG" --approved-sha "$APPR" --allow-exec-surface ) >/dev/null 2>&1 || RC=$?
assert_eq "0" "$RC" "explicit --allow-exec-surface (user-granted) lands"
( cd "$FIX" && bash "$LD_ABS" cleanup "$RUN" --script-sha "$LDSHA" --sig "$SIG" ) >/dev/null 2>&1 || true; rm -rf "$FIX"

# --- denylist class coverage: *.gradle.kts / vite.config.ts are execution surface ---
FIX=$(_ld_fixture)
( cd "$FIX" && echo 'x' > build.gradle.kts && git add -A && git commit -qm g ) >/dev/null
read -r RUN SIG <<<"$( cd "$FIX" && bash "$LD_ABS" setup )" || true
IMPL_WT=$(sed -n 's/^IMPL_WT=//p' "$RUN/state" | head -1)
echo 'evil' > "$IMPL_WT/build.gradle.kts"
( cd "$FIX" && bash "$LD_ABS" capture "$RUN" --sig "$SIG" ) >/dev/null 2>&1 || true
printf '%s\n' src/app.py a.txt package.json build.gradle.kts installer .github/workflows/ci.yml | ( cd "$FIX" && bash "$LD_ABS" check-plan-paths "$RUN" ) >/dev/null 2>&1 || true
cp "$RUN/full.1.patch" "$RUN/approved.patch"; APPR=$( cd "$FIX" && bash "$LD_ABS" approve "$RUN" 2>/dev/null ) || true
RC=0; ( cd "$FIX" && bash "$LD_ABS" land "$RUN" --script-sha "$LDSHA" --sig "$SIG" --approved-sha "$APPR" ) >/dev/null 2>&1 || RC=$?
assert_eq "1" "$RC" "gradle.kts blocked as execution surface"
( cd "$FIX" && bash "$LD_ABS" cleanup "$RUN" --script-sha "$LDSHA" --sig "$SIG" ) >/dev/null 2>&1 || true; rm -rf "$FIX"

# --- dependency manifest blocked as execution surface ---
FIX=$(_ld_fixture)
( cd "$FIX" && echo 'requests==1.0' > requirements.txt && git add -A && git commit -qm req ) >/dev/null
read -r RUN SIG <<<"$( cd "$FIX" && bash "$LD_ABS" setup )" || true
IMPL_WT=$(sed -n 's/^IMPL_WT=//p' "$RUN/state" | head -1)
echo 'evil==6.6.6' > "$IMPL_WT/requirements.txt"
( cd "$FIX" && bash "$LD_ABS" capture "$RUN" --sig "$SIG" ) >/dev/null 2>&1 || true
printf '%s\n' requirements.txt | ( cd "$FIX" && bash "$LD_ABS" check-plan-paths "$RUN" ) >/dev/null 2>&1 || true
cp "$RUN/full.1.patch" "$RUN/approved.patch"; APPR=$( cd "$FIX" && bash "$LD_ABS" approve "$RUN" 2>/dev/null ) || true
RC=0; ( cd "$FIX" && bash "$LD_ABS" land "$RUN" --script-sha "$LDSHA" --sig "$SIG" --approved-sha "$APPR" ) >/dev/null 2>&1 || RC=$?
assert_eq "1" "$RC" "dependency manifest blocked as execution surface"
( cd "$FIX" && bash "$LD_ABS" cleanup "$RUN" --script-sha "$LDSHA" --sig "$SIG" ) >/dev/null 2>&1 || true; rm -rf "$FIX"

# --- containment guard: build touching files outside the landed set fails verify ---
FIX=$(_ld_fixture)
read -r RUN SIG <<<"$( cd "$FIX" && bash "$LD_ABS" setup )"
IMPL_WT=$(sed -n 's/^IMPL_WT=//p' "$RUN/state" | head -1)
echo 'x=2' > "$IMPL_WT/src/app.py"
( cd "$FIX" && bash "$LD_ABS" capture "$RUN" --sig "$SIG" ) >/dev/null || true
printf '%s\n' src/app.py a.txt package.json build.gradle.kts installer .github/workflows/ci.yml | ( cd "$FIX" && bash "$LD_ABS" check-plan-paths "$RUN" ) >/dev/null 2>&1 || true
cp "$RUN/full.1.patch" "$RUN/approved.patch"; APPR=$( cd "$FIX" && bash "$LD_ABS" approve "$RUN" 2>/dev/null ) || true
( cd "$FIX" && bash "$LD_ABS" land "$RUN" --script-sha "$LDSHA" --sig "$SIG" --approved-sha "$APPR" ) >/dev/null 2>&1 || true
echo 'generated' > "$FIX/a.txt"                          # simulated build side-effect outside landed set
RC=0; ERR=$( cd "$FIX" && bash "$LD_ABS" verify "$RUN" --build-ok 1 2>&1 ) || RC=$?
assert_eq "1" "$RC" "containment guard fires on out-of-set build side effects"
assert_contains "$ERR" "outside the landed set" "containment guard names the violation"
( cd "$FIX" && bash "$LD_ABS" cleanup "$RUN" --script-sha "$LDSHA" --sig "$SIG" ) >/dev/null 2>&1 || true; rm -rf "$FIX"

# --- rollback: reverts pristine landed file, PRESERVES user-modified one ---
FIX=$(_ld_fixture)
read -r RUN SIG <<<"$( cd "$FIX" && bash "$LD_ABS" setup )"
IMPL_WT=$(sed -n 's/^IMPL_WT=//p' "$RUN/state" | head -1)
echo 'x=2' > "$IMPL_WT/src/app.py"; echo 'world' > "$IMPL_WT/a.txt"
( cd "$FIX" && bash "$LD_ABS" capture "$RUN" --sig "$SIG" ) >/dev/null || true
printf '%s\n' src/app.py a.txt package.json build.gradle.kts installer .github/workflows/ci.yml | ( cd "$FIX" && bash "$LD_ABS" check-plan-paths "$RUN" ) >/dev/null 2>&1 || true
cp "$RUN/full.1.patch" "$RUN/approved.patch"; APPR=$( cd "$FIX" && bash "$LD_ABS" approve "$RUN" 2>/dev/null ) || true
( cd "$FIX" && bash "$LD_ABS" land "$RUN" --script-sha "$LDSHA" --sig "$SIG" --approved-sha "$APPR" ) >/dev/null 2>&1 || true
assert_file_exists "$RUN/ok.landed" "prerequisites healthy before rollback test"
echo 'precious user edit' > "$FIX/a.txt"                 # user edits a landed file during the build window
RC=0; OUT=$( cd "$FIX" && bash "$LD_ABS" rollback "$RUN" --script-sha "$LDSHA" --sig "$SIG" 2>&1 ) || RC=$?
assert_eq "1" "$RC" "rollback reports partial (user-modified file present)"
assert_eq "x=1" "$(cat "$FIX/src/app.py")" "pristine landed file reverted to base"
assert_eq "precious user edit" "$(cat "$FIX/a.txt")" "user-modified file preserved, not reverted"
( cd "$FIX" && bash "$LD_ABS" cleanup "$RUN" --script-sha "$LDSHA" --sig "$SIG" ) >/dev/null 2>&1 || true; rm -rf "$FIX"

# --- re-capture invalidates downstream sentinels (stale ok.build cannot be committed) ---
FIX=$(_ld_fixture)
read -r RUN SIG <<<"$( cd "$FIX" && bash "$LD_ABS" setup )" || true
IMPL_WT=$(sed -n 's/^IMPL_WT=//p' "$RUN/state" | head -1)
echo 'x=2' > "$IMPL_WT/src/app.py"
( cd "$FIX" && bash "$LD_ABS" capture "$RUN" --sig "$SIG" ) >/dev/null 2>&1 || true
printf '%s\n' src/app.py a.txt package.json build.gradle.kts installer .github/workflows/ci.yml | ( cd "$FIX" && bash "$LD_ABS" check-plan-paths "$RUN" ) >/dev/null 2>&1 || true
cp "$RUN/full.1.patch" "$RUN/approved.patch"; APPR=$( cd "$FIX" && bash "$LD_ABS" approve "$RUN" 2>/dev/null ) || true
( cd "$FIX" && bash "$LD_ABS" land "$RUN" --script-sha "$LDSHA" --sig "$SIG" --approved-sha "$APPR" ) >/dev/null 2>&1 || true
( cd "$FIX" && bash "$LD_ABS" verify "$RUN" --build-ok 1 ) >/dev/null 2>&1 || true
( cd "$FIX" && bash "$LD_ABS" rollback "$RUN" --script-sha "$LDSHA" --sig "$SIG" ) >/dev/null 2>&1 || true   # host back to base
echo 'x=3' > "$IMPL_WT/src/app.py"
( cd "$FIX" && bash "$LD_ABS" capture "$RUN" --sig "$SIG" ) >/dev/null 2>&1 || true    # generation 2
assert_file_exists "$RUN/full.2.patch" "re-capture after rollback produces generation 2"
RC=0; ( cd "$FIX" && bash "$LD_ABS" commit "$RUN" "stale" --script-sha "$LDSHA" --approved-sha "$APPR" ) >/dev/null 2>&1 || RC=$?
[ "$RC" -ne 0 ] && BLOCKED=yes || BLOCKED=no
assert_eq "yes" "$BLOCKED" "re-capture invalidates stale ok.build (commit blocked)"
( cd "$FIX" && bash "$LD_ABS" cleanup "$RUN" --script-sha "$LDSHA" --sig "$SIG" ) >/dev/null 2>&1 || true; rm -rf "$FIX"

# --- .github/workflows is denied even WITH --allow-exec-surface ---
FIX=$(_ld_fixture)
( cd "$FIX" && mkdir -p .github/workflows && echo 'on: push' > .github/workflows/ci.yml && git add -A && git commit -qm wf ) >/dev/null
read -r RUN SIG <<<"$( cd "$FIX" && bash "$LD_ABS" setup )" || true
IMPL_WT=$(sed -n 's/^IMPL_WT=//p' "$RUN/state" | head -1)
echo 'on: [push, evil]' > "$IMPL_WT/.github/workflows/ci.yml"
( cd "$FIX" && bash "$LD_ABS" capture "$RUN" --sig "$SIG" ) >/dev/null 2>&1 || true
printf '%s\n' src/app.py a.txt package.json build.gradle.kts installer .github/workflows/ci.yml | ( cd "$FIX" && bash "$LD_ABS" check-plan-paths "$RUN" ) >/dev/null 2>&1 || true
cp "$RUN/full.1.patch" "$RUN/approved.patch"; APPR=$( cd "$FIX" && bash "$LD_ABS" approve "$RUN" 2>/dev/null ) || true
RC=0; ( cd "$FIX" && bash "$LD_ABS" land "$RUN" --script-sha "$LDSHA" --sig "$SIG" --approved-sha "$APPR" --allow-exec-surface ) >/dev/null 2>&1 || RC=$?
assert_eq "1" "$RC" "workflow edits hard-denied even with --allow-exec-surface"
( cd "$FIX" && bash "$LD_ABS" cleanup "$RUN" --script-sha "$LDSHA" --sig "$SIG" ) >/dev/null 2>&1 || true; rm -rf "$FIX"

# --- new executable file rejected at approve ---
FIX=$(_ld_fixture)
read -r RUN SIG <<<"$( cd "$FIX" && bash "$LD_ABS" setup )" || true
IMPL_WT=$(sed -n 's/^IMPL_WT=//p' "$RUN/state" | head -1)
printf '#!/bin/sh\necho hi\n' > "$IMPL_WT/installer"; chmod +x "$IMPL_WT/installer"
( cd "$FIX" && bash "$LD_ABS" capture "$RUN" --sig "$SIG" ) >/dev/null 2>&1 || true
cp "$RUN/full.1.patch" "$RUN/approved.patch"
RC=0; APPR=$( cd "$FIX" && bash "$LD_ABS" approve "$RUN" 2>/dev/null ) || RC=$?
assert_eq "1" "$RC" "new executable file rejected at approve"
( cd "$FIX" && bash "$LD_ABS" cleanup "$RUN" --script-sha "$LDSHA" --sig "$SIG" ) >/dev/null 2>&1 || true; rm -rf "$FIX"

# --- rollback resets the reference worktree: a fresh land afterwards succeeds ---
FIX=$(_ld_fixture)
read -r RUN SIG <<<"$( cd "$FIX" && bash "$LD_ABS" setup )" || true
IMPL_WT=$(sed -n 's/^IMPL_WT=//p' "$RUN/state" | head -1)
echo 'x=2' > "$IMPL_WT/src/app.py"
( cd "$FIX" && bash "$LD_ABS" capture "$RUN" --sig "$SIG" ) >/dev/null 2>&1 || true
printf '%s\n' src/app.py a.txt package.json build.gradle.kts installer .github/workflows/ci.yml | ( cd "$FIX" && bash "$LD_ABS" check-plan-paths "$RUN" ) >/dev/null 2>&1 || true
cp "$RUN/full.1.patch" "$RUN/approved.patch"; APPR=$( cd "$FIX" && bash "$LD_ABS" approve "$RUN" 2>/dev/null ) || true
( cd "$FIX" && bash "$LD_ABS" land "$RUN" --script-sha "$LDSHA" --sig "$SIG" --approved-sha "$APPR" ) >/dev/null 2>&1 || true
( cd "$FIX" && bash "$LD_ABS" rollback "$RUN" --script-sha "$LDSHA" --sig "$SIG" ) >/dev/null 2>&1 || true
echo 'x=9' > "$IMPL_WT/src/app.py"
( cd "$FIX" && bash "$LD_ABS" capture "$RUN" --sig "$SIG" ) >/dev/null 2>&1 || true
cp "$RUN/$(sed -n 's/^LATEST_FULL=//p' "$RUN/state" | tail -1)" "$RUN/approved.patch"
APPR=$( cd "$FIX" && bash "$LD_ABS" approve "$RUN" 2>/dev/null ) || true
RC=0; ( cd "$FIX" && bash "$LD_ABS" land "$RUN" --script-sha "$LDSHA" --sig "$SIG" --approved-sha "$APPR" ) >/dev/null 2>&1 || RC=$?
assert_eq "0" "$RC" "re-land after rollback succeeds (reference worktree was reset)"
assert_eq "x=9" "$(cat "$FIX/src/app.py")" "second-generation edit landed"
( cd "$FIX" && bash "$LD_ABS" cleanup "$RUN" --script-sha "$LDSHA" --sig "$SIG" ) >/dev/null 2>&1 || true; rm -rf "$FIX"

# --- tampered approved.patch hunk rejected by the subset check ---
FIX=$(_ld_fixture)
read -r RUN SIG <<<"$( cd "$FIX" && bash "$LD_ABS" setup )" || true
IMPL_WT=$(sed -n 's/^IMPL_WT=//p' "$RUN/state" | head -1)
echo 'x=2' > "$IMPL_WT/src/app.py"
( cd "$FIX" && bash "$LD_ABS" capture "$RUN" --sig "$SIG" ) >/dev/null 2>&1 || true
sed 's/x=2/x=666/' "$RUN/full.1.patch" > "$RUN/approved.patch"      # edited hunk = not a subset
RC=0; APPR=$( cd "$FIX" && bash "$LD_ABS" approve "$RUN" 2>/dev/null ) || RC=$?
assert_eq "1" "$RC" "edited hunk fails the subset check at approve"
( cd "$FIX" && bash "$LD_ABS" cleanup "$RUN" --script-sha "$LDSHA" --sig "$SIG" ) >/dev/null 2>&1 || true; rm -rf "$FIX"

# --- hooks content tampering (same size/mtime) blocks commit ---
FIX=$(_ld_fixture)
mkdir -p "$FIX/.git/hooks"; printf '#!/bin/sh\nexit 0\n' > "$FIX/.git/hooks/pre-commit"; chmod +x "$FIX/.git/hooks/pre-commit"
read -r RUN SIG <<<"$( cd "$FIX" && bash "$LD_ABS" setup )" || true
IMPL_WT=$(sed -n 's/^IMPL_WT=//p' "$RUN/state" | head -1)
echo 'x=2' > "$IMPL_WT/src/app.py"
( cd "$FIX" && bash "$LD_ABS" capture "$RUN" --sig "$SIG" ) >/dev/null 2>&1 || true
printf '%s\n' src/app.py a.txt package.json build.gradle.kts installer .github/workflows/ci.yml | ( cd "$FIX" && bash "$LD_ABS" check-plan-paths "$RUN" ) >/dev/null 2>&1 || true
cp "$RUN/full.1.patch" "$RUN/approved.patch"; APPR=$( cd "$FIX" && bash "$LD_ABS" approve "$RUN" 2>/dev/null ) || true
( cd "$FIX" && bash "$LD_ABS" land "$RUN" --script-sha "$LDSHA" --sig "$SIG" --approved-sha "$APPR" ) >/dev/null 2>&1 || true
( cd "$FIX" && bash "$LD_ABS" verify "$RUN" --build-ok 1 ) >/dev/null 2>&1 || true
assert_file_exists "$RUN/ok.build" "prerequisites healthy before hook tamper"
printf '#!/bin/sh\nexit 1\n' > "$FIX/.git/hooks/pre-commit"          # same size, content changed
touch -r "$RUN/ok.setup" "$FIX/.git/hooks/pre-commit" 2>/dev/null || true
RC=0; ( cd "$FIX" && bash "$LD_ABS" commit "$RUN" "tampered" --script-sha "$LDSHA" --approved-sha "$APPR" ) >/dev/null 2>&1 || RC=$?
[ "$RC" -ne 0 ] && HOOKBLOCK=yes || HOOKBLOCK=no
assert_eq "yes" "$HOOKBLOCK" "content-tampered hook blocks commit (hash covers content, not just metadata)"
( cd "$FIX" && bash "$LD_ABS" cleanup "$RUN" --script-sha "$LDSHA" --sig "$SIG" ) >/dev/null 2>&1 || true; rm -rf "$FIX"

# --- symlink escape gate at setup ---
FIX=$(_ld_fixture)
( cd "$FIX" && ln -s /etc/passwd escape.link && git add -A && git commit -qm link ) >/dev/null
RC=0; ( cd "$FIX" && bash "$LD_ABS" setup ) >/dev/null 2>&1 || RC=$?
assert_eq "1" "$RC" "branch-committed escaping symlink blocks setup"
rm -rf "$FIX"
