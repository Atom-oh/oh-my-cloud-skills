"""Implementation planning requires explicit mode selection and valid READY evidence.

Every provider boundary is stubbed; unexpected provider launches fail locally.
"""
import contextlib
import io
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

class ImplementationPlanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.user_config = self.root / "user.json"
        env = patch.dict(os.environ, {
            "PATH": os.environ.get("PATH", ""),
            "CO_AGENT_USER_CONFIG": str(self.user_config),
            "CO_AGENT_HOST": "claude",
        }, clear=True)
        env.start()
        self.addCleanup(env.stop)
        self.launches = []
        real_popen = subprocess.Popen

        def no_provider(argv, *args, **kwargs):
            if argv[0] == "git":
                return real_popen(argv, *args, **kwargs)
            self.launches.append(argv)
            raise AssertionError("unexpected external process")

        guard = patch.object(subprocess, "Popen", side_effect=no_provider)
        guard.start()
        self.addCleanup(guard.stop)


    def configure(self, value, user=False):
        path = self.user_config if user else self.root / ".claude/co-agent.local.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))
        return path


    def cli(self, args, module=config, use_root=True):
        stdout, stderr = io.StringIO(), io.StringIO()
        argv = ["helper.py", *args]
        if use_root:
            argv += ["--root", str(self.root)]
        with patch.object(sys, "argv", argv):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                rc = module.main()
        return rc, stdout.getvalue().strip(), stderr.getvalue()


    def ready(self, host, states):
        """Use the real summary producer; stub only discovery/provider calls."""
        probes = []

        def probe(peer):
            probes.append(peer)
            return states[peer], ""

        with patch.object(panel, "detect_cli",
                          side_effect=lambda peer: "/fake/" + peer if peer in states else None):
            with patch.object(panel, "detect_plugin", return_value=False):
                with patch.object(panel, "probe", side_effect=probe):
                    with contextlib.redirect_stdout(io.StringIO()):
                        self.assertEqual(0, panel.report(str(self.root), "/no-plugins",
                                                         as_json=True, host=host))
        return probes


    def assert_invalid_plan(self, host):
        for flag in ([], ["--allow-host-implementation"]):
            with self.subTest(host=host, allow_host=bool(flag)):
                rc, output, diagnostic = self.cli(["implementation-plan", "--host", host, *flag])
                self.assertEqual((2, ""), (rc, output))
                self.assertTrue(diagnostic)


    def test_host_implementation_requires_explicit_opt_in_and_ready_external_review(self):
        self.ready("codex", {"claude": "READY"})
        rc, output, _ = self.cli(["implementation-plan", "--host", "codex"])
        self.assertEqual((3, ""), (rc, output))
        rc, output, _ = self.cli(["implementation-plan", "--host", "codex",
                                  "--allow-host-implementation"])
        self.assertEqual(0, rc)
        self.assertEqual({"schema_version": 1, "mode": "host", "host": "codex",
                          "implementer": None, "reviewers": ["claude"]}, json.loads(output))

    def test_task_cwd_uses_explicit_setup_root_for_readiness_and_model_overrides(self):
        override = self.configure({
            "panel": {"codex": {"model": "fixture-review-model", "effort": "low"}},
            "harness": {"implementer": "codex",
                        "implementer_models": {"codex": "fixture-writer-model"},
                        "implementer_efforts": {"codex": "medium"}},
        })
        self.ready("claude", {"codex": "READY"})
        # A task checkout lacks the orchestration project's ignored local state.
        task = self.root / "task-worktree"
        task.mkdir()
        previous = os.getcwd()
        os.chdir(task)
        try:
            self.assertEqual((2, ""), self.cli(
                ["implementation-plan", "--host", "claude"], use_root=False)[:2])
            self.assertNotIn("fixture-writer-model", self.cli(
                ["impl-flags", "codex", "--host", "claude"], use_root=False)[1])
            self.assertEqual((0, "fresh"), self.cli(
                ["fresh", "--host", "claude"], module=panel)[:2])
            self.assertEqual((0, "true"), self.cli(
                ["gate-eligible", "codex", "--host", "claude"], module=panel)[:2])
            rc, output, _ = self.cli(["implementation-plan", "--host", "claude"])
            self.assertEqual(0, rc)
            self.assertEqual({"schema_version": 1, "mode": "peer", "host": "claude",
                              "implementer": "codex", "reviewers": ["codex"]},
                             json.loads(output))
            self.assertEqual((0, '-m\nfixture-review-model\n-c\nmodel_reasoning_effort="low"'),
                             self.cli(["flags", "codex", "--host", "claude"])[:2])
            self.assertEqual(
                (0, '-s\nworkspace-write\n-m\nfixture-writer-model\n-c\nmodel_reasoning_effort="medium"'),
                self.cli(["impl-flags", "codex", "--host", "claude"])[:2])
            override.write_text('{"harness":')
            self.assert_invalid_plan("claude")
        finally:
            os.chdir(previous)


    def test_planner_rejects_malformed_overrides_without_changing_advisory_loading(self):
        for user in (False, True):
            for host, peer in (("codex", "claude"), ("claude", "codex")):
                for content in (b'{"harness":{"implementer":"agy"},', b'\xff'):
                    with self.subTest(user=user, content=content):
                        self.ready(host, {peer: "READY"})
                        path = self.configure({}, user=user)
                        path.write_bytes(content)
                        self.assert_invalid_plan(host)
                        if content.startswith(b"{"):
                            rc, output, diagnostic = self.cli(["panel", "--host", host])
                            self.assertEqual(0, rc)
                            self.assertIn(peer, output.split())
                            self.assertIn("ignoring malformed", diagnostic)
                        path.unlink()


    def test_planner_rejects_invalid_shapes_even_when_setup_recorded_them(self):
        cases = [
            {"harness": []}, {"harness": False}, {"consensus": []},
            {"pr_gate": []}, {"push_gate": False}, {"profile": []},
            {"harness": {"implementer_models": []}},
            {"harness": {"implementer_efforts": {"codex": []}}},
            {"panel": {"claude": {"enabled": "false"}}},
            {"panel": {"claude": {"model": []}}},
            {"panel": {"claude": {"models": "model-name"}}},
            {"panel": {"claude": {"models": [[]]}}},
        ]
        for user in (False, True):
            for value in cases:
                with self.subTest(user=user, value=value):
                    path = self.configure(value, user=user)
                    self.ready("codex", {"claude": "READY"})
                    self.assert_invalid_plan("codex")
                    path.unlink()


    def test_planner_rejects_nonobject_override_documents(self):
        self.ready("codex", {"claude": "READY"})
        for user in (False, True):
            for value in (None, [], False, {"panel": []}, {"panel": {"claude": []}}):
                with self.subTest(user=user, value=value):
                    path = self.configure(value, user=user)
                    self.assert_invalid_plan("codex")
                    path.unlink()


    def test_planner_rejects_unreadable_overrides_instead_of_treating_them_as_absent(self):
        real_open = open
        for user in (False, True):
            for host, peer in (("codex", "claude"), ("claude", "codex")):
                self.ready(host, {peer: "READY"})
                path = self.configure({}, user=user)

                def deny_override(name, *args, **kwargs):
                    if os.fspath(name) == str(path):
                        raise PermissionError("fixture config is unreadable")
                    return real_open(name, *args, **kwargs)

                with self.subTest(user=user, failure="permission"), patch(
                        "builtins.open", side_effect=deny_override):
                    self.assert_invalid_plan(host)
                path.unlink()
                with self.subTest(user=user, failure="directory"):
                    path.mkdir()
                    self.assert_invalid_plan(host)
                    path.rmdir()
                with self.subTest(user=user, failure="broken symlink"):
                    path.symlink_to(self.root / "missing-target")
                    self.assert_invalid_plan(host)
                    path.unlink()


    def test_host_fallback_rejects_missing_stale_and_nonready_review_evidence(self):
        command = ["implementation-plan", "--host", "codex", "--allow-host-implementation"]
        self.assertEqual(2, self.cli(command)[0])
        self.ready("codex", {"claude": "AUTH", "kiro-cli": "TIMEOUT"})
        self.assertEqual(2, self.cli(command)[0])
        self.ready("codex", {"claude": "READY"})
        self.configure({"panel": {"claude": {"enabled": False}}})
        self.assertEqual(2, self.cli(command)[0])
        self.ready("codex", {"claude": "READY"})
        self.assertEqual(2, self.cli(command)[0])


    def test_plugin_only_readiness_cannot_authorize_host_implementation(self):
        self.ready("claude", {"kiro-cli": "AUTH", "codex": "READY"})
        path = self.root / ".claude/co-agent-panel.local.json"
        summary = json.loads(path.read_text())
        summary["peers"]["codex"].update(raw_cli=False, access="plugin")
        path.write_text(json.dumps(summary))
        self.assertEqual(2, self.cli(["implementation-plan", "--host", "claude",
                                      "--allow-host-implementation"])[0])


    def test_host_fallback_rejects_wrong_host_missing_hash_and_nonboolean_raw_cli(self):
        command = ["implementation-plan", "--host", "codex", "--allow-host-implementation"]
        self.ready("claude", {"codex": "READY"})
        self.assertEqual(2, self.cli(command)[0])
        self.ready("codex", {"claude": "READY"})
        with patch.object(panel, "_config_hash", return_value=""):
            self.assertFalse(panel.is_fresh(str(self.root), host="codex"))
            self.assertEqual(2, self.cli(command)[0])
        path = self.root / ".claude/co-agent-panel.local.json"
        summary = json.loads(path.read_text())
        summary["peers"]["claude"]["raw_cli"] = "false"
        path.write_text(json.dumps(summary))
        self.assertFalse(panel.gate_eligible(str(self.root), "claude", host="codex"))
        self.assertEqual(2, self.cli(command)[0])


    def test_only_ready_codex_can_be_delegated_writer_and_host_fallback_is_not_a_peer(self):
        self.ready("claude", {"codex": "READY", "kiro-cli": "READY"})
        rc, output, _ = self.cli(["implementation-plan", "--host", "claude"])
        self.assertEqual(0, rc)
        self.assertEqual({"schema_version": 1, "mode": "peer", "host": "claude",
                          "implementer": "codex", "reviewers": ["kiro-cli", "codex"]},
                         json.loads(output))
        self.configure({"panel": {"codex": {"enabled": False}}})
        self.ready("claude", {"kiro-cli": "READY"})
        self.assertEqual(3, self.cli(["implementation-plan", "--host", "claude"])[0])
        rc, output, _ = self.cli(["implementation-plan", "--host", "claude",
                                  "--allow-host-implementation"])
        self.assertEqual(0, rc)
        self.assertEqual("host", json.loads(output)["mode"])
        self.assertIsNone(json.loads(output)["implementer"])


if __name__ == "__main__":
    unittest.main()
