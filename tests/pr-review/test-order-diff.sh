if python3 -I tests/pr-review/test-order-diff.py; then
  pass "review diff lists maintained source before documentation and generated copies"
else
  fail "review diff lists maintained source before documentation and generated copies"
fi
