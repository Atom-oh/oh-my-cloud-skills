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
assert_eq "none 0"   "$(ac kiro-cli 0 0)" "no cli, no plugin → none"

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
assert_eq "ABSENT"    "$(PATH="$SHIM" python3 "$CP" probe claude 2>&1)"         "probe: known peer, missing CLI → ABSENT"
# Gemini support was removed (Agy superseded it — ADR-010): it is not an ADAPTERS entry at
# all, so probing it is an unknown-peer ERROR, not ABSENT (ABSENT implies "recognized but
# not installed", which would misrepresent gemini as still a supported peer).
assert_eq "ERROR"     "$(PATH="$SHIM" python3 "$CP" probe gemini 2>&1)"         "probe: unsupported peer → ERROR, not ABSENT"
rm -rf "$SHIM"

# --- Task 4: report + readers (fake CLIs so probe is deterministic) ---
S2=$(mktemp -d "${TMPDIR:-/tmp}/coagent-shim2.XXXXXX"); R=$(mktemp -d "${TMPDIR:-/tmp}/coagent-root.XXXXXX")
printf '#!/usr/bin/env bash\ncat\n' > "$S2/codex"; chmod +x "$S2/codex"   # codex READY via stdin echo
# Isolated PATH: shim dir + a python3 symlink + /usr/bin:/bin (for the shim shebang) — but NOT
# ~/.local/bin or /usr/local/bin where the real peer CLIs install. Otherwise report() probes a
# real kiro-cli/agy/gemini, which can hang on an interactive prompt and make the suite flaky.
ln -sf "$(command -v python3)" "$S2/python3"
ISO="$S2:/usr/bin:/bin"
PATH="$ISO" python3 "$CP" report --root "$R" --plugins-root /nonexistent >/dev/null 2>&1
SUM="$R/.claude/co-agent-panel.local.json"
assert_file_exists "$SUM" "report writes the readiness summary"
assert_json_valid "$SUM" "summary is valid JSON"
assert_contains "$(cat "$SUM")" "schema_version" "summary has schema_version"
assert_contains "$(cat "$SUM")" "generated_at" "summary has generated_at"
assert_contains "$(cat "$SUM")" "config_hash" "summary has config_hash"
assert_eq "READY" "$(PATH="$ISO" python3 "$CP" status codex --root "$R" 2>&1)" "status reader returns codex READY"
assert_eq "raw"   "$(PATH="$ISO" python3 "$CP" access codex --root "$R" 2>&1)" "access reader returns codex raw (no plugin)"
assert_eq "none"  "$(python3 "$CP" access codex --root "$(mktemp -d)" 2>&1)" "access reader: no summary → sane default none"
rm -rf "$S2" "$R"

# --- Task 5: command + manifest wiring ---
CMD="plugins/co-agent/commands/setup.md"
assert_file_exists "$CMD" "setup command file exists"
assert_contains "$(cat "$CMD" 2>/dev/null)" "check_panel.py" "command runs check_panel.py"
assert_contains "$(cat "$CMD" 2>/dev/null)" "marketplace add" "command offers the official plugin install"
PJ="plugins/co-agent/.claude-plugin/plugin.json"
assert_eq "True" "$(python3 -c "import json;print('./commands/setup.md' in json.load(open('$PJ'))['commands'])" 2>&1)" "setup registered in plugin.json"
assert_contains "$(cat plugins/co-agent/skills/co-agent/SKILL.md 2>/dev/null)" "co-agent:setup" "SKILL.md mentions setup"
assert_contains "$(cat .gitignore 2>/dev/null)" "co-agent-panel.local.json" "panel summary is gitignored"

# --- Task 6: v3 adapter + readiness consult documented ---
ADP="plugins/co-agent/skills/co-agent/references/ai-cli-adapters.md"
assert_contains "$(cat "$ADP" 2>/dev/null)" " --v3" "Kiro adapter documents --v3"
assert_contains "$(cat "$ADP" 2>/dev/null)" "fs_read" "Kiro adapter uses fs_read tool name"
assert_contains "$(cat "$ADP" 2>/dev/null)" "co-agent-panel.local.json" "adapters doc references readiness summary"
assert_contains "$(cat plugins/co-agent/commands/harness.md 2>/dev/null)" "co-agent-panel" "harness consults readiness (run /co-agent:setup)"

