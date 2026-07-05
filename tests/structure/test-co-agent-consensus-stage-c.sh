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

# --- cumulative-diff: missing --plan → usage err ---
python3 "$ST" cumulative-diff "$D" --base HEAD >/dev/null 2>&1 && CD=0 || CD=$?
assert_eq "2" "$CD" "cumulative-diff without --plan → exit 2"

# Set up a real git repo so the base ref resolves (a valid base is required).
G=$(mktemp -d "${TMPDIR:-/tmp}/cscg.XXXXXX")
git -C "$G" init -q
git -C "$G" config user.email t@t.t; git -C "$G" config user.name t
printf '# Plan\n### Task 1: a\n**Files:**\n- Modify: `README.md`\n- [ ] x\n' > "$G/plan.md"
printf 'hello\n' > "$G/README.md"
git -C "$G" add README.md plan.md >/dev/null 2>&1
git -C "$G" commit -q -m init >/dev/null 2>&1
python3 "$ST" cumulative-diff "$G" --plan "$G/plan.md" --base HEAD >/dev/null 2>&1 && CD2=0 || CD2=$?
assert_eq "0" "$CD2" "cumulative-diff with --plan + valid base → exit 0"
# bad base ref → exit 2 (must not masquerade as an empty/passing diff)
python3 "$ST" cumulative-diff "$G" --plan "$G/plan.md" --base no-such-ref >/dev/null 2>&1 && CD3=0 || CD3=$?
assert_eq "2" "$CD3" "cumulative-diff with bad --base → exit 2"

# --- cumulative-diff must reuse scope_guard's fixed normalization, not a second
#     lstrip("./")-based file-list builder (that duplicate had the same traversal-
#     collapsing bug as scope_guard.py before it was fixed — see test-co-agent-
#     consensus-stage-b.sh) ---
assert_grep_match "scope_guard\.allowed_set" "$(cat "$ST")" "cumulative-diff reuses scope_guard.allowed_set (no duplicate lstrip logic)"

# A plan entry with a redundant leading "./" must still resolve to the right file
# (basic sanity that routing the file list through scope_guard.allowed_set didn't
# break the common case).
printf '# Plan\n### Task 1: a\n**Files:**\n- Modify: `./README.md`\n- [ ] x\n' > "$G/plan2.md"
python3 "$ST" cumulative-diff "$G" --plan "$G/plan2.md" --base HEAD >/dev/null 2>&1 && CD4=0 || CD4=$?
assert_eq "0" "$CD4" "cumulative-diff normalizes a redundant './' plan entry the same way scope_guard does"
rm -rf "$G"

# --- resume: phase/task_index persist and round-trip ---
python3 "$ST" set "$D" phase P3 >/dev/null 2>&1
python3 "$ST" set "$D" task_index 2 >/dev/null 2>&1
assert_eq "P3" "$(python3 "$ST" get "$D" phase 2>&1)" "resume: phase persisted"
assert_eq "2" "$(python3 "$ST" get "$D" task_index 2>&1)" "resume: task_index persisted"

rm -rf "$D"
