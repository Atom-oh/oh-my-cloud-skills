if python3 tests/hooks/test-readme-language.py; then
  pass "README hook requests canonical English maintenance for absolute and relative paths"
else
  fail "README hook requests canonical English maintenance for absolute and relative paths"
fi
