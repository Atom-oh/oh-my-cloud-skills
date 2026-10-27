# tests/structure/test-reactive-footer.sh (sourced by run-all.sh, no shebang or exit)
# Footer text spacing follows the logo width. Skips without Playwright.
if RP_FOOTER_OUTPUT=$(python3 tests/structure/reactive_footer_test.py 2>&1); then
  if grep -q "SKIPPED-ALL" <<< "$RP_FOOTER_OUTPUT"; then
    pass "deck footer follows logo # SKIP playwright unavailable"
  else
    pass "deck footer follows logo"
  fi
else
  fail "deck footer follows logo" "$RP_FOOTER_OUTPUT"
fi
