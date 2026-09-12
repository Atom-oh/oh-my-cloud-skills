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

    def skill(self, directory):
        path = self.plugin / directory / "example"
        path.mkdir(parents=True, exist_ok=True)
        (path / "SKILL.md").write_text("---\nname: example\ndescription: Test capability\n---\nRead inputs.\n")

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
            "plugin": "sample",
            "skills": [{
                "name": "example",
                "path": ".codex-plugin/skills/example/SKILL.md",
                "sources": ["skills/example/SKILL.md"],
            }],
        }))
        return inventory

    def test_existing_default_skill_directory_remains_valid(self):
        self.assertEqual([], self.validate())

    def test_custom_skill_directory_is_validated_without_generated_inventory(self):
        # An arbitrary custom directory does not opt into the generated-adapter
        # contract; the reserved .codex-plugin/skills path is tested separately.
        self.skill("custom-skills")
        self.manifest["skills"] = "./custom-skills/"
        self.assertEqual([], self.validate())
        (self.plugin / "custom-skills/example/SKILL.md").unlink()
        self.assertTrue(any("missing SKILL.md" in error for error in self.validate()))

    def test_generated_adapter_requires_inventory(self):
        inventory = self.generated_adapter()
        self.assertEqual([], self.validate())
        inventory.unlink()
        self.assertTrue(any("Codex inventory missing" in error for error in self.validate()))

    def test_generated_inventory_must_cover_all_source_procedures(self):
        self.generated_adapter()
        self.assertEqual([], self.validate())
        command = self.plugin / "commands/review.md"
        command.parent.mkdir()
        command.write_text("---\ndescription: Review the requested files\n---\nInspect the diff.\n")
        errors = self.validate()
        self.assertTrue(any(
            "procedure coverage mismatch" in error and "commands/review.md" in error
            for error in errors
        ), errors)

    def test_generated_inventory_rejects_missing_referenced_source(self):
        self.generated_adapter()
        self.assertEqual([], self.validate())
        (self.plugin / "skills/example/SKILL.md").unlink()
        errors = self.validate()
        self.assertTrue(any(
            "missing procedure skills/example/SKILL.md" in error for error in errors
        ), errors)

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
