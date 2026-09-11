"""Validate declared package paths without executing any plugin code."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = Path(os.environ.get("CODEX_VALIDATOR_UNDER_TEST",
                             str(ROOT / "scripts/test-codex-plugins.py")))
SPEC = importlib.util.spec_from_file_location("codex_validator", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ComponentTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="codex components ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.plugin = self.root / "plugins/sample"
        (self.plugin / ".codex-plugin").mkdir(parents=True)
        (self.plugin / ".claude-plugin").mkdir()
        self.manifest = {
            "name": "sample", "version": "1.0.0", "description": "Test plugin",
            "author": {"name": "Test"}, "skills": "./skills/",
            "interface": {
                "displayName": "Sample", "shortDescription": "Test",
                "longDescription": "Test plugin", "developerName": "Test",
                "category": "Testing", "capabilities": ["Skills"], "defaultPrompt": "Test",
            },
        }
        (self.plugin / ".claude-plugin/plugin.json").write_text(json.dumps(self.manifest))
        self.skill("skills")

    def skill(self, directory, name="example"):
        path = self.plugin / directory / name
        path.mkdir(parents=True, exist_ok=True)
        (path / "SKILL.md").write_text(f"---\nname: {name}\ndescription: Test capability\n---\nRead inputs.\n")

    def validate(self):
        (self.plugin / ".codex-plugin/plugin.json").write_text(json.dumps(self.manifest))
        validator = MODULE.CodexPluginValidator(self.root)
        validator.validate_manifest("sample")
        return validator.errors

    def generated_adapter(self):
        self.skill(".codex-plugin/skills")
        self.manifest["skills"] = "./.codex-plugin/skills/"
        inventory = self.plugin / ".codex-plugin/inventory.json"
        inventory.write_text(json.dumps({
            "plugin": "sample", "skills": [{"name": "example",
                "path": ".codex-plugin/skills/example/SKILL.md",
                "sources": ["skills/example/SKILL.md"]}],
        }))
        return inventory

    def test_existing_default_skill_directory_remains_valid(self):
        self.assertEqual([], self.validate())

    def test_missing_project_init_adapter_is_an_error(self):
        source = self.root / "plugins/project-init/.claude-plugin/plugin.json"
        source.parent.mkdir(parents=True)
        source.write_text(json.dumps({"name": "project-init"}))
        validator = MODULE.CodexPluginValidator(self.root)
        validator.discover_plugins()
        self.assertTrue(any("project-init: no .codex-plugin manifest" in error
                            for error in validator.errors), validator.errors)

    def test_declared_skill_directory_is_validated(self):
        self.generated_adapter()
        self.assertEqual([], self.validate())
        (self.plugin / ".codex-plugin/skills/example/SKILL.md").unlink()
        self.assertTrue(any("missing SKILL.md" in error for error in self.validate()))

    def test_custom_skill_directory_does_not_require_generated_inventory(self):
        self.skill("custom-skills")
        self.manifest["skills"] = "./custom-skills/"
        self.assertEqual([], self.validate())

    def test_generated_inventory_is_required_for_normalized_reserved_paths(self):
        inventory = self.generated_adapter()
        self.assertEqual([], self.validate())
        inventory.unlink()
        for path in ("./.codex-plugin/skills/", "./.codex-plugin/skills", "././.codex-plugin/skills/"):
            with self.subTest(path=path):
                self.manifest["skills"] = path
                self.assertTrue(any("inventory missing" in error for error in self.validate()))

    def test_new_sources_are_not_hidden_by_manifest_conventions(self):
        self.generated_adapter()
        for relative in ("commands/review.md", "agents/reviewer.md", "skills/extra/SKILL.md"):
            with self.subTest(source=relative):
                source = self.plugin / relative
                source.parent.mkdir(parents=True, exist_ok=True)
                source.write_text("---\ndescription: Review inputs\n---\nInspect the diff.\n")
                errors = self.validate()
                self.assertTrue(any("coverage mismatch" in e and relative in e for e in errors), errors)
                source.unlink()

    def test_missing_and_nonprocedure_inventory_sources_are_rejected(self):
        inventory = self.generated_adapter()
        (self.plugin / "skills/example/SKILL.md").unlink()
        self.assertTrue(any("missing procedure" in e for e in self.validate()))
        self.skill("skills")
        extra = self.plugin / "references/guide.md"
        extra.parent.mkdir()
        extra.write_text("Reference, not an entry procedure.\n")
        data = json.loads(inventory.read_text())
        data["skills"][0]["sources"].append("references/guide.md")
        inventory.write_text(json.dumps(data))
        self.assertTrue(any("coverage mismatch" in e and "references/guide.md" in e
                            for e in self.validate()))

    def test_inventory_rejects_duplicate_sources_and_unlisted_wrappers(self):
        inventory = self.generated_adapter()
        data = json.loads(inventory.read_text())
        data["skills"][0]["sources"] *= 2
        inventory.write_text(json.dumps(data))
        self.assertTrue(any("duplicate source" in e for e in self.validate()))
        self.generated_adapter()
        self.skill(".codex-plugin/skills", "unexpected")
        self.assertTrue(any("entry coverage mismatch" in e for e in self.validate()))

    def test_inventory_schema_and_entry_paths_are_strict(self):
        inventory = self.generated_adapter()
        valid = json.loads(inventory.read_text())
        cases = [
            {**valid, "plugin": "other"}, {**valid, "skills": None},
            {**valid, "skills": [None]}, {**valid, "skills": []},
        ]
        for field, value in (("name", "../escape"), ("name", ""),
                             ("path", "skills/example/SKILL.md"), ("sources", []),
                             ("sources", ["../foreign.md"]), ("sources", [None])):
            cases.append({**valid, "skills": [{**valid["skills"][0], field: value}]})
        for data in cases:
            with self.subTest(data=data):
                inventory.write_text(json.dumps(data))
                self.assertTrue(self.validate())
        inventory.write_bytes(b"\xff")
        self.assertTrue(self.validate())

    def test_routing_docs_are_not_source_procedures(self):
        self.generated_adapter()
        for directory in ("agents", "commands"):
            folder = self.plugin / directory
            folder.mkdir()
            for name in ("README.md", "CLAUDE.md", "AGENTS.md"):
                (folder / name).write_text("Routing documentation.\n")
        self.assertEqual([], self.validate())

    def test_declared_mcp_and_hook_files(self):
        (self.plugin / ".codex-plugin/mcp.json").write_text(json.dumps({
            "mcpServers": {"docs": {"type": "http", "url": "https://example.com/mcp"}},
        }))
        (self.plugin / ".codex-plugin/hooks.json").write_text(json.dumps({"hooks": {}}))
        self.manifest.update(mcpServers="./.codex-plugin/mcp.json",
                             hooks="./.codex-plugin/hooks.json")
        self.assertEqual([], self.validate())
        (self.plugin / ".codex-plugin/hooks.json").unlink()
        self.assertTrue(any("hooks missing" in error for error in self.validate()))

    def test_component_paths_cannot_escape_package(self):
        for field in ("skills", "mcpServers", "hooks"):
            with self.subTest(field=field):
                self.manifest[field] = "./../outside"
                self.assertTrue(any("escapes the plugin" in error for error in self.validate()))
                if field == "skills":
                    self.manifest[field] = "./skills/"
                else:
                    del self.manifest[field]

    def test_symlink_outside_package_is_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.plugin / "escape").symlink_to(outside, target_is_directory=True)
        self.manifest["skills"] = "./escape/"
        self.assertTrue(any("escapes the plugin" in error for error in self.validate()))

    def test_empty_capabilities_is_an_error(self):
        self.manifest["interface"]["capabilities"] = []
        self.assertTrue(any("capabilities" in error for error in self.validate()))

    def test_duplicate_marketplace_entry_is_an_error(self):
        path = self.root / ".agents/plugins/marketplace.json"
        path.parent.mkdir(parents=True)
        entry = {
            "name": "sample", "source": {"source": "local", "path": "./plugins/sample"},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_USE"},
            "category": "Testing",
        }
        path.write_text(json.dumps({
            "name": "test", "interface": {"displayName": "Test"}, "plugins": [entry, entry],
        }))
        validator = MODULE.CodexPluginValidator(self.root)
        validator.validate_marketplace(["sample"])
        self.assertTrue(any("duplicate entry" in error for error in validator.errors))


if __name__ == "__main__":
    unittest.main()
