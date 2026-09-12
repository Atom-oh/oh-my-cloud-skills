"""Exercise converter discovery from consumer projects and installed caches."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch


REPO = Path(__file__).resolve().parents[2]
CONVERTERS = {
    "kiro": REPO / "plugins/kiro-power-converter/skills/kiro-convert/scripts/convert_plugin_to_power.py",
    "agentcore": REPO / "plugins/agentcore-creator/skills/agentcore-create/scripts/convert_plugin_to_agentcore.py",
}


class MarketplaceDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.home = self.base / "home"
        self.cwd = self.base / "consumer"
        self.cwd.mkdir()
        old_cwd = Path.cwd()
        os.chdir(self.cwd)
        self.addCleanup(os.chdir, old_cwd)
        home_patch = patch.object(Path, "home", return_value=self.home)
        home_patch.start()
        self.addCleanup(home_patch.stop)
        env_patch = patch.dict(os.environ, {"CODEX_HOME": str(self.base / "codex")})
        env_patch.start()
        self.addCleanup(env_patch.stop)
        self.searches = {}
        for kind, script in CONVERTERS.items():
            search = runpy.run_path(str(script), run_name="audit_test")["search_marketplace"]
            # Simulate the converter living in a checkout separate from the consumer.
            search.__globals__["__file__"] = str(
                self.base / "marketplace/plugins" / script.parents[3].name
                / "skills/converter/scripts/convert.py"
            )
            self.searches[kind] = search

    def plugin(self, root, name="audit-target"):
        manifest = root / ".claude-plugin/plugin.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({"name": name, "version": "1.17.0"}))
        return root

    def assert_found(self, expected):
        for kind, search in self.searches.items():
            with self.subTest(converter=kind):
                try:
                    result = search("audit-target")
                except FileNotFoundError:
                    result = None
                paths = [Path(item["path"]) for item in result] if isinstance(result, list) else [result]
                self.assertIn(expected, paths)

    def test_checkout_sibling_is_found_from_consumer_project(self):
        expected = self.plugin(self.base / "marketplace/plugins/audit-target")
        self.assert_found(expected)

    def test_codex_cache_respects_codex_home_and_version_layout(self):
        expected = self.plugin(self.base / "codex/plugins/cache/team/audit-target/1.17.0")
        self.assert_found(expected)

    def test_default_codex_home_cache_is_found(self):
        expected = self.plugin(self.home / ".codex/plugins/cache/team/audit-target/1.17.0")
        with patch.dict(os.environ):
            os.environ.pop("CODEX_HOME", None)
            self.assert_found(expected)

    def test_claude_versioned_cache_is_found(self):
        expected = self.plugin(self.home / ".claude/plugins/cache/team/audit-target/1.17.0")
        self.assert_found(expected)

    def test_workspace_source_remains_first_choice(self):
        expected = self.plugin(self.cwd / "plugins/audit-target")
        self.plugin(self.base / "codex/plugins/cache/team/audit-target/1.17.0")
        for kind, search in self.searches.items():
            with self.subTest(converter=kind):
                result = search("audit-target")
                first = Path(result[0]["path"]) if isinstance(result, list) else result
                self.assertEqual(expected, first)

    def test_same_checkout_is_not_listed_twice(self):
        expected = self.plugin(self.base / "marketplace/plugins/audit-target")
        os.chdir(self.base / "marketplace")
        result = self.searches["kiro"]("audit-target")
        self.assertEqual([expected], [Path(item["path"]) for item in result])

    def test_agentcore_requires_explicit_source_for_multiple_cached_versions(self):
        for version in ("1.16.0", "1.17.0"):
            self.plugin(self.base / "codex/plugins/cache/team/audit-target" / version)
        with self.assertRaisesRegex(ValueError, "--source"):
            self.searches["agentcore"]("audit-target")

    def agentcore_inventory(self, root, manifest):
        return self.searches["agentcore"].__globals__["build_inventory"](root, manifest)

    def inventory_fixture(self):
        root = self.base / "inventory-plugin"
        agents = root / "agents"
        agents.mkdir(parents=True)
        for name in ("z-runner", "a-reviewer"):
            (agents / f"{name}.md").write_text(f"---\nname: {name}\n---\nAgent instructions.\n")
        for name in ("README.md", "CLAUDE.md", "readme.md"):
            (agents / name).write_text("Documentation, not an agent.\n")
        (agents / "directory.md").mkdir()
        (agents / "nested").mkdir()
        (agents / "nested/ignored.md").write_text("Not a top-level agent.\n")
        for name in ("z-worker", "a-planner"):
            skill = root / "skills" / name
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(f"---\nname: {name}\n---\nSkill instructions.\n")
        (root / "skills/z-worker/references").mkdir()
        (root / "skills/z-worker/references/guide.md").write_text("Reference content.\n")
        (root / "skills/not-a-skill").mkdir()
        return root

    def test_agentcore_inventory_discovers_actual_project_init_components(self):
        root = REPO / "plugins/project-init"
        with (root / ".claude-plugin/plugin.json").open(encoding="utf-8") as stream:
            manifest = json.load(stream)
        inventory = self.agentcore_inventory(root, manifest)
        self.assertEqual(["doc-sync-checker"], [agent["name"] for agent in inventory["agents"]])
        self.assertEqual(["project-scaffolder"], [skill["name"] for skill in inventory["skills"]])
        self.assertTrue(inventory["references"])

    def test_agentcore_inventory_conventions_exclude_docs_and_non_components(self):
        inventory = self.agentcore_inventory(self.inventory_fixture(), {"name": "fixture"})
        self.assertEqual(["a-reviewer", "z-runner"], [agent["name"] for agent in inventory["agents"]])
        self.assertEqual(["a-planner", "z-worker"], [skill["name"] for skill in inventory["skills"]])
        self.assertEqual(["guide"], [ref["name"] for ref in inventory["references"]])
        self.assertIn("Agent instructions.", inventory["agents"][0]["body"])
        self.assertIn("Skill instructions.", inventory["skills"][0]["body"])

    def test_agentcore_inventory_preserves_each_explicit_empty_array(self):
        root = self.inventory_fixture()
        cases = [
            ({"agents": []}, [], ["a-planner", "z-worker"]),
            ({"skills": []}, ["a-reviewer", "z-runner"], []),
            ({"agents": [], "skills": []}, [], []),
        ]
        for manifest, agents, skills in cases:
            with self.subTest(manifest=manifest):
                inventory = self.agentcore_inventory(root, manifest)
                self.assertEqual(agents, [item["name"] for item in inventory["agents"]])
                self.assertEqual(skills, [item["name"] for item in inventory["skills"]])
                if not skills:
                    self.assertEqual([], inventory["references"])

    def test_agentcore_inventory_keeps_explicit_component_selection(self):
        root = self.inventory_fixture()
        inventory = self.agentcore_inventory(root, {
            "agents": ["./agents/z-runner.md"], "skills": ["./skills/z-worker"],
        })
        self.assertEqual(["z-runner"], [item["name"] for item in inventory["agents"]])
        self.assertEqual(["z-worker"], [item["name"] for item in inventory["skills"]])

    def test_broken_unrelated_manifest_does_not_hide_valid_cached_plugin(self):
        broken = self.base / "codex/plugins/cache/team/a-broken/1.0/.claude-plugin/plugin.json"
        broken.parent.mkdir(parents=True)
        broken.write_text("{")
        expected = self.plugin(self.base / "codex/plugins/cache/team/audit-target/1.17.0")
        with redirect_stderr(io.StringIO()):
            self.assert_found(expected)

    def test_kiro_skips_malformed_manifest_name_and_description(self):
        expected = self.plugin(self.base / "codex/plugins/cache/team/audit-target/1.17.0")
        broken = self.base / "codex/plugins/cache/team/a-broken/1.0/.claude-plugin/plugin.json"
        broken.parent.mkdir(parents=True)
        for field in ("name", "description"):
            for value in (None, 42, False, [], {}):
                with self.subTest(field=field, value=value):
                    data = {"name": "unrelated", "description": "fixture"}
                    data[field] = value
                    broken.write_text(json.dumps(data))
                    diagnostics = io.StringIO()
                    with redirect_stderr(diagnostics):
                        matches = self.searches["kiro"]("audit-target")
                        all_matches = self.searches["kiro"]("")
                    self.assertEqual([str(expected)], [item["path"] for item in matches])
                    self.assertEqual([str(expected)], [item["path"] for item in all_matches])
                    self.assertIn(str(broken), diagnostics.getvalue())
                    self.assertIn(field, diagnostics.getvalue())

    def cached_versions(self):
        sources = []
        for version in ("1.16.0", "1.17.0"):
            root = self.plugin(self.base / "codex/plugins/cache/team/audit-target" / version)
            (root / "CLAUDE.md").write_text(f"Selected version: {version}\n")
            sources.append(root)
        return sources

    def kiro_cli(self, arguments, stdin=""):
        """Run the actual argument parser and conversion using isolated local fixtures."""
        main = self.searches["kiro"].__globals__["main"]
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(sys, "argv", ["converter", *arguments]):
            with patch.object(sys, "stdin", io.StringIO(stdin)):
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    try:
                        main()
                        rc = 0
                    except SystemExit as exc:
                        rc = exc.code
        return rc, stdout.getvalue(), stderr.getvalue()

    def test_kiro_cli_aborts_ambiguous_eof_and_invalid_selection_without_conversion(self):
        self.cached_versions()
        for index, stdin in enumerate(("", "invalid\n", "99\n", "-1\n", "\n")):
            with self.subTest(stdin=stdin):
                output = self.base / f"existing-output-{index}"
                output.mkdir()
                sentinel = output / "keep.txt"
                sentinel.write_text("existing user output")
                rc, _, stderr = self.kiro_cli(
                    ["--marketplace", "audit-target", "--output", str(output)], stdin)
                self.assertNotEqual(0, rc)
                self.assertIn("--source", stderr)
                self.assertEqual("existing user output", sentinel.read_text())
                self.assertFalse((output / "POWER.md").exists())

    def test_kiro_cli_converts_explicit_valid_selection(self):
        self.cached_versions()
        output = self.base / "selected-output"
        rc, _, stderr = self.kiro_cli(
            ["--marketplace", "audit-target", "--output", str(output)], "1\n")
        self.assertEqual(0, rc, stderr)
        self.assertTrue((output / "POWER.md").is_file())
        self.assertIn("Selected version: 1.17.0", (output / "steering/routing.md").read_text())

    def test_kiro_cli_explicit_source_bypasses_cache_ambiguity(self):
        sources = self.cached_versions()
        output = self.base / "explicit-output"
        rc, _, stderr = self.kiro_cli(["--source", str(sources[1]), "--output", str(output)])
        self.assertEqual(0, rc, stderr)
        self.assertTrue((output / "POWER.md").is_file())
        self.assertIn("Selected version: 1.17.0", (output / "steering/routing.md").read_text())


if __name__ == "__main__":
    unittest.main()
