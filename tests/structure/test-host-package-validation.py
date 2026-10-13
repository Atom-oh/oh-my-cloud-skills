"""Exercise trusted validators on synthetic host packages without a generator."""
import hashlib
import json
from pathlib import Path
import runpy
import tempfile
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
HOST = runpy.run_path(str(ROOT / "scripts/test-host-packages.py"))
CLAUDE = runpy.run_path(str(ROOT / "scripts/test-plugins.py"))
CODEX = runpy.run_path(str(ROOT / "scripts/test-codex-plugins.py"))


class HostValidationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="host validation ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.identity = {"name": "sample", "version": "1.0.0", "description": "Fixture",
                         "author": {"name": "Fixture"}}
        self.write("hosts/catalog.json", {"plugins": {"sample": self.identity}})
        self.write("plugins/sample/.claude-plugin/plugin.json", self.identity)
        self.packages = {}
        for host in ("claude", "codex"):
            package = self.root / "packages" / host / "sample"
            self.packages[host] = package
            config = {"skills": "./.codex-plugin/skills/", "interface": {
                "displayName": "Sample", "shortDescription": "Fixture",
                "longDescription": "Fixture package", "developerName": "Fixture",
                "category": "Testing", "capabilities": ["Skills"], "defaultPrompt": "Read data.",
            }} if host == "codex" else {
                "agents": ["./agents/reader.md"], "skills": [], "mcpServers": "./.mcp.json"}
            self.write(f"hosts/{host}/sample/plugin.json", config)
            self.write(f"hosts/{host}/sample/package.json", {"exclude": []})
            self.write(f"packages/{host}/sample/.{host}-plugin/plugin.json",
                       {**self.identity, **config})
            if host == "claude":
                mcp = {"mcpServers": {"server": {"command": "fixture", "args": []}}}
                self.write("hosts/claude/sample/.mcp.json", mcp)
                self.write("packages/claude/sample/.mcp.json", mcp)
                settings = {"model": "opus", "tools": "Read", "mcpServers": ["server"]}
                self.write("hosts/claude/sample/agents.json", {"reader.md": settings})
                self.write("packages/claude/sample/agents/reader.md",
                           '---\nname: reader\ndescription: Read fixture data\n'
                           'model: "opus"\ntools: "Read"\nmcpServers:\n  - "server"\n'
                           '---\nRead the supplied document.\n')
            else:
                self.write("hosts/codex/sample/execution.json",
                           {"reasoning": {}, "explicit_skills": ["example"]})
                entry = ".codex-plugin/skills/example/SKILL.md"
                self.write("packages/codex/sample/" + entry,
                           "---\nname: example\ndescription: Fixture\n---\nRead data.\n")
                self.write("packages/codex/sample/skills/example/SKILL.md",
                           "---\nname: example\ndescription: Fixture\n---\nRead data.\n")
                self.write("packages/codex/sample/.codex-plugin/inventory.json", {
                    "plugin": "sample", "skills": [{"name": "example", "path": entry,
                                                    "sources": ["skills/example/SKILL.md"]}]})
                self.write("packages/codex/sample/.codex-plugin/skills/example/agents/openai.yaml",
                           'interface:\n  display_name: Example\n  short_description: Fixture\n'
                           'policy:\n  allow_implicit_invocation: false\n')
            self.refresh(host)
        entry = {"name": "sample", "version": "1.0.0"}
        self.write(".claude-plugin/marketplace.json",
                   {"plugins": [{**entry, "source": "./packages/claude/sample"}]})
        self.write(".agents/plugins/marketplace.json", {"plugins": [{
            **entry, "source": {"source": "local", "path": "./packages/codex/sample"}}]})

    def write(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value if isinstance(value, str) else json.dumps(value),
                        encoding="utf-8")
        return path

    def refresh(self, host):
        package = self.packages[host]
        files = {
            str(path.relative_to(package)): {
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "executable": bool(path.stat().st_mode & 0o111),
            }
            for path in package.rglob("*")
            if path.is_file() and path != package / "package-inventory.json"
        }
        self.write(f"packages/{host}/sample/package-inventory.json",
                   {"host": host, "plugin": "sample", "version": "1.0.0", "files": files})

    def errors(self):
        return HOST["validate"](self.root)

    def test_file_based_claude_mcp_passes_both_trusted_validators(self):
        self.assertEqual([], self.errors())
        suite = CLAUDE["PluginTestSuite"](self.packages["claude"])
        suite.run_all()
        self.assertEqual([], suite.errors)
        self.assertEqual({"server"}, set(suite.manifest["mcpServers"]))

    def test_packaged_codex_manifest_validates_its_interface_and_source_inventory(self):
        validator = CODEX["CodexPluginValidator"](self.root)
        validator.plugins_dir = self.root / "packages/codex"
        validator.validate_manifest("sample")
        self.assertEqual([], validator.errors)
        (self.packages["codex"] / "skills/example/SKILL.md").unlink()
        validator.validate_manifest("sample")
        self.assertTrue(any("missing procedure" in error for error in validator.errors))

    def test_mcp_escaping_path_and_malformed_file_report_errors_without_crashing(self):
        manifest = self.packages["claude"] / ".claude-plugin/plugin.json"
        for value in ("./../../outside.json", "./.mcp.json"):
            with self.subTest(value=value):
                data = json.loads(manifest.read_text(encoding="utf-8"))
                data["mcpServers"] = value
                manifest.write_text(json.dumps(data), encoding="utf-8")
                self.write("packages/claude/sample/.mcp.json", "not JSON")
                suite = CLAUDE["PluginTestSuite"](self.packages["claude"])
                suite.run_all()
                self.assertTrue(any("Invalid mcpServers file" in error for error in suite.errors))

    def test_non_object_claude_manifest_is_reported_without_crashing(self):
        self.write("packages/claude/sample/.claude-plugin/plugin.json", "[]")
        suite = CLAUDE["PluginTestSuite"](self.packages["claude"])
        suite.run_all()
        self.assertTrue(any("JSON object" in error for error in suite.errors))

    def test_linked_mcp_file_is_rejected_even_when_its_target_is_internal(self):
        package = self.packages["claude"]
        target = package / "real-mcp.json"
        (package / ".mcp.json").rename(target)
        (package / ".mcp.json").symlink_to(target)
        suite = CLAUDE["PluginTestSuite"](package)
        suite.run_all()
        self.assertTrue(any("Invalid mcpServers file" in error for error in suite.errors))

    def test_nested_inventory_is_not_exempt_from_coverage(self):
        self.write("packages/codex/sample/assets/package-inventory.json", "{}")
        self.assertTrue(any("untracked or missing" in error for error in self.errors()))
        self.refresh("codex")
        self.assertEqual([], self.errors())

    def test_yaml_description_cannot_override_real_invocation_policy(self):
        self.write("packages/codex/sample/.codex-plugin/skills/example/agents/openai.yaml",
                   "interface:\n  short_description: |\n    allow_implicit_invocation: false\n"
                   "policy:\n  allow_implicit_invocation: true\n")
        self.refresh("codex")
        self.assertTrue(any("permits implicit" in error for error in self.errors()))

    def test_multiline_quoted_yaml_cannot_spoof_policy(self):
        for quote in ("'", '"'):
            with self.subTest(quote=quote):
                self.write("packages/codex/sample/.codex-plugin/skills/example/agents/openai.yaml",
                           f"interface:\n  short_description: {quote}description\n"
                           f"policy:\n  allow_implicit_invocation: false\n{quote}\n"
                           "policy: {allow_implicit_invocation: true}\n")
                self.refresh("codex")
                self.assertTrue(any("permits implicit" in error for error in self.errors()))

    def test_duplicate_policy_keys_are_rejected(self):
        self.write("packages/codex/sample/.codex-plugin/skills/example/agents/openai.yaml",
                   "policy:\n  allow_implicit_invocation: false\n"
                   "  allow_implicit_invocation: true\n")
        self.refresh("codex")
        self.assertTrue(any("permits implicit" in error for error in self.errors()))

    def test_catalog_cannot_carry_execution_fields(self):
        self.write("hosts/catalog.json", {"plugins": {
            "sample": {**self.identity, "hooks": "./hidden-hooks.json"}}})
        self.assertTrue(any("non-identity" in error for error in self.errors()))

    def test_linked_package_root_is_rejected(self):
        package = self.packages["codex"]
        target = self.root / "other-package"
        package.rename(target)
        package.symlink_to(target, target_is_directory=True)
        self.assertTrue(any("linked or escaping package root" in error for error in self.errors()))

    def test_malformed_marketplace_name_does_not_truncate_other_diagnostics(self):
        self.write(".claude-plugin/marketplace.json", {"plugins": [{"name": {}}]})
        self.write("packages/codex/sample/untracked.txt", "fixture")
        errors = self.errors()
        self.assertTrue(any("marketplace membership" in error for error in errors))
        self.assertTrue(any("untracked or missing" in error for error in errors))

    def test_malformed_agent_list_is_reported_without_crashing(self):
        self.write("packages/claude/sample/agents/reader.md",
                   '---\nname: reader\nmodel: "opus"\ntools: "Read"\n'
                   "mcpServers:\n  - unquoted-server\n---\nRead data.\n")
        self.refresh("claude")
        self.assertTrue(any("agent setting drift" in error for error in self.errors()))

    def test_body_scalar_cannot_mask_active_agent_permissions(self):
        agent = self.packages["claude"] / "agents/reader.md"
        text = agent.read_text(encoding="utf-8").replace('tools: "Read"', 'tools: "Bash"')
        agent.write_text(text + '\n```yaml\ntools: "Read"\n```\n', encoding="utf-8")
        self.refresh("claude")
        self.assertTrue(any("reader.md/tools" in error for error in self.errors()))

    def test_body_list_cannot_supply_missing_frontmatter_setting(self):
        agent = self.packages["claude"] / "agents/reader.md"
        text = agent.read_text(encoding="utf-8").replace('mcpServers:\n  - "server"\n', "")
        agent.write_text(text + '\n```yaml\nmcpServers:\n  - "server"\n```\n', encoding="utf-8")
        self.refresh("claude")
        self.assertTrue(any("reader.md/mcpServers" in error for error in self.errors()))

    def test_multiline_quoted_description_cannot_spoof_agent_tools(self):
        self.write("packages/claude/sample/agents/reader.md",
                   "---\nname: reader\ndescription: 'description\n"
                   "tools: \"Read\"\n'\nmodel: \"opus\"\ntools: \"Bash\"\n"
                   "mcpServers:\n  - \"server\"\n---\nRead data.\n")
        self.refresh("claude")
        self.assertTrue(any("non-canonical agent" in error for error in self.errors()))

    def test_duplicate_agent_keys_are_rejected(self):
        agent = self.packages["claude"] / "agents/reader.md"
        text = agent.read_text(encoding="utf-8").replace(
            'tools: "Read"', 'tools: "Read"\ntools: "Bash"')
        agent.write_text(text, encoding="utf-8")
        self.refresh("claude")
        self.assertTrue(any("non-canonical agent" in error for error in self.errors()))

    def test_stale_explicit_skill_name_is_reported(self):
        self.write("hosts/codex/sample/execution.json",
                   {"reasoning": {}, "explicit_skills": ["example", "removed"]})
        self.assertTrue(any("unknown inventory entries" in error for error in self.errors()))

    def test_empty_mcp_endpoint_is_not_accepted(self):
        for endpoint in (None, "", "   "):
            with self.subTest(endpoint=endpoint):
                self.write("packages/claude/sample/.mcp.json",
                           {"mcpServers": {"server": {"url": endpoint}}})
                suite = CLAUDE["PluginTestSuite"](self.packages["claude"])
                suite.run_all()
                self.assertTrue(any("missing command or url" in error for error in suite.errors))

    def test_malformed_catalog_identity_is_reported_once_without_crashing(self):
        for identity in (None, [], "invalid"):
            with self.subTest(identity=identity):
                self.write("hosts/catalog.json", {"plugins": {"sample": identity}})
                errors = self.errors()
                self.assertEqual(1, sum("invalid identity" in error for error in errors))

    def test_non_object_catalog_uses_cli_diagnostic_instead_of_traceback(self):
        self.write("hosts/catalog.json", "[]")
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/test-plugins.py"), "--root", str(self.root)],
            capture_output=True, text=True,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("Invalid host catalog", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_linked_host_configuration_is_rejected(self):
        config = self.root / "hosts/claude/sample/plugin.json"
        target = self.root / "actual-config.json"
        config.rename(target)
        config.symlink_to(target)
        self.assertTrue(any("linked or escaping data file" in error for error in self.errors()))


if __name__ == "__main__":
    unittest.main()
