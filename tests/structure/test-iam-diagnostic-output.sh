if python3 -B tests/structure/test-iam-diagnostic-output.py; then
  pass "IAM's documented pod diagnostic exposes presence without credential values"
else
  fail "IAM pod diagnostic credential-output regression"
fi
