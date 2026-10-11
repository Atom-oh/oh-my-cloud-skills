#!/usr/bin/env python3
"""Local behavioral regressions for Kiro support-file preparation."""

import concurrent.futures
import importlib.util
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "plugins/kiro/skills/kiro-delegate/scripts"
HELPER = SCRIPTS / "prepare_worktree.py"
SPEC = importlib.util.spec_from_file_location("kiro_prepare", HELPER)
PREPARE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PREPARE)
NAME = "spec_1"
PROMPT = b"Literal task $(touch unexpected) `echo untouched` 'quotes'\n"


def git(directory, *args):
    return subprocess.run(
        ["git", "-C", str(directory), "-c", "core.hooksPath=/dev/null", *args],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull},
    ).stdout


def snapshot(directory):
    """Record bytes, symlink targets and directory names without following links."""
    result = {}
    if not directory.exists() and not directory.is_symlink():
        return result
    for base, dirs, files in os.walk(directory, followlinks=False):
        for name in dirs + files:
            path = Path(base) / name
            relative = str(path.relative_to(directory))
            if path.is_symlink():
                result[relative] = ("link", os.readlink(path))
            elif path.is_dir():
                result[relative] = ("directory",)
            else:
                result[relative] = ("file", path.read_bytes())
    return result


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="kiro-preparation-test-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base / "source with spaces"
        self.root.mkdir()
        git(self.root, "init", "-q")
        git(self.root, "config", "user.email", "fixture@example.invalid")
        git(self.root, "config", "user.name", "Fixture")
        (self.root / "tracked.txt").write_text("base\n")
        git(self.root, "add", "tracked.txt")
        git(self.root, "commit", "-qm", "fixture base")
        self.worktree = self.base / "worktree with spaces"
        git(self.root, "worktree", "add", "--detach", str(self.worktree), "HEAD")
        self.spec_dir = f".kiro/specs/{NAME}"
        self.source_files = {
            ".kiro/agents/kiro-implementer.json": b'{"name":"kiro-implementer"}\n',
            f"{self.spec_dir}/requirements.md": b"Requirements\n",
            f"{self.spec_dir}/design.md": b"Design\n",
            f"{self.spec_dir}/tasks.md": b"**Files:** `tracked.txt`\n",
            f"{self.spec_dir}/additional notes.md": b"Additional specification\n",
        }
        for relative, data in self.source_files.items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        self.outside = self.base / "outside"
        self.outside.mkdir()
        self.sentinel = self.outside / "sentinel"
        self.sentinel.write_bytes(b"outside must survive\n")
        self.exclude = Path(os.fsdecode(git(self.worktree, "rev-parse",
                                           "--path-format=absolute",
                                           "--git-path", "info/exclude")).strip())

    def invoke(self, command="prepare", prompt=PROMPT):
        args = [sys.executable, str(HELPER), command, "--worktree", str(self.worktree)]
        if command == "prepare":
            args += ["--root", str(self.root), "--spec-name", NAME]
        return subprocess.run(args, input=prompt, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, check=False)

    def unchanged_after_refusal(self):
        before = snapshot(self.worktree / ".kiro")
        outside = snapshot(self.outside)
        exclude = self.exclude.read_bytes()
        result = self.invoke()
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(b"REFUSE:", result.stderr)
        self.assertEqual(before, snapshot(self.worktree / ".kiro"))
        self.assertEqual(outside, snapshot(self.outside))
        self.assertEqual(exclude, self.exclude.read_bytes())
        return result

    def test_normal_preparation_preserves_text_and_excludes_all_support(self):
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        for relative, data in self.source_files.items():
            self.assertEqual((self.worktree / relative).read_bytes(), data)
        self.assertEqual((self.worktree / ".kiro/task-prompt.md").read_bytes(), PROMPT)
        self.assertFalse((self.worktree / "unexpected").exists())
        # capture-diff's git add -A cannot capture the helper's support files.
        git(self.worktree, "add", "-A")
        self.assertEqual(git(self.worktree, "diff", "--cached", "--name-only"), b"")
        (self.worktree / "tracked.txt").write_text("implementation\n")
        git(self.worktree, "add", "-A")
        self.assertEqual(git(self.worktree, "diff", "--cached", "--name-only"),
                         b"tracked.txt\n")

    def test_each_directory_symlink_is_refused_before_writes(self):
        for relative in (".kiro", ".kiro/agents", ".kiro/specs", self.spec_dir):
            with self.subTest(relative=relative):
                path = self.worktree / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.symlink_to(self.outside, target_is_directory=True)
                self.unchanged_after_refusal()
                path.unlink()

    def test_every_actual_copied_leaf_and_prompt_symlink_is_refused(self):
        for relative in (*self.source_files, ".kiro/task-prompt.md"):
            with self.subTest(relative=relative):
                path = self.worktree / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.symlink_to(self.sentinel)
                self.unchanged_after_refusal()
                path.unlink()

    def test_committed_spec_leaf_symlink_cannot_overwrite_outside(self):
        relative = f"{self.spec_dir}/tasks.md"
        path = self.worktree / relative
        path.parent.mkdir(parents=True)
        path.symlink_to(self.sentinel)
        git(self.worktree, "add", relative)
        git(self.worktree, "commit", "-qm", "fixture committed spec symlink")
        self.unchanged_after_refusal()

    def test_tracked_support_collision_precedes_all_writes(self):
        # An additional tracked non-Markdown spec is still a reserved-directory
        # collision, even though it is not in the actual copied-file list.
        for relative in (".kiro/agents/kiro-implementer.json",
                         ".kiro/task-prompt.md", f"{self.spec_dir}/tracked.txt"):
            with self.subTest(relative=relative):
                path = self.worktree / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"tracked sentinel\n")
                git(self.worktree, "add", relative)
                result = self.unchanged_after_refusal()
                self.assertIn(b"tracked support path", result.stderr)
                git(self.worktree, "rm", "-f", "--", relative)

    def test_existing_untracked_leaf_is_preserved(self):
        path = self.worktree / f"{self.spec_dir}/design.md"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"existing untracked content\n")
        self.unchanged_after_refusal()

    def test_source_spec_symlink_is_not_read(self):
        path = self.root / f"{self.spec_dir}/additional notes.md"
        path.unlink()
        path.symlink_to(self.sentinel)
        self.unchanged_after_refusal()

    def test_source_directory_symlink_is_refused(self):
        path = self.root / ".kiro/agents"
        shutil.rmtree(path)
        path.symlink_to(self.outside, target_is_directory=True)
        self.unchanged_after_refusal()

    def test_hardlinked_destination_is_preserved(self):
        path = self.worktree / ".kiro/task-prompt.md"
        path.parent.mkdir()
        os.link(self.sentinel, path)
        self.unchanged_after_refusal()

    def test_unsafe_exclude_file_aborts_before_support_writes(self):
        self.exclude.unlink()
        self.exclude.symlink_to(self.sentinel)
        before = snapshot(self.worktree / ".kiro")
        result = self.invoke()
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(before, snapshot(self.worktree / ".kiro"))
        self.assertEqual(self.sentinel.read_bytes(), b"outside must survive\n")

    def test_directory_swap_after_preflight_is_refused(self):
        (self.worktree / ".kiro").mkdir()
        original = PREPARE.SafeTree.create
        swapped = False

        def race(tree, relative, data):
            nonlocal swapped
            if not swapped:
                swapped = True
                (self.worktree / ".kiro").rename(self.worktree / "parked-kiro")
                (self.worktree / ".kiro").symlink_to(self.outside, target_is_directory=True)
            return original(tree, relative, data)

        before = snapshot(self.outside)
        with mock.patch.object(PREPARE.SafeTree, "create", race):
            with self.assertRaises((PREPARE.Refusal, OSError)):
                PREPARE.prepare(str(self.root), str(self.worktree), NAME, PROMPT)
        self.assertEqual(before, snapshot(self.outside))
        self.assertEqual(snapshot(self.worktree / "parked-kiro"), {})

    def test_leaf_swap_after_preflight_is_refused_by_exclusive_open(self):
        original = PREPARE.SafeTree.create

        def race(tree, relative, data):
            if relative.endswith("/tasks.md"):
                path = self.worktree / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.symlink_to(self.sentinel)
            return original(tree, relative, data)

        with mock.patch.object(PREPARE.SafeTree, "create", race):
            with self.assertRaises((PREPARE.Refusal, OSError)):
                PREPARE.prepare(str(self.root), str(self.worktree), NAME, PROMPT)
        self.assertEqual(self.sentinel.read_bytes(), b"outside must survive\n")

    def test_retry_writes_literal_stdin_without_following_symlink(self):
        self.assertEqual(self.invoke().returncode, 0)
        retry = b"Failure: $(touch unexpected) `echo unsafe`\n"
        result = self.invoke("write-prompt", retry)
        self.assertEqual(result.returncode, 0, result.stderr)
        path = self.worktree / ".kiro/task-prompt.md"
        self.assertEqual(path.read_bytes(), retry)
        path.unlink()
        path.symlink_to(self.sentinel)
        result = self.invoke("write-prompt", retry)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.sentinel.read_bytes(), b"outside must survive\n")

    def test_final_exclude_phase_directory_swap_is_refused(self):
        original = PREPARE._append_excludes

        def swap(tree, expected, patterns):
            (self.worktree / ".kiro").rename(self.worktree / "parked-support")
            (self.worktree / ".kiro").symlink_to(self.outside, target_is_directory=True)
            return original(tree, expected, patterns)

        before = snapshot(self.outside)
        with mock.patch.object(PREPARE, "_append_excludes", swap):
            with self.assertRaises(PREPARE.Refusal):
                PREPARE.prepare(str(self.root), str(self.worktree), NAME, PROMPT)
        self.assertEqual(before, snapshot(self.outside))

    def test_final_exclude_phase_regular_leaf_replacement_is_refused(self):
        original = PREPARE._append_excludes
        path = self.worktree / ".kiro/agents/kiro-implementer.json"

        def swap(tree, expected, patterns):
            path.rename(path.with_name("original-agent.json"))
            path.write_bytes(b'{"name":"replacement"}\n')
            return original(tree, expected, patterns)

        with mock.patch.object(PREPARE, "_append_excludes", swap):
            with self.assertRaisesRegex(PREPARE.Refusal, "support leaf changed"):
                PREPARE.prepare(str(self.root), str(self.worktree), NAME, PROMPT)

    def test_final_exclude_phase_same_inode_content_change_is_refused(self):
        original = PREPARE._append_excludes
        path = self.worktree / ".kiro/task-prompt.md"

        def update(tree, expected, patterns):
            path.write_bytes(b"unexpected replacement text\n")
            return original(tree, expected, patterns)

        with mock.patch.object(PREPARE, "_append_excludes", update):
            with self.assertRaisesRegex(PREPARE.Refusal, "support contents changed"):
                PREPARE.prepare(str(self.root), str(self.worktree), NAME, PROMPT)

    def test_final_exclude_leaf_replacement_is_refused(self):
        original = PREPARE._append_excludes

        def update(tree, expected, patterns):
            identity = original(tree, expected, patterns)
            self.exclude.unlink()
            self.exclude.symlink_to(self.sentinel)
            return identity

        with mock.patch.object(PREPARE, "_append_excludes", update):
            with self.assertRaises(PREPARE.Refusal):
                PREPARE.prepare(str(self.root), str(self.worktree), NAME, PROMPT)
        self.assertEqual(self.sentinel.read_bytes(), b"outside must survive\n")

    def test_final_exclude_pattern_removal_is_refused(self):
        original = PREPARE._append_excludes

        def update(tree, expected, patterns):
            identity = original(tree, expected, patterns)
            self.exclude.write_bytes(b"# replaced exclude patterns\n")
            return identity

        with mock.patch.object(PREPARE, "_append_excludes", update):
            with self.assertRaisesRegex(PREPARE.Refusal, "required git exclude patterns"):
                PREPARE.prepare(str(self.root), str(self.worktree), NAME, PROMPT)

    def test_retry_leaf_swap_between_validation_and_open_is_refused(self):
        self.assertEqual(self.invoke().returncode, 0)
        real_open = os.open
        path = self.worktree / ".kiro/task-prompt.md"

        def race(name, flags, *args, **kwargs):
            if name == "task-prompt.md" and flags & os.O_WRONLY:
                path.unlink()
                path.symlink_to(self.sentinel)
            return real_open(name, flags, *args, **kwargs)

        with mock.patch.object(PREPARE.os, "open", race):
            with self.assertRaises((PREPARE.Refusal, OSError)):
                PREPARE.write_prompt(str(self.worktree), b"retry\n")
        self.assertEqual(self.sentinel.read_bytes(), b"outside must survive\n")

    def test_bad_slug_and_main_checkout_are_refused(self):
        for worktree, name in ((self.worktree, "../escape"), (self.root, NAME)):
            with self.subTest(worktree=worktree, name=name):
                with self.assertRaises(PREPARE.Refusal):
                    PREPARE.prepare(str(self.root), str(worktree), name, PROMPT)
        self.assertFalse((self.worktree / ".kiro").exists())

    def test_parallel_runs_keep_attempt_logs_and_credit_totals_separate(self):
        def new_run(_):
            result = subprocess.run(
                [sys.executable, str(HELPER), "new-run"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
                env={**os.environ, "TMPDIR": str(self.worktree)},
            )
            return Path(os.fsdecode(result.stdout).strip())

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            runs = list(executor.map(new_run, range(2)))
        for run in runs:
            self.addCleanup(shutil.rmtree, run)
        self.assertNotEqual(runs[0], runs[1])
        for run in runs:
            self.assertEqual(stat.S_IMODE(run.stat().st_mode), 0o700)
            self.assertNotIn(self.worktree, run.parents)
        (runs[0] / "task-1-attempt-0.log").write_text("Credits: 0.25\n")
        (runs[0] / "task-1-attempt-1.log").write_text("Credits: 0.10\n")
        (runs[1] / "task-1-attempt-0.log").write_text("Credits: 9.99\n")
        # Execute the documented run-directory glob, with paths passed as data.
        command = 'python3 "$1" credits "$2"/*.log'
        for run, expected in zip(runs, (b"0.35\n", b"9.99\n")):
            result = subprocess.run(
                ["sh", "-c", command, "credit-fixture", str(SCRIPTS / "kiro_run.py"),
                 str(run)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
            )
            self.assertEqual(result.stdout, expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
