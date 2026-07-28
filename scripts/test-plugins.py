#!/usr/bin/env python3
"""Plugin validation test suite for oh-my-cloud-skills."""
import json
import os
import sys
import re
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Valid constants
VALID_MODELS = {"haiku", "sonnet", "opus", "fable"}  # fable = Fable 5, a valid model alias
VALID_TOOLS = {"Read", "Write", "Edit", "Glob", "Grep", "Bash", "AskUserQuestion",
               "Agent", "Skill", "WebFetch", "WebSearch", "NotebookEdit"}
VALID_HOOK_EVENTS = {"SessionStart", "PreToolUse", "PostToolUse", "PostToolUseFailure",
                     "UserPromptSubmit", "Stop", "Notification", "SubagentStart",
                     "SubagentStop", "PermissionRequest", "SessionEnd", "PreCompact"}
VALID_HOOK_TYPES = {"command", "prompt", "agent"}

# Plugins mirrored byte-identically from an upstream fork source, whose plugin.json is
# kept verbatim and therefore declares no agents/skills arrays. ONLY these may fall back
# to on-disk discovery — see test_manifest(). Mirror procedure:
# plugins/project-init/references/upstream-sync.md
# Keep in sync with CLAUDE_ONLY in test-codex-plugins.py (same plugin, other surface).
MIRRORED_PLUGINS = {"project-init"}

# Files under agents/ that are documentation, not agent definitions — discovery must not
# hand them to the frontmatter validator.
NON_AGENT_FILES = {"README.md", "CLAUDE.md"}

# Tools whose `tools:` entry may carry a `(scope)` suffix. Upstream's mirrored
# doc-sync-checker ships `tools: Read, Glob, Grep, Bash(find:*), Bash(git log:*),
# Bash(ls:*)` (arriving with the mirroring in #138 — the copy in THIS tree still declares
# a bare `Bash`), so the parser has to accept the form. Whether Claude Code actually
# honors a scope in a subagent's `tools:` — as opposed to a command's `allowed-tools`,
# where the syntax is documented — is NOT established, so a scoped Bash gets a warning
# rather than being silently blessed as a narrowing that may not exist at runtime.
SCOPED_TOOLS = {"Bash"}
# A scope item that grants everything (`*`, `*:*`) is a lie regardless of enforcement.
UNRESTRICTED_SCOPE_ITEMS = {"", "*", "*:*"}


def _split_tools(tools_str: str) -> Tuple[List[str], bool]:
    """Split a `tools:` string on commas OUTSIDE a scope suffix's parens.

    `Bash(git add:*, git commit:*)` is ONE declaration; a plain `split(',')` would break it
    in half and report both pieces as invalid tools.

    Returns (declarations, balanced). `balanced` is False for any unmatched paren in either
    direction — an earlier version clamped the depth at 0, which made a stray closing paren
    (`Bash(a))`) split identically to the balanced form and then slip past the caller's
    greedy `(.*)` fullmatch as scope `a)`."""
    parts: List[str] = []
    cur = ""
    depth = 0
    balanced = True
    for ch in tools_str:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                balanced = False
                depth = 0        # keep splitting sanely; the caller reports the error
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    if depth != 0:
        balanced = False
    return [p.strip() for p in parts if p.strip()], balanced


