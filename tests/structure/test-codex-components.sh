# Run schema/path checks against synthetic packages, without executing plugin code.
if python3 tests/structure/test-codex-components.py; then
  pass "Codex component paths, source inventory coverage and marketplace uniqueness"
else
  fail "Codex component paths, source inventory coverage and marketplace uniqueness"
fi
