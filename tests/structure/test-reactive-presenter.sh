# tests/structure/test-reactive-presenter.sh   (sourced by run-all.sh — no shebang, no exit)
# Browser regressions for presenter-view preview fidelity. Skips without Playwright.
if RP_PRESENTER_OUTPUT=$(python3 tests/structure/reactive_presenter_test.py 2>&1); then
  if grep -q "SKIPPED-ALL" <<< "$RP_PRESENTER_OUTPUT"; then
    pass "presenter preview fidelity # SKIP playwright unavailable"
  else
    pass "presenter preview fidelity"
  fi
else
  fail "presenter preview fidelity" "$RP_PRESENTER_OUTPUT"
fi
if command -v node >/dev/null 2>&1; then
  RP_PV_CHECK="fail"
  node --check plugins/aws-content-plugin/skills/reactive-presentation/assets/presenter-view.js >/dev/null 2>&1 && RP_PV_CHECK="ok"
  assert_eq "ok" "$RP_PV_CHECK" "presenter-view.js passes node --check"
fi
