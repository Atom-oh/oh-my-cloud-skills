# Test Framework Templates

Templates for the `tests/` directory that `/init-project` generates (Core tier). The suite checks the harness contract: hook scripts and their registration, secret patterns, project structure, version consistency, and CLAUDE.md content. Write each file from its block as shown, then run `bash tests/run-all.sh`. A failure means the generated harness breaks its contract, so fix the generated file, not the test. The exception is content that existed before this run: when a test flags the user's own files, a released CHANGELOG section, or a version file that disagrees with CHANGELOG, leave that content as it is and report the failure as pre-existing in the summary. Never add a CHANGELOG release or bump a version to make a test pass.

---

## Test Runner

Path: `tests/run-all.sh`

```bash
#!/bin/bash
# Test runner for harness engineering tests.
# Usage: bash tests/run-all.sh [test-file-pattern]
# Example: bash tests/run-all.sh          # run all tests
#          bash tests/run-all.sh hooks     # run only hook tests

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

TOTAL=0
PASSED=0
FAILED=0
SKIPPED=0
FAILURES=()

export TEST_RUNNER_ACTIVE=1

pass() {
    TOTAL=$((TOTAL + 1))
    PASSED=$((PASSED + 1))
    echo -e "  ${GREEN}✓${NC} $1"
}

fail() {
    TOTAL=$((TOTAL + 1))
    FAILED=$((FAILED + 1))
    FAILURES+=("$1: $2")
    echo -e "  ${RED}✗${NC} $1"
    echo -e "    ${RED}→ $2${NC}"
}

skip() {
    TOTAL=$((TOTAL + 1))
    SKIPPED=$((SKIPPED + 1))
    echo -e "  ${YELLOW}○${NC} $1 (skipped: $2)"
}

assert_eq() {
    local desc="$1" expected="$2" actual="$3"
    if [ "$expected" = "$actual" ]; then pass "$desc"; else fail "$desc" "expected '$expected', got '$actual'"; fi
}

# A glob match, not `echo | grep -q`: grep -q exits at the first match, and under pipefail the
# writer's SIGPIPE then fails the pipeline at random on long output.
assert_contains() {
    local desc="$1" haystack="$2" needle="$3"
    if [[ "$haystack" == *"$needle"* ]]; then pass "$desc"; else fail "$desc" "output does not contain '$needle'"; fi
}

assert_file_exists() {
    local desc="$1" filepath="$2"
    if [ -f "$filepath" ]; then pass "$desc"; else fail "$desc" "file not found: $filepath"; fi
}

assert_file_executable() {
    local desc="$1" filepath="$2"
    if [ -x "$filepath" ]; then pass "$desc"; else fail "$desc" "file not executable: $filepath"; fi
}

assert_json_valid() {
    local desc="$1" filepath="$2"
    if python3 -m json.tool "$filepath" > /dev/null 2>&1; then pass "$desc"; else fail "$desc" "invalid JSON: $filepath"; fi
}

assert_bash_syntax() {
    local desc="$1" filepath="$2"
    if bash -n "$filepath" 2>/dev/null; then pass "$desc"; else fail "$desc" "bash syntax error in: $filepath"; fi
}

export -f pass fail skip assert_eq assert_contains assert_file_exists
export -f assert_file_executable assert_json_valid assert_bash_syntax

FILTER="${1:-}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Directories under tests/ whose test-*.sh files this runner sources. It sources them into its own
# shell, so list only harness test directories: a project's own shell tests (e2e, integration) may
# call exit or need their own setup, and would end the run early.
TEST_DIRS="hooks structure"

# A sourced test file that calls exit, or an unguarded failure under set -e, ends the run early.
# Report that as a failure, so a Stop gate or CI never reads a truncated run as green.
RUNALL_CURRENT="setup"
RUNALL_FINISHED=0
trap 'runall_rc=$?; if [ "$RUNALL_FINISHED" -eq 0 ]; then echo -e "${RED}run-all.sh stopped early in $RUNALL_CURRENT (exit $runall_rc): a sourced test file exited or hit an unguarded failure${NC}" >&2; exit 1; fi' EXIT

echo -e "${CYAN}=== Harness Test Suite ===${NC}"
echo ""

# One path per line, read on fd 3: paths may contain spaces, and a sourced test that reads stdin
# cannot swallow the rest of the list.
while IFS= read -r test_file <&3; do
    test_name=$(basename "$test_file" .sh)
    if [ -n "$FILTER" ] && ! grep -q -- "$FILTER" <<< "$test_name"; then
        continue
    fi
    RUNALL_CURRENT="$test_name"
    echo -e "${CYAN}▸ $test_name${NC}"
    source "$test_file"
    echo ""
done 3< <(for dir in $TEST_DIRS; do
    [ -d "$SCRIPT_DIR/$dir" ] && find "$SCRIPT_DIR/$dir" -name "test-*.sh"
done | sort)
RUNALL_FINISHED=1

echo -e "${CYAN}=== Results ===${NC}"
echo -e "  Total:   $TOTAL"
echo -e "  ${GREEN}Passed:  $PASSED${NC}"
[ "$FAILED" -gt 0 ] && echo -e "  ${RED}Failed:  $FAILED${NC}" || echo -e "  Failed:  0"
[ "$SKIPPED" -gt 0 ] && echo -e "  ${YELLOW}Skipped: $SKIPPED${NC}" || echo -e "  Skipped: 0"

if [ "$FAILED" -gt 0 ]; then
    echo ""
    echo -e "${RED}=== Failures ===${NC}"
    for f in "${FAILURES[@]}"; do
        echo -e "  ${RED}✗${NC} $f"
    done
    exit 1
fi
echo ""
echo -e "${GREEN}All tests passed.${NC}"
```

Test files are sourced, not run as subprocesses, under `set -euo pipefail`. This has these consequences for every test file:
- Guard any command that may fail, with `|| true`, or with `( ... ) && echo 0 || echo $?` to capture an expected exit code. An unguarded failure aborts the whole run, and the runner reports it as a failure.
- Give a variable to a reader that can stop early (`grep -q`, `awk '... exit'`, `head`) as a here-string (`grep -q x <<< "$VAR"`), not through `printf ... |`. Under pipefail the writer's SIGPIPE fails the pipeline at random, which aborts the run or flips an `if`.
- Never call `exit`: it ends the runner itself, which then reports the run as failed instead of printing results.
- End the file with a command that succeeds, because a failing last command fails the `source`.
- Prefix variables and helper functions per file (`HK_`/`hk_` in the hook tests, `SP_`/`sp_` in the pattern tests), because they persist into later files.

