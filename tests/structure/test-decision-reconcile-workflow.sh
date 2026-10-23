#!/usr/bin/env bash
# decision-reconcile-panel workflow: orchestration and synthesis against canned agent answers.

DRW_SCRIPT="plugins/co-agent/workflows/decision-reconcile-panel.js"
DRW_TEST="tests/structure/decision_reconcile_workflow_test.cjs"
DRW_SKILL="plugins/co-agent/skills/decision-reconcile/SKILL.md"

assert_file_exists "$DRW_SCRIPT" "decision-reconcile-panel workflow exists"
assert_file_exists "$DRW_TEST" "workflow harness test exists"

# The runtime registers a plugin workflow under its plugin namespace; the bare name is "not found".
DRW_SKILL_TEXT=$(cat "$DRW_SKILL")
assert_contains "$DRW_SKILL_TEXT" 'name: "co-agent:decision-reconcile-panel"' "the skill calls the workflow by its namespaced name"
assert_grep_no_match 'name: "decision-reconcile-panel"' "$DRW_SKILL_TEXT" "the skill never calls the bare workflow name"

if command -v node >/dev/null 2>&1; then
    DRW_LOG=$(mktemp "${TMPDIR:-/tmp}/drw.XXXXXX")
    if node --test "$DRW_TEST" >"$DRW_LOG" 2>&1; then
        pass "workflow harness tests pass ($(grep -E '^# (pass|fail) ' "$DRW_LOG" | tr '\n' ' '))"
    else
        cat "$DRW_LOG"
        fail "workflow harness tests pass"
    fi
    rm -f "$DRW_LOG"
else
    fail "node is required for the workflow harness tests"
fi
