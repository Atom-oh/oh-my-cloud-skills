AGENTCORE_CONVERSION_OUTPUT=$(python3 -B tests/structure/test-agentcore-conversion-regressions.py 2>&1) && AGENTCORE_CONVERSION_RC=0 || AGENTCORE_CONVERSION_RC=$?
assert_eq "0" "$AGENTCORE_CONVERSION_RC" "AgentCore generated runtime, hook coverage and unsupported Lambda regressions pass"
if [[ "$AGENTCORE_CONVERSION_RC" != 0 ]]; then
  printf '# %s\n' "$AGENTCORE_CONVERSION_OUTPUT"
fi
