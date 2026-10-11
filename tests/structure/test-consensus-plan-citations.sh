CONSENSUS_CITATIONS_OUTPUT=$(python3 -B tests/structure/test-consensus-plan-citations.py 2>&1) && CONSENSUS_CITATIONS_RC=0 || CONSENSUS_CITATIONS_RC=$?
assert_eq "0" "$CONSENSUS_CITATIONS_RC" "consensus plan/diff citation regressions pass"
if [[ "$CONSENSUS_CITATIONS_RC" != 0 ]]; then
  printf '# %s\n' "$CONSENSUS_CITATIONS_OUTPUT"
fi
