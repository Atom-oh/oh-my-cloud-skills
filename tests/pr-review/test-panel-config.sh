#!/usr/bin/env bash
# Tests for scripts/pr-review/panel_config.py — pr-review lens×model matrix membership.
# Mirrors tests/structure/test-co-agent-config.sh's style (sourced by run-all.sh; uses the
# harness's exported assert_* helpers — not standalone-runnable, same as that file).

CFG="scripts/pr-review/panel_config.py"
DEF="scripts/pr-review/pr-review.defaults.json"

assert_file_exists "$CFG" "panel_config.py exists"
assert_file_executable "$CFG" "panel_config.py is executable"
assert_json_valid "$DEF" "pr-review.defaults.json is valid JSON"

R=$(mktemp -d "${TMPDIR:-/tmp}/prreviewcfg.XXXXXX")

# (a) fresh --root → all 3 kiro cells + codex enabled by default
CELLS=$(python3 "$CFG" kiro-cells --root "$R" 2>&1)
assert_eq "claude-opus-4.8:kiro-opus
kimi-k2.5:kiro-kimi
glm-5:kiro-glm" "$CELLS" "kiro-cells lists all 3 kiro cells in fixed order by default"
python3 "$CFG" codex-enabled --root "$R" >/dev/null 2>&1 && RC=0 || RC=$?
assert_eq "0" "$RC" "codex-enabled exits 0 by default"

# (b) disabling a kiro cell removes it from kiro-cells (and only that one)
python3 "$CFG" set kiro-glm enabled false --root "$R" >/dev/null 2>&1
CELLS_B=$(python3 "$CFG" kiro-cells --root "$R" 2>&1)
assert_eq "claude-opus-4.8:kiro-opus
kimi-k2.5:kiro-kimi" "$CELLS_B" "disabling kiro-glm removes only that cell from kiro-cells"

# (c) disabling codex flips codex-enabled's exit code
python3 "$CFG" set codex enabled false --root "$R" >/dev/null 2>&1
python3 "$CFG" codex-enabled --root "$R" >/dev/null 2>&1 && RC=0 || RC=$?
assert_eq "1" "$RC" "codex-enabled exits 1 after set codex enabled false"

# (d) unknown cell name is rejected
python3 "$CFG" set nope enabled true --root "$R" >/dev/null 2>&1 && RC=0 || RC=$?
assert_eq "2" "$RC" "set rejects an unknown cell name"

# (e) invalid enabled value is rejected
python3 "$CFG" set kiro-opus enabled maybe --root "$R" >/dev/null 2>&1 && RC=0 || RC=$?
assert_eq "2" "$RC" "set rejects a non-boolean enabled value"

# (f) codex has no model knob
python3 "$CFG" set codex model gpt-5.5 --root "$R" >/dev/null 2>&1 && RC=0 || RC=$?
assert_eq "2" "$RC" "set codex model is rejected (codex has no model knob)"

# (g) changing a kiro cell's model shows up in kiro-cells output
R2=$(mktemp -d "${TMPDIR:-/tmp}/prreviewcfg.XXXXXX")
python3 "$CFG" set kiro-opus model kimi-k2.5 --root "$R2" >/dev/null 2>&1
CELLS_G=$(python3 "$CFG" kiro-cells --root "$R2" 2>&1)
assert_contains "$CELLS_G" "kimi-k2.5:kiro-opus" "set <cell> model updates that cell's kiro-cells entry"

# (h) a malformed local override warns but doesn't crash — falls back to defaults
R3=$(mktemp -d "${TMPDIR:-/tmp}/prreviewcfg.XXXXXX")
mkdir -p "$R3/.claude"
echo "{not valid json" > "$R3/.claude/pr-review.local.json"
CELLS_H=$(python3 "$CFG" kiro-cells --root "$R3" 2>/dev/null)
assert_eq "claude-opus-4.8:kiro-opus
kimi-k2.5:kiro-kimi
glm-5:kiro-glm" "$CELLS_H" "a malformed local override is ignored, not fatal"

# (i) $PR_REVIEW_CONFIG_ROOT env is honored when --root is omitted (test-isolation parity
# with co-agent's $CO_AGENT_USER_CONFIG) — same disabled-cell state as (b)/(c) above.
CELLS_I=$(PR_REVIEW_CONFIG_ROOT="$R" python3 "$CFG" kiro-cells 2>&1)
assert_eq "claude-opus-4.8:kiro-opus
kimi-k2.5:kiro-kimi" "$CELLS_I" "\$PR_REVIEW_CONFIG_ROOT is honored when --root is omitted"

rm -rf "$R" "$R2" "$R3"
