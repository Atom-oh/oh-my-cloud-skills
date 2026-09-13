#!/usr/bin/env bash
# Supports the shared harness and the standalone command documented in the guide.
if ! declare -F pass >/dev/null; then
  pass() { echo "ok - $1"; }
  fail() { echo "not ok - $1" >&2; exit 1; }
fi
if python3 tests/pr-review/test-specialist-roles.py; then
  pass "configured specialists retain complete input, unique roles and cross-family risk coverage"
else
  fail "configured specialists retain complete input, unique roles and cross-family risk coverage"
fi
