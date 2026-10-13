"""Pinned, data-only diff capture for privileged CI and local review state."""

import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "plugins/co-agent/skills/pr-autofix/scripts/pr_diff.py"
spec = importlib.util.spec_from_file_location("pr_diff", SCRIPT)
pr_diff = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pr_diff)


def git(repo, *args):
    return subprocess.check_output(
        ["git", "-C", str(repo), *args], stderr=subprocess.DEVNULL,
        text=True).strip()


class DiffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="pr-diff-origin-")
        cls.root = Path(cls.temp.name)
        seed = cls.root / "seed"
        seed.mkdir()
        git(seed, "init", "-q", "-b", "main")
        git(seed, "config", "user.name", "Fixture")
        git(seed, "config", "user.email", "fixture@example.invalid")
        (seed / "existing.txt").write_text("original\n")
        (seed / ".gitattributes").write_text("*.txt diff=probe\n")
        git(seed, "add", ".")
        git(seed, "commit", "-qm", "shared ancestor")
        git(seed, "checkout", "-qb", "feature")
        for number in range(350):
            (seed / f"file-{number:03}.txt").write_text(f"entry {number}\n")
        (seed / "existing.txt").write_text("changed\n")
        (seed / "space name.txt").write_text("space path\n")
        (seed / "한글.txt").write_text("unicode path\n")
        git(seed, "add", ".")
        git(seed, "commit", "-qm", "large feature")
        cls.head = git(seed, "rev-parse", "HEAD")
        git(seed, "checkout", "-q", "main")
        (seed / "base-only.txt").write_text("base advanced\n")
        git(seed, "add", ".")
        git(seed, "commit", "-qm", "advance base")
        cls.base = git(seed, "rev-parse", "HEAD")
        cls.origin = cls.root / "origin.git"
        git(cls.root, "clone", "-q", "--bare", str(seed), str(cls.origin))
        cls.expected = subprocess.check_output([
            "git", "-C", str(seed), "diff", "--no-ext-diff", "--no-textconv",
            "--no-color", "--full-index", "--no-renames", "--submodule=short",
            "--src-prefix=a/", "--dst-prefix=b/",
            f"{cls.base}...{cls.head}", "--",
        ])

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pr-diff-consumer-")
        self.root = Path(self.temp.name)
        self.repo = self.root / "checkout"
        git(self.root, "clone", "-q", "--depth", "1", "--branch", "main",
            self.origin.as_uri(), str(self.repo))
        self.output = self.root / "diff.txt"

    def tearDown(self):
        self.temp.cleanup()

    def capture(self, **kwargs):
        pr_diff.capture(self.repo, self.base, self.head, self.output, **kwargs)

    def test_shallow_large_diff_matches_three_dot_scope(self):
        self.assertEqual("true", git(self.repo, "rev-parse", "--is-shallow-repository"))
        self.capture(verify_base_checkout=True)
        self.assertNotEqual(self.base, git(self.repo, "merge-base", self.base, self.head))
        self.assertEqual(self.expected, self.output.read_bytes())
        self.assertGreater(self.output.read_bytes().count(b"diff --git "), 300)
        self.assertNotIn(b"base-only.txt", self.output.read_bytes())
        self.assertEqual(self.base, git(self.repo, "rev-parse", "HEAD"))
        self.assertEqual("", git(self.repo, "status", "--porcelain"))

    def test_same_diff_from_non_shallow_head_checkout(self):
        self.capture()
        git(self.repo, "checkout", "-q", self.head)
        self.capture()
        self.assertEqual(self.expected, self.output.read_bytes())
        self.assertEqual(self.head, git(self.repo, "rev-parse", "HEAD"))

    def test_invalid_shas_are_rejected_before_git(self):
        for head in ("feature", "--upload-pack=bad", "a" * 39, self.head.upper()):
            with self.subTest(head=head), patch.object(pr_diff, "git") as run:
                with self.assertRaises(pr_diff.DiffError):
                    pr_diff.capture(self.repo, self.base, head, self.output)
                run.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_wrong_trusted_base_is_rejected(self):
        with self.assertRaisesRegex(pr_diff.DiffError, "trusted checkout"):
            pr_diff.capture(self.repo, self.head, self.base, self.output,
                            verify_base_checkout=True)
        self.assertFalse(self.output.exists())

    def test_unavailable_commit_preserves_existing_output(self):
        self.output.write_text("prior verified output\n")
        with self.assertRaises(pr_diff.DiffError):
            pr_diff.capture(self.repo, self.base, "0" * 40, self.output)
        self.assertEqual("prior verified output\n", self.output.read_text())

    def test_external_diff_textconv_fsmonitor_and_hooks_do_not_run(self):
        marker = self.root / "unexpected-execution"
        command = self.root / "probe.sh"
        command.write_text(f"#!/bin/sh\nprintf ran > '{marker}'\n")
        command.chmod(0o755)
        git(self.repo, "config", "diff.probe.command", str(command))
        git(self.repo, "config", "diff.probe.textconv", str(command))
        git(self.repo, "config", "core.fsmonitor", str(command))
        hooks = self.root / "hooks"
        hooks.mkdir()
        hook = hooks / "reference-transaction"
        hook.write_bytes(command.read_bytes())
        hook.chmod(0o755)
        git(self.repo, "config", "core.hooksPath", str(hooks))
        with patch.dict(os.environ, {"GIT_EXTERNAL_DIFF": str(command)}):
            self.capture()
        self.assertFalse(marker.exists())
        self.assertEqual(self.expected, self.output.read_bytes())

    def test_symlink_output_is_rejected(self):
        target = self.root / "target"
        target.write_text("keep\n")
        self.output.symlink_to(target)
        with self.assertRaisesRegex(pr_diff.DiffError, "symlink"):
            self.capture()
        self.assertEqual("keep\n", target.read_text())

    def test_git_errors_do_not_echo_remote_credentials(self):
        result = subprocess.CompletedProcess(
            [], 128, stdout=b"", stderr=b"https://private-token@example.invalid")
        with patch.object(pr_diff.subprocess, "run", return_value=result):
            with self.assertRaises(pr_diff.DiffError) as error:
                pr_diff.git(self.repo, "fetch", "origin")
        self.assertNotIn("private-token", str(error.exception))

    def test_checkout_change_preserves_existing_output(self):
        self.output.write_text("prior\n")
        original = pr_diff.git
        reads = 0

        def changing(repo, *args, **kwargs):
            nonlocal reads
            if args == ("rev-parse", "--verify", "HEAD"):
                reads += 1
                if reads == 2:
                    return self.head
            return original(repo, *args, **kwargs)

        with patch.object(pr_diff, "git", side_effect=changing):
            with self.assertRaisesRegex(pr_diff.DiffError, "checkout changed"):
                self.capture()
        self.assertEqual("prior\n", self.output.read_text())
        self.assertEqual([], list(self.root.glob(".pr-diff-*")))


if __name__ == "__main__":
    unittest.main()