The runner sources only the directories in `TEST_DIRS`. If the project already has shell tests named `test-*.sh` (for example under `tests/e2e/`), keep them out of `TEST_DIRS` and run them the way the project already does; list that in the summary.

---

## Hook Tests

Path: `tests/hooks/test-hooks.sh`

Checks each hook's existence, permissions, and syntax, and its registration contract: gates have nothing after `.sh`, observational hooks end with `2>/dev/null || true`, and every command resolves through `$CLAUDE_PROJECT_DIR`. It also checks the stdin JSON contract, the exit-2 commit gate in throwaway git repos (staged, chained `git add && git commit`, `commit -am`, `git -C`, a quoted `git -c` value, a staged rename, a glob pathspec, `git add -f` of an ignored file from the directory that add runs in, a `cd --` before the commit, a CLAUDE.md despite the `*.md` skip, a tests/fixtures file other than the two samples) and its visible warning when python3 is missing, check-doc-sync's once-per-session note, hooks in a linked worktree, and the commit-msg hook that `scripts/install-hooks.sh` installs. Core hooks must exist. Tests for Optional hooks run only when their script exists.

```bash
#!/bin/bash
# Tests for .claude/hooks/*.sh
# Sourced by run-all.sh under `set -euo pipefail`: every command that may fail is guarded, and
# hooks are called with an argument or explicit stdin so none of them blocks on a read.
# Core hooks must exist; Optional hooks (session-context, notify, verify-on-stop) are tested when present.

HK_ROOT="$PWD"
HK_TMP=$(mktemp -d)

# --- Existence, permissions, syntax ---

for hook in check-doc-sync secret-scan; do
    assert_file_exists "$hook.sh exists" ".claude/hooks/$hook.sh"
done
for hook_file in .claude/hooks/*.sh; do
    [ -f "$hook_file" ] || continue
    assert_file_executable "$(basename "$hook_file") is executable" "$hook_file"
    assert_bash_syntax "$(basename "$hook_file") valid bash" "$hook_file"
done

# --- settings.json registration contract ---

assert_file_exists "settings.json exists" ".claude/settings.json"
assert_json_valid "settings.json is valid JSON" ".claude/settings.json"

# One line per registered command: <event> TAB <matcher> TAB <command>
HK_REGS=$(python3 -c '
import json
hooks = json.load(open(".claude/settings.json")).get("hooks", {})
for event, groups in hooks.items():
    for group in groups:
        for hook in group.get("hooks", []):
            print("%s\t%s\t%s" % (event, group.get("matcher", ""), hook.get("command", "")))
' 2>/dev/null || true)

# hk_check_reg <event> <matcher> <script> <gate|observational>
# A gate must be able to block, so nothing may follow the script path. Every command resolves the
# script through $CLAUDE_PROJECT_DIR, because a relative path exits 127 once Claude cds into a
# subdirectory, and a non-2 exit silently opens a gate.
hk_check_reg() {
    local event="$1" matcher="$2" script="$3" kind="$4" cmd desc
    desc="$event${matcher:+ ($matcher)} runs $script"
    cmd=$(awk -F'\t' -v e="$event" -v m="$matcher" -v s="$script" \
        '$1 == e && $2 == m && index($3, s) { print $3; exit }' <<< "$HK_REGS")
    if [ -z "$cmd" ]; then
        fail "$desc" "no matching registration in .claude/settings.json"
        return 0
    fi
    pass "$desc"
    assert_contains "$script registration resolves via \$CLAUDE_PROJECT_DIR" "$cmd" '"$CLAUDE_PROJECT_DIR"/.claude/hooks/'
    if [ "$kind" = gate ]; then
        if [[ "$cmd" == *"$script" ]]; then
            pass "$script gate registered without || true"
        else
            fail "$script gate registered without || true" "command must end at $script, got: $cmd"
        fi
    elif [[ "$cmd" == *" 2>/dev/null || true" ]]; then
        pass "$script observational registration ends with 2>/dev/null || true"
    else
        fail "$script observational registration ends with 2>/dev/null || true" "got: $cmd"
    fi
}
hk_check_reg PreToolUse Bash secret-scan.sh gate
hk_check_reg PostToolUse "Write|Edit" check-doc-sync.sh observational
if [ -f .claude/hooks/session-context.sh ]; then hk_check_reg SessionStart "" session-context.sh observational; fi
if [ -f .claude/hooks/notify.sh ]; then hk_check_reg Notification "" notify.sh observational; fi
if [ -f .claude/hooks/verify-on-stop.sh ]; then hk_check_reg Stop "" verify-on-stop.sh gate; fi

# --- check-doc-sync.sh: $1 and stdin JSON contract ---

hk_doc_sync() { CLAUDE_PROJECT_DIR="$HK_ROOT" TMPDIR="$HK_TMP" bash .claude/hooks/check-doc-sync.sh "$@" 2>&1 || true; }

OUTPUT=$(hk_doc_sync "")
assert_eq "check-doc-sync: empty path produces no output" "" "$OUTPUT"

# Probe a module that does not exist under the first SOURCE_ROOTS entry
HK_SRC=$(sed -n 's/^SOURCE_ROOTS="\([^" ]*\).*/\1/p' .claude/hooks/check-doc-sync.sh)
HK_SRC="${HK_SRC:-src}"
HK_PROBE="{\"tool_input\":{\"file_path\":\"$HK_SRC/__probe__/x.ts\"},\"session_id\":\"hk-test\"}"
OUTPUT=$(printf '%s' "$HK_PROBE" | hk_doc_sync)
if [ -f "$HK_SRC/CLAUDE.md" ]; then
    assert_eq "check-doc-sync: $HK_SRC/CLAUDE.md covers every module below it" "" "$OUTPUT"
else
    assert_contains "check-doc-sync: reads file_path from stdin JSON" "$OUTPUT" "additionalContext"
    assert_contains "check-doc-sync: names the uncovered module" "$OUTPUT" "$HK_SRC/__probe__/CLAUDE.md is missing"
    HK_JSON_OK=$(printf '%s' "$OUTPUT" | python3 -m json.tool >/dev/null 2>&1 && echo yes || echo no)
    assert_eq "check-doc-sync: output is valid JSON" "yes" "$HK_JSON_OK"
    OUTPUT=$(printf '%s' "$HK_PROBE" | hk_doc_sync)
    assert_eq "check-doc-sync: notes each module once per session" "" "$OUTPUT"
fi

# --- secret-scan.sh: commit gate ---

OUTPUT=$(echo '{"tool_input":{"command":"ls -la"}}' | bash .claude/hooks/secret-scan.sh 2>&1; echo "exit=$?")
assert_eq "secret-scan: non-commit command passes silently with exit 0" "exit=0" "$OUTPUT"

# Sample key built at runtime so this file never matches the scan itself
HK_AWS_ID="AKIA""IOSFODNN7EXAMPLE"

# hk_repo: print the path of a fresh repo whose only commit holds a clean cfg.py.
# It fails loudly rather than fall back to the current directory, which is the real repo.
hk_repo() {
    local dir
    dir=$(mktemp -d "$HK_TMP/repo.XXXXXX") && [ -d "$dir" ] || return 1
    (
        cd "$dir" && git init -q && printf 'x = 1\n' > cfg.py && git add cfg.py &&
            git -c user.name=test -c user.email=test@example.invalid -c commit.gpgsign=false \
                commit -q --no-verify -m init
    ) >/dev/null 2>&1 || true
    printf '%s\n' "$dir"
}
# hk_scan_rc <repo> <command>: exit code of secret-scan.sh for that Bash command, run from <repo>
# (`&& ... || echo $?` keeps the runner's `set -e` from aborting on the expected exit 2)
hk_scan_rc() {
    local json
    json=$(python3 -c 'import json,sys; print(json.dumps({"tool_input": {"command": sys.argv[1]}}))' "$2")
    ( cd "$1" && printf '%s' "$json" | bash "$HK_ROOT/.claude/hooks/secret-scan.sh" >/dev/null 2>&1 ) && echo 0 || echo $?
}

HK_REPO=$(hk_repo)
printf 'key = "%s"\n' "$HK_AWS_ID" > "$HK_REPO/cfg.py"
(cd "$HK_REPO" && git add cfg.py) || true
assert_eq "secret-scan: staged secret blocks commit with exit 2" "2" "$(hk_scan_rc "$HK_REPO" "git commit -m test")"
assert_eq "secret-scan: git -C . commit is gated too" "2" "$(hk_scan_rc "$HK_REPO" "git -C . commit -m x")"

HK_REPO=$(hk_repo)
printf 'key = "%s"\n' "$HK_AWS_ID" > "$HK_REPO/new.py"
assert_eq "secret-scan: chained git add && git commit is scanned" "2" "$(hk_scan_rc "$HK_REPO" "git add new.py && git commit -m x")"

HK_REPO=$(hk_repo)
printf 'key = "%s"\n' "$HK_AWS_ID" > "$HK_REPO/cfg.py"
assert_eq "secret-scan: commit -am scans modified tracked files" "2" "$(hk_scan_rc "$HK_REPO" "git commit -am x")"

HK_REPO=$(hk_repo)
mkdir -p "$HK_REPO/.claude/hooks"
cp .claude/hooks/secret-scan.sh "$HK_REPO/.claude/hooks/secret-scan.sh"
(cd "$HK_REPO" && git add .claude/hooks/secret-scan.sh) || true
assert_eq "secret-scan: its own pattern definitions do not block" "0" "$(hk_scan_rc "$HK_REPO" "git commit -m x")"

hk_commit() { git -c user.name=test -c user.email=test@example.invalid -c commit.gpgsign=false commit -q --no-verify "$@"; }

# renames are scanned (git reports R once the new file is mostly the old one)
HK_REPO=$(hk_repo)
(cd "$HK_REPO" && seq 1 40 > big.py && git add big.py && hk_commit -m big && git mv big.py moved.py &&
    printf 'key = "%s"\n' "$HK_AWS_ID" >> moved.py && git add moved.py) >/dev/null 2>&1 || true
assert_eq "secret-scan: a staged rename that adds a secret blocks" "2" "$(hk_scan_rc "$HK_REPO" "git commit -m x")"
HK_REPO=$(hk_repo)
(cd "$HK_REPO" && git mv cfg.py moved.py) >/dev/null 2>&1 || true
assert_eq "secret-scan: a clean rename passes" "0" "$(hk_scan_rc "$HK_REPO" "git commit -m x")"

# a quoted git option value still counts as a commit
HK_REPO=$(hk_repo)
printf 'key = "%s"\n' "$HK_AWS_ID" > "$HK_REPO/cfg.py"
(cd "$HK_REPO" && git add cfg.py) || true
assert_eq "secret-scan: git -c user.name=\"Claude Code\" commit is gated" "2" \
    "$(hk_scan_rc "$HK_REPO" 'git -c user.name="Claude Code" -c user.email=noreply@anthropic.com commit -m "init"')"

# a glob pathspec is matched by git; git add -f resolves its paths where that add runs; cd options
# (-P, --) are not the directory
HK_REPO=$(hk_repo)
printf 'key = "%s"\n' "$HK_AWS_ID" > "$HK_REPO/cfg.py"
assert_eq "secret-scan: git commit -- '*.py' (a glob) scans the matching files" "2" "$(hk_scan_rc "$HK_REPO" "git commit -m x -- '*.py'")"
HK_REPO=$(hk_repo)
mkdir -p "$HK_REPO/sub"
printf 'sub/.env\n' > "$HK_REPO/.gitignore"
printf 'KEY="%s"\n' "$HK_AWS_ID" > "$HK_REPO/sub/.env"
assert_eq "secret-scan: git -C sub add -f .env && git commit blocks" "2" "$(hk_scan_rc "$HK_REPO" 'git -C sub add -f .env && git commit -m x')"
assert_eq "secret-scan: cd -- sub && git add -f .env && git commit blocks" "2" \
    "$(hk_scan_rc "$HK_REPO" 'cd -- sub && git add -f .env && git commit -m x')"

# CLAUDE.md is scanned despite '*.md'; tests/fixtures is scanned beyond the two sample files
HK_REPO=$(hk_repo)
mkdir -p "$HK_REPO/docs"
printf 'key %s\n' "$HK_AWS_ID" > "$HK_REPO/docs/CLAUDE.md"
(cd "$HK_REPO" && git add docs) || true
assert_eq "secret-scan: a CLAUDE.md with a secret blocks" "2" "$(hk_scan_rc "$HK_REPO" "git commit -m x")"
HK_REPO=$(hk_repo)
mkdir -p "$HK_REPO/tests/fixtures"
printf 'Authorization: %s\n' "$HK_AWS_ID" > "$HK_REPO/tests/fixtures/cassette.yaml"
(cd "$HK_REPO" && git add tests) || true
assert_eq "secret-scan: other files under tests/fixtures are scanned" "2" "$(hk_scan_rc "$HK_REPO" "git commit -m x")"

# without python3 the commit goes through, with a warning the user (systemMessage) and Claude see
HK_REPO=$(hk_repo)
printf 'key = "%s"\n' "$HK_AWS_ID" > "$HK_REPO/cfg.py"
(cd "$HK_REPO" && git add cfg.py) || true
HK_NOPY="$HK_TMP/nopy-bin"
mkdir -p "$HK_NOPY"
for hk_tool in git cat tr; do
    ln -s "$(command -v "$hk_tool")" "$HK_NOPY/$hk_tool" 2>/dev/null || true
done
HK_OUT=$( (cd "$HK_REPO" && printf '%s' '{"tool_input":{"command":"git commit -m x"}}' |
    PATH="$HK_NOPY" "$BASH" "$HK_ROOT/.claude/hooks/secret-scan.sh" 2>/dev/null; echo "exit=$?") || true)
assert_contains "secret-scan: without python3 the commit goes through" "$HK_OUT" "exit=0"
assert_contains "secret-scan: without python3 the warning reaches the user" "$HK_OUT" '"systemMessage"'

# --- Linked worktrees: CLAUDE_PROJECT_DIR stays at the main checkout, the edited path is in the worktree ---

HK_REPO=$(hk_repo)
HK_WT="$HK_REPO/.claude/worktrees/wt1"
(cd "$HK_REPO" && git worktree add -q "$HK_WT") >/dev/null 2>&1 || true
mkdir -p "$HK_WT/$HK_SRC/__probe__"
HK_EVENT=$(python3 -c 'import json,sys; print(json.dumps({"tool_input": {"file_path": sys.argv[1]}}))' "$HK_WT/$HK_SRC/__probe__/x.ts")
OUTPUT=$(printf '%s' "$HK_EVENT" | CLAUDE_PROJECT_DIR="$HK_REPO" TMPDIR="$HK_TMP" bash .claude/hooks/check-doc-sync.sh 2>&1 || true)
assert_contains "check-doc-sync: a worktree edit is checked in that worktree" "$OUTPUT" "$HK_SRC/__probe__/CLAUDE.md is missing"

# --- scripts/install-hooks.sh: the commit-msg hook it installs ---

if [ -f scripts/install-hooks.sh ]; then
    # hk_git_env: only the repo's own config, so a global core.hooksPath cannot redirect the hooks
    hk_git_env() { HOME="$HK_TMP" XDG_CONFIG_HOME="$HK_TMP" GIT_CONFIG_NOSYSTEM=1 "$@"; }
    HK_REPO=$(hk_repo)
    HK_RC=$( (cd "$HK_REPO" && hk_git_env bash "$HK_ROOT/scripts/install-hooks.sh" >/dev/null 2>&1) && echo 0 || echo $?)
    assert_eq "install-hooks: installs the commit-msg hook in a fresh repository" "0" "$HK_RC"
    HK_SED_I=$(grep -v '^[[:space:]]*#' "$HK_REPO/.git/hooks/commit-msg" 2>/dev/null |
        grep -E "sed[[:space:]]+(-[A-Za-z]*[[:space:]]+)*-i([[:space:]\"']|$)" || true)
    assert_eq "install-hooks: commit-msg avoids a bare sed -i, which fails on macOS" "" "$HK_SED_I"
    ( cd "$HK_REPO" && printf 'z\n' > z.txt && git add z.txt &&
        printf 'subject\n\nCo-Authored-By: Claude <noreply@anthropic.com>\n' | hk_git_env git -c user.name=test \
            -c user.email=test@example.invalid -c commit.gpgsign=false commit -q -F - ) >/dev/null 2>&1 || true
    assert_eq "install-hooks: commit-msg keeps the message and removes Co-Authored-By lines" "subject" \
        "$(git -C "$HK_REPO" log -1 --format=%B 2>/dev/null || true)"
    assert_eq "install-hooks: commit-msg runs with /bin/sh, since /bin/bash is missing on some systems" "#!/bin/sh" \
        "$(sed -n 1p "$HK_REPO/.git/hooks/commit-msg" 2>/dev/null || true)"
    HK_RC=$( (cd "$HK_REPO" && hk_git_env bash "$HK_ROOT/scripts/install-hooks.sh" >/dev/null 2>&1) && echo 0 || echo $?)
    assert_eq "install-hooks: a rerun replaces the hook it installed" "0" "$HK_RC"
    printf '#!/bin/sh\n# add Change-Id\nexit 0\n' > "$HK_REPO/.git/hooks/commit-msg" 2>/dev/null || true
    HK_RC=$( (cd "$HK_REPO" && hk_git_env bash "$HK_ROOT/scripts/install-hooks.sh" >/dev/null 2>&1) && echo 0 || echo $?)
    assert_eq "install-hooks: a commit-msg hook it did not install is left alone (exit 1)" "1" "$HK_RC"
fi

# --- Optional hooks ---

if [ -f .claude/hooks/session-context.sh ]; then
    HK_RC=$( (CLAUDE_PROJECT_DIR="$HK_ROOT" bash .claude/hooks/session-context.sh </dev/null >/dev/null 2>&1) && echo 0 || echo $?)
    assert_eq "session-context: exits 0 without reading stdin" "0" "$HK_RC"
    OUTPUT=$(CLAUDE_PROJECT_DIR="$HK_ROOT" bash .claude/hooks/session-context.sh </dev/null 2>&1 || true)
    HK_GIT_LINES=$(echo "$OUTPUT" | grep -E "^(Branch|Last commit|Uncommitted changes):" || true)
    assert_eq "session-context: leaves git state to Claude Code's own context" "" "$HK_GIT_LINES"
fi

if [ -f .claude/hooks/notify.sh ]; then
    OUTPUT=$(CLAUDE_NOTIFY_WEBHOOK="" bash .claude/hooks/notify.sh "test" "msg" 2>&1 || true)
    assert_eq "notify.sh: no webhook URL produces no output" "" "$OUTPUT"
fi

if [ -f .claude/hooks/verify-on-stop.sh ]; then
    # hk_stop_rc <repo> <stdin> <check>: exit code of verify-on-stop.sh with <check> as VERIFY_CMD
    hk_stop_rc() {
        ( cd "$1" && printf '%s' "$2" | CLAUDE_PROJECT_DIR="$1" TMPDIR="$HK_TMP" VERIFY_CMD="$3" \
            bash "$HK_ROOT/.claude/hooks/verify-on-stop.sh" >/dev/null 2>&1 ) && echo 0 || echo $?
    }
    HK_REPO=$(hk_repo)
    assert_eq "verify-on-stop: clean tree skips the check" "0" "$(hk_stop_rc "$HK_REPO" '{}' false)"
    printf 'y = 2\n' > "$HK_REPO/new.py"
    assert_eq "verify-on-stop: failing check on a changed tree blocks with exit 2" "2" "$(hk_stop_rc "$HK_REPO" '{}' false)"
    assert_eq "verify-on-stop: stop_hook_active on an unchanged tree lets the turn end" "0" \
        "$(hk_stop_rc "$HK_REPO" '{"stop_hook_active": true}' false)"
    assert_eq "verify-on-stop: an unchanged red tree is not blocked again" "0" "$(hk_stop_rc "$HK_REPO" '{}' false)"
    printf 'y = 3\n' > "$HK_REPO/new.py"
    assert_eq "verify-on-stop: stop_hook_active after a change runs the check again" "2" \
        "$(hk_stop_rc "$HK_REPO" '{"stop_hook_active": true}' false)"
    printf 'y = 4\n' > "$HK_REPO/new.py"
    assert_eq "verify-on-stop: passing check lets the turn end" "0" "$(hk_stop_rc "$HK_REPO" '{}' true)"
    HK_COUNTED="echo run >> '$HK_TMP/verify-runs'; true"   # a passing check that counts its runs
    hk_stop_rc "$HK_REPO" '{}' "$HK_COUNTED" >/dev/null
    hk_stop_rc "$HK_REPO" '{}' "$HK_COUNTED" >/dev/null
    assert_eq "verify-on-stop: unchanged tree after a green run is skipped" "1" "$( (wc -l < "$HK_TMP/verify-runs") 2>/dev/null | tr -d ' ')"

    # a nested repository (an untracked dir/ entry) does not end the fingerprint early
    HK_REPO=$(hk_repo)
    (cd "$HK_REPO" && mkdir -p vendor/lib && cd vendor/lib && git init -q) >/dev/null 2>&1 || true
    printf 'ok\n' > "$HK_REPO/zz.py"
    assert_eq "verify-on-stop: green run beside a nested repository" "0" "$(hk_stop_rc "$HK_REPO" '{}' 'grep -q ok zz.py')"
    printf 'bad\n' > "$HK_REPO/zz.py"
    assert_eq "verify-on-stop: an untracked file listed after a nested repository counts as a change" "2" \
        "$(hk_stop_rc "$HK_REPO" '{}' 'grep -q ok zz.py')"

    # the event's cwd follows Claude into a linked worktree
    HK_REPO=$(hk_repo)
    HK_WT="$HK_REPO/.claude/worktrees/wt1"
    (cd "$HK_REPO" && git worktree add -q "$HK_WT" && printf '.claude/worktrees/\n' >> .git/info/exclude) >/dev/null 2>&1 || true
    printf 'BROKEN\n' > "$HK_WT/new.py"
    HK_EVENT=$(python3 -c 'import json,sys; print(json.dumps({"cwd": sys.argv[1]}))' "$HK_WT")
    assert_eq "verify-on-stop: a red linked worktree (event cwd) blocks" "2" \
        "$(hk_stop_rc "$HK_REPO" "$HK_EVENT" '! grep -q BROKEN new.py')"

    # A run the hook timeout kills leaves "pending <fingerprint>" in the cache (simulated below): the
    # next Stop on that tree tells the user once, in systemMessage, and does not run the check again
    HK_REPO=$(hk_repo)
    printf 'y = 2\n' > "$HK_REPO/new.py"
    HK_KILL_TMP=$(mktemp -d "$HK_TMP/killed.XXXXXX")
    HK_KILL_CMD="echo run >> '$HK_TMP/killed-runs'; true"
    # hk_stop_out: stdout of verify-on-stop.sh with HK_KILL_CMD as the check, then "exit=<code>"
    hk_stop_out() {
        ( cd "$HK_REPO" && printf '{}' | CLAUDE_PROJECT_DIR="$HK_REPO" TMPDIR="$HK_KILL_TMP" VERIFY_CMD="$HK_KILL_CMD" \
            bash "$HK_ROOT/.claude/hooks/verify-on-stop.sh" 2>/dev/null; echo "exit=$?" ) || true
    }
    hk_stop_out >/dev/null
    for hk_f in "$HK_KILL_TMP"/claude-verify-on-stop-*; do
        if [ -f "$hk_f" ]; then printf 'pending %s\n' "$(cat "$hk_f")" > "$hk_f"; fi
    done
    rm -f "$HK_TMP/killed-runs"
    HK_OUT=$(hk_stop_out)
    HK_MSG=$(printf '%s' "${HK_OUT%exit=*}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["systemMessage"])' 2>/dev/null || echo "no JSON systemMessage")
    assert_contains "verify-on-stop: a killed run is reported to the user" "$HK_MSG" "did not finish"
    assert_contains "verify-on-stop: a killed run lets the turn end" "$HK_OUT" "exit=0"
    assert_eq "verify-on-stop: a killed run is not rerun on the same tree" "no" "$([ -f "$HK_TMP/killed-runs" ] && echo yes || echo no)"
    assert_eq "verify-on-stop: a killed run is reported once" "exit=0" "$(hk_stop_out)"
fi

rm -rf -- "$HK_TMP"   # -f: git objects are read-only, and rm would prompt on a terminal
```

