if python3 -B tests/pr-review/test-review-format.py; then
  pass "shared review format preserves citations and rejects assignments"
else
  fail "shared review format preserves citations and rejects assignments"
fi
