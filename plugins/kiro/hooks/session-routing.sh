#!/usr/bin/env bash
# SessionStart hook — emit the plugin banner AND, when the corresponding toggle is on,
# the routing instructions that make `default_delegate` / `websearch.enabled` actually
# fire.
#
# WHY THIS EXISTS: those two rules used to live only in `plugins/kiro/CLAUDE.md`, whose
# own text claimed "this file is always loaded — this is what makes default_delegate
# fire". That premise is FALSE: a plugin's CLAUDE.md is NOT injected into the session
# context (only the *project's* own CLAUDE.md files are). So on every repo where kiro is
# installed as a plugin, the toggle was dead — `default_delegate: true` changed nothing
# and the host kept implementing everything itself, with no error to explain why. The one
# plugin-side channel whose output DOES land in context is a SessionStart hook, so the
# rules have to be emitted from here to be real. `plugins/kiro/CLAUDE.md` keeps the long
# rationale (it's still loaded when working ON this plugin); this script carries the
# minimum the host must know to route correctly in ANY repo.
#
# Deliberately quiet when a toggle is off: an unconditional wall of routing prose on
# every session start is context noise, and the off state needs no instruction.
set -uo pipefail

SK="${CLAUDE_PLUGIN_ROOT}/skills/kiro-delegate/scripts"

echo "kiro loaded. Claude plans + verifies, Kiro CLI implements + reviews (cost savings): /kiro:delegate · review · setup · configure. Run /kiro:setup first to detect kiro-cli and pick models."

# `--root` omitted on purpose: kiro_config.py resolves the repo root itself via
# `git rev-parse --show-toplevel`, so this works from any cwd the session starts in.
# Every check is best-effort — a missing/broken config must never make SessionStart fail
# (a non-zero SessionStart hook is a startup error, far worse than a silent toggle).
if python3 "$SK/kiro_config.py" default-delegate >/dev/null 2>&1; then
  cat <<'ROUTING'

[kiro] default_delegate is ON for this repo. Before starting any non-trivial
implementation task — even when the request never names Kiro ("이 함수 구현해줘",
"add a retry to this function") — route it through `/kiro:delegate` (or the
`kiro-delegate-agent`) instead of implementing it directly. That is the entire point of
the toggle: it moves token-expensive code-writing onto Kiro's flat-rate subscription
credits. Fall back to implementing it yourself ONLY when kiro-cli is unavailable or its
per-task fix loop is exhausted, and say so when you do. Trivial edits (a typo, a
one-line tweak, a rename) do not need delegation.
ROUTING
fi

if python3 "$SK/kiro_config.py" websearch-enabled >/dev/null 2>&1; then
  cat <<'ROUTING'

[kiro] websearch.enabled is ON for this repo. If this session has NO `WebSearch` tool
(the common case on Bedrock) and a task genuinely needs current/external information,
route the search through kiro-cli's native web_search: Write the query to a
per-invocation-unique temp file, then run the command below with that path, and delete
the file afterwards. Never use it when a native WebSearch tool IS available.
ROUTING
  # Printed separately, with the path RESOLVED at hook time. Inside the quoted heredoc
  # above, `$CLAUDE_PLUGIN_ROOT` would reach the host verbatim — and that variable does
  # not exist in the ordinary Bash tool calls the host makes later, so the one command
  # this routing block exists to hand over would fail in every consumer repo. Left as
  # its own `echo` rather than unquoting the heredoc: the text is full of backticks,
  # which an unquoted heredoc would run as command substitution.
  echo "  \`python3 \"$SK/kiro_websearch.py\" --query-file <that path>\`"
fi

exit 0
