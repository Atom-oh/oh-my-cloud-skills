# Exercise only local fixture hooks and Git discovery; no providers are invoked.
if python3 -B tests/structure/test-codex-hook-routing.py; then
  pass "Codex hook rename routing, project root, regex aliases and blocking decisions"
else
  fail "Codex hook rename routing, project root, regex aliases and blocking decisions"
fi
