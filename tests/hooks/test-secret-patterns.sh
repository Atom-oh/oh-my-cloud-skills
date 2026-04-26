#!/usr/bin/env bash
# Test secret detection regex patterns from secret-scan.sh

# --- True Positive tests (MUST detect) ---
assert_grep_match 'AKIA[0-9A-Z]{16}' "AKIAIOSFODNN7EXAMPLE" "TP: AWS Access Key ID"
assert_grep_match 'gh[pousr]_[A-Za-z0-9_]{36,}' "ghp_1234567890abcdefghijklmnopqrstuvwxyz1234" "TP: GitHub Token"
assert_grep_match 'sk-[A-Za-z0-9]{32,}' "sk-1234567890abcdefghijklmnopqrstuvwxyz" "TP: OpenAI/Anthropic Key"

# Runtime-constructed tokens (avoid triggering GitHub Push Protection)
SLACK_PREFIX="xoxb-"
SLACK_BODY="123456789012-1234567890123-abcdef"
assert_grep_match 'xox[baprs]-[A-Za-z0-9-]+' "${SLACK_PREFIX}${SLACK_BODY}" "TP: Slack Bot Token"

assert_grep_match '(password|passwd|pwd)\s*[:=]\s*["'"'"'][^"'"'"']{8,}' 'password="SuperSecret123!"' "TP: Hardcoded Password"

# --- False Positive tests (must NOT detect) ---
assert_grep_no_match 'AKIA[0-9A-Z]{16}' "AKIA_PLACEHOLDER_KEY" "FP: AWS placeholder"
assert_grep_no_match 'AKIA[0-9A-Z]{16}' "dGhpcyBpcyBhIHRlc3Q=" "FP: Normal base64"
assert_grep_no_match '(password|passwd|pwd)\s*[:=]\s*["'"'"'][^"'"'"']{8,}' 'password=""' "FP: Empty password"
assert_grep_no_match '(password|passwd|pwd)\s*[:=]\s*["'"'"'][^"'"'"']{8,}' 'password="short"' "FP: Short password value"
assert_grep_no_match 'gh[pousr]_[A-Za-z0-9_]{36,}' "ghp_placeholder" "FP: GitHub token too short"
assert_grep_no_match 'AKIA[0-9A-Z]{16}' 'AWS_ACCESS_KEY_ID=' "FP: Empty AWS key variable"
