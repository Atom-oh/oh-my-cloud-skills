# tests/structure/test-reactive-detail.sh (sourced by run-all.sh, no shebang or exit)
# Browser regressions for core plus detail only. Skips without Playwright.
if RP_DETAIL_OUTPUT=$(python3 tests/structure/reactive_detail_test.py 2>&1); then
  if grep -q "SKIPPED-ALL" <<< "$RP_DETAIL_OUTPUT"; then
    pass "deck detail tooltip/panel/terms # SKIP playwright unavailable"
  else
    pass "deck detail tooltip/panel/terms"
  fi
else
  fail "deck detail tooltip/panel/terms" "$RP_DETAIL_OUTPUT"
fi
if command -v node >/dev/null 2>&1; then
  for RP_JS in deck-overlay.js deck-detail.js; do
    RP_JS_CHECK="fail"
    node --check "plugins/aws-content-plugin/skills/reactive-presentation/assets/$RP_JS" >/dev/null 2>&1 && RP_JS_CHECK="ok"
    assert_eq "ok" "$RP_JS_CHECK" "$RP_JS passes node --check"
  done
fi
