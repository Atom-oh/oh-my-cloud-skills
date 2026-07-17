#!/usr/bin/env bash
# PreToolUse(Bash) hook — when the command is `git commit`, run kiro_review.py on the
# staged diff and block (exit 2) if it finds anything at/above the configured block
# level (default: critical). Fails OPEN on any internal error, missing/unauthenticated
# kiro-cli, or `review.on_commit=false` — a broken reviewer must never wedge commits.
set -euo pipefail

if [ "${KIRO_REVIEW:-}" = "off" ]; then
  exit 0
fi

# Read the hook JSON payload (stdin) for the command that's about to run.
PAYLOAD="$(cat)"
CMD="$(printf '%s' "$PAYLOAD" | python3 -c 'import json,sys
try:
    d = json.load(sys.stdin)
except Exception:
    d = {}
print((d.get("tool_input") or {}).get("command", ""))' 2>/dev/null || true)"

# Match `git commit` at a command boundary (start of line, or after ; & | && ||),
# tolerating `env `/`VAR=val` prefixes — same convention as co-agent's PR-gate regex.
# Blank out quoted spans first so a `git commit` literally inside a string/echo
# doesn't trigger this.
CMD_DETECT="$(printf '%s' "$CMD" | python3 -c 'import re,sys
s = sys.stdin.read()
print(re.sub(r"\x27[^\x27]*\x27|\"[^\"]*\"", lambda m: " " * len(m.group()), s))' 2>/dev/null || true)"

if ! printf '%s' "$CMD_DETECT" | grep -qP '(?:^|[\n;&|])\s*(?:env\s+)?(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*git\s+commit\b'; then
  exit 0
fi

SK="${CLAUDE_PLUGIN_ROOT}/skills/kiro-delegate/scripts"

if ! python3 "$SK/kiro_config.py" review-on-commit --root . >/dev/null 2>&1; then
  exit 0
fi

python3 "$SK/kiro_review.py" --staged --root . 1>&2
exit $?
