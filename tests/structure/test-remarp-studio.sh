# Source-map export uses the canonical parser/build gate and preserves exact spans.
if python3 -B tests/structure/test-remarp-studio.py; then
  pass "Remarp Studio canonical build and source provenance"
else
  fail "Remarp Studio canonical build and source provenance"
fi
