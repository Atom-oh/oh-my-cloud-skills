if python3 -B tests/structure/test-pr-target.py; then
  pass "PR target binds bare push to one open PR repository and branch"
else
  fail "PR target binds bare push to one open PR repository and branch"
fi
