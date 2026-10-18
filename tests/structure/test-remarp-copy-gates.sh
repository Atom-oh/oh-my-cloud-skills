# tests/structure/test-remarp-copy-gates.sh   (sourced by run-all.sh — no shebang, no exit)
# EM_DASH / AI_TONE copy gates in remarp validate.
if RP_COPY_OUTPUT=$(python3 tests/structure/remarp_copy_gates_test.py 2>&1); then
  pass "Remarp EM_DASH and AI_TONE copy gates"
else
  fail "Remarp EM_DASH and AI_TONE copy gates" "$RP_COPY_OUTPUT"
fi
