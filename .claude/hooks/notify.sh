#!/bin/bash
# Send notifications via webhook on Claude Code events.
# Triggered by Notification events.
# Configure WEBHOOK_URL in .env or export it before use.

WEBHOOK_URL="${CLAUDE_NOTIFY_WEBHOOK:-}"
[ -z "$WEBHOOK_URL" ] && exit 0
case "$WEBHOOK_URL" in
    https://*) ;;
    *) echo "[notify] CLAUDE_NOTIFY_WEBHOOK must be https://, refusing to send." >&2; exit 0 ;;
esac
# Without jq, every step below (parsing stdin, building the payload) fails
# silently and would end up POSTing an empty/malformed body with no error —
# fail loudly-but-non-blocking instead (a missing notifier must never affect
# the tool call it's attached to; see also kiro_review.py's fail-open
# convention for the same "missing tool ≠ block the caller" reasoning).
command -v jq >/dev/null 2>&1 || { echo "[notify] jq not found, skipping." >&2; exit 0; }

# Claude Code delivers the Notification hook's payload as JSON on stdin, not
# as $1/$2 — this script's settings.json wiring calls it with no arguments at
# all, so reading positional args here always produced the fallback text
# regardless of the real event. Parse stdin instead.
HOOK_JSON="$(cat)"
EVENT="$(printf '%s' "$HOOK_JSON" | jq -r '.hook_event_name // "unknown"' 2>/dev/null)"
MESSAGE="$(printf '%s' "$HOOK_JSON" | jq -r '.message // "Claude Code event occurred"' 2>/dev/null)"
[ -z "$EVENT" ] && EVENT="unknown"
[ -z "$MESSAGE" ] && MESSAGE="Claude Code event occurred"

# Build payload with jq -n --arg so EVENT/MESSAGE/branch (which can contain
# quotes, backslashes, or newlines — e.g. a commit message passed as MESSAGE)
# are properly JSON-escaped instead of interpolated raw into a JSON literal.
BRANCH="$(git branch --show-current 2>/dev/null || echo 'unknown')"
PROJECT="$(basename "$(pwd)")"
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
PAYLOAD=$(jq -n \
    --arg event "$EVENT" --arg message "$MESSAGE" \
    --arg project "$PROJECT" --arg branch "$BRANCH" --arg ts "$TIMESTAMP" \
    '{text: "[\($event)] \($message)", project: $project, branch: $branch, timestamp: $ts}')

# Send notification (non-blocking, bounded so a hung webhook can't leave a
# process dangling past the hook's own lifetime). The payload already avoids
# curl argv (`-d @-`, stdin) since argv is visible to any local user via
# `ps`/`/proc/*/cmdline` — the webhook URL is exactly as sensitive (it's a
# bearer credential: whoever has it can post as this notifier) and belongs
# off argv too, so it goes in the same place the URL's own config, not the
# `-X POST "$WEBHOOK_URL"` argument. A 600-permission temp file holds both,
# removed by the SAME backgrounded subshell that uses it — not an EXIT trap,
# which would race the removal against the still-running backgrounded curl.
if [[ "$WEBHOOK_URL" == *'"'* ]]; then
    echo "[notify] CLAUDE_NOTIFY_WEBHOOK contains a double-quote, refusing to send." >&2
    exit 0
fi
CURL_CONF="$(mktemp)"
chmod 600 "$CURL_CONF"
cat > "$CURL_CONF" <<EOF
url = "$WEBHOOK_URL"
silent
connect-timeout = 5
max-time = 10
request = POST
header = "Content-Type: application/json"
data-binary = @-
EOF
( printf '%s' "$PAYLOAD" | curl -K "$CURL_CONF" > /dev/null 2>&1; rm -f "$CURL_CONF" ) &
