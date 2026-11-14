# tests/structure/test-measure-step-marks.sh   (sourced by run-all.sh — no shebang, no exit)
# measure_deck STEP_MARKS: "↓" marks in the notes versus real Down presses. Browser cases skip without Playwright.
if RP_MARKS_OUTPUT=$(python3 tests/structure/measure_step_marks_test.py 2>&1); then
  if grep -q "SKIPPED-BROWSER" <<< "$RP_MARKS_OUTPUT"; then
    pass "measure_deck STEP_MARKS # SKIP playwright unavailable (static checks passed)"
  else
    pass "measure_deck STEP_MARKS"
  fi
else
  fail "measure_deck STEP_MARKS" "$RP_MARKS_OUTPUT"
fi
