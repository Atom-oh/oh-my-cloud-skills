# Check custom paths and generated inventories separately, without executing plugin code.
if python3 tests/structure/test-codex-components.py; then
  pass "Codex component paths, generated inventory coverage, containment and marketplace uniqueness"
else
  fail "Codex component paths, generated inventory coverage, containment and marketplace uniqueness"
fi
