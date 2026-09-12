#!/usr/bin/env python3
"""Behavioral packaging regressions; no network or model calls."""
import json
import os
from pathlib import Path
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

    def test_hook_adapts_every_patch_file_and_preserves_denial(self):
        bridge = ROOT / "scripts/codex/hook.py"
        self.assertTrue(bridge.is_file(), str(bridge))
        with tempfile.TemporaryDirectory(prefix="codex hook ") as tmp:
            plugin = Path(tmp)
            adapter = plugin / ".codex-plugin"
            adapter.mkdir()
            shutil.copyfile(bridge, adapter / "hook.py")
            echo_script = plugin / "echo.py"
            echo_script.write_text(
                "import json,sys\np=json.load(sys.stdin)\n"
                "print(json.dumps({'hookSpecificOutput':{'hookEventName':'PostToolUse',"
                "'additionalContext':p['tool_input']['file_path']}}))\n"
            )
            spec = {
                "plugin": "test",
                "handlers": [
                    {"event": "PostToolUse", "matcher": "Edit|Write",
                     "command": 'python3 "$CLAUDE_PLUGIN_ROOT/echo.py"'},
                    {"event": "PreToolUse", "matcher": "Bash", "command":
                     """printf '%s' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"review missing"}}'"""},
                    {"event": "PostToolUse", "matcher": "Edit",
                     "command": 'python3 "$CLAUDE_PLUGIN_ROOT/echo.py"'},
                    {"event": "PostToolUse", "matcher": "Write",
                     "command": 'python3 "$CLAUDE_PLUGIN_ROOT/echo.py"'},
                ],
            }
            (adapter / "hook-handlers.json").write_text(json.dumps(spec))
            payload = {"cwd": tmp, "hook_event_name": "PostToolUse",
                       "tool_name": "apply_patch", "tool_input": {"command":
                           "*** Begin Patch\n*** Add File: new file.md\n+x\n"
                           "*** Update File: old.md\n*** Move to: moved.md\n@@\n-a\n+b\n"
                           "*** Delete File: removed.md\n*** End Patch"}}
            result = subprocess.run(
                [sys.executable, str(adapter / "hook.py"), "0"],
                input=json.dumps(payload), capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
            for relative in ("new file.md", "moved.md", "removed.md"):
                self.assertIn(str(plugin / relative), context)
            # Codex aliases apply_patch to BOTH Edit and Write. Distinguish file
            # operations so the legacy Edit/Write handlers do not both process
            # every file (and start the same background evaluator twice).
            for index, included, excluded in (
                ("2", "moved.md", "new file.md"),
                ("3", "new file.md", "moved.md"),
            ):
                result = subprocess.run(
                    [sys.executable, str(adapter / "hook.py"), index],
                    input=json.dumps(payload), capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
                self.assertIn(str(plugin / included), context)
                self.assertNotIn(str(plugin / excluded), context)
            payload.update(hook_event_name="PreToolUse", tool_name="Bash",
                           tool_input={"command": "git push"})
            result = subprocess.run(
                [sys.executable, str(adapter / "hook.py"), "1"],
                input=json.dumps(payload), capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"],
                             "deny")


if __name__ == "__main__":
    unittest.main()
