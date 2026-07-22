#!/bin/bash
# Send notifications via webhook on Claude Code events.
# Triggered by Notification events.
# Configure WEBHOOK_URL in .env or export it before use.

WEBHOOK_URL="${CLAUDE_NOTIFY_WEBHOOK:-}"
[ -z "$WEBHOOK_URL" ] && exit 0

EVENT="${1:-unknown}"
MESSAGE="${2:-Claude Code event occurred}"

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

# Send notification (non-blocking)
curl -s -X POST "$WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" > /dev/null 2>&1 &
