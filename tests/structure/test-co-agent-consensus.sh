#!/usr/bin/env bash
# Tests for co-agent consensus mode: citation tiers + multi-model panel.

CO="plugins/co-agent/skills/co-agent"
CIT="$CO/scripts/check_citations.py"
CFG="$CO/scripts/co_agent_config.py"
export CO_AGENT_THIRD_AI=agy

assert_file_exists "$CIT" "check_citations.py exists"
assert_file_executable "$CIT" "check_citations.py is executable"
assert_file_exists "$CO/references/consensus-mode.md" "consensus-mode.md exists"

# --- citation tiers ---
CD=$(mktemp "${TMPDIR:-/tmp}/cit.XXXXXX.diff"); CJ=$(mktemp "${TMPDIR:-/tmp}/cit.XXXXXX.json")
printf 'diff --git a/foo.py b/foo.py\n--- a/foo.py\n+++ b/foo.py\n@@ -1,2 +1,3 @@\n ctx\n+open(path)\n+x = 1\n' > "$CD"
printf '[{"ai":"kiro","severity":"HIGH","file":"foo.py","line":2,"snippet":"open(path)","issue":"leak"},{"ai":"codex","severity":"LOW","file":"foo.py","line":99,"issue":"far"},{"ai":"gemini","severity":"HIGH","file":"ghost.py","line":1,"issue":"halluc"}]' > "$CJ"
COUT=$(python3 "$CIT" "$CD" "$CJ" 2>&1)
assert_contains "$COUT" "1 supported" "citation: one supported"
assert_contains "$COUT" "1 needs-review" "citation: one needs-review"
assert_contains "$COUT" "1 unsupported" "citation: one unsupported (hallucinated path)"
rm -f "$CD" "$CJ"

# --- multi-model panel ---
R=$(mktemp -d "${TMPDIR:-/tmp}/coc.XXXXXX")
# Set the profile explicitly so these assertions don't depend on the committed default
# (which is `deep` — opus/kimi/glm as the mainstay Kiro panel).
python3 "$CFG" set profile default --root "$R" >/dev/null 2>&1
DEF=$(python3 "$CFG" pairs --root "$R" 2>/dev/null | wc -l | tr -d ' ')
assert_eq "3" "$DEF" "default profile → one pair per AI (3)"
python3 "$CFG" set profile deep --root "$R" >/dev/null 2>&1
DEEP=$(python3 "$CFG" pairs --root "$R" 2>/dev/null | wc -l | tr -d ' ')
assert_eq "5" "$DEEP" "deep profile → kiro 3 models + codex + agy (5)"
assert_contains "$(python3 "$CFG" matrix --root "$R" 2>&1)" "max calls" "matrix prints max-calls budget"
# Kiro's 3 models (opus/kimi/glm) are cross-vendor via the router → intended diversity,
# NOT the same-family redundancy warning.
assert_contains "$(python3 "$CFG" matrix --root "$R" 2>&1)" "cross-vendor" "matrix notes kiro cross-vendor diversity"
# A genuine same-family duplicate (two Agy-routed models) DOES warn.
python3 "$CFG" set agy models "gemini-2.5-pro,gemini-2.5-flash" --root "$R" >/dev/null 2>&1
assert_contains "$(python3 "$CFG" matrix --root "$R" 2>&1)" "same provider family" "matrix warns on same-family duplicates"
# invalid model name in list rejected (space/comma are list delimiters, so use a
# genuine shell metacharacter to trigger MODEL_RE rejection)
python3 "$CFG" set kiro models "good-model;rm" --root "$R" >/dev/null 2>&1 && MB=0 || MB=$?
assert_eq "2" "$MB" "models list rejects names with shell metacharacters"
rm -rf "$R"
unset CO_AGENT_THIRD_AI
