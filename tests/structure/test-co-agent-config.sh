#!/usr/bin/env bash
# Tests for co-agent co_agent_config.py — panel model/effort/enabled/timeout settings.
# Only headless-settable options are exposed.

CFG="plugins/co-agent/skills/co-agent/scripts/co_agent_config.py"
DEF="plugins/co-agent/skills/co-agent/co-agent.defaults.json"
export CO_AGENT_THIRD_AI=agy

assert_file_exists "$CFG" "co_agent_config.py exists"
assert_file_executable "$CFG" "co_agent_config.py is executable"
assert_json_valid "$DEF" "co-agent.defaults.json is valid JSON"

R=$(mktemp -d "${TMPDIR:-/tmp}/coagentcfg.XXXXXX")

# show on a fresh root → all three AIs + default timeout
SHOW=$(python3 "$CFG" show --root "$R" 2>&1)
assert_contains "$SHOW" "kiro-cli" "show lists kiro-cli"
assert_contains "$SHOW" "codex" "show lists codex"
assert_contains "$SHOW" "agy" "show lists agy"
assert_contains "$SHOW" "240" "show reports default timeout 240"

# Codex-hosted co-agent swaps the current host out of the advisory panel:
# Codex chairs; Claude becomes the external reviewer instead of calling Codex again.
CODEX_HOST_SHOW=$(python3 "$CFG" show --host codex --root "$R" 2>&1)
assert_contains "$CODEX_HOST_SHOW" "host codex" "codex-host show reports host"
assert_contains "$CODEX_HOST_SHOW" "claude" "codex-host show lists claude"
CODEX_HOST_PANEL=$(python3 "$CFG" panel --host codex --root "$R" 2>&1)
assert_eq "kiro-cli claude agy" "$CODEX_HOST_PANEL" "codex-host panel swaps codex for claude and prefers agy"

python3 "$CFG" set claude model sonnet --host codex --root "$R" >/dev/null 2>&1
python3 "$CFG" set claude effort max --host codex --root "$R" >/dev/null 2>&1
CLAUDE_FLAGS=$(python3 "$CFG" flags claude --host codex --root "$R" 2>&1 | tr '\n' ' ')   # flags are newline-delimited
assert_contains "$CLAUDE_FLAGS" "model sonnet" "claude flags include model (--model)"
assert_contains "$CLAUDE_FLAGS" "effort max" "claude flags include effort"

# Legacy fallback can still produce a Gemini panel when Agy is unavailable.
LEGACY_PANEL=$(CO_AGENT_THIRD_AI=gemini python3 "$CFG" panel --root "$R" 2>&1)
assert_eq "kiro-cli codex gemini" "$LEGACY_PANEL" "legacy fallback panel uses gemini when agy is unavailable"

# effort is available only where the headless CLI supports it; others show n/a
assert_contains "$SHOW" "n/a" "effort marked n/a for non-Codex"
# context window column present in show
assert_contains "$SHOW" "272,000" "show reports codex context window"

# set Codex model + effort → flags inject -m and reasoning effort
python3 "$CFG" set codex model gpt-5-codex --root "$R" >/dev/null 2>&1
python3 "$CFG" set codex effort high --root "$R" >/dev/null 2>&1
CODEX_FLAGS=$(python3 "$CFG" flags codex --root "$R" 2>&1 | tr '\n' ' ')   # flags are newline-delimited
# needle avoids a leading '-' so grep (in assert_contains) doesn't read it as a flag
assert_contains "$CODEX_FLAGS" "m gpt-5-codex" "codex flags include model (-m)"
assert_contains "$CODEX_FLAGS" 'model_reasoning_effort="high"' "codex flags include effort"
# agy model tokens contain spaces + parens (e.g. "Gemini 3.1 Pro (High)") — accepted, carried as ONE flag token
python3 "$CFG" set agy model "Gemini 3.1 Pro (High)" --root "$R" >/dev/null 2>&1 && AM=0 || AM=$?
assert_eq "0" "$AM" "agy spaced model accepted (exit 0)"
AGY_FLAGS=$(python3 "$CFG" flags agy --host claude --root "$R" 2>&1 | tr '\n' ' ')
assert_contains "$AGY_FLAGS" "model Gemini 3.1 Pro (High)" "agy flags carry the spaced model as one token"
# shell metacharacters in a model value are still rejected
python3 "$CFG" set agy model "Gemini; rm -rf /" --root "$R" >/dev/null 2>&1 && MM=0 || MM=$?
assert_eq "2" "$MM" "model with shell metacharacter still rejected (exit 2)"

