"""The repository hook keeps a canonical English README without translation churn."""
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


class ReadmeLanguageTests(unittest.TestCase):
    def test_readme_edits_request_english_maintenance(self):
        settings = json.loads((ROOT / ".claude/settings.json").read_text())
        command = next(h["command"] for group in settings["hooks"]["PostToolUse"]
                       for h in group["hooks"] if h.get("statusMessage") == "Checking README sync...")
        for path in ("/repo/README.md", "README.md"):
            with self.subTest(path=path):
                result = subprocess.run(
                    ["bash", "-c", command], input=json.dumps({"tool_input": {"file_path": path}}),
                    check=True, capture_output=True, text=True,
                )
                message = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
                self.assertIn("English", message)
                self.assertNotIn("translate it to Korean", message)
                self.assertIn("compatibility", message)


if __name__ == "__main__":
    unittest.main()
