#!/usr/bin/env bash
# Tests for co-agent consensus mode: citation tiers + multi-model panel.

CO="plugins/co-agent/skills/co-agent"
CIT="$CO/scripts/check_citations.py"
CFG="$CO/scripts/co_agent_config.py"

assert_file_exists "$CIT" "check_citations.py exists"
assert_file_executable "$CIT" "check_citations.py is executable"
assert_file_exists "$CO/references/consensus-mode.md" "consensus-mode.md exists"

# --- citation tiers ---
CD=$(mktemp "${TMPDIR:-/tmp}/cit.XXXXXX.diff"); CJ=$(mktemp "${TMPDIR:-/tmp}/cit.XXXXXX.json")
printf 'diff --git a/foo.py b/foo.py\n--- a/foo.py\n+++ b/foo.py\n@@ -1,1 +1,3 @@\n ctx\n+open(path)\n+x = 1\n' > "$CD"
printf '[{"ai":"kiro-cli","severity":"HIGH","file":"foo.py","line":2,"snippet":"open(path)","issue":"leak"},{"ai":"codex","severity":"LOW","file":"foo.py","line":99,"issue":"far"},{"ai":"gemini","severity":"HIGH","file":"ghost.py","line":1,"issue":"halluc"}]' > "$CJ"
COUT=$(python3 "$CIT" "$CD" "$CJ" 2>&1)
assert_contains "$COUT" "1 supported" "citation: one supported"
assert_contains "$COUT" "1 needs-review" "citation: one needs-review"
assert_contains "$COUT" "1 unsupported" "citation: one unsupported (hallucinated path)"
rm -f "$CD" "$CJ"

# --- multi-model panel ---
R=$(mktemp -d "${TMPDIR:-/tmp}/coc.XXXXXX")
# Shipped defaults disable Kiro with an empty models list, and Kiro joins only an eligible
# AWS task scope. Enable Kiro with a two-model fixture list, set the profile explicitly,
# and scope each Kiro-inclusive command inline (nothing leaks into later sourced suites).
CO_AGENT_HOST=claude python3 "$CFG" set kiro-cli enabled true --root "$R" >/dev/null 2>&1
CO_AGENT_HOST=claude python3 "$CFG" set kiro-cli models "kiro-model-a,kiro-model-b" --root "$R" >/dev/null 2>&1
CO_AGENT_HOST=claude python3 "$CFG" set profile default --root "$R" >/dev/null 2>&1
DEF=$(CO_AGENT_TASK_SCOPE=aws-architecture-review CO_AGENT_HOST=claude python3 "$CFG" pairs --root "$R" 2>/dev/null | wc -l | tr -d ' ')
assert_eq "2" "$DEF" "default profile → one pair per external AI (2)"
UDEF=$(env -u CO_AGENT_TASK_SCOPE CO_AGENT_HOST=claude python3 "$CFG" pairs --root "$R" 2>/dev/null | cut -f1 | paste -sd ' ' -)
assert_eq "codex" "$UDEF" "unscoped default profile excludes the enabled Kiro"
CO_AGENT_HOST=claude python3 "$CFG" set profile deep --root "$R" >/dev/null 2>&1
DEEP=$(CO_AGENT_TASK_SCOPE=aws-architecture-review CO_AGENT_HOST=claude python3 "$CFG" pairs --root "$R" 2>/dev/null | wc -l | tr -d ' ')
assert_eq "3" "$DEEP" "deep profile → kiro-cli 2 models + codex (3)"
UDEEP=$(env -u CO_AGENT_TASK_SCOPE CO_AGENT_HOST=claude python3 "$CFG" pairs --root "$R" 2>/dev/null | cut -f1 | paste -sd ' ' -)
assert_eq "codex" "$UDEEP" "unscoped deep profile excludes the enabled Kiro"
# --profile: per-invocation tiering override (hybrid gate: find=deep, verify=default)
POV=$(CO_AGENT_TASK_SCOPE=aws-architecture-review CO_AGENT_HOST=claude python3 "$CFG" pairs --profile default --root "$R" 2>/dev/null | wc -l | tr -d ' ')
assert_eq "2" "$POV" "pairs --profile default overrides configured deep (2 pairs)"
CO_AGENT_HOST=claude python3 "$CFG" set profile default --root "$R" >/dev/null 2>&1
POV2=$(CO_AGENT_TASK_SCOPE=aws-architecture-review CO_AGENT_HOST=claude python3 "$CFG" pairs --profile deep --root "$R" 2>/dev/null | wc -l | tr -d ' ')
assert_eq "3" "$POV2" "pairs --profile deep overrides configured default (3 pairs)"
CO_AGENT_HOST=claude python3 "$CFG" set profile deep --root "$R" >/dev/null 2>&1
CO_AGENT_HOST=claude python3 "$CFG" pairs --profile bogus --root "$R" >/dev/null 2>&1 && PB=0 || PB=$?
assert_eq "2" "$PB" "pairs --profile with invalid value rejected (exit 2)"
CO_AGENT_HOST=claude python3 "$CFG" pairs --root "$R" --profile >/dev/null 2>&1 && PM=0 || PM=$?
assert_eq "2" "$PM" "pairs --profile with missing value hard-fails (exit 2)"
assert_contains "$(CO_AGENT_HOST=claude python3 "$CFG" matrix --profile default --root "$R" 2>&1)" "profile default" "matrix --profile default reports the overridden profile"
assert_contains "$(CO_AGENT_HOST=claude python3 "$CFG" matrix --root "$R" 2>&1)" "max calls" "matrix prints max-calls budget"
# The fixture's 2 Kiro models are cross-vendor via the Kiro router, so the scoped matrix
# reports intended diversity, NOT the same-family redundancy warning.
assert_contains "$(CO_AGENT_TASK_SCOPE=aws-architecture-review CO_AGENT_HOST=claude python3 "$CFG" matrix --root "$R" 2>&1)" "cross-vendor" "matrix notes kiro-cli cross-vendor diversity"
assert_grep_no_match "kiro-cli" "$(env -u CO_AGENT_TASK_SCOPE CO_AGENT_HOST=claude python3 "$CFG" matrix --root "$R" 2>&1)" "unscoped matrix omits the enabled Kiro"
# A genuine same-family duplicate (two Codex models) DOES warn.
CO_AGENT_HOST=claude python3 "$CFG" set codex models "Model Alpha (High),Model Beta" --root "$R" >/dev/null 2>&1
assert_contains "$(CO_AGENT_HOST=claude python3 "$CFG" matrix --root "$R" 2>&1)" "same provider family" "matrix warns on same-family duplicates"
# invalid model name in list rejected (space/comma are list delimiters, so use a
# genuine shell metacharacter to trigger MODEL_RE rejection)
CO_AGENT_HOST=claude python3 "$CFG" set kiro-cli models "good-model;rm" --root "$R" >/dev/null 2>&1 && MB=0 || MB=$?
assert_eq "2" "$MB" "models list rejects names with shell metacharacters"
rm -rf "$R"
