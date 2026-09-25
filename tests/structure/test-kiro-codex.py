#!/usr/bin/env python3
"""Exercise Codex review transport, coverage and installed entry behavior offline."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "plugins/kiro/skills/kiro-delegate/scripts"
sys.path.insert(0, str(SCRIPTS))
import kiro_codex
import kiro_review
import kiro_setup


class CodexReviewTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="kiro codex consumer ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.response = "[]"
        self.returncode = 0
        self.calls = []

    def transport(self, argv, cwd, env, outp, errp, timeout, echo_tag=None):
        agent = json.loads((Path(cwd) / ".kiro/agents/kiro-review-notools.json").read_text())
        self.calls.append((argv, agent, env, timeout))
        Path(outp).write_text(self.response)
        Path(errp).write_text("")
        return self.returncode

    def invoke(self, *arguments, payload="diff --git a/example.py b/example.py\n+change\n"):
        output = io.StringIO()
        with mock.patch.object(kiro_review.shutil, "which", return_value="/fake/kiro-cli"), \
                mock.patch.object(kiro_review, "_run_streamed", side_effect=self.transport), \
                mock.patch("sys.stdin", io.StringIO(payload)), contextlib.redirect_stdout(output):
            status = kiro_codex.main(["review", "--root", str(self.root), "--diff", "-", *arguments])
        return status, json.loads(output.getvalue())

    def test_fresh_consumer_needs_no_agents_and_preserves_configuration(self):
        config = self.root / ".claude/kiro.local.json"
        config.parent.mkdir()
        config.write_text(json.dumps({"review": {"model": "selected-model", "effort": "max", "timeout": 57}}))
        payload = "diff\n+literal $(touch sentinel); `echo bad` \"quoted\"\n"
        with mock.patch.dict(os.environ, {"UNRELATED_API_KEY": "fixture-only"}):
            status, result = self.invoke(payload=payload)
        self.assertEqual((0, "PASS", "complete"), (status, result["status"], result["coverage"]))
        argv, agent, environment, timeout = self.calls[0]
        self.assertEqual(["kiro-cli", "chat", "--no-interactive", "--trust-tools="], argv[:4])
        self.assertEqual("selected-model", argv[argv.index("--model") + 1])
        self.assertEqual("max", argv[argv.index("--effort") + 1])
        self.assertEqual(57, timeout)
        self.assertNotIn("--v3", argv)
        self.assertIn(json.dumps(payload), " ".join(argv))
        for key in ("tools", "allowedTools", "resources"):
            self.assertEqual([], agent[key])
        self.assertEqual({}, agent["hooks"])
        self.assertEqual({}, agent["mcpServers"])
        self.assertIs(False, agent["useLegacyMcpJson"])
        self.assertNotIn("UNRELATED_API_KEY", environment)
        self.assertFalse((self.root / ".kiro").exists())

    def test_missing_or_tampered_consumer_agent_is_never_loaded(self):
        agent = self.root / ".kiro/agents/kiro-reviewer.json"
        agent.parent.mkdir(parents=True)
        agent.write_text('{"tools":["execute_bash"]}')
        self.assertEqual(0, self.invoke()[0])
        self.assertEqual([], self.calls[0][1]["tools"])
        self.assertEqual('{"tools":["execute_bash"]}', agent.read_text())

    def test_invalid_findings_are_errors_not_clean_reviews(self):
        for response in ("no response", '[null]', '[{"severity":"major"}]',
                         '[{"severity":[]}]', '[{"severity":{}}]',
                         '[{"severity":"critical","file":"x","issue":"bug","line":[]}]',
                         '[{"severity":"critical","file":"x","issue":"bug","line":true}]'):
            with self.subTest(response=response):
                self.response = response
                status, result = self.invoke()
                self.assertEqual((1, "ERROR"), (status, result["status"]))

    def test_failed_cli_and_timeout_are_errors(self):
        for returncode in (1, None):
            with self.subTest(returncode=returncode):
                self.returncode = returncode
                status, result = self.invoke()
                self.assertEqual((1, "ERROR"), (status, result["status"]))

    def test_critical_findings_return_failure(self):
        self.response = '[{"severity":"critical","file":"example.py","line":1,"issue":"bug"}]'
        status, result = self.invoke()
        self.assertEqual((2, "FAIL"), (status, result["status"]))
        self.assertEqual("bug", result["findings"][0]["issue"])

    def test_oversized_unicode_input_never_calls_kiro(self):
        status, result = self.invoke(payload="한" * (kiro_review._DIFF_CAP // 2))
        self.assertEqual((1, "ERROR"), (status, result["status"]))
        self.assertEqual([], self.calls)

    def test_encoded_argument_limit_is_reported_before_spawning(self):
        status, result = self.invoke(payload="\x01" * (kiro_review._DIFF_CAP - 1))
        self.assertEqual((1, "ERROR"), (status, result["status"]))
        self.assertIn("encoded review prompt", result["errors"]["review"])
        self.assertEqual([], self.calls)

    def test_invalid_block_setting_does_not_silently_change_threshold(self):
        config = self.root / ".claude/kiro.local.json"
        config.parent.mkdir()
        for block in ("typo", None, []):
            config.write_text(json.dumps({"review": {"block": block}}))
            status, result = self.invoke()
            self.assertEqual((1, "ERROR"), (status, result["status"]))
        self.assertEqual([], self.calls)

    def test_empty_input_is_not_a_review_pass(self):
        status, result = self.invoke(payload="")
        self.assertEqual((0, "NO_CHANGES"), (status, result["status"]))
        self.assertEqual([], self.calls)

    def test_incomplete_lens_review_keeps_findings_and_errors(self):
        finding = {"severity": "critical", "file": "x", "line": 1, "issue": "bug"}
        with mock.patch.object(kiro_review, "run_review_lenses",
                               return_value=([finding], {"scope": "timeout"}, False)):
            status, result = self.invoke("--lenses", "correctness,scope")
        self.assertEqual((1, "ERROR", "incomplete"), (status, result["status"], result["coverage"]))
        self.assertEqual([finding], result["findings"])
        self.assertIn("scope", result["errors"])

    def test_invalid_lens_and_mixed_scope_never_call_kiro(self):
        for arguments in (("--lenses", "correctness,correctness"), ("--lenses", "unknown"),
                          ("--", "ignored.py")):
            with self.subTest(arguments=arguments):
                self.assertEqual(1, self.invoke(*arguments)[0])
        self.assertEqual([], self.calls)

    def test_working_tree_includes_untracked_and_staged_paths(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        (self.root / "tracked.py").write_text("before\n")
        subprocess.run(["git", "-C", str(self.root), "add", "tracked.py"], check=True)
        subprocess.run(["git", "-C", str(self.root), "-c", "user.name=Fixture",
                        "-c", "user.email=fixture@example.test", "-c", "core.hooksPath=/dev/null",
                        "-c", "commit.gpgsign=false", "commit", "-qm", "fixture"], check=True)
        (self.root / "tracked.py").write_text("after\n")
        (self.root / "new file.py").write_text("new\n")
        (self.root / "staged.py").write_text("staged\n")
        subprocess.run(["git", "-C", str(self.root), "add", "staged.py"], check=True)
        output = io.StringIO()
        with mock.patch.object(kiro_review.shutil, "which", return_value="/fake/kiro-cli"), \
                mock.patch.object(kiro_review, "_run_streamed", side_effect=self.transport), \
                contextlib.redirect_stdout(output):
            status = kiro_codex.main(["review", "--root", str(self.root), "--working-tree"])
        self.assertEqual(0, status)
        prompt = " ".join(self.calls[0][0])
        self.assertIn("tracked.py", prompt)
        self.assertIn("new file.py", prompt)
        self.assertIn("staged.py", prompt)

    def test_doctor_does_not_claim_auth_without_probe(self):
        output = io.StringIO()
        version = subprocess.CompletedProcess([], 0, "kiro-cli fixture", "")
        with mock.patch.object(kiro_codex.shutil, "which", return_value="/fake/kiro-cli"), \
                mock.patch.object(kiro_codex.subprocess, "run", return_value=version), \
                mock.patch.object(kiro_setup, "probe") as probe, contextlib.redirect_stdout(output):
            self.assertEqual(0, kiro_codex.main(["doctor", "--root", str(self.root)]))
        probe.assert_not_called()
        self.assertEqual("NOT_PROBED", json.loads(output.getvalue())["authentication"])

    def test_untracked_collection_failure_cannot_report_complete_review(self):
        tracked = subprocess.CompletedProcess([], 0, "tracked diff\n", "")
        failure = subprocess.CompletedProcess([], 128, "", "fixture error")
        with mock.patch.object(kiro_review.subprocess, "run", side_effect=[tracked, failure]):
            diff, error = kiro_review._git_diff(str(self.root), ["."], False, strict=True)
        self.assertEqual("", diff)
        self.assertIn("ls-files", error)

    def test_untracked_diff_failure_cannot_report_complete_review(self):
        tracked = subprocess.CompletedProcess([], 0, "tracked diff\n", "")
        untracked = subprocess.CompletedProcess([], 0, "new.py\0", "")
        failure = subprocess.CompletedProcess([], 128, "", "fixture error")
        with mock.patch.object(kiro_review.subprocess, "run", side_effect=[tracked, untracked, failure]):
            diff, error = kiro_review._git_diff(str(self.root), ["."], False, strict=True)
        self.assertEqual("", diff)
        self.assertIn("new.py", error)

    def test_probe_keeps_selected_model_effort_and_empty_tool_trust(self):
        def process(argv, **kwargs):
            self.calls.append(argv)
            kwargs["stdout"].write("KIRO_SETUP_PROBE\n")
            return subprocess.CompletedProcess(argv, 0)
        with mock.patch.object(kiro_setup.shutil, "which", return_value="/fake/kiro-cli"), \
                mock.patch.object(kiro_setup.subprocess, "run", side_effect=process):
            self.assertEqual(("READY", ""), kiro_setup.probe(model="selected", effort="max"))
        argv = self.calls[0]
        self.assertIn("--trust-tools=", argv)
        self.assertNotIn("--v3", argv)
        self.assertEqual("selected", argv[argv.index("--model") + 1])
        self.assertEqual("max", argv[argv.index("--effort") + 1])

    def test_generator_embeds_native_entries_from_maintained_templates(self):
        spec = importlib.util.spec_from_file_location("codex_generator", ROOT / "scripts/sync-codex-plugins.py")
        generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generator)
        outputs = generator.generated_files(ROOT)
        for name in ("setup", "review", "configure"):
            target = ROOT / f"plugins/kiro/.codex-plugin/skills/{name}/SKILL.md"
            template = ROOT / f"scripts/codex/kiro-skills/{name}.md"
            self.assertIn(template.read_text().strip(), outputs[target])
            self.assertIn(f"../../../commands/{name}.md", outputs[target])


if __name__ == "__main__":
    unittest.main()
