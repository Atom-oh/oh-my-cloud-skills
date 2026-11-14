# tests/structure/test-reactive-notes-edit.sh (sourced by run-all.sh, no shebang or exit)
# Editable speaker notes in the presenter view. Browser part skips without Playwright.
if RP_NOTES_OUTPUT=$(python3 tests/structure/reactive_notes_edit_test.py 2>&1); then
  if grep -q "SKIPPED-ALL" <<< "$RP_NOTES_OUTPUT"; then
    pass "editable presenter notes # SKIP playwright unavailable"
  else
    pass "editable presenter notes"
  fi
else
  fail "editable presenter notes" "$RP_NOTES_OUTPUT"
fi
