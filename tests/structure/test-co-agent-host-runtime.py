"""Host selection and provider execution regressions; never invoke real AI CLIs."""
import contextlib
import io
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[2] / "plugins/co-agent/skills/co-agent/scripts"
sys.path.insert(0, str(SCRIPTS))
import check_panel as panel
import co_agent_config as config
import consensus_hooks as hooks


class HostRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ, {
            "PATH": os.environ.get("PATH", ""),
            "CO_AGENT_USER_CONFIG": str(self.root / "no-user-config.json"),
        }, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        # Any unexpected provider subprocess must fail locally instead of contacting AI.
        real_popen = subprocess.Popen

        def local_git_only(argv, *args, **kwargs):
            if argv[0] != "git":
                raise AssertionError("unexpected provider subprocess")
            return real_popen(argv, *args, **kwargs)

        self.process_guard = patch.object(subprocess, "Popen", side_effect=local_git_only)
        self.process_guard.start()
        self.addCleanup(self.process_guard.stop)

    def configure(self, value):
        directory = self.root / ".claude"
        directory.mkdir(exist_ok=True)
        (directory / "co-agent.local.json").write_text(json.dumps(value))

    def config_cli(self, args):
        output = io.StringIO()
        with patch.object(sys, "argv", ["co_agent_config.py", *args, "--root", str(self.root)]):
            with contextlib.redirect_stdout(output):
                rc = config.main()
        return rc, output.getvalue().strip()

    def test_host_detection_and_explicit_override(self):
        cases = [
            ({}, [], "kiro-cli codex agy"),
            ({"CODEX_THREAD_ID": "thread"}, [], "kiro-cli claude agy"),
            ({"CODEX_SESSION_ID": "session"}, [], "kiro-cli claude agy"),
            ({"PLUGIN_ROOT": "/installed/plugin", "PLUGIN_DATA": "/data"}, [],
             "kiro-cli claude agy"),
            ({"CODEX_THREAD_ID": "thread", "CLAUDECODE": "1"}, [], "kiro-cli codex agy"),
            ({"CODEX_THREAD_ID": "thread", "CO_AGENT_HOST": "claude"}, [],
             "kiro-cli codex agy"),
            ({"CO_AGENT_HOST": "claude"}, ["--host", "codex"], "kiro-cli claude agy"),
        ]
        for markers, flags, expected in cases:
            with self.subTest(markers=markers, flags=flags), patch.dict(os.environ, markers):
                self.assertEqual((0, expected), self.config_cli(["panel", *flags]))
        with patch.dict(os.environ, {"CODEX_THREAD_ID": "thread"}):
            self.assertEqual((0, "agy"), self.config_cli(["implementer"]))
            self.assertEqual((0, "codex"), self.config_cli(["host"]))

    def test_invalid_explicit_host_is_not_silently_replaced(self):
        with patch.dict(os.environ, {"CO_AGENT_HOST": "typo"}), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(2, self.config_cli(["panel"])[0])

    def test_config_loaded_by_file_path_can_import_its_host_helper(self):
        with patch.object(sys, "path", [p for p in sys.path if p != str(SCRIPTS)]):
            with patch.dict(sys.modules):
                sys.modules.pop("co_agent_host", None)
                spec = importlib.util.spec_from_file_location("config_by_path", SCRIPTS / "co_agent_config.py")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                with patch.dict(os.environ, {"CODEX_THREAD_ID": "thread"}):
                    self.assertEqual("codex", module.detect_host())

    def report(self, host=None):
        probes = []

        def probe(peer):
            probes.append(peer)
            return "READY", ""

        argv = ["check_panel.py", "report", "--root", str(self.root),
                "--plugins-root", str(self.root / "no-plugins"), "--json"]
        if host is not None:
            argv.extend(["--host", host])
        with patch.object(panel, "detect_cli", side_effect=lambda peer: "/fake/" + peer):
            with patch.object(panel, "probe", side_effect=probe), patch.object(sys, "argv", argv):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(0, panel.main())
        return json.loads((self.root / ".claude/co-agent-panel.local.json").read_text()), probes

    def test_setup_probes_only_enabled_peers_of_detected_host(self):
        self.configure({"panel": {"agy": {"enabled": False}}})
        with patch.dict(os.environ, {"CODEX_THREAD_ID": "thread"}):
            summary, probes = self.report()
        self.assertEqual(["kiro-cli", "claude"], probes)
        self.assertEqual({"kiro-cli", "claude"}, set(summary["peers"]))

    def test_setup_explicit_host_and_freshness_across_hosts(self):
        summary, probes = self.report(host="codex")
        self.assertEqual(["kiro-cli", "claude", "agy"], probes)
        self.assertEqual("codex", summary.get("host"))
        self.assertFalse(panel.is_fresh(str(self.root)))
        with patch.dict(os.environ, {"CO_AGENT_HOST": "codex"}):
            self.assertTrue(panel.is_fresh(str(self.root)))

    def test_readiness_never_counts_the_current_host_from_an_old_summary(self):
        self.report(host="claude")
        with patch.dict(os.environ, {"CO_AGENT_HOST": "codex"}):
            self.assertFalse(panel.gate_eligible(str(self.root), "codex"))

    def test_gate_panel_includes_claude_and_excludes_codex(self):
        with patch.dict(os.environ, {"CODEX_THREAD_ID": "thread"}):
            with patch.object(hooks.shutil, "which", side_effect=lambda peer: "/fake/" + peer):
                peers, _ = hooks._panel(str(self.root))
        self.assertEqual(["kiro-cli", "claude", "agy"], peers)

    def test_gate_path_fallback_still_uses_the_detected_host(self):
        with patch.dict(os.environ, {"CODEX_THREAD_ID": "thread"}):
            with patch.object(hooks, "cac", None):
                with patch.object(hooks.shutil, "which", side_effect=lambda peer: "/fake/" + peer):
                    peers, _ = hooks._panel(str(self.root))
        self.assertEqual({"kiro-cli", "claude", "agy"}, set(peers))

    def run_gate(self, event, verdict="BLOCK: correctness issue", returncode=0):
        self.configure({
            "panel": {"claude": {"model": "sonnet"}},
            "pr_gate": {"enabled": True, "block": True, "quorum": "any"},
            "push_gate": {"enabled": True, "block": True},
        })
        calls = []

        def run(argv, **kwargs):
            if argv[0] == "git":
                # The temporary fixture is not a git repo, so its local config is
                # not tracked. Keep the real consent/config logic in the gate.
                return subprocess.CompletedProcess(argv, 128, stdout="", stderr="not a repository")
            calls.append((argv, kwargs))
            return subprocess.CompletedProcess(argv, returncode, stdout=verdict, stderr="")

        command = "git push" if event == "push" else "gh pr create"
        diff = "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -1 +1 @@\n-old\n+new\n"
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ, {
                "CO_AGENT_HOST": "codex", "ANTHROPIC_API_KEY": "fixture",
                "ANTHROPIC_AUTH_TOKEN": "fixture", "GH_TOKEN": "unrelated",
                "AWS_SECRET_ACCESS_KEY": "unrelated",
            }))
            stack.enter_context(patch.object(hooks.shutil, "which",
                                             side_effect=lambda p: "/fake/claude" if p == "claude" else None))
            stack.enter_context(patch.object(sys, "stdin",
                                             io.StringIO(json.dumps({"tool_input": {"command": command}}))))
            stack.enter_context(patch.object(hooks, "_base_ref", return_value="main"))
            stack.enter_context(patch.object(hooks, "_resolve_push_range", return_value=("main...HEAD", None)))
            stack.enter_context(patch.object(hooks, "_git_diff", return_value=(True, diff, "")))
            stack.enter_context(patch.object(hooks.subprocess, "run", side_effect=run))
            stack.enter_context(contextlib.redirect_stderr(io.StringIO()))
            fn = hooks.ev_pre_push_gate if event == "push" else hooks.ev_pre_pr_gate
            rc = fn(str(self.root))
        return rc, calls

    def test_claude_only_peer_can_block_pr_and_push(self):
        for event, count in (("pr", 1), ("push", 3)):
            with self.subTest(event=event):
                rc, calls = self.run_gate(event)
                self.assertEqual(2, rc)
                self.assertEqual(count, len(calls))
                for argv, kwargs in calls:
                    self.assertEqual("claude", argv[0])
                    self.assertEqual("plan", argv[argv.index("--permission-mode") + 1])
                    self.assertEqual("Read,Grep,Glob", argv[argv.index("--tools") + 1])
                    self.assertEqual("sonnet", argv[argv.index("--model") + 1])
                    self.assertIn("+new", kwargs["input"])
                    self.assertNotIn("+new", " ".join(argv))
                    self.assertNotEqual(str(self.root), kwargs["cwd"])
                    self.assertIn("ANTHROPIC_API_KEY", kwargs["env"])
                    self.assertIn("ANTHROPIC_AUTH_TOKEN", kwargs["env"])
                    self.assertNotIn("GH_TOKEN", kwargs["env"])
                    self.assertNotIn("AWS_SECRET_ACCESS_KEY", kwargs["env"])

    def test_failed_claude_process_does_not_cast_a_verdict(self):
        for event in ("pr", "push"):
            with self.subTest(event=event):
                rc, calls = self.run_gate(event, returncode=1)
                self.assertGreater(len(calls), 0)
                self.assertEqual(0, rc)

    def test_codex_gate_can_start_in_its_isolated_non_git_directory(self):
        for argv in (hooks._build_argv("codex", None, "/tmp/review.diff"),
                     hooks._build_push_argv("codex", None, "/tmp/review.diff", "correctness")):
            self.assertIn("--skip-git-repo-check", argv)
            self.assertEqual("read-only", argv[argv.index("-s") + 1])


if __name__ == "__main__":
    unittest.main()
