#!/usr/bin/env bash
# Stage C: consensus_state `report` + `cumulative-diff` + resume (phase/task_index round-trip).

CO="plugins/co-agent/skills/co-agent"
ST="$CO/scripts/consensus_state.py"

D=$(mktemp -d "${TMPDIR:-/tmp}/csc.XXXXXX")
printf '# Plan\n### Task 1: a\n**Files:**\n- Modify: `README.md`\n- [ ] x\n' > "$D/plan.md"
python3 "$ST" init "$D" --docs "$D/plan.md" >/dev/null 2>&1

# --- report ---
python3 "$ST" task-start "$D" 0 >/dev/null 2>&1
python3 "$ST" task-round "$D" 0 >/dev/null 2>&1
python3 "$ST" task-done "$D" 0 >/dev/null 2>&1
python3 "$ST" set "$D" status done >/dev/null 2>&1
REP=$(python3 "$ST" report "$D" 2>&1)
assert_contains "$REP" "Consensus run report" "report has a title"
assert_contains "$REP" "1 done" "report counts done tasks"
assert_contains "$REP" "status\*\*: done" "report shows status"
assert_file_exists "$D/.claude/co-agent-consensus/report.md" "report.md written to session dir"
# report with no session → exit 2
E=$(mktemp -d "${TMPDIR:-/tmp}/cscx.XXXXXX")
python3 "$ST" report "$E" >/dev/null 2>&1 && RR=0 || RR=$?
assert_eq "2" "$RR" "report with no session → exit 2"
rm -rf "$E"

# --- cumulative-diff: missing --plan → usage err; with --plan → rc 0 ---
python3 "$ST" cumulative-diff "$D" --base main >/dev/null 2>&1 && CD=0 || CD=$?
assert_eq "2" "$CD" "cumulative-diff without --plan → exit 2"
python3 "$ST" cumulative-diff "$D" --plan "$D/plan.md" --base main >/dev/null 2>&1 && CD2=0 || CD2=$?
assert_eq "0" "$CD2" "cumulative-diff with --plan → exit 0"

# --- resume: phase/task_index persist and round-trip ---
python3 "$ST" set "$D" phase P3 >/dev/null 2>&1
python3 "$ST" set "$D" task_index 2 >/dev/null 2>&1
assert_eq "P3" "$(python3 "$ST" get "$D" phase 2>&1)" "resume: phase persisted"
assert_eq "2" "$(python3 "$ST" get "$D" task_index 2>&1)" "resume: task_index persisted"

rm -rf "$D"
