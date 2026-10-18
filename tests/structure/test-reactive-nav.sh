# tests/structure/test-reactive-nav.sh (sourced by run-all.sh, no shebang or exit)
# Browser regressions for agenda/search and cross-module behavior. Skips without Playwright.
if RP_NAV_OUTPUT=$(python3 tests/structure/reactive_nav_test.py 2>&1); then
  if grep -q "SKIPPED-ALL" <<< "$RP_NAV_OUTPUT"; then
    pass "deck nav agenda/search # SKIP playwright unavailable"
  else
    pass "deck nav agenda/search"
  fi
else
  fail "deck nav agenda/search" "$RP_NAV_OUTPUT"
fi
if command -v node >/dev/null 2>&1; then
  for RP_JS in deck-overlay.js deck-detail.js deck-nav.js slide-framework.js export-utils.js; do
    RP_JS_CHECK="fail"
    node --check "plugins/aws-content-plugin/skills/reactive-presentation/assets/$RP_JS" >/dev/null 2>&1 && RP_JS_CHECK="ok"
    assert_eq "ok" "$RP_JS_CHECK" "$RP_JS passes node --check"
  done
fi
RP_EU="$(cat plugins/aws-content-plugin/skills/reactive-presentation/assets/export-utils.js 2>/dev/null || true)"
for RP_OVERLAY_FILE in deck-overlay.js deck-overlay.css deck-detail.js deck-detail.css deck-nav.js deck-nav.css; do
  assert_contains "$RP_EU" "'$RP_OVERLAY_FILE'" "export-utils COMMON_FILES ships $RP_OVERLAY_FILE"
done
assert_contains "$RP_EU" ".rp-overlay-ui" "export-utils capture paths hide the overlay"
assert_contains "$RP_EU" "rp-detail-store" "export-utils browser PPTX export carries detail text into notes"
