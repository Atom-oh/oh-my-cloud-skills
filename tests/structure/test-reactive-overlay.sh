# tests/structure/test-reactive-overlay.sh   (sourced by run-all.sh — no shebang, no exit)
# Browser regressions for the deck overlay (agenda, cmd-k search, detail layer). Skips without Playwright.
if RP_OVERLAY_OUTPUT=$(python3 tests/structure/reactive_overlay_test.py 2>&1); then
  if grep -q "SKIPPED-ALL" <<< "$RP_OVERLAY_OUTPUT"; then
    pass "deck overlay agenda/search/detail # SKIP playwright unavailable"
  else
    pass "deck overlay agenda/search/detail"
  fi
else
  fail "deck overlay agenda/search/detail" "$RP_OVERLAY_OUTPUT"
fi
if command -v node >/dev/null 2>&1; then
  for RP_JS in deck-overlay.js slide-framework.js export-utils.js; do
    RP_JS_CHECK="fail"
    node --check "plugins/aws-content-plugin/skills/reactive-presentation/assets/$RP_JS" >/dev/null 2>&1 && RP_JS_CHECK="ok"
    assert_eq "ok" "$RP_JS_CHECK" "$RP_JS passes node --check"
  done
fi
RP_EU="$(cat plugins/aws-content-plugin/skills/reactive-presentation/assets/export-utils.js 2>/dev/null || true)"
assert_contains "$RP_EU" "'deck-overlay.js'" "export-utils COMMON_FILES ships deck-overlay.js"
assert_contains "$RP_EU" "'deck-overlay.css'" "export-utils COMMON_FILES ships deck-overlay.css"
assert_contains "$RP_EU" ".rp-overlay-ui" "export-utils capture paths hide the overlay"
assert_contains "$RP_EU" "rp-detail-store" "export-utils browser PPTX export carries detail text into notes"
