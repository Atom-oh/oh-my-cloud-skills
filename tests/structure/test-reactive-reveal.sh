if node tests/structure/test-reactive-reveal.js; then
  pass "Browser export final-state preparation freezes staggered groups before reveal"
else
  fail "Browser export final-state preparation"
fi
if python3 -B tests/structure/test-reactive-reveal.py; then
  pass "Remarp column remainder preserves fragment and Archify semantics"
else
  fail "Remarp column remainder semantics"
fi
