#!/usr/bin/env bash
# Stage B: scope_guard + consensus_hooks session-gating + consensus_state P3 progress.

CO="plugins/co-agent/skills/co-agent"
SG="$CO/scripts/scope_guard.py"
HK="$CO/scripts/consensus_hooks.py"
ST="$CO/scripts/consensus_state.py"

assert_file_exists "$SG" "scope_guard.py exists"
assert_file_executable "$SG" "scope_guard.py is executable"
assert_file_exists "$HK" "consensus_hooks.py exists"

# --- scope_guard ---
P=$(mktemp "${TMPDIR:-/tmp}/sgplan.XXXXXX.md")
printf '### Task 1: a\n**Files:**\n- Create: `src/a.py`\n- Test: `tests/a.sh`\n- [ ] x\n' > "$P"
python3 "$SG" --plan "$P" src/a.py >/dev/null 2>&1 && IN=0 || IN=$?
assert_eq "0" "$IN" "scope_guard: in-scope path allowed"
python3 "$SG" --plan "$P" src/evil.py >/dev/null 2>&1 && OUT=0 || OUT=$?
assert_eq "1" "$OUT" "scope_guard: out-of-scope path rejected"
assert_contains "$(python3 "$SG" --plan "$P" --list 2>&1)" "src/a.py" "scope_guard --list shows allowed set"
rm -f "$P"

# --- consensus_hooks session-gating ---
D=$(mktemp -d "${TMPDIR:-/tmp}/csb.XXXXXX")
printf '# Plan\n### Task 1: a\n- [ ] x\n' > "$D/plan.md"
python3 "$ST" init "$D" --docs "$D/plan.md" >/dev/null 2>&1
# inactive (P0, not autonomous) → stop hook no-op (empty output)
OUT0=$(echo '{}' | python3 "$HK" stop --root "$D" 2>&1)
assert_eq "" "$OUT0" "stop hook is a no-op when no active P3 session"
# activate P3 autonomous + pending task → stop emits block decision
python3 "$ST" set "$D" phase P3 >/dev/null 2>&1
python3 "$ST" autonomous "$D" on >/dev/null 2>&1
python3 "$ST" task-start "$D" 0 >/dev/null 2>&1
assert_contains "$(echo '{}' | python3 "$HK" stop --root "$D" 2>&1)" "block" "stop hook blocks while P3 task pending"
# task done → stop allows again (no-op)
python3 "$ST" task-done "$D" 0 >/dev/null 2>&1
OUT1=$(echo '{}' | python3 "$HK" stop --root "$D" 2>&1)
assert_eq "" "$OUT1" "stop hook allows stop once all tasks done"

# --- state progress ---
python3 "$ST" task-round "$D" 0 >/dev/null 2>&1
assert_contains "$(python3 "$ST" get "$D" tasks 2>&1)" "rounds" "task-round records per-task rounds"
python3 "$ST" set "$D" status bogus >/dev/null 2>&1 && SB=0 || SB=$?
assert_eq "2" "$SB" "status rejects invalid value"
rm -rf "$D"
