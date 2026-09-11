"""Exercise native project hooks without model calls or trust bypasses."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "scripts/codex/project-init-project/.codex"


class ProjectHookTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((TEMPLATE / "hooks.json").is_file(), "native Codex hook config is missing")
        self.assertTrue((TEMPLATE / "hooks/project_context.py").is_file(),
                        "native Codex project hook implementation is missing")
        temporary = tempfile.TemporaryDirectory(prefix="codex project hooks ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        shutil.copytree(TEMPLATE, self.root / ".codex")
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        (self.root / "src").mkdir()

    def hook(self, event, command="", tool="Bash"):
        result = subprocess.run(
            [sys.executable, str(self.root / ".codex/hooks/project_context.py")],
            input=json.dumps({"hook_event_name": event, "cwd": str(self.root / "src"),
                              "tool_name": tool, "tool_input": {"command": command}}),
            cwd=self.root / "src", capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"] if result.stdout else ""

    def test_session_context_uses_native_instructions(self):
        text = self.hook("SessionStart")
        self.assertIn("AGENTS.md", text)
        self.assertNotIn("CLAUDE.md", text)

    def test_patch_reminder_handles_multiple_files(self):
        text = self.hook("PostToolUse",
                         "*** Begin Patch\n*** Add File: src/one.py\n+x\n"
                         "*** Update File: src/two.py\n@@\n-y\n+z\n*** End Patch",
                         "apply_patch")
        self.assertIn("src/one.py", text)
        self.assertIn("src/two.py", text)

    def test_staged_secret_warning_never_echoes_value(self):
        secret = "ghp_" + "A" * 36
        (self.root / "config.txt").write_text(secret + "\n")
        subprocess.run(["git", "-C", str(self.root), "add", "config.txt"], check=True)
        text = self.hook("PreToolUse", "git status")
        self.assertIn("secret", text.lower())
        self.assertNotIn(secret, text)

    def test_staged_secret_warning_ignores_forced_git_diff_color(self):
        subprocess.run(["git", "-C", str(self.root), "config", "color.diff", "always"],
                       check=True)
        secret = "ghp_" + "B" * 36
        (self.root / "config.txt").write_text(secret + "\n")
        subprocess.run(["git", "-C", str(self.root), "add", "config.txt"], check=True)
        text = self.hook("PreToolUse", "git status")
        self.assertIn("secret", text.lower())
        self.assertNotIn(secret, text)
        self.assertNotIn("\x1b", text)
        configured = subprocess.run(
            ["git", "-C", str(self.root), "config", "--get", "color.diff"],
            check=True, capture_output=True, text=True,
        )
        self.assertEqual("always", configured.stdout.strip())

    def test_clean_staging_has_no_warning(self):
        (self.root / "src/one.py").write_text("print('hello')\n")
        subprocess.run(["git", "-C", str(self.root), "add", "src/one.py"], check=True)
        self.assertEqual("", self.hook("PreToolUse", "git status"))

    def test_config_commands_work_from_subdirectory(self):
        config = json.loads((self.root / ".codex/hooks.json").read_text())
        self.assertEqual({"SessionStart", "PreToolUse", "PostToolUse"}, set(config["hooks"]))
        command = config["hooks"]["SessionStart"][0]["hooks"][0]["command"]
        result = subprocess.run(
            ["bash", "-c", command], cwd=self.root / "src",
            input=json.dumps({"hook_event_name": "SessionStart"}),
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("AGENTS.md", json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"])


if __name__ == "__main__":
    unittest.main()
