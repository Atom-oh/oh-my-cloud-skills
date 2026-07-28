#!/usr/bin/env bash
# Test plugin structure and manifest validity

# Plugin manifests exist
assert_file_exists "plugins/aws-content-plugin/.claude-plugin/plugin.json" "content plugin manifest exists"
assert_file_exists "plugins/aws-ops-plugin/.claude-plugin/plugin.json" "ops plugin manifest exists"
assert_file_exists "plugins/kiro-power-converter/.claude-plugin/plugin.json" "converter plugin manifest exists"
assert_file_exists ".claude-plugin/marketplace.json" "marketplace.json exists"
assert_file_exists ".agents/plugins/marketplace.json" "codex marketplace.json exists"

# Manifests are valid JSON
assert_json_valid "plugins/aws-content-plugin/.claude-plugin/plugin.json" "content plugin.json valid"
assert_json_valid "plugins/aws-ops-plugin/.claude-plugin/plugin.json" "ops plugin.json valid"
assert_json_valid "plugins/kiro-power-converter/.claude-plugin/plugin.json" "converter plugin.json valid"
assert_json_valid ".claude-plugin/marketplace.json" "marketplace.json valid"
assert_json_valid ".agents/plugins/marketplace.json" "codex marketplace.json valid"

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
assert_file_exists "scripts/test-codex-plugins.py" "test-codex-plugins.py exists"

TOTAL=$((TOTAL + 1))
if python3 scripts/test-codex-plugins.py >/tmp/oh-my-cloud-codex-plugin-test.out 2>&1; then
  echo -e "${GREEN}ok $TOTAL - codex plugin validation passes${NC}"; PASS=$((PASS + 1))
else
  echo -e "${RED}not ok $TOTAL - codex plugin validation passes${NC}"; FAIL=$((FAIL + 1))
  cat /tmp/oh-my-cloud-codex-plugin-test.out
fi

# --- Validator relaxation invariants (plugin manifests + agent tool declarations).
# The agents/skills fallback must stay scoped to the upstream mirror, and a Bash scope
# suffix must be parsed and judged rather than stripped unchecked. Behavioral, against
# synthetic trees — the plugin name list is hardcoded in the validator, so the fixtures
# reuse real names (kiro = ordinary plugin, project-init = the mirror). ---
VAL_TMP="$(mktemp -d)"
[ -n "$VAL_TMP" ] && [ -d "$VAL_TMP" ] || { echo "not ok - mktemp -d failed"; exit 1; }
trap 'rm -rf "$VAL_TMP"' EXIT
mkdir -p "$VAL_TMP/plugins/kiro/.claude-plugin" "$VAL_TMP/.claude-plugin"
printf '{"name":"kiro","version":"1.0.0"}' > "$VAL_TMP/plugins/kiro/.claude-plugin/plugin.json"
printf '{"plugins":[]}' > "$VAL_TMP/.claude-plugin/marketplace.json"
NONMIRROR_OUT="$(python3 scripts/test-plugins.py --root "$VAL_TMP" 2>&1 || true)"
assert_contains "$NONMIRROR_OUT" "Missing required field 'agents'" "an ordinary plugin without an agents field is still an ERROR (the fallback is allowlist-scoped, not blanket)"
assert_contains "$NONMIRROR_OUT" "Missing required field 'skills'" "an ordinary plugin without a skills field is still an ERROR"

mv "$VAL_TMP/plugins/kiro" "$VAL_TMP/plugins/project-init"
printf '{"name":"project-init","version":"1.0.0"}' > "$VAL_TMP/plugins/project-init/.claude-plugin/plugin.json"
MIRROR_OUT="$(python3 scripts/test-plugins.py --root "$VAL_TMP" 2>&1 || true)"
assert_contains "$MIRROR_OUT" "not declared in plugin.json and no agents/\*.md found on disk" "a mirror with neither a declared field nor any file on disk errors instead of passing silently"

# A CLAUDE_ONLY plugin that no longer ships a .codex-plugin manifest must not keep its
# Codex marketplace entry: `expected` never contains it (so the missing-entry check can't
# fire) and its directory exists (so the source-path check passes) — this assertion covers
# the only check standing between a stale entry and a green run.
mkdir -p "$VAL_TMP/.agents/plugins"
printf '%s' '{"name":"oh-my-cloud-skills","interface":{"displayName":"x"},"plugins":[{"name":"project-init","category":"docs","source":{"source":"local","path":"./plugins/project-init"},"policy":{"installation":"AVAILABLE","authentication":"ON_USE"}}]}' > "$VAL_TMP/.agents/plugins/marketplace.json"
STALE_OUT="$(python3 scripts/test-codex-plugins.py --root "$VAL_TMP" 2>&1 || true)"
assert_contains "$STALE_OUT" "deliberately Claude-only" "a stale Codex marketplace entry for a CLAUDE_ONLY plugin is an ERROR"

TOOLS_OUT="$(python3 tests/structure/_tool_decl_probe.py 2>&1 || true)"
assert_contains "$TOOLS_OUT" "SPLIT \['Read', 'Bash(git add:\*, git commit:\*)', 'Grep'\]" "_split_tools keeps a comma INSIDE a Bash scope in one declaration instead of splitting it into two invalid tools"
assert_contains "$TOOLS_OUT" "BALANCED True" "a balanced scope suffix parses"
assert_contains "$TOOLS_OUT" "EXTRA_CLOSE False" "a stray CLOSING paren is reported unbalanced (the earlier depth clamp let it split identically to the valid form and slip past the fullmatch)"
assert_contains "$TOOLS_OUT" "EXTRA_OPEN False" "an unclosed paren is reported unbalanced"
assert_contains "$TOOLS_OUT" "SCOPED_TOOLS \['Bash'\]" "only Bash may carry a scope suffix — a scope on any other tool is an error, not silently stripped"
assert_contains "$TOOLS_OUT" "WIDE \['', '\*', '\*:\*'\]" "wildcard scope items are enumerated so one '*' entry in a comma list is caught, not just a wholly-'*' scope"
assert_contains "$TOOLS_OUT" "MIRRORED \['project-init'\]" "the mirror exception is a named allowlist"
rm -rf "$VAL_TMP"
trap - EXIT
