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

# --- Task 2: write-mode implementer flags ---
R2=$(mktemp -d "${TMPDIR:-/tmp}/coagent-harness2.XXXXXX")
assert_contains "$(python3 "$CFG" impl-flags codex --host claude --root "$R2" 2>&1)" "workspace-write" "codex impl-flags use workspace-write sandbox"
assert_contains "$(python3 "$CFG" impl-flags claude --host codex --root "$R2" 2>&1)" "acceptEdits" "claude impl-flags use acceptEdits permission mode"
assert_contains "$(python3 "$CFG" impl-flags agy --host claude --root "$R2" 2>&1)" "sandbox" "agy impl-flags keep sandbox"
python3 "$CFG" impl-flags claude --host claude --root "$R2" >/dev/null 2>&1 && HRC=0 || HRC=$?
assert_eq "2" "$HRC" "impl-flags rejects ai equal to host (exit 2)"
assert_grep_no_match "workspace-write|acceptEdits" "$(python3 "$CFG" flags codex --host claude --root "$R2" 2>&1)" "review flags stay read-only (no write sandbox)"
rm -rf "$R2"

# --- Task 3: needs-human status ---
R3=$(mktemp -d "${TMPDIR:-/tmp}/coagent-harness3.XXXXXX")
git -C "$R3" init -q
git -C "$R3" config user.email t@t.t; git -C "$R3" config user.name t
git -C "$R3" commit -q --allow-empty -m init >/dev/null 2>&1
python3 "$ST" init "$R3" --docs none --base HEAD >/dev/null 2>&1
python3 "$ST" set "$R3" status needs-human >/dev/null 2>&1 && NRC=0 || NRC=$?
assert_eq "0" "$NRC" "status needs-human accepted (exit 0)"
assert_eq "needs-human" "$(python3 "$ST" get "$R3" status 2>&1)" "get status returns needs-human"
python3 "$ST" set "$R3" status bogus >/dev/null 2>&1 && BRC=0 || BRC=$?
assert_eq "2" "$BRC" "invalid status still rejected (exit 2)"
rm -rf "$R3"

# --- Task 4: stage-result output gate ---
R4=$(mktemp -d "${TMPDIR:-/tmp}/coagent-harness4.XXXXXX")
python3 "$ST" stage-result check "$R4/missing.json" >/dev/null 2>&1 && M=0 || M=$?
assert_eq "1" "$M" "stage-result check on missing artifact fails (exit 1)"
python3 "$ST" stage-result write "$R4/plan-gate/result.json" --stage plan-gate --verdict PASS --rounds 1 --wall "$R4/stage_wall.tsv" >/dev/null 2>&1
assert_file_exists "$R4/plan-gate/result.json" "stage-result write creates result.json"
assert_json_valid "$R4/plan-gate/result.json" "result.json is valid JSON"
python3 "$ST" stage-result check "$R4/plan-gate/result.json" >/dev/null 2>&1 && C=0 || C=$?
assert_eq "0" "$C" "stage-result check on valid artifact passes (exit 0)"
assert_contains "$(cat "$R4/stage_wall.tsv")" "plan-gate" "stage_wall.tsv got a row"
rm -rf "$R4"

# --- Task 5: rebind after manual commit ---
R5=$(mktemp -d "${TMPDIR:-/tmp}/coagent-harness5.XXXXXX")
git -C "$R5" init -q
git -C "$R5" config user.email t@t.t; git -C "$R5" config user.name t
printf '.claude/\n' > "$R5/.gitignore"   # session state is gitignored (as in the real repo)
git -C "$R5" add .gitignore >/dev/null 2>&1
git -C "$R5" commit -q -m init >/dev/null 2>&1
python3 "$ST" init "$R5" --docs none --base HEAD >/dev/null 2>&1
git -C "$R5" commit -q --allow-empty -m "manual fix" >/dev/null 2>&1
python3 "$ST" verify "$R5" >/dev/null 2>&1 && V1=0 || V1=$?
assert_eq "1" "$V1" "verify fails after HEAD drift (exit 1)"
python3 "$ST" rebind "$R5" >/dev/null 2>&1 && RB=0 || RB=$?
assert_eq "0" "$RB" "rebind succeeds (exit 0)"
python3 "$ST" verify "$R5" >/dev/null 2>&1 && V2=0 || V2=$?
assert_eq "0" "$V2" "verify passes after rebind (exit 0)"
rm -rf "$R5"
