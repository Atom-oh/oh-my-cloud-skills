# tests/structure/test-reactive-hidden.sh (sourced by run-all.sh, no shebang or exit)
# Hidden slides: `@hidden` build output + browser navigation. Browser part skips without Playwright.
RP_HID_SRC="plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py"
RP_HID_DIR="$(mktemp -d "${TMPDIR:-/tmp}/rp-hidden-XXXXXX")"
printf -- '---\nremarp: true\nblock: demo\ntitle: Hide\n---\n\n# A\n\n---\n\n# B\n\n@hidden: true\n\n- x\n\n---\n\n# C\n\n- y\n' > "$RP_HID_DIR/deck.md"
RP_HID_BUILD="fail"
python3 "$RP_HID_SRC" build "$RP_HID_DIR/deck.md" -o "$RP_HID_DIR/out" >/dev/null 2>&1 && RP_HID_BUILD="ok"
assert_eq "ok" "$RP_HID_BUILD" "@hidden deck builds"
RP_HID_COUNT="$(grep -o 'data-hidden="true"' "$RP_HID_DIR"/out/*.html 2>/dev/null | wc -l | tr -d ' ')"
assert_eq "1" "$RP_HID_COUNT" "@hidden emits data-hidden on exactly the marked slide"
rm -rf "$RP_HID_DIR"
if RP_HID_OUTPUT=$(python3 tests/structure/reactive_hidden_test.py 2>&1); then
  if grep -q "SKIPPED-ALL" <<< "$RP_HID_OUTPUT"; then
    pass "hidden slides navigation # SKIP playwright unavailable"
  else
    pass "hidden slides navigation"
  fi
else
  fail "hidden slides navigation" "$RP_HID_OUTPUT"
fi