class PluginTestSuite:
    """Test suite for validating a single plugin."""

    def __init__(self, plugin_dir: Path, verbose: bool = False):
        self.plugin_dir = plugin_dir
        self.plugin_name = plugin_dir.name
        self.verbose = verbose
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.manifest: Optional[Dict[str, Any]] = None
        self.agent_count = 0
        self.skill_count = 0

    def log(self, msg: str):
        """Print verbose output."""
        if self.verbose:
            print(f"  [DEBUG] {msg}")

    def error(self, msg: str):
        """Record an error."""
        self.errors.append(msg)
        self.log(f"ERROR: {msg}")

    def warn(self, msg: str):
        """Record a warning."""
        self.warnings.append(msg)
        self.log(f"WARN: {msg}")

    def parse_frontmatter(self, filepath: Path) -> Tuple[Dict[str, Any], str]:
        """Parse YAML frontmatter from a markdown file.

        Returns (frontmatter_dict, body_content).
        Simple parser - no pyyaml dependency.
        """
        try:
            content = filepath.read_text(encoding='utf-8')
        except Exception as e:
            self.error(f"Cannot read {filepath}: {e}")
            return {}, ""

        # Check for frontmatter markers
        if not content.startswith('---'):
            return {}, content

        # Find the closing ---
        lines = content.split('\n')
        end_idx = -1
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == '---':
                end_idx = i
                break

        if end_idx == -1:
            self.error(f"Unclosed frontmatter in {filepath}")
            return {}, content

        frontmatter_lines = lines[1:end_idx]
        body = '\n'.join(lines[end_idx + 1:])

        # Parse frontmatter
        result: Dict[str, Any] = {}
        current_key: Optional[str] = None
        current_list: List[str] = []
        in_list = False

        for line in frontmatter_lines:
            # Skip empty lines
            if not line.strip():
                continue

            # Check for list item (starts with "  - " or "- ")
            list_match = re.match(r'^(\s*)-\s+(.*)$', line)
            if list_match:
                indent = len(list_match.group(1))
                value = list_match.group(2).strip()
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]

                if current_key and in_list:
                    current_list.append(value)
                continue

            # Check for key: value pair
            kv_match = re.match(r'^([a-zA-Z_-]+):\s*(.*)$', line)
            if kv_match:
                # Save previous list if any
                if current_key and in_list:
                    result[current_key] = current_list

                current_key = kv_match.group(1)
                value = kv_match.group(2).strip()

                # Empty value means list follows
                if not value:
                    in_list = True
                    current_list = []
                else:
                    in_list = False
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    result[current_key] = value

        # Save final list if any
        if current_key and in_list:
            result[current_key] = current_list

        return result, body

    def test_manifest(self):
        """Test 1: Manifest Validation."""
        self.log("Testing manifest...")
        manifest_path = self.plugin_dir / '.claude-plugin' / 'plugin.json'

        if not manifest_path.exists():
            self.error(f"plugin.json not found at {manifest_path}")
            return

        # Parse JSON
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                self.manifest = json.load(f)
        except json.JSONDecodeError as e:
            self.error(f"Invalid JSON in plugin.json: {e}")
            return

        # Required fields
        for field in ['name', 'version']:
            if field not in self.manifest:
                self.error(f"Missing required field '{field}' in plugin.json")

        if not self.manifest:
            return

        # `agents`/`skills` stay REQUIRED for every plugin except an upstream mirror.
        # A mirror (project-init) carries the fork source's manifest verbatim, which
        # lists neither — Claude Code discovers them by convention — so fall back to
        # on-disk discovery there, and only there, so their frontmatter still gets
        # validated instead of silently skipped. Keeping the exception an allowlist is
        # deliberate: a blanket relaxation would let a typo'd `skills/` directory or an
        # accidentally deleted field pass with 0 discovered files and 0 diagnostics in
        # any of the other plugins.
        for field, pattern in (('agents', 'agents/*.md'), ('skills', 'skills/*/SKILL.md')):
            # `.get() or` (not `in`): an explicit empty `agents: []` from upstream means
            # "nothing declared" too, and must still fall through to discovery.
            if self.manifest.get(field):
                continue
            if self.plugin_name not in MIRRORED_PLUGINS:
                self.error(f"Missing required field '{field}' in plugin.json")
                continue
            found = [f for f in sorted(self.plugin_dir.glob(pattern))
                     if not (field == 'agents' and f.name in NON_AGENT_FILES)]
            if not found:
                # Neither declared nor on disk: for a mirror this is the one case where
                # discovery can't tell "deliberately empty" from "wrong directory name",
                # so say so instead of passing silently.
                self.error(f"'{field}' not declared in plugin.json and no {pattern} "
                           f"found on disk — nothing was validated for this field")
                continue
            if field == 'skills':
                # The declared path errors on a skill dir with no SKILL.md
                # ("SKILL.md not found", below). Discovery globs SKILL.md itself, so it
                # would simply not see that dir — restore the check explicitly.
                for d in sorted(p for p in self.plugin_dir.glob('skills/*') if p.is_dir()):
                    if not (d / 'SKILL.md').exists():
                        self.error(f"Skill directory has no SKILL.md: "
                                   f"{d.relative_to(self.plugin_dir).as_posix()}")
            # Injected into the manifest on purpose: every path/frontmatter check below
            # reads it from there, and the log line beneath records that this field came
            # from disk rather than from the file.
            self.manifest[field] = [
                './' + (f.parent if field == 'skills' else f)
                .relative_to(self.plugin_dir).as_posix()
                for f in found
            ]
            self.log(f"{field} not declared in plugin.json — discovered {len(found)} on disk")

        # Validate agent paths
        agents = self.manifest.get('agents', [])
        self.agent_count = len(agents)
        for agent_path in agents:
            # Remove leading ./ if present
            clean_path = agent_path.lstrip('./')
            full_path = self.plugin_dir / clean_path
            if not full_path.exists():
                self.error(f"Agent file not found: {agent_path} -> {full_path}")
            elif not full_path.suffix == '.md':
                self.error(f"Agent file must be .md: {agent_path}")

        # Validate skill paths
        skills = self.manifest.get('skills', [])
        self.skill_count = len(skills)
        for skill_path in skills:
            clean_path = skill_path.lstrip('./')
            skill_dir = self.plugin_dir / clean_path
            if not skill_dir.exists():
                self.error(f"Skill directory not found: {skill_path} -> {skill_dir}")
            elif not skill_dir.is_dir():
                self.error(f"Skill path is not a directory: {skill_path}")
            else:
                skill_md = skill_dir / 'SKILL.md'
                if not skill_md.exists():
                    self.error(f"SKILL.md not found in {skill_path}")

        # Validate hooks if present
        hooks = self.manifest.get('hooks', {})
        if hooks:
            self._validate_hooks(hooks)

        # Validate mcpServers if present
        mcp_servers = self.manifest.get('mcpServers', {})
        if mcp_servers:
            for server_name, config in mcp_servers.items():
                if 'command' not in config:
                    self.error(f"MCP server '{server_name}' missing 'command' field")

        self.log(f"Manifest OK: {self.agent_count} agents, {self.skill_count} skills")

    def _validate_hooks(self, hooks: Dict[str, Any]):
        """Validate hooks configuration."""
        for event_name, hook_list in hooks.items():
            if event_name not in VALID_HOOK_EVENTS:
                self.error(f"Invalid hook event: '{event_name}' (valid: {VALID_HOOK_EVENTS})")

            if not isinstance(hook_list, list):
                self.error(f"Hook '{event_name}' value must be a list")
                continue

            for hook_entry in hook_list:
                self._validate_hook_entry(event_name, hook_entry)

    def _validate_hook_entry(self, event_name: str, entry: Dict[str, Any]):
        """Validate a single hook entry."""
        # PostToolUse has nested structure with matcher
        if 'hooks' in entry:
            # This is a matcher-style hook (PostToolUse pattern)
            if 'matcher' in entry:
                matcher = entry['matcher']
                if not isinstance(matcher, str) or not matcher:
                    self.error(f"Hook '{event_name}' matcher must be non-empty string")
            for nested_hook in entry.get('hooks', []):
                self._validate_hook_entry(event_name, nested_hook)
            return

        # Direct hook entry
        hook_type = entry.get('type')
        if hook_type not in VALID_HOOK_TYPES:
            self.error(f"Hook '{event_name}' has invalid type: '{hook_type}' (valid: {VALID_HOOK_TYPES})")

        if hook_type == 'command':
            if not entry.get('command'):
                self.error(f"Hook '{event_name}' type=command missing 'command' field")
        elif hook_type == 'prompt':
            if not entry.get('prompt'):
                self.error(f"Hook '{event_name}' type=prompt missing 'prompt' field")

    def test_agents(self):
        """Test 2: Agent Frontmatter Validation."""
        if not self.manifest:
            return

        self.log("Testing agents...")
        agents = self.manifest.get('agents', [])
        skill_names = self._get_skill_names()
        mcp_server_names = set(self.manifest.get('mcpServers', {}).keys())

        for agent_path in agents:
            clean_path = agent_path.lstrip('./')
            full_path = self.plugin_dir / clean_path

            if not full_path.exists():
                continue  # Already reported in test_manifest

            frontmatter, body = self.parse_frontmatter(full_path)

            # Required fields
            if 'name' not in frontmatter:
                self.error(f"Agent {agent_path}: missing 'name' in frontmatter")
            if 'description' not in frontmatter:
                self.error(f"Agent {agent_path}: missing 'description' in frontmatter")
            elif not frontmatter.get('description'):
                self.error(f"Agent {agent_path}: 'description' is empty")

            # Optional model validation
            model = frontmatter.get('model')
            if model and model not in VALID_MODELS:
                self.error(f"Agent {agent_path}: invalid model '{model}' (valid: {VALID_MODELS})")

            # Optional skills validation
            agent_skills = frontmatter.get('skills', [])
            if isinstance(agent_skills, list):
                for skill_name in agent_skills:
                    if skill_name not in skill_names:
                        self.error(f"Agent {agent_path}: references unknown skill '{skill_name}'")

            # Optional mcpServers validation
            agent_mcp = frontmatter.get('mcpServers', [])
            if isinstance(agent_mcp, list):
                for server_name in agent_mcp:
                    if server_name not in mcp_server_names:
                        self.error(f"Agent {agent_path}: references unknown MCP server '{server_name}'")

            # Optional tools validation
            tools_str = frontmatter.get('tools', '')
            if tools_str:
                # `tools:` is normally a comma string, but the frontmatter parser returns a
                # LIST for the block form. Joining keeps both shapes on one path — the old
                # `tools_str.split(',')` raised AttributeError on the list form.
                if isinstance(tools_str, list):
                    tools_str = ','.join(str(t) for t in tools_str)
                decls, balanced = _split_tools(tools_str)
                if not balanced:
                    self.error(f"Agent {agent_path}: unbalanced parentheses in 'tools' — "
                               f"{tools_str!r}")
                for decl in decls:
                    # `[^()]*` not `.*`: a greedy scope group swallows a stray closing
                    # paren and calls the result well-formed.
                    m = re.fullmatch(r'([A-Za-z][A-Za-z0-9_]*)(?:\(([^()]*)\))?', decl)
                    if not m:
                        self.error(f"Agent {agent_path}: malformed tool declaration "
                                   f"'{decl}' (expected `Tool` or `Bash(<scope>)`)")
                        continue
                    tool, scope = m.group(1), m.group(2)
                    if tool not in VALID_TOOLS:
                        self.error(f"Agent {agent_path}: invalid tool '{tool}' (valid: {VALID_TOOLS})")
                    elif scope is not None:
                        if tool not in SCOPED_TOOLS:
                            self.error(f"Agent {agent_path}: tool '{tool}' does not take a "
                                       f"scope suffix (only {sorted(SCOPED_TOOLS)} do): '{decl}'")
                            continue
                        # A scope is a COMMA LIST, so check each item: one `*` entry in
                        # `Bash(git log:*, *)` grants everything while the declaration
                        # still looks narrowed. That's an error, not a warning — warnings
                        # never reach the exit code, and this is the case where the
                        # declaration actively misrepresents the grant.
                        items = [i.strip() for i in scope.split(',')]
                        wide = [i for i in items if i in UNRESTRICTED_SCOPE_ITEMS]
                        if wide:
                            self.error(f"Agent {agent_path}: '{decl}' has an unrestricted "
                                       f"scope item ({', '.join(repr(w) for w in wide)}) — "
                                       f"grants the same as a bare '{tool}' while reading "
                                       f"as narrowed")
                        else:
                            # See SCOPED_TOOLS: the narrowing is documented for a command's
                            # `allowed-tools`, not verified for a subagent's `tools:`.
                            self.warn(f"Agent {agent_path}: '{decl}' — a scope suffix in an "
                                      f"agent's 'tools' is not verified to be enforced at "
                                      f"runtime; treat it as a full '{tool}' grant")

    def _get_skill_names(self) -> set:
        """Extract skill directory names from manifest."""
        skill_names = set()
        for skill_path in self.manifest.get('skills', []):
            # Extract the directory name (last component)
            clean_path = skill_path.lstrip('./')
            skill_name = Path(clean_path).name
            skill_names.add(skill_name)
        return skill_names

    def test_skills(self):
        """Test 3: Skill Frontmatter Validation."""
        if not self.manifest:
            return

        self.log("Testing skills...")
        skills = self.manifest.get('skills', [])

        for skill_path in skills:
            clean_path = skill_path.lstrip('./')
            skill_dir = self.plugin_dir / clean_path
            skill_md = skill_dir / 'SKILL.md'

            if not skill_md.exists():
                continue  # Already reported in test_manifest

            frontmatter, body = self.parse_frontmatter(skill_md)

            # Required fields
            if 'name' not in frontmatter:
                self.error(f"Skill {skill_path}: missing 'name' in frontmatter")
            if 'description' not in frontmatter:
                self.error(f"Skill {skill_path}: missing 'description' in frontmatter")

            # Optional model validation
            model = frontmatter.get('model')
            if model and model not in VALID_MODELS:
                self.error(f"Skill {skill_path}: invalid model '{model}' (valid: {VALID_MODELS})")

            # Optional triggers validation
            triggers = frontmatter.get('triggers', [])
            if triggers:
                if not isinstance(triggers, list):
                    self.error(f"Skill {skill_path}: 'triggers' must be a list")
                else:
                    for trigger in triggers:
                        if not trigger or not isinstance(trigger, str):
                            self.error(f"Skill {skill_path}: trigger must be non-empty string")

            # Optional allowed-tools validation
            allowed_tools = frontmatter.get('allowed-tools', [])
            if allowed_tools:
                if not isinstance(allowed_tools, list):
                    self.error(f"Skill {skill_path}: 'allowed-tools' must be a list")
                else:
                    for tool in allowed_tools:
                        if tool not in VALID_TOOLS:
                            self.error(f"Skill {skill_path}: invalid tool '{tool}' (valid: {VALID_TOOLS})")

            # Body must be non-empty
            if not body.strip():
                self.error(f"Skill {skill_path}: SKILL.md body is empty")

    def test_hooks(self):
        """Test 4: Hook Validation (already done in test_manifest)."""
        # Hooks are validated in test_manifest's _validate_hooks
        pass

    def test_cross_refs(self):
        """Test 5: Cross-Reference Validation."""
        if not self.manifest:
            return

        self.log("Testing cross-references...")
        # Agent and skill path validation already done in test_manifest
        # This is a double-check

        # Verify agents exist
        for agent_path in self.manifest.get('agents', []):
            clean_path = agent_path.lstrip('./')
            full_path = self.plugin_dir / clean_path
            if not full_path.exists():
                self.error(f"Orphan agent reference: {agent_path}")

        # Verify skills exist
        for skill_path in self.manifest.get('skills', []):
            clean_path = skill_path.lstrip('./')
            skill_dir = self.plugin_dir / clean_path
            if not skill_dir.exists() or not (skill_dir / 'SKILL.md').exists():
                self.error(f"Orphan skill reference: {skill_path}")

    def test_token_budget(self):
        """Test 6: Token Budget Check (warnings only)."""
        self.log("Testing token budget...")

        # Check CLAUDE.md
        claude_md = self.plugin_dir / 'CLAUDE.md'
        if claude_md.exists():
            lines = claude_md.read_text(encoding='utf-8').count('\n') + 1
            if lines > 200:
                self.warn(f"CLAUDE.md exceeds 200 lines ({lines} lines)")

        if not self.manifest:
            return

        # Check agent bodies
        for agent_path in self.manifest.get('agents', []):
            clean_path = agent_path.lstrip('./')
            full_path = self.plugin_dir / clean_path
            if full_path.exists():
                _, body = self.parse_frontmatter(full_path)
                body_lines = body.count('\n') + 1
                if body_lines > 500:
                    self.warn(f"Agent {agent_path} body exceeds 500 lines ({body_lines} lines)")

        # Check skill bodies
        for skill_path in self.manifest.get('skills', []):
            clean_path = skill_path.lstrip('./')
            skill_md = self.plugin_dir / clean_path / 'SKILL.md'
            if skill_md.exists():
                _, body = self.parse_frontmatter(skill_md)
                body_lines = body.count('\n') + 1
                if body_lines > 500:
                    self.warn(f"Skill {skill_path} body exceeds 500 lines ({body_lines} lines)")

    def run_all(self):
        """Run all tests."""
        self.test_manifest()
        if self.manifest:  # Only continue if manifest is valid
            self.test_agents()
            self.test_skills()
            self.test_hooks()
            self.test_cross_refs()
            self.test_token_budget()

    def report(self) -> bool:
        """Print results, return True if no errors."""
        print(f"\n{'=' * 50}")
        print(f"  {self.plugin_name}")
        print(f"{'=' * 50}")

        if self.manifest:
            print(f"  Agents: {self.agent_count}")
            print(f"  Skills: {self.skill_count}")

        if self.errors:
            print(f"\n  ERRORS ({len(self.errors)}):")
            for err in self.errors:
                print(f"    - {err}")

        if self.warnings:
            print(f"\n  WARNINGS ({len(self.warnings)}):")
            for warn in self.warnings:
                print(f"    - {warn}")

        if not self.errors and not self.warnings:
            print(f"\n  All checks passed!")

        status = "PASS" if not self.errors else "FAIL"
        print(f"\n  Status: {status}")
        print(f"{'=' * 50}")

        return len(self.errors) == 0


