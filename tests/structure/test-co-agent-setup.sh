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

# --- Task 3: probe via fake CLIs on PATH (never the real ones) ---
SHIM=$(mktemp -d "${TMPDIR:-/tmp}/coagent-shim.XXXXXX")
# codex/agy read stdin: a good shim echoes stdin; a bad shim ignores it.
printf '#!/usr/bin/env bash\ncat\n' > "$SHIM/codex"          # echoes stdin → sentinel returns
printf '#!/usr/bin/env bash\necho ignored\n' > "$SHIM/agy"   # ignores stdin → NO_INGEST
# kiro-cli reads the positional INPUT (last non-flag arg). Echo every arg so the sentinel returns.
printf '#!/usr/bin/env bash\nfor a in "$@"; do printf "%%s\\n" "$a"; done\n' > "$SHIM/kiro-cli"
chmod +x "$SHIM/codex" "$SHIM/agy" "$SHIM/kiro-cli"
# python3 may share a dir with a real peer CLI (e.g. /usr/bin); link it into the shim dir so the
# "PATH=$SHIM only" assertion can still run python3 while every real peer CLI stays absent.
ln -sf "$(command -v python3)" "$SHIM/python3"
assert_eq "READY"     "$(PATH="$SHIM:$PATH" python3 "$CP" probe codex 2>&1)"    "probe: stdin-echo codex → READY"
assert_eq "NO_INGEST" "$(PATH="$SHIM:$PATH" python3 "$CP" probe agy 2>&1)"      "probe: stdin-ignoring agy → NO_INGEST"
assert_eq "READY"     "$(PATH="$SHIM:$PATH" python3 "$CP" probe kiro-cli 2>&1)" "probe: kiro-cli argv INPUT echoed → READY"
assert_eq "ABSENT"    "$(PATH="$SHIM" python3 "$CP" probe gemini 2>&1)"         "probe: missing CLI → ABSENT"
rm -rf "$SHIM"

# --- Task 4: report + readers (fake CLIs so probe is deterministic) ---
S2=$(mktemp -d "${TMPDIR:-/tmp}/coagent-shim2.XXXXXX"); R=$(mktemp -d "${TMPDIR:-/tmp}/coagent-root.XXXXXX")
printf '#!/usr/bin/env bash\ncat\n' > "$S2/codex"; chmod +x "$S2/codex"   # codex READY via stdin echo
PATH="$S2:$PATH" python3 "$CP" report --root "$R" --plugins-root /nonexistent >/dev/null 2>&1
SUM="$R/.claude/co-agent-panel.local.json"
assert_file_exists "$SUM" "report writes the readiness summary"
assert_json_valid "$SUM" "summary is valid JSON"
assert_contains "$(cat "$SUM")" "schema_version" "summary has schema_version"
assert_contains "$(cat "$SUM")" "generated_at" "summary has generated_at"
assert_contains "$(cat "$SUM")" "config_hash" "summary has config_hash"
assert_eq "READY" "$(PATH="$S2:$PATH" python3 "$CP" status codex --root "$R" 2>&1)" "status reader returns codex READY"
assert_eq "raw"   "$(PATH="$S2:$PATH" python3 "$CP" access codex --root "$R" 2>&1)" "access reader returns codex raw (no plugin)"
assert_eq "none"  "$(python3 "$CP" access codex --root "$(mktemp -d)" 2>&1)" "access reader: no summary → sane default none"
rm -rf "$S2" "$R"
