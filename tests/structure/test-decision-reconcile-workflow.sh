#!/usr/bin/env bash
# decision-reconcile-panel workflow: orchestration and synthesis against canned agent answers.

DRW_SCRIPT="plugins/co-agent/workflows/decision-reconcile-panel.js"
DRW_TEST="tests/structure/decision_reconcile_workflow_test.cjs"

assert_file_exists "$DRW_SCRIPT" "decision-reconcile-panel workflow exists"
assert_file_exists "$DRW_TEST" "workflow harness test exists"

if command -v node >/dev/null 2>&1; then
  DRW_LOG=$(mktemp "${TMPDIR:-$HOME/.tmp}/drw.XXXXXX")
  node --test "$DRW_TEST" >"$DRW_LOG" 2>&1
  DRW_RC=$?
  assert_eq "0" "$DRW_RC" "workflow harness tests pass ($(grep -E '^# (pass|fail) ' "$DRW_LOG" | tr '\n' ' '))"
  rm -f "$DRW_LOG"
else
  assert_eq "node" "missing" "node is required for the workflow harness tests"
fi
