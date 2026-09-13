#!/usr/bin/env bash
if ! declare -F pass >/dev/null; then
  pass() { echo "ok - $1"; }
  fail() { echo "not ok - $1" >&2; exit 1; }
fi
if python3 tests/pr-review/test-provider-diagnostics.py; then
  pass "provider diagnostics, bounded recovery and explicit model pins"
else
  fail "provider diagnostics, bounded recovery and explicit model pins"
fi
