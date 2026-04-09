#!/usr/bin/env bash
# Test plugin structure and manifest validity

# Plugin manifests exist
assert_file_exists "plugins/aws-content-plugin/.claude-plugin/plugin.json" "content plugin manifest exists"
assert_file_exists "plugins/aws-ops-plugin/.claude-plugin/plugin.json" "ops plugin manifest exists"
assert_file_exists "plugins/kiro-power-converter/.claude-plugin/plugin.json" "converter plugin manifest exists"
assert_file_exists ".claude-plugin/marketplace.json" "marketplace.json exists"

# Manifests are valid JSON
assert_json_valid "plugins/aws-content-plugin/.claude-plugin/plugin.json" "content plugin.json valid"
assert_json_valid "plugins/aws-ops-plugin/.claude-plugin/plugin.json" "ops plugin.json valid"
assert_json_valid "plugins/kiro-power-converter/.claude-plugin/plugin.json" "converter plugin.json valid"
assert_json_valid ".claude-plugin/marketplace.json" "marketplace.json valid"

# Version consistency
V1=$(python3 -c "import json; print(json.load(open('plugins/aws-content-plugin/.claude-plugin/plugin.json'))['version'])")
V2=$(python3 -c "import json; print(json.load(open('plugins/aws-ops-plugin/.claude-plugin/plugin.json'))['version'])")
V3=$(python3 -c "import json; print(json.load(open('plugins/kiro-power-converter/.claude-plugin/plugin.json'))['version'])")
MV=$(python3 -c "import json; vs=set(p['version'] for p in json.load(open('.claude-plugin/marketplace.json'))['plugins']); print(vs.pop() if len(vs)==1 else 'MISMATCH')")

assert_eq "$V1" "$V2" "content and ops versions match"
assert_eq "$V1" "$V3" "content and converter versions match"
assert_eq "$V1" "$MV" "plugin and marketplace versions match"

# CLAUDE.md files exist
assert_file_exists "CLAUDE.md" "root CLAUDE.md exists"
assert_file_exists "plugins/aws-content-plugin/CLAUDE.md" "content plugin CLAUDE.md exists"

# Key scripts exist and are executable
assert_file_exists "scripts/eval-skills.py" "eval-skills.py exists"
assert_file_exists "scripts/test-plugins.py" "test-plugins.py exists"
