#!/usr/bin/env bash
# decision-reconcile: verify_quotes.py drops any finding whose quotes are not in the cited ADR.

VQ_SCRIPT="plugins/co-agent/skills/decision-reconcile/scripts/verify_quotes.py"
VQ_TEST="tests/structure/decision_reconcile_verify_quotes_test.py"

assert_file_exists "$VQ_SCRIPT" "verify_quotes.py exists"
assert_file_exists "$VQ_TEST" "verify_quotes unit tests exist"

VQ_LOG=$(mktemp "${TMPDIR:-$HOME/.tmp}/drvq.XXXXXX")
python3 -I "$VQ_TEST" >"$VQ_LOG" 2>&1
VQ_RC=$?
assert_eq "0" "$VQ_RC" "verify_quotes unit tests pass ($(grep -E '^(Ran|OK|FAILED)' "$VQ_LOG" | tr '\n' ' '))"
rm -f "$VQ_LOG"
