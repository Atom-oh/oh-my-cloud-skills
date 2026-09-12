if python3 tests/structure/test-pr-autofix-review-state.py; then
  pass "PR review state migration, checkpoint, wait budget and verdict grammar"
else
  fail "PR review state migration, checkpoint, wait budget and verdict grammar"
fi
