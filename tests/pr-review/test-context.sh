if python3 tests/pr-review/test-context.py; then
  pass "review context validates provenance and derives distinct inventory populations"
else
  fail "review context validates provenance and derives distinct inventory populations"
fi
