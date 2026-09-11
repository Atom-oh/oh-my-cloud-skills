if python3 tests/structure/test-codex-rpc.py; then
  pass "Codex runtime probe drains coalesced RPC frames"
else
  fail "Codex runtime probe drains coalesced RPC frames"
fi
