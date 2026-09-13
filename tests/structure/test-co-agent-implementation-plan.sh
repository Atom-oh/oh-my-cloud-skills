# Provider-neutral planner regressions; all external boundaries are mocked.
if TMPDIR="${TMPDIR:-/var/tmp}" python3 tests/structure/test-co-agent-implementation-plan.py; then
  assert_eq "0" "0" "co-agent implementation planning rejects invalid configuration and requires READY review"
else
  assert_eq "0" "1" "co-agent implementation planning rejects invalid configuration and requires READY review"
fi
