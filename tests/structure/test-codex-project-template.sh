# Native Codex project-hook templates; no provider calls or hook trust changes.
if python3 tests/structure/test-codex-project-template.py; then
  pass "Codex native project hook templates"
else
  fail "Codex native project hook templates"
fi
