#!/usr/bin/env bash
# Tests for co-agent co_agent_config.py — panel model/effort/enabled/timeout settings.
# Only headless-settable options are exposed (model: all 3; effort: Codex only).

CFG="plugins/co-agent/skills/co-agent/scripts/co_agent_config.py"
DEF="plugins/co-agent/skills/co-agent/co-agent.defaults.json"

assert_file_exists "$CFG" "co_agent_config.py exists"
assert_file_executable "$CFG" "co_agent_config.py is executable"
assert_json_valid "$DEF" "co-agent.defaults.json is valid JSON"

R=$(mktemp -d "${TMPDIR:-/tmp}/coagentcfg.XXXXXX")

# show on a fresh root → all three AIs + default timeout
SHOW=$(python3 "$CFG" show --root "$R" 2>&1)
assert_contains "$SHOW" "kiro" "show lists kiro"
assert_contains "$SHOW" "codex" "show lists codex"
assert_contains "$SHOW" "gemini" "show lists gemini"
assert_contains "$SHOW" "240" "show reports default timeout 240"

# effort is Codex-only — show marks gemini/kiro as n/a
assert_contains "$SHOW" "n/a (CLI has no headless effort)" "effort marked n/a for non-Codex"

# set Codex model + effort → flags inject -m and reasoning effort
python3 "$CFG" set codex model gpt-5-codex --root "$R" >/dev/null 2>&1
python3 "$CFG" set codex effort high --root "$R" >/dev/null 2>&1
CODEX_FLAGS=$(python3 "$CFG" flags codex --root "$R" 2>&1)
# needle avoids a leading '-' so grep (in assert_contains) doesn't read it as a flag
assert_contains "$CODEX_FLAGS" "m gpt-5-codex" "codex flags include model (-m)"
assert_contains "$CODEX_FLAGS" 'model_reasoning_effort="high"' "codex flags include effort"

# effort on a non-Codex AI is rejected (not a dead setting)
python3 "$CFG" set gemini effort high --root "$R" >/dev/null 2>&1 && GE_RC=0 || GE_RC=$?
assert_eq "2" "$GE_RC" "set gemini effort → rejected (exit 2)"

# invalid effort value rejected
python3 "$CFG" set codex effort turbo --root "$R" >/dev/null 2>&1 && IE_RC=0 || IE_RC=$?
assert_eq "2" "$IE_RC" "invalid effort value → exit 2"

# disable kiro → dropped from panel, enabled check fails
python3 "$CFG" set kiro enabled false --root "$R" >/dev/null 2>&1
PANEL=$(python3 "$CFG" panel --root "$R" 2>&1)
assert_eq "codex gemini" "$PANEL" "disabled kiro removed from panel"
python3 "$CFG" enabled kiro --root "$R" >/dev/null 2>&1 && KI_RC=0 || KI_RC=$?
assert_eq "1" "$KI_RC" "enabled kiro → exit 1 when disabled"
python3 "$CFG" enabled codex --root "$R" >/dev/null 2>&1 && CO_RC=0 || CO_RC=$?
assert_eq "0" "$CO_RC" "enabled codex → exit 0 when enabled"

# timeout round-trip
python3 "$CFG" set timeout 300 --root "$R" >/dev/null 2>&1
assert_eq "300" "$(python3 "$CFG" timeout --root "$R" 2>&1)" "set/get timeout round-trips"

# autosync (sync-on-change) toggle: default off, opt-in
R2=$(mktemp -d "${TMPDIR:-/tmp}/coagentcfg2.XXXXXX")
python3 "$CFG" autosync --root "$R2" >/dev/null 2>&1 && AS0=0 || AS0=$?
assert_eq "1" "$AS0" "autosync default off → exit 1"
python3 "$CFG" set autosync on --root "$R2" >/dev/null 2>&1
python3 "$CFG" autosync --root "$R2" >/dev/null 2>&1 && AS1=0 || AS1=$?
assert_eq "0" "$AS1" "set autosync on → exit 0"
assert_contains "$(python3 "$CFG" show --root "$R2" 2>&1)" "autosync on" "show reports autosync on"
python3 "$CFG" set autosync bogus --root "$R2" >/dev/null 2>&1 && ASB=0 || ASB=$?
assert_eq "2" "$ASB" "invalid autosync value → exit 2"
rm -rf "$R2"

# local override file is written under .claude/
assert_file_exists "$R/.claude/co-agent.local.json" "writes .claude/co-agent.local.json"
assert_json_valid "$R/.claude/co-agent.local.json" "local override is valid JSON"

rm -rf "$R"
