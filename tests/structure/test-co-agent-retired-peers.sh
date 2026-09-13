# Sourced by the TAP runner; all provider boundaries are local test doubles.
if python3 -B tests/structure/test-co-agent-retired-peers.py; then
  pass "retired co-agent peers stay excluded across config, probes, hooks and writer planning"
else
  fail "retired co-agent peers stay excluded across config, probes, hooks and writer planning"
fi
