if python3 -B tests/pr-review/test-review-gate.py; then
  pass "CI review severity, verdict and required-coverage consistency"
else
  fail "CI review severity, verdict and required-coverage consistency"
fi
