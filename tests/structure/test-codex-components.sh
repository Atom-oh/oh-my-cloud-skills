# Run schema/path checks against synthetic packages, without executing plugin code.
if python3 tests/structure/test-codex-components.py; then
  pass "Codex declared component paths, package containment and marketplace uniqueness"
else
  fail "Codex declared component paths, package containment and marketplace uniqueness"
fi
