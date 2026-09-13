"""Retired peers cannot return through config, readiness, hooks, or writer fallback.

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
import consensus_hooks as hooks
import co_agent_env as environment

RETIRED = ("agy", "antigravity", "gemini")


class RetiredPeerTests(unittest.TestCase):
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

    def cli(self, args, module=config):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(sys, "argv", ["helper.py", *args, "--root", str(self.root)]):
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

    def test_default_panel_and_model_matrix_are_host_cross_peers_only(self):
        for host, peers in (("claude", ["kiro-cli", "codex"]),
                            ("codex", ["kiro-cli", "claude"])):
            with self.subTest(host=host):
                rc, text, _ = self.cli(["panel", "--host", host])
                self.assertEqual((0, peers), (rc, text.split()))
                rc, text, _ = self.cli(["pairs", "--host", host, "--profile", "deep"])
                self.assertEqual(0, rc)
                self.assertEqual(set(peers), {line.split("\t")[0] for line in text.splitlines()})

    def test_stale_overrides_cannot_restore_retired_panel_members_or_model_pairs(self):
        for user in (False, True):
            for retired in RETIRED:
                with self.subTest(scope="user" if user else "local", retired=retired):
                    path = self.configure({
                        "panel": {"kiro-cli": {"enabled": False}, "codex": {"enabled": False},
                                  retired: {"enabled": True, "models": ["DO_NOT_ECHO_MODEL"]}},
                        "harness": {"implementer_models": {retired: "DO_NOT_ECHO_MODEL"},
                                    "implementer_efforts": {retired: "high"}},
                    }, user=user)
                    for command in ("panel", "pairs", "matrix"):
                        rc, text, diagnostic = self.cli([command, "--host", "claude"])
                        self.assertEqual(0, rc)
                        if command != "matrix":
                            self.assertEqual("", text)
                        self.assertNotIn("DO_NOT_ECHO_MODEL", text + diagnostic)
                        self.assertIn(retired, diagnostic)
                        self.assertIn("remov", diagnostic.lower())
                        self.assertIn(str(path), diagnostic)
                    with contextlib.redirect_stderr(io.StringIO()):
                        effective = config.effective(str(self.root))
                    self.assertNotIn(retired, effective["panel"])
                    self.assertNotIn(retired, effective["harness"]["implementer_models"])
                    path.unlink()

    def test_explicit_retired_cli_selectors_fail_with_migration_guidance(self):
        for peer in RETIRED:
            commands = (["flags", peer], ["enabled", peer], ["context-limit", peer],
                        ["fits", peer, "1"], ["impl-flags", peer],
                        ["set", peer, "enabled", "true"],
                        ["set", "harness", "implementer", peer])
            for command in commands:
                with self.subTest(command=command):
                    rc, output, diagnostic = self.cli(command)
                    self.assertEqual(2, rc)
                    self.assertEqual("", output)
                    self.assertIn("retir", diagnostic.lower())

    def test_retired_setup_queries_cannot_use_ready_cached_entries(self):
        directory = self.root / ".claude"
        directory.mkdir()
        (directory / "co-agent-panel.local.json").write_text(json.dumps({
            "peers": {peer: {"status": "READY", "access": "raw", "raw_cli": True}
                      for peer in RETIRED},
        }))
        for peer in RETIRED:
            for command in ("status", "access", "gate-eligible", "probe"):
                with self.subTest(peer=peer, command=command):
                    with patch.object(panel, "detect_cli", return_value="/fake/" + peer):
                        rc, output, diagnostic = self.cli([command, peer], module=panel)
                    self.assertEqual(2, rc)
                    self.assertNotEqual("READY", output)
                    self.assertIn("retir", diagnostic.lower())
            self.assertFalse(panel.gate_eligible(str(self.root), peer, host="claude"))
        self.assertEqual([], self.launches)

    def test_report_does_not_discover_or_probe_retired_clis(self):
        self.configure({"panel": {"agy": {"enabled": True}, "antigravity": {},
                                  "gemini": {"enabled": True}}})
        with contextlib.redirect_stderr(io.StringIO()):
            probes = self.ready("codex", {"kiro-cli": "READY", "claude": "READY",
                                          "agy": "READY"})
        self.assertEqual(["kiro-cli", "claude"], probes)
        summary = panel._read_summary(str(self.root))
        self.assertEqual({"kiro-cli", "claude"}, set(summary["peers"]))

    def test_hook_panels_and_config_failure_fallback_do_not_reintroduce_retired_peers(self):
        self.configure({"panel": {peer: {"enabled": True} for peer in RETIRED}})
        for host, expected in (("claude", {"kiro-cli", "codex"}),
                               ("codex", {"kiro-cli", "claude"})):
            for unavailable in (False, True):
                with self.subTest(host=host, unavailable=unavailable):
                    with contextlib.ExitStack() as stack:
                        stack.enter_context(patch.dict(os.environ, {"CO_AGENT_HOST": host}))
                        stack.enter_context(patch.object(hooks.shutil, "which",
                                                         side_effect=lambda peer: "/fake/" + peer))
                        stack.enter_context(contextlib.redirect_stderr(io.StringIO()))
                        if unavailable:
                            stack.enter_context(patch.object(hooks, "cac", None))
                        selected, _ = hooks._panel(str(self.root))
                    self.assertEqual(expected, set(selected))

    def test_direct_retired_probe_and_gate_dispatch_never_launch(self):
        for peer in RETIRED:
            with self.subTest(peer=peer):
                with patch.object(panel, "detect_cli", return_value="/fake/" + peer):
                    status, reason = panel.probe(peer, timeout=1)
                self.assertEqual("ERROR", status)
                self.assertIn("retir", reason.lower())
                output = {}
                with contextlib.redirect_stderr(io.StringIO()):
                    hooks._review_one(peer, "fixture diff", None, "", str(self.root), 1, output)
                    hooks._review_one_push(peer, "security", "fixture diff", None, "",
                                           str(self.root), 1, output)
                self.assertTrue(all(value.startswith("__ERROR__") for value in output.values()))
        self.assertEqual([], self.launches)

    def test_codex_host_does_not_resolve_an_external_writer_implicitly(self):
        rc, output, diagnostic = self.cli(["implementer", "--host", "codex"])
        self.assertEqual((3, ""), (rc, output))
        self.assertIn("--allow-host-implementation", diagnostic)
        for peer in ("claude", "kiro-cli", "codex", "host", *RETIRED):
            self.assertEqual(2, self.cli(["impl-flags", peer, "--host", "codex"])[0])

    def test_disabled_writer_cannot_get_write_flags_directly(self):
        self.configure({"panel": {"codex": {"enabled": False}}})
        rc, output, diagnostic = self.cli(["impl-flags", "codex", "--host", "claude"])
        self.assertEqual((2, ""), (rc, output))
        self.assertIn("disabled", diagnostic)

    def test_obsolete_third_peer_environment_does_not_select_a_peer(self):
        for peer in RETIRED:
            with patch.dict(os.environ, {"CO_AGENT_THIRD_AI": peer}):
                rc, output, diagnostic = self.cli(["panel"])
            self.assertEqual((0, "kiro-cli codex"), (rc, output))
            self.assertIn("CO_AGENT_THIRD_AI", diagnostic)
            self.assertIn("retir", diagnostic.lower())











    def test_explicit_retired_writer_requires_migration_not_silent_fallback(self):
        for peer in RETIRED:
            self.configure({"harness": {"implementer": peer}})
            with contextlib.redirect_stderr(io.StringIO()):
                self.ready("codex", {"claude": "READY"})
            rc, output, diagnostic = self.cli(["implementation-plan", "--host", "codex",
                                               "--allow-host-implementation"])
            self.assertEqual((2, ""), (rc, output))
            self.assertIn("retir", diagnostic.lower())
            self.assertIn("implementer", diagnostic)

    def test_generic_model_tokens_and_write_flag_validation_are_preserved(self):
        model = "Gemini 3.1 Pro (High)"
        self.assertEqual(0, self.cli(["set", "kiro-cli", "model", model])[0])
        self.assertEqual((0, "--model\n" + model), self.cli(["flags", "kiro-cli"])[:2])
        self.assertEqual(2, self.cli(["set", "codex", "model", "bad;command"])[0])
        self.configure({"harness": {"implementer": "codex",
                                   "implementer_models": {"codex": "bad\n--flag"}}})
        self.assertEqual(2, self.cli(["impl-flags", "codex"])[0])

    def test_google_credentials_are_filtered_even_after_peer_retirement(self):
        with patch.dict(os.environ, {
            "GEMINI_API_KEY": "fixture", "GOOGLE_API_KEY": "fixture",
            "GOOGLE_APPLICATION_CREDENTIALS": "/fixture",
            "CLOUDSDK_CONFIG": "/fixture", "gcloud_project": "fixture",
            "OPENAI_API_KEY": "codex-fixture", "GH_TOKEN": "fixture",
        }):
            filtered = environment.sanitized_env("codex")
        self.assertEqual("codex-fixture", filtered["OPENAI_API_KEY"])
        for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_APPLICATION_CREDENTIALS",
                     "CLOUDSDK_CONFIG", "gcloud_project", "GH_TOKEN"):
            self.assertNotIn(name, filtered)


if __name__ == "__main__":
    unittest.main()