# effort on a non-effort AI is rejected (not a dead setting)
python3 "$CFG" set agy effort high --root "$R" >/dev/null 2>&1 && GE_RC=0 || GE_RC=$?
assert_eq "2" "$GE_RC" "set agy effort → rejected (exit 2)"

# invalid effort value rejected
python3 "$CFG" set codex effort turbo --root "$R" >/dev/null 2>&1 && IE_RC=0 || IE_RC=$?
assert_eq "2" "$IE_RC" "invalid effort value → exit 2"

# disable kiro-cli → dropped from panel, enabled check fails
python3 "$CFG" set kiro-cli enabled false --root "$R" >/dev/null 2>&1
PANEL=$(python3 "$CFG" panel --root "$R" 2>&1)
assert_eq "codex agy" "$PANEL" "disabled kiro-cli removed from panel"
python3 "$CFG" enabled kiro-cli --root "$R" >/dev/null 2>&1 && KI_RC=0 || KI_RC=$?
assert_eq "1" "$KI_RC" "enabled kiro-cli → exit 1 when disabled"
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

# model value is charset-validated (blocks shell-metachar / glob injection at the source)
python3 "$CFG" set codex model 'x; rm -rf ~' --root "$R" >/dev/null 2>&1 && MJ=0 || MJ=$?
assert_eq "2" "$MJ" "model with shell metachars rejected (exit 2)"
python3 "$CFG" set codex model '*' --root "$R" >/dev/null 2>&1 && MG=0 || MG=$?
assert_eq "2" "$MG" "model with glob char rejected (exit 2)"
python3 "$CFG" set codex model gpt-4.1 --root "$R" >/dev/null 2>&1 && MV=0 || MV=$?
assert_eq "0" "$MV" "valid model accepted (exit 0)"

# context-size guard: defaults Kiro/Agy 1M, Codex 272K
R3=$(mktemp -d "${TMPDIR:-/tmp}/coagentctx3.XXXXXX")
assert_eq "272000" "$(python3 "$CFG" context-limit codex --root "$R3" 2>&1)" "codex default context-limit 272000"
assert_eq "1000000" "$(python3 "$CFG" context-limit kiro-cli --root "$R3" 2>&1)" "kiro-cli default context-limit 1000000"
assert_eq "1000000" "$(python3 "$CFG" context-limit agy --root "$R3" 2>&1)" "agy default context-limit 1000000"
python3 "$CFG" fits codex 200000 --root "$R3" >/dev/null 2>&1 && F1=0 || F1=$?
assert_eq "0" "$F1" "200K tokens fits codex window (exit 0)"
python3 "$CFG" fits codex 812861 --root "$R3" >/dev/null 2>&1 && F2=0 || F2=$?
assert_eq "1" "$F2" "812K tokens exceeds codex window (exit 1)"
python3 "$CFG" fits kiro-cli 812861 --root "$R3" >/dev/null 2>&1 && F3=0 || F3=$?
assert_eq "0" "$F3" "812K tokens fits kiro-cli 1M window (exit 0)"
python3 "$CFG" set codex context_limit 900000 --root "$R3" >/dev/null 2>&1
python3 "$CFG" fits codex 812861 --root "$R3" >/dev/null 2>&1 && F4=0 || F4=$?
assert_eq "0" "$F4" "raised codex context_limit lets 812K fit (exit 0)"
python3 "$CFG" set codex context_limit 0 --root "$R3" >/dev/null 2>&1 && CL0=0 || CL0=$?
assert_eq "2" "$CL0" "context_limit must be positive (0 rejected)"
rm -rf "$R3"

# local override file is written under .claude/
assert_file_exists "$R/.claude/co-agent.local.json" "writes .claude/co-agent.local.json"
assert_json_valid "$R/.claude/co-agent.local.json" "local override is valid JSON"

rm -rf "$R"
unset CO_AGENT_THIRD_AI
