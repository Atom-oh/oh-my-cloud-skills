#!/usr/bin/env python3
"""Behavioral packaging regressions; no network or model calls."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
GENERATOR = ROOT / "scripts/sync-codex-plugins.py"


class PortabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Test the generator against source inputs, independently of whether a
        # checkout has already published the generated adapters.
        cls.temporary = tempfile.TemporaryDirectory(prefix="codex generated ")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.generated = Path(cls.temporary.name)
        patterns = ("*/.claude-plugin/plugin.json", "*/.mcp.json",
                    "*/skills/*/SKILL.md", "*/commands/*.md", "*/agents/*.md")
        for pattern in patterns:
            for source in (ROOT / "plugins").glob(pattern):
                target = cls.generated / source.relative_to(ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
        shutil.copytree(ROOT / "scripts/codex", cls.generated / "scripts/codex")
        target = cls.generated / ".agents/plugins/marketplace.json"
        target.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / ".agents/plugins/marketplace.json", target)
        subprocess.run([sys.executable, str(GENERATOR), "--root", str(cls.generated)],
                       check=True, capture_output=True, text=True)

    def test_generated_adapters_are_current(self):
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--root", str(self.generated), "--check"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_check_rejects_modified_generated_entry(self):
        path = next((self.generated / "plugins").glob("*/.codex-plugin/skills/*/SKILL.md"))
        original = path.read_text()
        try:
            path.write_text(original + "\nUnreviewed drift.\n")
            result = subprocess.run(
                [sys.executable, str(GENERATOR), "--root", str(self.generated), "--check"],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("stale Codex artifact", result.stdout)
        finally:
            path.write_text(original)

    def test_real_checkout_gate_cannot_skip_missing_or_downgraded_adapters(self):
        gate = ROOT / "tests/structure/test-codex-published.sh"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(self.generated, root, dirs_exist_ok=True)
            shutil.copyfile(GENERATOR, root / "scripts/sync-codex-plugins.py")
            command = ["bash", "-euo", "pipefail", "-c",
                       'pass() { :; }; fail() { return 1; }; source "$1"', "fixture", str(gate)]
            result = subprocess.run(command, cwd=root, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            manifest = root / "plugins/project-init/.codex-plugin/plugin.json"
            original = manifest.read_bytes()
            manifest.unlink()
            result = subprocess.run(command, cwd=root, capture_output=True, text=True)
            self.assertNotEqual(0, result.returncode, "missing package escaped the real-checkout gate")
            data = json.loads(original)
            data["skills"] = "./skills/"
            manifest.write_text(json.dumps(data))
            result = subprocess.run(command, cwd=root, capture_output=True, text=True)
            self.assertNotEqual(0, result.returncode, "downgraded package escaped the real-checkout gate")

    def test_relative_root_preserves_generated_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            shutil.copytree(self.generated, root)
            before = set(root.glob("plugins/*/.codex-plugin/skills/*/SKILL.md"))
            self.assertTrue(before)
            for flags in ([], ["--check"]):
                result = subprocess.run(
                    [sys.executable, str(GENERATOR), "--root", ".", *flags],
                    cwd=root, capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertTrue(all(path.is_file() for path in before),
                                "generation with a relative root deleted valid skills")

    def test_regeneration_removes_obsolete_skill_directory(self):
        plugin = next((self.generated / "plugins").iterdir())
        obsolete = plugin / ".codex-plugin/skills/obsolete/SKILL.md"
        obsolete.parent.mkdir(parents=True)
        obsolete.write_text("---\nname: obsolete\ndescription: Removed source\n---\n")
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--root", str(self.generated)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(obsolete.parent.exists())

    def test_scoped_generation_does_not_rewrite_other_plugins(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            shutil.copytree(self.generated, root)
            other = root / "plugins/atlas/.codex-plugin/runtime.md"
            changed = other.read_text() + "\nUnrelated pending change.\n"
            other.write_text(changed)
            for flags in ([], ["--check"]):
                result = subprocess.run(
                    [sys.executable, str(GENERATOR), "--root", str(root),
                     "--plugin", "kiro", *flags], capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(changed, other.read_text())
            result = subprocess.run(
                [sys.executable, str(GENERATOR), "--root", str(root), "--check"],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 1, "full check must still detect unselected drift")

    def test_regeneration_updates_selected_marketplace_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            shutil.copytree(self.generated, root)
            source = root / "plugins/kiro/.claude-plugin/plugin.json"
            manifest = json.loads(source.read_text())
            manifest["version"] = "9.8.7"
            source.write_text(json.dumps(manifest))
            market = root / ".agents/plugins/marketplace.json"
            before = json.loads(market.read_text())
            selected = next(p for p in before["plugins"] if p["name"] == "kiro")
            selected["policy"]["installation"] = "NOT_AVAILABLE"
            market.write_text(json.dumps(before))
            subprocess.run([sys.executable, str(GENERATOR), "--root", str(root),
                            "--plugin", "kiro"], check=True, capture_output=True)
            after = json.loads(market.read_text())
            actual = next(p for p in after["plugins"] if p["name"] == "kiro")
            self.assertEqual("9.8.7", actual["version"])
            self.assertEqual(selected["policy"], actual["policy"])
            self.assertEqual([p for p in before["plugins"] if p["name"] != "kiro"],
                             [p for p in after["plugins"] if p["name"] != "kiro"])

    def test_removed_optional_artifacts_fail_check_and_are_pruned(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            shutil.copytree(self.generated, root)
            adapter = root / "plugins/project-init/.codex-plugin"
            guide = root / "scripts/codex/project-init.md"
            guide.unlink(missing_ok=True)
            args = [sys.executable, str(GENERATOR), "--root", str(root),
                    "--plugin", "project-init"]
            subprocess.run(args, check=True, capture_output=True)
            names = ("hook.py", "hooks.json", "hook-handlers.json", "mcp.json", "workflow.md")
            for name in names:
                (adapter / name).write_text("obsolete generated artifact\n")
            manual = adapter / "operator-notes.txt"
            manual.write_text("Keep this unowned file.\n")
            self.assertNotEqual(0, subprocess.run(args + ["--check"], capture_output=True).returncode)
            subprocess.run(args, check=True, capture_output=True)
            self.assertTrue(all(not (adapter / name).exists() for name in names))
            self.assertEqual("Keep this unowned file.\n", manual.read_text())
            self.assertEqual(0, subprocess.run(args + ["--check"], capture_output=True).returncode)

    def test_every_plugin_exposes_all_source_procedures(self):
        for plugin in sorted((self.generated / "plugins").iterdir()):
            if not (plugin / ".claude-plugin/plugin.json").is_file():
                continue
            with self.subTest(plugin=plugin.name):
                inventory = plugin / ".codex-plugin/inventory.json"
                self.assertTrue(inventory.is_file(), str(inventory))
                data = json.loads(inventory.read_text())
                actual = {s for entry in data["skills"] for s in entry["sources"]}
                expected = {
                    str(p.relative_to(plugin))
                    for pattern in ("skills/*/SKILL.md", "commands/*.md", "agents/*.md")
                    for p in plugin.glob(pattern)
                    if p.name not in {"README.md", "CLAUDE.md", "AGENTS.md"}
                }
                self.assertEqual(actual, expected)
                for entry in data["skills"]:
                    skill = plugin / entry["path"]
                    self.assertTrue(skill.is_file(), str(skill))
                    for source in entry["sources"]:
                        self.assertTrue((plugin / source).is_file(), source)

    def test_internal_workers_and_duplicate_delegate_alias_require_explicit_selection(self):
        kiro = self.generated / "plugins/kiro/.codex-plugin/skills"
        for name in ("kiro-delegate-agent", "delegate"):
            policy = kiro / name / "agents/openai.yaml"
            self.assertEqual("policy:\n  allow_implicit_invocation: false\n", policy.read_text())
        for name in ("kiro-delegate", "configure"):
            self.assertFalse((kiro / name / "agents/openai.yaml").exists())
        # A combined canonical skill + specialist stays an automatic workflow entry.
        co = self.generated / "plugins/co-agent/.codex-plugin/skills/co-agent"
        self.assertFalse((co / "agents/openai.yaml").exists())

    def test_generated_file_hooks_explicitly_match_apply_patch(self):
        checked = 0
        for path in (self.generated / "plugins").glob("*/.codex-plugin/hook-handlers.json"):
            originals = json.loads(path.read_text())["handlers"]
            configured = json.loads((path.parent / "hooks.json").read_text())["hooks"]
            emitted = [(event, group.get("matcher", ""))
                       for event, groups in configured.items()
                       for group in groups for _ in group["hooks"]]
            self.assertEqual(len(originals), len(emitted))
            for original, (event, matcher) in zip(originals, emitted):
                if event in {"PreToolUse", "PostToolUse"} and any(
                    alias in original.get("matcher", "") for alias in ("Edit", "Write")
                ):
                    self.assertIsNotNone(re.search(matcher, "apply_patch"), matcher)
                    checked += 1
        self.assertGreater(checked, 0)

    def test_runner_uses_installed_root_preserves_cwd_argv_and_status(self):
        runner = ROOT / "scripts/codex/run.py"
        self.assertTrue(runner.is_file(), str(runner))
        with tempfile.TemporaryDirectory(prefix="codex portability ") as tmp:
            tmp = Path(tmp)
            plugin = tmp / "installed plugin"
            adapter = plugin / ".codex-plugin"
            adapter.mkdir(parents=True)
            shutil.copyfile(runner, adapter / "run.py")
            (adapter / "inventory.json").write_text(json.dumps({"plugin": "co-agent"}))
            helper = plugin / "skills/test/scripts/probe.py"
            helper.parent.mkdir(parents=True)
            helper.write_text(
                "import json, os, sys\n"
                "print(json.dumps({'cwd': os.getcwd(), 'args': sys.argv[1:], "
                "'root': os.environ['CLAUDE_PLUGIN_ROOT'], "
                "'host': os.environ['CO_AGENT_HOST']}))\nsys.exit(7)\n"
            )
            target = tmp / "user repository"
            target.mkdir()
            result = subprocess.run(
                [sys.executable, str(adapter / "run.py"),
                 "skills/test/scripts/probe.py", "space and $(literal)", "--flag"],
                cwd=target, capture_output=True, text=True,
                env={**os.environ, "CO_AGENT_HOST": "claude"},
            )
            self.assertEqual(result.returncode, 7, result.stderr)
            output = json.loads(result.stdout)
            self.assertEqual(output, {
                "cwd": str(target), "args": ["space and $(literal)", "--flag"],
                "root": str(plugin), "host": "codex",
            })

    def test_runner_rejects_out_of_package_script(self):
        runner = ROOT / "scripts/codex/run.py"
        self.assertTrue(runner.is_file(), str(runner))
        with tempfile.TemporaryDirectory() as tmp:
            plugin = Path(tmp) / "plugin"
            adapter = plugin / ".codex-plugin"
            adapter.mkdir(parents=True)
            shutil.copyfile(runner, adapter / "run.py")
            sentinel = Path(tmp) / "should-not-exist"
            outside = Path(tmp) / "outside.py"
            outside.write_text(f"from pathlib import Path\nPath({str(sentinel)!r}).touch()\n")
            (plugin / "escape.py").symlink_to(outside)
            for source in ("../outside.py", str(outside), "escape.py"):
                result = subprocess.run(
                    [sys.executable, str(adapter / "run.py"), source],
                    capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertFalse(sentinel.exists())

if __name__ == "__main__":
    unittest.main()
