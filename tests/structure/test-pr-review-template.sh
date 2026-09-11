# Execute the shipped YAML, using mock providers and GitHub APIs only.
if python3 -B tests/structure/test-pr-review-template.py; then
  pass "bundled PR review template: status, exact HEAD, and trusted context"
else
  fail "bundled PR review template: status, exact HEAD, and trusted context"
fi
