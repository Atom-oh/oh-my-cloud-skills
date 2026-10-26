# tests/structure/test-reactive-pen.sh (sourced by run-all.sh, no shebang or exit)
# Pen mode: pure ink model unit test and syntax check.
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

# --- Browser test (Playwright) is added by Task 2 below this line ---
