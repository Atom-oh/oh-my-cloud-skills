# tests/structure/test-reactive-pen.sh (sourced by run-all.sh, no shebang or exit)
# Pen mode: ink model unit test, syntax check and deck-window browser test.
RP_PEN_JS="plugins/aws-content-plugin/skills/reactive-presentation/assets/deck-pen.js"
if command -v node >/dev/null 2>&1; then
  if RP_PEN_OUTPUT=$(node --test tests/structure/reactive_pen_model.test.cjs 2>&1); then
    pass "deck pen ink model unit tests"
  else
    fail "deck pen ink model unit tests" "$RP_PEN_OUTPUT"
  fi
  RP_PEN_CHECK="fail"
  node --check "$RP_PEN_JS" >/dev/null 2>&1 && RP_PEN_CHECK="ok"
  assert_eq "ok" "$RP_PEN_CHECK" "deck-pen.js passes node --check"
fi

# Browser test for the deck-window overlay. Skips without Playwright.
if RP_PEN_BROWSER_OUTPUT=$(python3 tests/structure/reactive_pen_test.py 2>&1); then
  if grep -q "SKIPPED-ALL" <<< "$RP_PEN_BROWSER_OUTPUT"; then
    pass "deck pen overlay keys/canvas/badge # SKIP playwright unavailable"
  else
    pass "deck pen overlay keys/canvas/badge"
  fi
else
  fail "deck pen overlay keys/canvas/badge" "$RP_PEN_BROWSER_OUTPUT"
fi