def test_version_consistency(project_root: Path, plugin_names: List[str], verbose: bool = False):
    """Test version consistency across all plugins and marketplace.json."""
    print(f"\n{'=' * 50}")
    print(f"  Version Consistency Check")
    print(f"{'=' * 50}")

    versions: Dict[str, str] = {}
    errors: List[str] = []

    # Read plugin versions
    plugins_dir = project_root / 'plugins'
    for plugin_name in plugin_names:
        manifest_path = plugins_dir / plugin_name / '.claude-plugin' / 'plugin.json'
        if manifest_path.exists():
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    versions[f"plugin:{plugin_name}"] = data.get('version', 'MISSING')
            except Exception as e:
                errors.append(f"Cannot read {plugin_name}/plugin.json: {e}")

    # Read marketplace.json
    marketplace_path = project_root / '.claude-plugin' / 'marketplace.json'
    if marketplace_path.exists():
        try:
            with open(marketplace_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for plugin_entry in data.get('plugins', []):
                    name = plugin_entry.get('name', 'unknown')
                    version = plugin_entry.get('version', 'MISSING')
                    versions[f"marketplace:{name}"] = version
        except Exception as e:
            errors.append(f"Cannot read marketplace.json: {e}")
    else:
        errors.append("marketplace.json not found at .claude-plugin/marketplace.json")

    # Check consistency
    unique_versions = set(versions.values())
    unique_versions.discard('MISSING')

    if verbose:
        print("\n  Versions found:")
        for key, ver in sorted(versions.items()):
            print(f"    {key}: {ver}")

    if len(unique_versions) == 0:
        errors.append("No versions found")
    elif len(unique_versions) > 1:
        errors.append(f"Version mismatch: {unique_versions}")
        print(f"\n  Version mismatch detected:")
        for key, ver in sorted(versions.items()):
            print(f"    {key}: {ver}")
    else:
        version = unique_versions.pop()
        print(f"\n  All versions match: {version}")

    if errors:
        print(f"\n  ERRORS:")
        for err in errors:
            print(f"    - {err}")
        print(f"\n  Status: FAIL")
        return False
    else:
        print(f"\n  Status: PASS")
        return True


def main():
    parser = argparse.ArgumentParser(description="Validate oh-my-cloud-skills plugins")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--plugin", "-p", help="Test only this plugin")
    parser.add_argument("--root", help="Validate a different repo root instead of this script's "
                         "own checkout (e.g. a PR-head tree fetched as data by pr-review's L1 gate)")
    args = parser.parse_args()

    project_root = Path(args.root).resolve() if args.root else Path(__file__).parent.parent.resolve()
    plugins_dir = project_root / 'plugins'

    plugins = ["aws-content-plugin", "aws-ops-plugin", "kiro-power-converter", "co-agent", "agentcore-creator", "project-init", "kiro"]
    if args.plugin:
        if args.plugin not in plugins:
            print(f"Unknown plugin: {args.plugin}")
            print(f"Available plugins: {', '.join(plugins)}")
            sys.exit(1)
        plugins = [args.plugin]

    print("=" * 50)
    print("  oh-my-cloud-skills Plugin Validation Suite")
    if args.root:
        print(f"  root: {project_root}")
    print("=" * 50)

    total_errors = 0
    total_warnings = 0
    total_agents = 0
    total_skills = 0
    all_passed = True

    for plugin_name in plugins:
        plugin_dir = plugins_dir / plugin_name
        if not plugin_dir.exists():
            print(f"\nSKIP: {plugin_name} - directory not found")
            continue

        suite = PluginTestSuite(plugin_dir, args.verbose)
        suite.run_all()
        passed = suite.report()

        if not passed:
            all_passed = False

        total_errors += len(suite.errors)
        total_warnings += len(suite.warnings)
        total_agents += suite.agent_count
        total_skills += suite.skill_count

    # Version consistency check
    version_ok = test_version_consistency(project_root, plugins, args.verbose)
    if not version_ok:
        all_passed = False
        total_errors += 1

    # Final summary
    print(f"\n{'=' * 50}")
    print(f"  SUMMARY")
    print(f"{'=' * 50}")
    print(f"  Plugins tested: {len(plugins)}")
    print(f"  Total agents:   {total_agents}")
    print(f"  Total skills:   {total_skills}")
    print(f"  Errors:         {total_errors}")
    print(f"  Warnings:       {total_warnings}")
    print(f"{'=' * 50}")

    if all_passed:
        print("  RESULT: ALL TESTS PASSED")
    else:
        print("  RESULT: TESTS FAILED")

    print(f"{'=' * 50}\n")

    sys.exit(0 if total_errors == 0 else 1)


if __name__ == "__main__":
    main()
