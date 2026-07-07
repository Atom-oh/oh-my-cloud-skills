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
gpt-5.5:kiro-gpt
glm-5:kiro-glm" "$CELLS" "kiro-cells lists all 3 kiro cells in fixed order by default"
python3 "$CFG" codex-enabled --root "$R" >/dev/null 2>&1 && RC=0 || RC=$?
assert_eq "0" "$RC" "codex-enabled exits 0 by default"

# (b) disabling a kiro cell removes it from kiro-cells (and only that one)
python3 "$CFG" set kiro-glm enabled false --root "$R" >/dev/null 2>&1
CELLS_B=$(python3 "$CFG" kiro-cells --root "$R" 2>&1)
assert_eq "claude-opus-4.8:kiro-opus
gpt-5.5:kiro-gpt" "$CELLS_B" "disabling kiro-glm removes only that cell from kiro-cells"

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
python3 "$CFG" set kiro-opus model gpt-5.5 --root "$R2" >/dev/null 2>&1
CELLS_G=$(python3 "$CFG" kiro-cells --root "$R2" 2>&1)
assert_contains "$CELLS_G" "gpt-5.5:kiro-opus" "set <cell> model updates that cell's kiro-cells entry"

# (h) a malformed local override fails CLOSED on the gate paths (kiro-cells/codex-enabled)
# that run-panel.sh actually consumes -- this file doubles as the documented mechanism for
# disabling Kiro on a sensitive diff, so a JSON typo silently falling back to "everything
# enabled" would silently defeat that control (17th review MAJOR-1). `show`/`set` stay
# lenient (operator-facing repair tools), asserted separately below.
R3=$(mktemp -d "${TMPDIR:-/tmp}/prreviewcfg.XXXXXX")
mkdir -p "$R3/.claude"
echo "{not valid json" > "$R3/.claude/pr-review.local.json"
python3 "$CFG" kiro-cells --root "$R3" >/dev/null 2>&1 && RC=0 || RC=$?
assert_eq "1" "$RC" "kiro-cells fails closed (exit 1) on a malformed local override"
python3 "$CFG" codex-enabled --root "$R3" >/dev/null 2>&1 && RC=0 || RC=$?
assert_eq "2" "$RC" "codex-enabled fails closed (exit 2, distinct from disabled=1) on a malformed local override"
CELLS_H=$(python3 "$CFG" show --root "$R3" 2>/dev/null)
assert_contains "$CELLS_H" "kiro-opus" "show stays lenient on a malformed override (falls back to defaults, doesn't crash)"

# (h2) a wrong-shape-but-valid-JSON override (e.g. "panel" isn't an object) also fails
# closed -- deep_merge alone wouldn't catch this (a non-dict value just overwrites the
# key without erroring); validate_shape() is what surfaces it.
R4=$(mktemp -d "${TMPDIR:-/tmp}/prreviewcfg.XXXXXX")
mkdir -p "$R4/.claude"
echo '{"panel": "not-an-object"}' > "$R4/.claude/pr-review.local.json"
python3 "$CFG" kiro-cells --root "$R4" >/dev/null 2>&1 && RC=0 || RC=$?
assert_eq "1" "$RC" "kiro-cells fails closed on a wrong-shape override (panel isn't an object)"

# (h3) set can still repair a malformed override instead of being locked out by it
python3 "$CFG" set kiro-glm enabled false --root "$R3" >/dev/null 2>&1 && RC=0 || RC=$?
assert_eq "0" "$RC" "set succeeds against a malformed override (repairs it rather than refusing)"
CELLS_H3=$(python3 "$CFG" kiro-cells --root "$R3" 2>&1)
assert_eq "claude-opus-4.8:kiro-opus
gpt-5.5:kiro-gpt" "$CELLS_H3" "set's repair replaced the malformed override -- kiro-cells now succeeds"

# (i) $PR_REVIEW_CONFIG_ROOT env is honored when --root is omitted (test-isolation parity
# with co-agent's $CO_AGENT_USER_CONFIG) — same disabled-cell state as (b)/(c) above.
CELLS_I=$(PR_REVIEW_CONFIG_ROOT="$R" python3 "$CFG" kiro-cells 2>&1)
assert_eq "claude-opus-4.8:kiro-opus
gpt-5.5:kiro-gpt" "$CELLS_I" "\$PR_REVIEW_CONFIG_ROOT is honored when --root is omitted"

