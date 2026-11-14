# tests/structure/test-reactive-step-cue.sh (sourced by run-all.sh, no shebang or exit)
# Presenter step cue under the arrow buttons. Browser part skips without Playwright.
if RP_CUE_OUTPUT=$(python3 tests/structure/reactive_step_cue_test.py 2>&1); then
  if grep -q "SKIPPED-ALL" <<< "$RP_CUE_OUTPUT"; then
    pass "presenter step cue # SKIP playwright unavailable"
  else
    pass "presenter step cue"
  fi
else
  fail "presenter step cue" "$RP_CUE_OUTPUT"
fi