If a project covers its whole source root with one `CLAUDE.md` (for example `src/CLAUDE.md`), the check-doc-sync probe expects silence instead of a note.

---

## Secret Pattern Tests

Path: `tests/hooks/test-secret-patterns.sh`

Reads the `PATTERNS` array from `.claude/hooks/secret-scan.sh` and matches it with Python `re`, the engine the hook uses, so the patterns live in one place. Every pattern must compile and have at least one true-positive sample, so a custom pattern added to the hook needs a sample here.

**Important:** Construct sensitive-looking tokens at runtime via string concatenation to avoid triggering GitHub Push Protection.

```bash
#!/bin/bash
# Tests for the secret patterns in .claude/hooks/secret-scan.sh
# Validates true positives (must detect) and false positives (must not detect).
#
# The hook's PATTERNS array is the single source: it is read from the hook and matched with
# python3 `re`, the engine the hook uses, so a pattern that works only under grep -P fails here.
#
# Note: Some test tokens are constructed at runtime via string concatenation
# to avoid triggering GitHub Push Protection on this test file.

FIXTURES="tests/fixtures"
SP_HOOK=".claude/hooks/secret-scan.sh"

# A child bash evaluates only the array definition, so quoting and comments parse exactly as in the hook.
SP_PATTERNS=()
while IFS= read -r sp_line; do
    SP_PATTERNS+=("$sp_line")
done < <(bash -c "$(sed -n '/^PATTERNS=(/,/^)/p' "$SP_HOOK")"'
printf "%s\n" "${PATTERNS[@]}"' 2>/dev/null || true)

if [ "${#SP_PATTERNS[@]}" -gt 0 ]; then
    pass "PATTERNS read from $SP_HOOK (${#SP_PATTERNS[@]} patterns)"
else
    fail "PATTERNS read from $SP_HOOK" "no PATTERNS=( ... ) array found"
    SP_PATTERNS=('a^')   # never matches; keeps the checks below running under set -u
fi

SP_BAD=$(python3 -c '
import re, sys
for pattern in sys.argv[1:]:
    try:
        re.compile(pattern)
    except re.error as err:
        print("%s (%s)" % (pattern, err))
' "${SP_PATTERNS[@]}" 2>&1 || true)
assert_eq "Every PATTERNS entry compiles with python3 re" "" "$SP_BAD"

# sp_match <text>: print the first hook pattern that matches <text>, or nothing
sp_match() {
    printf '%s' "$1" | python3 -c '
import re, sys
text = sys.stdin.read()
for pattern in sys.argv[1:]:
    try:
        if re.search(pattern, text):
            print(pattern)
            break
    except re.error:
        pass
' "${SP_PATTERNS[@]}" 2>/dev/null || true
}
SP_TP_SAMPLES=()
sp_detects() {
    local hit
    SP_TP_SAMPLES+=("$2")
    hit=$(sp_match "$2")
    if [ -n "$hit" ]; then pass "$1"; else fail "$1" "no secret-scan.sh pattern matched"; fi
}
sp_ignores() {
    local hit
    hit=$(sp_match "$2")
    if [ -z "$hit" ]; then pass "$1"; else fail "$1" "matched pattern '$hit' (expected no match)"; fi
}

# --- True Positive Tests ---

sp_detects "TP: AWS Access Key ID" "AKIAIOSFODNN7EXAMPLE"
sp_detects "TP: GitHub PAT" "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij"
sp_detects "TP: GitHub OAuth Token" "gho_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij"
sp_detects "TP: Azure Connection String" "DefaultEndpointsProtocol=https;AccountName=myaccount"
sp_detects "TP: Password assignment" 'password = "mysecretpassword123"'
sp_detects "TP: API key assignment" 'api_key = "sk_abcdefghijklmnop"'

# Runtime-constructed tokens (avoid GitHub Push Protection)
# Google API Key
GAPI_PREFIX="AIza"
GAPI_BODY="SyABCDEFGHIJKLMNOPQRSTUVWXYZ1234567"
sp_detects "TP: Google API Key" "${GAPI_PREFIX}${GAPI_BODY}"

# Slack Bot / User Token
SLACK_PREFIX="xoxb-"
SLACK_USER_PREFIX="xoxp-"
SLACK_BODY="123456789012-1234567890123-abcdef"
sp_detects "TP: Slack Bot Token" "${SLACK_PREFIX}${SLACK_BODY}"
sp_detects "TP: Slack User Token" "${SLACK_USER_PREFIX}${SLACK_BODY}"

# Stripe Secret / Restricted Key
STRIPE_PREFIX="sk_live_"
STRIPE_RK_PREFIX="rk_live_"
STRIPE_BODY="ABCDEFGHIJKLMNOPQRSTUVWX"
sp_detects "TP: Stripe Secret Key" "${STRIPE_PREFIX}${STRIPE_BODY}"
sp_detects "TP: Stripe Restricted Key" "${STRIPE_RK_PREFIX}${STRIPE_BODY}"

# AWS Secret Access Key (AWS documentation example value) in ini, .env, and JSON form
SP_AWS_NAME="aws_secret_access""_key"
SP_AWS_SECRET="wJalrXUtnFEMI/K7MDENG/""bPxRfiCYEXAMPLEKEY"
sp_detects "TP: AWS Secret Key (ini)" "${SP_AWS_NAME} = ${SP_AWS_SECRET}"
sp_detects "TP: AWS Secret Key (.env, upper case)" "$(printf '%s' "$SP_AWS_NAME" | tr 'a-z' 'A-Z')=${SP_AWS_SECRET}"
sp_detects "TP: AWS Secret Key (JSON)" "\"${SP_AWS_NAME}\": \"${SP_AWS_SECRET}\""

# OpenAI, GitHub fine-grained PAT, Google OAuth, generic secret assignment
SP_ALNUM20="ABCDEFGHIJKLMNOPQRST"
sp_detects "TP: OpenAI API Key" "sk-${SP_ALNUM20}T3Blbk""FJ${SP_ALNUM20}"
sp_detects "TP: GitHub Fine-grained PAT" "github_pat_$(printf 'A%.0s' {1..82})"
sp_detects "TP: Google OAuth Token" "ya29.$(printf 'b%.0s' {1..50})"
sp_detects "TP: Secret assignment" "secret = \"hunter2""hunter2\""

# Anthropic and current OpenAI keys have base64url bodies, so `_` and `-` appear anywhere
SP_B64URL=$(printf 'aB3_x-Y9%.0s' {1..12})
sp_detects "TP: Anthropic API Key (base64url body)" "sk-ant-""api03-${SP_B64URL}AA"
sp_detects "TP: OpenAI project key" "sk-""proj-${SP_B64URL}"
sp_detects "TP: OpenAI service account key" "sk-""svcacct-${SP_B64URL}"
sp_detects "TP: OpenAI admin key" "sk-""admin-${SP_B64URL}"

# Private keys (PEM, OpenSSH, and PGP headers)
SP_PEM_BEGIN="-----BEGIN"
SP_PEM_KEY="PRIVATE ""KEY-----"
sp_detects "TP: PKCS#8 private key" "${SP_PEM_BEGIN} ${SP_PEM_KEY}"
sp_detects "TP: RSA private key" "${SP_PEM_BEGIN} RSA ${SP_PEM_KEY}"
sp_detects "TP: OpenSSH private key" "${SP_PEM_BEGIN} OPENSSH ${SP_PEM_KEY}"
sp_detects "TP: EC private key" "${SP_PEM_BEGIN} EC ${SP_PEM_KEY}"
sp_detects "TP: PGP private key block" "${SP_PEM_BEGIN} PGP PRIVATE ""KEY BLOCK-----"

# Quoted password, secret, and API key assignments in any case, in JSON, and in longer names
SP_PW="hunter2""hunter2"
sp_detects "TP: Password in JSON" "{\"password\": \"${SP_PW}\"}"
sp_detects "TP: Password, upper-case name" "PASSWORD=\"${SP_PW}\""
sp_detects "TP: Password, prefixed name" "DB_PASSWORD: '${SP_PW}'"
sp_detects "TP: Password with spaces" 'password = "correct horse battery"'
sp_detects "TP: Django SECRET_KEY" "SECRET_KEY = 'django-insecure-9f8a7s6d5f4g'"
sp_detects "TP: camelCase clientSecret" "clientSecret: \"${SP_PW}\""
sp_detects "TP: API key in JSON" '"api_key": "abcdefghijklmnop"'
sp_detects "TP: camelCase apiKey" "apiKey: 'abcdefghijklmnop'"

# Every hook pattern must be exercised by at least one sample above, so a new pattern needs a TP.
SP_UNTESTED=$(python3 -c '
import re, sys
patterns, samples = sys.argv[1].split("\n"), sys.argv[2].split("\n")
for pattern in patterns:
    try:
        rule = re.compile(pattern)
    except re.error:
        continue
    if not any(rule.search(sample) for sample in samples):
        print(pattern)
' "$(printf '%s\n' "${SP_PATTERNS[@]}")" "$(printf '%s\n' "${SP_TP_SAMPLES[@]}")" 2>&1 || true)
assert_eq "Every PATTERNS entry has a true-positive sample" "" "$SP_UNTESTED"

# --- False Positive Tests ---

sp_ignores "FP: Normal base64 not a secret" "dGhpcyBpcyBhIHRlc3QgYmFzZTY0IHN0cmluZw=="
sp_ignores "FP: SHA256 hash not a secret" "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
sp_ignores "FP: Git commit hash not a token" "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0"
sp_ignores "FP: URL path not a secret" "https://api.example.com/v1/users/profile"
sp_ignores "FP: Empty password not detected" 'password = ""'
sp_ignores "FP: Short API key not detected" 'api_key = "short"'
sp_ignores "FP: Version string not a secret" "VERSION=1.0.0-alpha.1+build.123"
sp_ignores "FP: PEM header not a secret" "-----BEGIN CERTIFICATE-----"
sp_ignores "FP: AWS secret read from the environment" "${SP_AWS_NAME} = \${AWS_SECRET_ACCESS_KEY}"
sp_ignores "FP: 40-char base64 without a key name" "value = ${SP_AWS_SECRET}"
sp_ignores "FP: PEM public key header" "${SP_PEM_BEGIN} PUBLIC KEY-----"
sp_ignores "FP: PGP public key block" "${SP_PEM_BEGIN} PGP PUBLIC KEY BLOCK-----"
sp_ignores "FP: Short OpenAI-style prefix" "sk-proj-short"
# A value that starts with $ % { < is a reference or placeholder, not a literal
sp_ignores "FP: Password from an environment variable" 'password: "${DB_PASSWORD}"'
sp_ignores "FP: Helm template value" 'secret: "{{ .Values.secret }}"'
sp_ignores "FP: Python %-format placeholder" 'password = "%(db_password)s"'
sp_ignores "FP: Angle-bracket placeholder" 'api_key = "<your-api-key-here>"'
sp_ignores "FP: Password read from os.environ" 'password = os.environ["DB_PASSWORD"]'
sp_ignores "FP: Name that only starts with SECRET" 'SECRET_NAME = "my-app-secret-name"'

# --- Bulk scan: fixture files (non-comment, non-blank lines) ---

# sp_count_lines <file>: print "<lines matching any hook pattern> <lines>"
sp_count_lines() {
    python3 -c '
import re, sys
rules = []
for pattern in sys.argv[2:]:
    try:
        rules.append(re.compile(pattern))
    except re.error:
        pass
with open(sys.argv[1], encoding="utf-8") as handle:
    lines = [line for line in handle.read().splitlines() if line.strip() and not line.startswith("#")]
print(sum(1 for line in lines if any(rule.search(line) for rule in rules)), len(lines))
' "$1" "${SP_PATTERNS[@]}" 2>/dev/null || echo "0 0"
}

TP_FILE="$FIXTURES/secret-samples.txt"
if [ -f "$TP_FILE" ]; then
    read -r TP_DETECTED TP_TOTAL <<< "$(sp_count_lines "$TP_FILE")"
    if [ "$TP_DETECTED" -ge 6 ]; then
        pass "Bulk TP: detected $TP_DETECTED/$TP_TOTAL secrets in fixture file (threshold: >=6)"
    else
        fail "Bulk TP: detected $TP_DETECTED/$TP_TOTAL secrets in fixture file" "expected at least 6"
    fi
else
    skip "Bulk TP test" "fixtures file not found"
fi

FP_FILE="$FIXTURES/false-positives.txt"
if [ -f "$FP_FILE" ]; then
    read -r FP_DETECTED FP_TOTAL <<< "$(sp_count_lines "$FP_FILE")"
    if [ "$FP_DETECTED" -le 1 ]; then
        pass "Bulk FP: $FP_DETECTED/$FP_TOTAL false positives (threshold: <=1)"
    else
        fail "Bulk FP: $FP_DETECTED/$FP_TOTAL false positives" "expected at most 1"
    fi
else
    skip "Bulk FP test" "fixtures file not found"
fi
```

