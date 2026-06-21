#!/usr/bin/env bash
# Tests for co-agent:harness — implementer resolution, write-mode flags,
# stage-result/needs-human/rebind state, and the worktree helper.
CFG="plugins/co-agent/skills/co-agent/scripts/co_agent_config.py"
ST="plugins/co-agent/skills/co-agent/scripts/consensus_state.py"
WT="plugins/co-agent/skills/co-agent/scripts/worktree.py"

# --- Task 1: implementer resolution ---
R=$(mktemp -d "${TMPDIR:-/tmp}/coagent-harness.XXXXXX")
assert_eq "codex" "$(python3 "$CFG" implementer --host claude --root "$R" 2>&1)" "default implementer for claude host = codex"
assert_eq "claude" "$(python3 "$CFG" implementer --host codex --root "$R" 2>&1)" "default implementer for codex host = claude"
python3 "$CFG" set harness implementer agy --root "$R" >/dev/null 2>&1
assert_eq "agy" "$(python3 "$CFG" implementer --host claude --root "$R" 2>&1)" "override implementer respected"
python3 "$CFG" set harness implementer claude --root "$R" >/dev/null 2>&1
python3 "$CFG" implementer --host claude --root "$R" >/dev/null 2>&1 && IRC=0 || IRC=$?
assert_eq "2" "$IRC" "implementer equal to host rejected (exit 2)"
rm -rf "$R"
