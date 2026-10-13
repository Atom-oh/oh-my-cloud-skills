if python3 tests/structure/test-host-package-validation.py; then
  pass "trusted host validators accept file MCP and reject inconsistent package data"
else
  fail "trusted host validators accept file MCP and reject inconsistent package data"
fi