### Test Fixture Files

Avoid placing full tokens in fixture files; use comments for tokens that must be constructed at runtime. The hook's `SKIP_PATTERNS` names these two files exactly, so anything else under `tests/fixtures/` (recorded HTTP responses, config fixtures) is still scanned.

Path: `tests/fixtures/secret-samples.txt` (true positives)

```text
# True Positives - these MUST be detected
# Note: Some tokens are intentionally shortened or split to avoid GitHub Push Protection.
# Full-length tokens are constructed at runtime in test-secret-patterns.sh.

# AWS Access Key ID
TP_AWS_KEY=AKIAIOSFODNN7EXAMPLE
# AWS Secret Access Key — constructed at runtime in test-secret-patterns.sh
# Anthropic API Key
TP_ANTHROPIC=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# GitHub PAT (ghp_ + 36 chars)
TP_GITHUB_PAT=ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij
# GitHub OAuth (gho_ + 36 chars)
TP_GITHUB_OAUTH=gho_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij
# Google API Key (AIza + 35 chars) — constructed at runtime to avoid GitHub scanning
# Azure Connection String
TP_AZURE=DefaultEndpointsProtocol=https;AccountName=myaccount;AccountKey=abc123
# Password assignment
TP_PASSWORD=password = "mysecretpassword123"
# API key assignment
TP_APIKEY=api_key = "sk_abcdefghijklmnop"
# Password in JSON
TP_PASSWORD_JSON={"password": "mysecretpassword123"}
# Secret key with an upper-case name (Django settings)
TP_DJANGO=SECRET_KEY = 'django-insecure-9f8a7s6d5f4g'
# Private keys and current OpenAI / Anthropic formats — constructed at runtime in test-secret-patterns.sh
```

