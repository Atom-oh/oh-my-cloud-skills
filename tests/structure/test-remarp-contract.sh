# Behavioral compiler tests (sourced by the TAP runner).
if REMARP_CONTRACT_OUTPUT=$(python3 tests/structure/remarp_contract_test.py 2>&1); then
  pass "Remarp source/build contract regressions"
else
  fail "Remarp source/build contract regressions" "$REMARP_CONTRACT_OUTPUT"
fi
