if python3 tests/pr-review/test-chair-publication.py; then
  pass "chair publication preserves blockers and reports content-free diagnostics"
else
  fail "chair publication preserves blockers and reports content-free diagnostics"
fi
