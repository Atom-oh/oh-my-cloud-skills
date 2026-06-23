#!/usr/bin/env bash
# Tests for co-agent:setup — classify(), access tiers, probe via fake CLIs, report/readers.
CP="plugins/co-agent/skills/co-agent/scripts/check_panel.py"

# --- Task 1: classify() taxonomy ---
assert_file_exists "$CP" "check_panel.py exists"
cl() { printf '%s' "$2" | python3 "$CP" classify --sentinel "$1" --exit "$3" --timeout "$4" 2>&1; }
assert_eq "READY"     "$(cl TOK 'TOK' 0 0)"            "classify: exact sentinel + exit0 → READY"
assert_eq "READY"     "$(cl TOK '  TOK
'  0 0)"                                                "classify: sentinel with surrounding whitespace → READY"
assert_eq "NO_INGEST" "$(cl TOK 'hello there' 0 0)"   "classify: exit0 but no sentinel → NO_INGEST"
assert_eq "AUTH"      "$(cl TOK 'Error: not logged in. Run login' 1 0)" "classify: auth pattern → AUTH"
assert_eq "TIMEOUT"   "$(cl TOK '' 0 1)"              "classify: timed_out → TIMEOUT"
assert_eq "ERROR"     "$(cl TOK 'boom' 7 0)"          "classify: non-zero unknown → ERROR"

# --- Task 2: tiered access decision ---
ac() { python3 "$CP" --selftest-access "$1" "$2" "$3" 2>&1; }
assert_eq "plugin 0" "$(ac codex 1 1)" "codex with plugin+cli → plugin (no install nudge)"
assert_eq "plugin 0" "$(ac codex 0 1)" "codex with plugin only → plugin"
assert_eq "raw 1"    "$(ac codex 1 0)" "codex cli-only → raw + install nudge"
assert_eq "raw 0"    "$(ac agy 1 0)"   "agy cli-only → raw, no nudge (no official plugin)"
assert_eq "none 0"   "$(ac gemini 0 0)" "gemini absent → none"
