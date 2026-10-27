# tests/structure/test-reactive-fullscreen.sh (sourced by run-all.sh, no shebang or exit)
# Escape is locked while the deck is fullscreen so pen mode and overview see it first. Skips without Playwright.
if RP_FS_OUTPUT=$(python3 tests/structure/reactive_fullscreen_test.py 2>&1); then
  if grep -q "SKIPPED-ALL" <<< "$RP_FS_OUTPUT"; then
    pass "deck locks Escape in fullscreen # SKIP playwright unavailable"
  else
    pass "deck locks Escape in fullscreen"
  fi
else
  fail "deck locks Escape in fullscreen" "$RP_FS_OUTPUT"
fi
