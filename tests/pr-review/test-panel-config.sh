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

# (a) fresh --root → 2 enabled kiro cells (kiro-opus, kiro-gpt) + codex enabled by
# default; kiro-glm (glm-5) is disabled by default (false-positive rate — see
# AWS-Demo-Platform ADR-015 / this repo's ADR on dropping kiro-glm).
CELLS=$(python3 "$CFG" kiro-cells --root "$R" 2>&1)
assert_eq "claude-opus-5:kiro-opus
gpt-5.6-terra:kiro-gpt" "$CELLS" "kiro-cells lists the 2 enabled kiro cells in fixed order by default (kiro-glm disabled)"
python3 "$CFG" codex-enabled --root "$R" >/dev/null 2>&1 && RC=0 || RC=$?
assert_eq "0" "$RC" "codex-enabled exits 0 by default"

# (b) disabling a kiro cell removes it from kiro-cells (and only that one) — uses
# kiro-gpt since kiro-glm is already disabled by default and wouldn't exercise the
# disable code path.
python3 "$CFG" set kiro-gpt enabled false --root "$R" >/dev/null 2>&1
CELLS_B=$(python3 "$CFG" kiro-cells --root "$R" 2>&1)
assert_eq "claude-opus-5:kiro-opus" "$CELLS_B" "disabling kiro-gpt removes only that cell from kiro-cells"

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
assert_eq "claude-opus-5:kiro-opus
gpt-5.6-terra:kiro-gpt" "$CELLS_H3" "set's repair replaced the malformed override -- kiro-cells now succeeds"

# (i) $PR_REVIEW_CONFIG_ROOT env is honored when --root is omitted (test-isolation parity
# with co-agent's $CO_AGENT_USER_CONFIG) — same disabled-cell state as (b)/(c) above
# (kiro-gpt and codex disabled, kiro-glm disabled by default → only kiro-opus remains).
CELLS_I=$(PR_REVIEW_CONFIG_ROOT="$R" python3 "$CFG" kiro-cells 2>&1)
assert_eq "claude-opus-5:kiro-opus" "$CELLS_I" "\$PR_REVIEW_CONFIG_ROOT is honored when --root is omitted"

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
# kiro-glm defaults to disabled now, so this override must explicitly re-enable it --
# otherwise "enabled" merges in as false from defaults and the model check never fires,
# making the assertion a tautology instead of exercising the invalid-model path.
R6=$(mktemp -d "${TMPDIR:-/tmp}/prreviewcfg.XXXXXX")
mkdir -p "$R6/.claude"
echo '{"panel": {"kiro-glm": {"enabled": true, "model": ""}}}' > "$R6/.claude/pr-review.local.json"
python3 "$CFG" kiro-cells --root "$R6" >/dev/null 2>&1 && RC=0 || RC=$?
assert_eq "1" "$RC" "kiro-cells fails closed when an enabled cell's model is empty"

# (l2) the documented one-command re-enable path (`set kiro-glm enabled true`, no model
# override) must actually work -- this is exactly the regression a bare `{"enabled":
# false}` disabled-default (no model key) would cause: an operator flips enabled back on,
# defaults.json has no model to merge in, validate_shape() raises ConfigError, and
# kiro-cells fails closed for the WHOLE roster, not just kiro-glm. Guards that
# pr-review.defaults.json keeps `model: glm-5` on the disabled entry.
R6B=$(mktemp -d "${TMPDIR:-/tmp}/prreviewcfg.XXXXXX")
python3 "$CFG" set kiro-glm enabled true --root "$R6B" >/dev/null 2>&1
CELLS_R6B=$(python3 "$CFG" kiro-cells --root "$R6B" 2>&1); RC=$?
assert_eq "0" "$RC" "the documented one-command re-enable (set kiro-glm enabled true) does not fail closed"
assert_contains "$CELLS_R6B" "glm-5:kiro-glm" "the documented one-command re-enable actually restores the kiro-glm cell"

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

