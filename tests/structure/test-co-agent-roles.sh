# Sourced by tests/run-all.sh. Structural contracts, not host execution proof.
if python3 -B tests/structure/test-co-agent-roles.py; then
  pass "co-agent consolidated roles, generated entries and host analysis contracts"
else
  fail "co-agent consolidated roles, generated entries and host analysis contracts"
fi
