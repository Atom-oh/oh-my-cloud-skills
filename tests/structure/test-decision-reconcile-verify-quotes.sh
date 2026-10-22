#!/usr/bin/env bash
# decision-reconcile: verify_quotes.py drops any finding whose quotes are not in the cited ADR.

VQ_SCRIPT="plugins/co-agent/skills/decision-reconcile/scripts/verify_quotes.py"
VQ_TEST="tests/structure/decision_reconcile_verify_quotes_test.py"

assert_file_exists "$VQ_SCRIPT" "verify_quotes.py exists"
assert_file_executable "$VQ_SCRIPT" "verify_quotes.py is executable"
assert_file_exists "$VQ_TEST" "verify_quotes unit tests exist"

VQ_LOG=$(mktemp "${TMPDIR:-/tmp}/drvq.XXXXXX")
if python3 -I "$VQ_TEST" >"$VQ_LOG" 2>&1; then
    pass "verify_quotes unit tests pass ($(grep -E '^(Ran|OK)' "$VQ_LOG" | tr '\n' ' '))"
else
    cat "$VQ_LOG"
    fail "verify_quotes unit tests pass"
fi
rm -f "$VQ_LOG"
