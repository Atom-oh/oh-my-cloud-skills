# Packaging/runtime regressions without network, AWS calls or inference.
if python3 tests/structure/test-codex-portability.py; then
  pass "Codex entry coverage, generated artifacts and installed helper runtime"
else
  fail "Codex entry coverage, generated artifacts and installed helper runtime"
fi
