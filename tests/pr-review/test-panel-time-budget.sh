# Run only local fake launchers; TMPDIR is supplied by the invoking test runner.
if python3 -B tests/pr-review/test-panel-time-budget.py; then
  pass "panel cell total deadline, retry allowances, numeric bounds and Kiro isolation"
else
  fail "panel cell total deadline, retry allowances, numeric bounds and Kiro isolation"
fi
