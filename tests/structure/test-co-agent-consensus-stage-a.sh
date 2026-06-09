#!/usr/bin/env bash
# Stage A of the consensus pipeline: consensus_state.py + parse_plan.py.

CO="plugins/co-agent/skills/co-agent"
ST="$CO/scripts/consensus_state.py"
PP="$CO/scripts/parse_plan.py"

assert_file_exists "$ST" "consensus_state.py exists"
assert_file_executable "$ST" "consensus_state.py is executable"
assert_file_exists "$PP" "parse_plan.py exists"
assert_file_exists "$CO/references/consensus-pipeline.md" "consensus-pipeline.md exists"

# --- input detection ---
D=$(mktemp -d "${TMPDIR:-/tmp}/cstate.XXXXXX")
printf '# ADR-007: choice\n' > "$D/ADR-007-choice.md"
printf '# Feature Plan\n### Task 1: thing\n- [ ] do it\n' > "$D/myplan.md"
printf '# Design Spec\n## Non-Goals\nx\n' > "$D/design.md"
DET=$(python3 "$ST" detect "$D" "$D/ADR-007-choice.md" "$D/myplan.md" "$D/design.md" 2>&1)
assert_contains "$DET" "$(printf 'ADR-007-choice.md\tadr')" "detect: ADR → adr"
assert_contains "$DET" "$(printf 'myplan.md\tplan')" "detect: checkbox-task doc → plan"
assert_contains "$DET" "$(printf 'design.md\tspec')" "detect: design/Non-Goals → spec"

# --- state init / get / set ---
python3 "$ST" init "$D" --docs "$D/myplan.md" --base main >/dev/null 2>&1
assert_eq "P0" "$(python3 "$ST" get "$D" phase 2>&1)" "init → phase P0"
SID=$(python3 "$ST" get "$D" session_id 2>&1)
assert_eq "1" "$(printf '%s' "$SID" | grep -cE '^[0-9a-f]{16}$')" "session_id is 16-hex"
python3 "$ST" set "$D" phase P2 >/dev/null 2>&1
assert_eq "P2" "$(python3 "$ST" get "$D" phase 2>&1)" "set phase → P2"
python3 "$ST" set "$D" task_index 3 >/dev/null 2>&1
assert_eq "3" "$(python3 "$ST" get "$D" task_index 2>&1)" "set task_index → 3"
assert_file_exists "$D/.claude/co-agent-consensus/state.local.md" "state file written"
# set rejects unknown key
python3 "$ST" set "$D" bogus x >/dev/null 2>&1 && SK=0 || SK=$?
assert_eq "2" "$SK" "set rejects unknown key"
rm -rf "$D"

# --- parse_plan ---
PD=$(mktemp "${TMPDIR:-/tmp}/plan.XXXXXX.md")
printf '# Plan\n\n### Task 1: alpha\n**Files:**\n- Create: `a/b.py`\n- Test: `t/x.sh`\n- [ ] step one\n- [ ] step two\n\n### Task 2: beta\n**Files:**\n- Modify: `a/b.py:10-20`\n- [ ] step\n' > "$PD"
assert_eq "2" "$(python3 "$PP" "$PD" --count 2>&1)" "parse_plan counts 2 tasks"
FILES=$(python3 "$PP" "$PD" --files 2>&1)
assert_contains "$FILES" "a/b.py" "parse_plan extracts Create/Modify path"
assert_contains "$FILES" "t/x.sh" "parse_plan extracts Test path"
assert_eq "2" "$(printf '%s\n' "$FILES" | grep -c .)" "parse_plan de-dupes a/b.py (2 unique files)"
rm -f "$PD"
