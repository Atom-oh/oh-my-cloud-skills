#!/usr/bin/env bash
# Test hook file existence, permissions, and syntax

# Hook files exist
assert_file_exists ".claude/hooks/check-doc-sync.sh" "check-doc-sync.sh exists"
assert_file_exists ".claude/hooks/secret-scan.sh" "secret-scan.sh exists"
assert_file_exists ".claude/hooks/session-context.sh" "session-context.sh exists"
assert_file_exists ".claude/hooks/notify.sh" "notify.sh exists"

# Hook files are executable
assert_file_executable ".claude/hooks/check-doc-sync.sh" "check-doc-sync.sh is executable"
assert_file_executable ".claude/hooks/secret-scan.sh" "secret-scan.sh is executable"
assert_file_executable ".claude/hooks/session-context.sh" "session-context.sh is executable"
assert_file_executable ".claude/hooks/notify.sh" "notify.sh is executable"

# Hook files have valid bash syntax
assert_bash_syntax ".claude/hooks/check-doc-sync.sh" "check-doc-sync.sh valid syntax"
assert_bash_syntax ".claude/hooks/secret-scan.sh" "secret-scan.sh valid syntax"
assert_bash_syntax ".claude/hooks/session-context.sh" "session-context.sh valid syntax"
assert_bash_syntax ".claude/hooks/notify.sh" "notify.sh valid syntax"

# settings.json exists and is valid JSON
assert_file_exists ".claude/settings.json" "settings.json exists"
assert_json_valid ".claude/settings.json" "settings.json is valid JSON"
