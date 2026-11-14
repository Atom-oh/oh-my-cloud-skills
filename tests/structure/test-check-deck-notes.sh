# tests/structure/test-check-deck-notes.sh   (sourced by run-all.sh — no shebang, no exit)
# check_deck.py note lint: NOTE_OPERATING_INSTRUCTION and NOTE_MARK_IN_META.
if RP_CDN_OUTPUT=$(python3 tests/structure/check_deck_notes_test.py 2>&1); then
  pass "check_deck note lint"
else
  fail "check_deck note lint" "$RP_CDN_OUTPUT"
fi
