#!/usr/bin/env bash
# Tests for co-agent check_ai_context.py — validator/staleness checker for the
# distilled AI context file (AGENTS.md) generated from CLAUDE.md.

SCRIPT="plugins/co-agent/skills/co-agent/scripts/check_ai_context.py"
CMD="plugins/co-agent/commands/sync-context.md"
KIRO_BRIDGE=".kiro/steering/project-context.md"

assert_file_exists "$SCRIPT" "co-agent check_ai_context.py exists"
assert_file_executable "$SCRIPT" "check_ai_context.py is executable"
assert_file_exists "$CMD" "sync-context command exists"
CMD_BODY=$(cat "$CMD" 2>/dev/null)
assert_contains "$CMD_BODY" ".kiro/steering/project-context.md" "sync-context documents Kiro steering bridge"
assert_grep_match "#\\[\\[file:AGENTS\\.md\\]\\]" "$CMD_BODY" "sync-context references AGENTS.md from Kiro steering (shared with Codex/Agy, not a separate CLAUDE.md copy)"
assert_grep_no_match "GEMINI\\.md" "$CMD_BODY" "sync-context no longer targets GEMINI.md"
assert_file_exists "$KIRO_BRIDGE" "repo Kiro steering bridge exists"
assert_grep_match "#\\[\\[file:AGENTS\\.md\\]\\]" "$(cat "$KIRO_BRIDGE" 2>/dev/null)" "repo Kiro steering bridge references AGENTS.md"

# Scratch project with a minimal CLAUDE.md. run-all.sh sources this under `set -e`, so any
# assert/command below that returns non-zero aborts the whole test run immediately — trap
# EXIT rather than relying on the rm -rf at the bottom of this file to ever be reached.
CTX_DIR=$(mktemp -d "${TMPDIR:-/tmp}/coagentctx.XXXXXX")
trap 'rm -rf "$CTX_DIR"' EXIT
printf '# Project\nUse python3. Run tests with bash tests/run-all.sh.\n' > "$CTX_DIR/CLAUDE.md"

# --emit-marker prints a marker carrying the CLAUDE.md sha
MARKER=$(python3 "$SCRIPT" "$CTX_DIR" --emit-marker)
assert_contains "$MARKER" "generated-by: co-agent" "emit-marker includes co-agent marker"
assert_contains "$MARKER" "claude-md-sha:" "emit-marker includes claude-md-sha"

# No AI files yet → in sync (files are optional), exit 0
python3 "$SCRIPT" "$CTX_DIR" >/dev/null 2>&1
assert_eq "0" "$?" "no AI files → exit 0 (nothing to sync)"

# In-sync generated file (correct sha) → exit 0
printf '%s\n# Codex context\n' "$MARKER" > "$CTX_DIR/AGENTS.md"
python3 "$SCRIPT" "$CTX_DIR" >/dev/null 2>&1
assert_eq "0" "$?" "in-sync AGENTS.md → exit 0"

# Legacy generated GEMINI.md is ignored; sync-context now manages AGENTS.md only.
printf '<!-- generated-by: co-agent · claude-md-sha: 000000000000 -->\n# old gemini context\n' > "$CTX_DIR/GEMINI.md"
GEMINI_OUT=$(python3 "$SCRIPT" "$CTX_DIR" 2>&1) && GEMINI_RC=0 || GEMINI_RC=$?
assert_eq "0" "$GEMINI_RC" "legacy GEMINI.md → ignored"
assert_grep_no_match "GEMINI\\.md: STALE" "$GEMINI_OUT" "legacy GEMINI.md → no stale warning"

# Stale marker (wrong sha) → exit 1 + STALE message
# (capture with the `&& rc=0 || rc=$?` idiom so set -e in the runner doesn't abort)
printf '<!-- generated-by: co-agent · claude-md-sha: 000000000000 -->\n# old\n' > "$CTX_DIR/AGENTS.md"
STALE_OUT=$(python3 "$SCRIPT" "$CTX_DIR" 2>&1) && STALE_RC=0 || STALE_RC=$?
assert_eq "1" "$STALE_RC" "stale AGENTS.md → exit 1"
assert_contains "$STALE_OUT" "STALE" "stale AGENTS.md → STALE message"

# Secret in generated file → exit 1 + secret warning
printf '%s\nAKIAIOSFODNN7EXAMPLE\n' "$MARKER" > "$CTX_DIR/AGENTS.md"
SECRET_OUT=$(python3 "$SCRIPT" "$CTX_DIR" 2>&1) && SECRET_RC=0 || SECRET_RC=$?
assert_eq "1" "$SECRET_RC" "secret in AGENTS.md → exit 1"
assert_contains "$SECRET_OUT" "secret" "secret in AGENTS.md → secret warning"

# Hand-written file (no co-agent marker) → left alone, exit 0
printf '# My own AGENTS.md\nNo marker here.\n' > "$CTX_DIR/AGENTS.md"
HAND_OUT=$(python3 "$SCRIPT" "$CTX_DIR" 2>&1) && HAND_RC=0 || HAND_RC=$?
assert_eq "0" "$HAND_RC" "hand-written AGENTS.md (no marker) → exit 0"
assert_contains "$HAND_OUT" "hand-written" "hand-written AGENTS.md → noted, not clobbered"
