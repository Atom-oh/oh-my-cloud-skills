# Final integration gate: check every plugin, including missing or regressed adapters.
if python3 scripts/sync-codex-plugins.py --check; then
  pass "all Codex adapters match source in the real checkout"
else
  fail "all Codex adapters match source in the real checkout"
fi