# (j) MODEL_RE rejects ':' -- run-panel.sh's consumer does a first-colon split
# ("${entry%%:*}"), so a model value containing ':' would be silently truncated instead
# of rejected if this regex allowed it (17th review MINOR).
python3 "$CFG" set kiro-opus model "a:b" --root "$R" >/dev/null 2>&1 && RC=0 || RC=$?
assert_eq "2" "$RC" "set rejects a model value containing ':' (would be silently truncated by run-panel.sh's parser)"

# (k) a hand-edited override with a JSON *string* "false" (not boolean) must fail closed,
# not silently stay enabled -- Python treats "false" as truthy, so `p.get("enabled", True)`
# alone would keep the cell on even though an operator wrote it believing they'd turned it
# off (18th review MAJOR L3-1 -- this file is the documented "disable Kiro on a sensitive
# diff" control, so a wrong-type value here is a security-relevant fail-open, not just a
# usability papercut).
R5=$(mktemp -d "${TMPDIR:-/tmp}/prreviewcfg.XXXXXX")
mkdir -p "$R5/.claude"
echo '{"panel": {"kiro-opus": {"enabled": "false"}}}' > "$R5/.claude/pr-review.local.json"
python3 "$CFG" kiro-cells --root "$R5" >/dev/null 2>&1 && RC=0 || RC=$?
assert_eq "1" "$RC" "kiro-cells fails closed when enabled is a JSON string instead of a boolean"
python3 "$CFG" codex-enabled --root "$R5" >/dev/null 2>&1 && RC=0 || RC=$?
assert_eq "2" "$RC" "codex-enabled fails closed when a cell's enabled is a JSON string instead of a boolean"

# (l) a hand-edited override with an invalid model on a cell left enabled must also fail
# closed -- cmd_kiro_cells' own per-cell check only skips-with-warning (exit 0), which
# silently shrinks the roster without tripping the coverage floor (the exact failure mode
# the floor exists to catch). validate_shape() promotes this to a ConfigError under strict.
R6=$(mktemp -d "${TMPDIR:-/tmp}/prreviewcfg.XXXXXX")
mkdir -p "$R6/.claude"
echo '{"panel": {"kiro-glm": {"model": ""}}}' > "$R6/.claude/pr-review.local.json"
python3 "$CFG" kiro-cells --root "$R6" >/dev/null 2>&1 && RC=0 || RC=$?
assert_eq "1" "$RC" "kiro-cells fails closed when an enabled cell's model is empty"

# (m) a typo'd cell name merges in as a brand-new key that no consumer ever reads -- the
# *correctly*-spelled cell stays at its default (still enabled), so the override is a
# silent no-op instead of the disable the operator intended (19th review MAJOR -- same
# fail-open family as (k)/(l), one level up: a wrong *name* instead of a wrong *value*).
R7=$(mktemp -d "${TMPDIR:-/tmp}/prreviewcfg.XXXXXX")
mkdir -p "$R7/.claude"
echo '{"panel": {"kiro-gml": {"enabled": false}}}' > "$R7/.claude/pr-review.local.json"
python3 "$CFG" kiro-cells --root "$R7" >/dev/null 2>&1 && RC=0 || RC=$?
assert_eq "1" "$RC" "kiro-cells fails closed on a typo'd/unknown cell name"

# (n2) a typo'd key within an otherwise-known cell (e.g. "enabeld" for "enabled") is the
# same failure mode one level down -- also must fail closed.
R8=$(mktemp -d "${TMPDIR:-/tmp}/prreviewcfg.XXXXXX")
mkdir -p "$R8/.claude"
echo '{"panel": {"kiro-glm": {"enabeld": false}}}' > "$R8/.claude/pr-review.local.json"
python3 "$CFG" kiro-cells --root "$R8" >/dev/null 2>&1 && RC=0 || RC=$?
assert_eq "1" "$RC" "kiro-cells fails closed on a typo'd/unknown key within a known cell"

rm -rf "$R" "$R2" "$R3" "$R4" "$R5" "$R6" "$R7" "$R8"
