# Sourced by tests/run-all.sh; the Python suite stubs every provider process.
if python3 -B tests/structure/test-co-agent-host-runtime.py; then
  pass "co-agent host selection, readiness, and Claude gate runtime regressions"
else
  fail "co-agent host selection, readiness, and Claude gate runtime regressions"
fi