Path: `tests/fixtures/false-positives.txt` (must not trigger)

```text
# False Positives - these must NOT be detected
# Normal base64 encoded config (40 chars)
CONFIG_VALUE=dGhpcyBpcyBhIHRlc3QgYmFzZTY0IHN0cmluZw==
# PEM certificate header
-----BEGIN CERTIFICATE-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA
-----END CERTIFICATE-----
# Normal hash values
SHA256=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
# Git commit hash
COMMIT=a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0
# Package version strings
VERSION=1.0.0-alpha.1+build.123
# Normal URL with path
URL=https://api.example.com/v1/users/profile
# Comment about passwords
# The password field must be at least 8 characters
# Empty password value
password = ""
# Short API key (less than 8 chars)
api_key = "short"
# AWS secret key read from the environment or left as a placeholder
aws_secret_access_key = ${AWS_SECRET_ACCESS_KEY}
aws_secret_access_key = <your-secret-access-key>
# Passwords, secrets, and API keys that reference a variable, template, or placeholder
password: "${DB_PASSWORD}"
secret: "{{ .Values.secret }}"
password = "%(db_password)s"
api_key = "<your-api-key-here>"
# PEM public key header
-----BEGIN PUBLIC KEY-----
```

---

## Structure Tests

Path: `tests/structure/test-plugin-structure.sh`

