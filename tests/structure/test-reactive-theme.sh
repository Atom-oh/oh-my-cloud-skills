# tests/structure/test-reactive-theme.sh (sourced by run-all.sh, no shebang or exit)
# T dark/light toggle browser regression. Skips without Playwright.
if RP_THEME_OUTPUT=$(python3 tests/structure/reactive_theme_test.py 2>&1); then
  if grep -q "SKIPPED-ALL" <<< "$RP_THEME_OUTPUT"; then
    pass "theme toggle # SKIP playwright unavailable"
  else
    pass "theme toggle"
  fi
else
  fail "theme toggle" "$RP_THEME_OUTPUT"
fi
