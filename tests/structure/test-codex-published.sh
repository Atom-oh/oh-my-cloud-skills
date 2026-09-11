# Final closure gate: missing or regressed packages must not disappear from selection.
if python3 scripts/sync-codex-plugins.py --check; then
  pass "all Codex adapters match source in the real checkout"
else
  fail "all Codex adapters match source in the real checkout"
fi
