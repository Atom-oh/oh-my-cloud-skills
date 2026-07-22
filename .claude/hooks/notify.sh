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
# process dangling past the hook's own lifetime). Payload goes via stdin
# (`-d @-`), not as a `-d` argv value — argv is visible to any local user via
# `ps`/`/proc/*/cmdline`, and the payload can carry a commit message or other
# session text that shouldn't be locally readable that way.
printf '%s' "$PAYLOAD" | curl -s --connect-timeout 5 --max-time 10 -X POST "$WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -d @- > /dev/null 2>&1 &