# --- Task 7: review-fix regressions (I1 claude probe, I2 narrowed auth regex, #3 exact plugin-dir match) ---
# I1: claude is a legitimate read-only peer when codex hosts; it must be probeable via stdin.
S7=$(mktemp -d "${TMPDIR:-/tmp}/coagent-shim7.XXXXXX")
printf '#!/usr/bin/env bash\ncat\n' > "$S7/claude"; chmod +x "$S7/claude"
ln -sf "$(command -v python3)" "$S7/python3"
assert_eq "READY" "$(PATH="$S7:$PATH" python3 "$CP" probe claude 2>&1)" "I1: claude adapter present, stdin-echo → READY"
rm -rf "$S7"

# I2: exit-0 output containing "author" must NOT be misclassified AUTH; genuine "not logged in" on exit 1 still AUTH.
assert_eq "NO_INGEST" "$(cl TOK 'written by the author' 0 0)" "I2: 'author' on exit0 → NO_INGEST (not AUTH)"
assert_eq "AUTH" "$(cl TOK 'Error: not logged in' 1 0)" "I2: 'not logged in' on exit1 → still AUTH"

# #3: detect_plugin uses an exact basename match — a fork dir must not falsely satisfy codex's official plugin.
DP_FORK=$(mktemp -d "${TMPDIR:-/tmp}/coagent-pf.XXXXXX"); mkdir -p "$DP_FORK/codex-plugin-cc-fork"
assert_eq "False" "$(python3 -c "import sys; sys.path.insert(0,'plugins/co-agent/skills/co-agent/scripts'); import check_panel; print(check_panel.detect_plugin('codex', '$DP_FORK'))" 2>&1)" "#3: codex-plugin-cc-fork does NOT match official plugin"
DP_OK=$(mktemp -d "${TMPDIR:-/tmp}/coagent-po.XXXXXX"); mkdir -p "$DP_OK/codex-plugin-cc"
assert_eq "True" "$(python3 -c "import sys; sys.path.insert(0,'plugins/co-agent/skills/co-agent/scripts'); import check_panel; print(check_panel.detect_plugin('codex', '$DP_OK'))" 2>&1)" "#3: exact codex-plugin-cc dir matches"
rm -rf "$DP_FORK" "$DP_OK"

# #4: real installs name the on-disk marketplace dir after marketplace.json's own "name"
# field ("openai-codex"), not the git repo's name ("codex-plugin-cc") -- the #3 dir-name-
# only match silently missed this and kept prompting to (re)install an already-installed
# plugin. detect_plugin must also recognize a marketplace.json that declares a plugin entry
# named after the peer ("codex"), regardless of what the marketplace directory is called.
DP_MP=$(mktemp -d "${TMPDIR:-/tmp}/coagent-pm.XXXXXX")
mkdir -p "$DP_MP/marketplaces/openai-codex/.claude-plugin" "$DP_MP/marketplaces/openai-codex/plugins/codex"
cat > "$DP_MP/marketplaces/openai-codex/.claude-plugin/marketplace.json" <<'EOF'
{"name": "openai-codex", "plugins": [{"name": "codex", "source": "./plugins/codex"}]}
EOF
assert_eq "True" "$(python3 -c "import sys; sys.path.insert(0,'plugins/co-agent/skills/co-agent/scripts'); import check_panel; print(check_panel.detect_plugin('codex', '$DP_MP'))" 2>&1)" "#4: marketplace.json declaring a 'codex' plugin entry matches, regardless of directory name"
# a marketplace that happens to be installed but does NOT declare a "codex" plugin entry
# must not false-positive just because *some* marketplace.json exists under plugins_root.
DP_MP_OTHER=$(mktemp -d "${TMPDIR:-/tmp}/coagent-pmo.XXXXXX")
mkdir -p "$DP_MP_OTHER/marketplaces/some-other/.claude-plugin"
cat > "$DP_MP_OTHER/marketplaces/some-other/.claude-plugin/marketplace.json" <<'EOF'
{"name": "some-other", "plugins": [{"name": "unrelated-tool", "source": "./plugins/unrelated-tool"}]}
EOF
assert_eq "False" "$(python3 -c "import sys; sys.path.insert(0,'plugins/co-agent/skills/co-agent/scripts'); import check_panel; print(check_panel.detect_plugin('codex', '$DP_MP_OTHER'))" 2>&1)" "#4: an unrelated marketplace.json does NOT false-positive"
rm -rf "$DP_MP" "$DP_MP_OTHER"