# (n3) a typo'd *top-level* key (e.g. "panle" for "panel") is the same failure mode one
# level up from (m) -- merges in as a brand-new key, leaving the correctly-spelled "panel"
# untouched at its defaults, so the override is a silent no-op (20th review MAJOR-1).
R9=$(mktemp -d "${TMPDIR:-/tmp}/prreviewcfg.XXXXXX")
mkdir -p "$R9/.claude"
echo '{"panle": {"kiro-opus": {"enabled": false}}}' > "$R9/.claude/pr-review.local.json"
python3 "$CFG" kiro-cells --root "$R9" >/dev/null 2>&1 && RC=0 || RC=$?
assert_eq "1" "$RC" "kiro-cells fails closed on a typo'd/unknown top-level key"

# (o2) defaults.json itself (the committed "경로 A" file docs/ci-pr-review.md now documents
# as the only verified-working way to change CI matrix membership) must be validated too --
# effective() previously only ran validate_shape() when a *local override* was present, so a
# wrong-type value committed straight into defaults.json (e.g. "enabled": "false" as a JSON
# string) sailed through unvalidated on every real CI run (which never has a local override
# -- gitignored + checkout clean). Uses $PR_REVIEW_DEFAULTS_PATH to point at a broken fixture
# without touching the real committed file (21st review MAJOR L3-1).
BROKEN_DEFAULTS=$(mktemp "${TMPDIR:-/tmp}/prreview-defaults.XXXXXX.json")
cat > "$BROKEN_DEFAULTS" <<'EOF'
{
  "panel": {
    "codex":     { "enabled": true },
    "kiro-opus": { "enabled": "false" },
    "kiro-gpt":  { "enabled": true, "model": "gpt-5.5" },
    "kiro-glm":  { "enabled": true, "model": "glm-5" }
  }
}
EOF
R10=$(mktemp -d "${TMPDIR:-/tmp}/prreviewcfg.XXXXXX")
PR_REVIEW_DEFAULTS_PATH="$BROKEN_DEFAULTS" python3 "$CFG" kiro-cells --root "$R10" >/dev/null 2>&1 && RC=0 || RC=$?
assert_eq "1" "$RC" "kiro-cells fails closed when defaults.json itself has a wrong-type value (no local override present)"
PR_REVIEW_DEFAULTS_PATH="$BROKEN_DEFAULTS" python3 "$CFG" show --root "$R10" >/dev/null 2>&1 && RC=0 || RC=$?
assert_eq "1" "$RC" "show also fails closed (clean message, not a raw traceback) on broken defaults.json"
rm -rf "$BROKEN_DEFAULTS" "$R10"

# (o3) a known cell missing *entirely* from defaults.json (e.g. its line deleted while
# hand-editing to remove a flaky model -- the most natural mis-edit) is invisible to every
# per-cell check, since they all iterate panel.items(). cmd_kiro_cells sees the absent cell
# as p={} -> enabled defaults True, model=None -> falls into its own "unreachable under
# strict" defense-in-depth branch, which actually fires here and silently shrinks the
# roster via warn+skip+exit 0 instead of failing closed (22nd review MAJOR).
MISSING_CELL_DEFAULTS=$(mktemp "${TMPDIR:-/tmp}/prreview-defaults.XXXXXX.json")
cat > "$MISSING_CELL_DEFAULTS" <<'EOF'
{
  "panel": {
    "codex":     { "enabled": true },
    "kiro-opus": { "enabled": true, "model": "claude-opus-5" },
    "kiro-gpt":  { "enabled": true, "model": "gpt-5.5" }
  }
}
EOF
R11=$(mktemp -d "${TMPDIR:-/tmp}/prreviewcfg.XXXXXX")
PR_REVIEW_DEFAULTS_PATH="$MISSING_CELL_DEFAULTS" python3 "$CFG" kiro-cells --root "$R11" >/dev/null 2>&1 && RC=0 || RC=$?
assert_eq "1" "$RC" "kiro-cells fails closed when a known cell (kiro-glm) is missing entirely from defaults.json"
rm -rf "$MISSING_CELL_DEFAULTS" "$R11"

rm -rf "$R" "$R2" "$R3" "$R4" "$R5" "$R6" "$R7" "$R8" "$R9"
