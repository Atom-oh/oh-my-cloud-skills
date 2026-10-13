if python3 tests/structure/test-pr-diff.py; then
  pass "pinned PR diff captures large shallow histories without executing PR tools"
else
  fail "pinned PR diff captures large shallow histories without executing PR tools"
fi
