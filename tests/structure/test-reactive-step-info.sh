# tests/structure/test-reactive-step-info.sh (sourced by run-all.sh, no shebang or exit)
# deck.getStepInfo browser behavior. Skips without Playwright.
if RP_SI_OUTPUT=$(python3 tests/structure/reactive_step_info_test.py 2>&1); then
  if grep -q "SKIPPED-ALL" <<< "$RP_SI_OUTPUT"; then
    pass "deck.getStepInfo # SKIP playwright unavailable"
  else
    pass "deck.getStepInfo"
  fi
else
  fail "deck.getStepInfo" "$RP_SI_OUTPUT"
fi
