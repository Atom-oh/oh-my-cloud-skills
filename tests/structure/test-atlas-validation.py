#!/usr/bin/env python3
"""Exercise Atlas validation exit codes against real disposable wiki files."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[2]
INDEX = REPO / "plugins/atlas/skills/atlas/scripts/atlas_index.py"


class AtlasValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="atlas validation ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.wiki = self.root / "docs/atlas"
        self.wiki.mkdir(parents=True)
        self.env = {
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_COUNT": "2",
            "GIT_CONFIG_KEY_0": "core.hooksPath",
            "GIT_CONFIG_VALUE_0": "/dev/null",
            "GIT_CONFIG_KEY_1": "commit.gpgsign",
            "GIT_CONFIG_VALUE_1": "false",
        }
        self.git("init", "-q")
        (self.root / "main.py").write_text("print('fixture')\n")
        self.git("add", "main.py")
        self.git("-c", "user.name=Atlas Test", "-c", "user.email=atlas@example.invalid",
                 "commit", "-q", "-m", "test: fixture source")
        self.head = self.git("rev-parse", "HEAD").stdout.strip()

    def git(self, *args):
        return subprocess.run(
            ["git", *args], cwd=self.root, env=self.env,
            check=True, capture_output=True, text=True,
        )

    def document(self, name="topic.md", related="[]"):
        path = self.wiki / name
        path.write_text(
            "---\n"
            "title: Fixture behavior\n"
            "description: Describe the fixture's local greeting output.\n"
            "covers: [main.py]\n"
            f"related: {related}\n"
            f"code_rev: {self.head}\n"
            "updated: 2026-09-11\n"
            "---\n\n"
            "The fixture prints a local greeting.\n"
        )
        return path

    def validate(self):
        return subprocess.run(
            [sys.executable, "-B", str(INDEX), "--validate", "--root", str(self.root)],
            cwd=self.root, env=self.env, capture_output=True, text=True,
        )

    def test_single_valid_orphan_warns_without_failing(self):
        self.document()
        result = self.validate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("advisory: topic.md: orphan", result.stdout)
        self.assertNotIn("error:", result.stdout)

    def test_multiple_orphans_all_warn_without_failing(self):
        self.document("first.md")
        self.document("second.md")
        result = self.validate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("advisory: first.md: orphan", result.stdout)
        self.assertIn("advisory: second.md: orphan", result.stdout)

    def test_broken_related_link_still_fails_alongside_orphan_warning(self):
        self.document(related="[missing.md]")
        result = self.validate()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("error: topic.md: broken related link: missing.md", result.stdout)
        self.assertIn("advisory: topic.md: orphan", result.stdout)

    def test_schema_errors_still_fail_alongside_orphan_warning(self):
        cases = [
            ("missing description",
             "description: Describe the fixture's local greeting output.\n", "",
             "missing required key: description"),
            ("scalar covers", "covers: [main.py]", "covers: main.py",
             "covers is not a list"),
            ("empty covers", "covers: [main.py]", "covers: []",
             "covers is empty"),
            ("scalar related", "related: []", "related: topic.md",
             "related is not a list"),
        ]
        for label, old, new, expected in cases:
            with self.subTest(case=label):
                path = self.document()
                path.write_text(path.read_text().replace(old, new))
                result = self.validate()
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(f"error: topic.md: {expected}", result.stdout)
                self.assertIn("advisory: topic.md: orphan", result.stdout)

    def test_valid_linked_docs_remain_clean(self):
        self.document("first.md", "[second.md]")
        self.document("second.md", "[first.md]")
        result = self.validate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
