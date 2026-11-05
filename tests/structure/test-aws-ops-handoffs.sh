AWS_OPS_HANDOFF_OUTPUT=$(python3 -B tests/structure/test-aws-ops-handoffs.py 2>&1) && AWS_OPS_HANDOFF_RC=0 || AWS_OPS_HANDOFF_RC=$?
assert_eq "0" "$AWS_OPS_HANDOFF_RC" "AWS Ops host-safe handoffs, secret guidance and pod diagnostics regressions pass"
if [[ "$AWS_OPS_HANDOFF_RC" != 0 ]]; then
  printf '# %s\n' "$AWS_OPS_HANDOFF_OUTPUT"
fi