Checks the Core files, scripts, the frontmatter of every generated command, version consistency, and the CLAUDE.md sections. Uncomment the version-consistency block only when the project has a version file, and point it at that file; otherwise leave it commented.

```bash
#!/bin/bash
# Tests for project structure: settings, Core files, scripts, commands, CLAUDE.md sections

# --- Settings and Core files ---
assert_json_valid "settings.json is valid JSON" ".claude/settings.json"
assert_json_valid ".mcp.json is valid JSON" ".mcp.json"
for core_file in CLAUDE.md README.md CHANGELOG.md docs/architecture.md docs/onboarding.md \
    docs/decisions/.template.md docs/runbooks/.template.md .env.example .editorconfig .gitignore; do
    assert_file_exists "$core_file exists" "$core_file"
done

# --- Scripts ---
for script in scripts/setup.sh scripts/install-hooks.sh; do
    assert_file_executable "$script is executable" "$script"
    assert_bash_syntax "$script valid bash" "$script"
done

# --- Command frontmatter (every generated command; /review, /test-all, /deploy depend on the tier choice) ---
for cmd_file in .claude/commands/*.md; do
    [ -f "$cmd_file" ] || continue
    CMD_CONTENT=$(cat "$cmd_file")
    assert_contains "$(basename "$cmd_file"): has description" "$CMD_CONTENT" "description:"
    assert_contains "$(basename "$cmd_file"): has allowed-tools" "$CMD_CONTENT" "allowed-tools:"
done

# --- Version consistency: uncomment when the project has a version file (package.json,
# pyproject.toml, Cargo.toml, ...), and point PROJECT_VER at it. It skips until CHANGELOG has a
# release, and a mismatch is reported, never fixed by adding a release or bumping a version. ---
# PROJECT_VER=$(python3 -c "import json; print(json.load(open('package.json'))['version'])" 2>/dev/null || echo "missing")
# CHANGELOG_VER=$(python3 -c "
# import re
# m = re.search(r'^## \[(\d+\.\d+\.\d+)\]', open('CHANGELOG.md', encoding='utf-8').read(), re.M)
# print(m.group(1) if m else 'missing')" 2>/dev/null || echo "missing")
# if [ "$PROJECT_VER" = "missing" ] || [ "$CHANGELOG_VER" = "missing" ]; then
#     skip "Version sync: latest CHANGELOG release matches package.json" "no version file or no CHANGELOG release yet"
# else
#     assert_eq "Version sync: latest CHANGELOG release matches package.json" "$PROJECT_VER" "$CHANGELOG_VER"
# fi

# --- CLAUDE.md content (grep -F: fixed strings) ---
for section in "Overview" "Tech Stack" "Project Structure" "Conventions" "Key Commands" "Auto-Sync Rules"; do
    if grep -qF "## $section" CLAUDE.md; then
        pass "CLAUDE.md: has $section"
    else
        fail "CLAUDE.md: has $section" "section '## $section' not found in CLAUDE.md"
    fi
done
```

For a plugin marketplace project, also compare `.claude-plugin/marketplace.json` (`metadata.version` and each `plugins[].version`) with `plugins/<name>/.claude-plugin/plugin.json`.

---

## Test Directory Structure

```text
tests/
├── run-all.sh                    # Test runner with assertions; sources the TEST_DIRS below
├── hooks/
│   ├── test-hooks.sh             # Hook existence, registration contract, behavior
│   └── test-secret-patterns.sh   # Secret detection TP/FP tests against the hook's PATTERNS
├── structure/
│   └── test-plugin-structure.sh  # Core files, commands, versions, CLAUDE.md sections
└── fixtures/
    ├── secret-samples.txt        # True positive samples
    └── false-positives.txt       # False positive samples (must not trigger)
```

### Adding New Tests

1. Create `tests/<category>/test-<name>.sh`. For a new `<category>` directory, add it to `TEST_DIRS` in `run-all.sh`, which sources only the directories listed there.
2. Use the runner's assertion functions: `pass`, `fail`, `skip`, `assert_eq`, `assert_contains`, `assert_file_exists`, `assert_file_executable`, `assert_json_valid`, `assert_bash_syntax`.
3. Run `bash tests/run-all.sh <name>` to run only that file.
