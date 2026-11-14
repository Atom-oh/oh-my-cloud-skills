# tests/structure/test-reactive-raf-stall.sh (sourced by run-all.sh, no shebang or exit)
# Animation steps draw while the deck window gets no animation frames. Skips without Playwright.
if RP_RAF_OUTPUT=$(python3 tests/structure/reactive_raf_stall_test.py 2>&1); then
  if grep -q "SKIPPED-ALL" <<< "$RP_RAF_OUTPUT"; then
    pass "animation redraw without frames # SKIP playwright unavailable"
  else
    pass "animation redraw without frames"
  fi
else
  fail "animation redraw without frames" "$RP_RAF_OUTPUT"
fi
