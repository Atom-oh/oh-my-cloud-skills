# tests/structure/test-measure-runon.sh   (sourced by run-all.sh — no shebang, no exit)
# measure_deck SENTENCE_RUNON and overlay hiding. Browser cases skip without Playwright.
if RP_RUNON_OUTPUT=$(python3 tests/structure/measure_runon_test.py 2>&1); then
  if grep -q "SKIPPED-BROWSER" <<< "$RP_RUNON_OUTPUT"; then
    pass "measure_deck SENTENCE_RUNON # SKIP playwright unavailable (static checks passed)"
  else
    pass "measure_deck SENTENCE_RUNON"
  fi
else
  fail "measure_deck SENTENCE_RUNON" "$RP_RUNON_OUTPUT"
fi
