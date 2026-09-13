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

BACKEND_AUTH = {
    "BEDROCK": """AWS_REGION AWS_DEFAULT_REGION AWS_PROFILE AWS_CONFIG_FILE
        AWS_SHARED_CREDENTIALS_FILE AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
        AWS_ROLE_ARN AWS_ROLE_SESSION_NAME AWS_WEB_IDENTITY_TOKEN_FILE
        AWS_CONTAINER_CREDENTIALS_RELATIVE_URI AWS_CONTAINER_CREDENTIALS_FULL_URI
        AWS_CONTAINER_AUTHORIZATION_TOKEN AWS_CONTAINER_AUTHORIZATION_TOKEN_FILE
        AWS_BEARER_TOKEN_BEDROCK""".split(),
    "VERTEX": """GOOGLE_APPLICATION_CREDENTIALS google_application_credentials
        GOOGLE_CLOUD_PROJECT GCLOUD_PROJECT GOOGLE_CLOUD_QUOTA_PROJECT CLOUDSDK_CONFIG""".split(),
    "FOUNDRY": """ANTHROPIC_FOUNDRY_API_KEY ANTHROPIC_FOUNDRY_AUTH_TOKEN
        AZURE_CLIENT_ID AZURE_TENANT_ID AZURE_CLIENT_SECRET AZURE_AUTHORITY_HOST
        AZURE_CLIENT_CERTIFICATE_PATH AZURE_CLIENT_CERTIFICATE_PASSWORD
        AZURE_FEDERATED_TOKEN_FILE AZURE_TOKEN_CREDENTIALS
        IDENTITY_ENDPOINT IDENTITY_HEADER MSI_ENDPOINT MSI_SECRET""".split(),
}


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
        real_popen = self.real_popen = subprocess.Popen

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
            ({}, [], "kiro-cli codex"),
            ({"CODEX_THREAD_ID": "thread"}, [], "kiro-cli claude"),
            ({"CODEX_SESSION_ID": "session"}, [], "kiro-cli claude"),
            ({"PLUGIN_ROOT": "/installed/plugin", "PLUGIN_DATA": "/data"}, [],
             "kiro-cli claude"),
            ({"CODEX_THREAD_ID": "thread", "CLAUDECODE": "1"}, [], "kiro-cli codex"),
            ({"CODEX_THREAD_ID": "thread", "CO_AGENT_HOST": "claude"}, [],
             "kiro-cli codex"),
            ({"CO_AGENT_HOST": "claude"}, ["--host", "codex"], "kiro-cli claude"),
        ]
        for markers, flags, expected in cases:
            with self.subTest(markers=markers, flags=flags), patch.dict(os.environ, markers):
                self.assertEqual((0, expected), self.config_cli(["panel", *flags]))
        with patch.dict(os.environ, {"CODEX_THREAD_ID": "thread"}):
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual((3, ""), self.config_cli(["implementer"]))
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
        self.configure({"panel": {"claude": {"enabled": False}}})
        with patch.dict(os.environ, {"CODEX_THREAD_ID": "thread"}):
            summary, probes = self.report()
        self.assertEqual(["kiro-cli"], probes)
        self.assertEqual({"kiro-cli"}, set(summary["peers"]))

    def test_setup_explicit_host_and_freshness_across_hosts(self):
        summary, probes = self.report(host="codex")
        self.assertEqual(["kiro-cli", "claude"], probes)
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
        self.assertEqual(["kiro-cli", "claude"], peers)

    def test_gate_path_fallback_still_uses_the_detected_host(self):
        with patch.dict(os.environ, {"CODEX_THREAD_ID": "thread"}):
            with patch.object(hooks, "cac", None):
                with patch.object(hooks.shutil, "which", side_effect=lambda peer: "/fake/" + peer):
                    peers, _ = hooks._panel(str(self.root))
        self.assertEqual({"kiro-cli", "claude"}, set(peers))

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
                    self.assertEqual("", argv[argv.index("--setting-sources") + 1])
                    self.assertIn("--strict-mcp-config", argv)
                    self.assertEqual('{"mcpServers":{}}', argv[argv.index("--mcp-config") + 1])
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

    def test_only_selected_claude_backend_receives_its_auth(self):
        cloud = {key: "fixture" for keys in BACKEND_AUTH.values() for key in keys}
        unrelated = dict(GH_TOKEN="fixture", KIRO_API_KEY="fixture", OPENAI_API_KEY="fixture",
                         AWS_UNRELATED_SECRET="fixture", GOOGLE_API_KEY="fixture")
        for backend, required in BACKEND_AUTH.items():
            for enabled in ("1", "true", " YES ", "on", "0", "false", ""):
                with self.subTest(backend=backend, enabled=enabled), patch.dict(os.environ, {
                    **cloud, **unrelated, "CLAUDE_CODE_USE_" + backend: enabled,
                }):
                    result = hooks._sanitized_env("claude")
                    selected = set(required) if enabled in ("1", "true", " YES ", "on") else set()
                    self.assertEqual(selected, set(cloud) & result.keys())
                    self.assertFalse(unrelated.keys() & result.keys())
                    self.assertIn("PATH", result)
                    for peer in ("codex", "agy", "kiro-cli"):
                        previous_project_config = set()
                        self.assertEqual(previous_project_config,
                                         set(cloud) & hooks._sanitized_env(peer).keys())

    def test_probe_and_both_gates_use_identical_env_with_stub_cli(self):
        self.assertIs(panel._sanitized_env, hooks._sanitized_env)
        stub = self.root / "claude-stub.py"
        stub.write_text(
            "import json,os,sys\n"
            "with open(os.environ['FIXTURE_ENV_LOG'],'a') as f:\n"
            "    f.write(json.dumps(dict(os.environ),sort_keys=True)+'\\n')\n"
            "data=sys.stdin.read()\n"
            "print(data.strip() if data.startswith('COAGENT_PROBE_') else 'BLOCK: fixture')\n")
        def launch(argv, *args, **kwargs):
            self.assertEqual([sys.executable, str(stub)], argv[:2])
            self.assertEqual("", argv[argv.index("--setting-sources") + 1])
            self.assertIn("--strict-mcp-config", argv)
            self.assertEqual('{"mcpServers":{}}', argv[argv.index("--mcp-config") + 1])
            self.assertEqual("Read,Grep,Glob", argv[argv.index("--tools") + 1])
            return self.real_popen(argv, *args, **kwargs)
        for backend, required in BACKEND_AUTH.items():
            log = self.root / (backend + ".jsonl")
            with contextlib.ExitStack() as stack:
                stack.enter_context(patch.dict(os.environ, {
                    **{key: "fixture" for key in required}, "GH_TOKEN": "unrelated",
                    "CLAUDE_CODE_USE_" + backend: "1", "FIXTURE_ENV_LOG": str(log)}))
                for adapters in (panel.ADAPTERS, hooks._REVIEW):
                    spec = adapters["claude"]
                    stack.enter_context(patch.dict(adapters, {
                        "claude": {**spec, "argv": [sys.executable, str(stub), *spec["argv"][1:]]}}))
                stack.enter_context(patch.object(panel, "detect_cli", return_value=str(stub)))
                stack.enter_context(patch.object(subprocess, "Popen", side_effect=launch))
                self.assertEqual("READY", panel.probe("claude", timeout=5, gate=True)[0])
                result = {}
                hooks._review_one("claude", "fixture", None, "", str(self.root), 5, result)
                hooks._review_one_push("claude", "security", "fixture", None, "", str(self.root), 5, result)
                self.assertTrue(all(text.startswith("BLOCK:") for text in result.values()))
            environments = [json.loads(line) for line in log.read_text().splitlines()]
            self.assertEqual(3, len(environments))
            self.assertTrue(all(env == environments[0] for env in environments))
            self.assertTrue(set(required) <= environments[0].keys())
            self.assertNotIn("GH_TOKEN", environments[0])

    def test_related_claude_backends_and_disabled_cloud_flags(self):
        cases = [
            ("MANTLE", {"AWS_PROFILE", "AWS_BEARER_TOKEN_BEDROCK"}),
            ("ANTHROPIC_AWS", {"AWS_PROFILE", "ANTHROPIC_AWS_API_KEY"}),
            ("ANTHROPIC_GOOGLE_CLOUD", {"GOOGLE_APPLICATION_CREDENTIALS"}),
        ]
        credentials = {key: "fixture" for _, keys in cases for key in keys}
        for backend, required in cases:
            with self.subTest(backend=backend), patch.dict(os.environ, {
                **credentials, "CLAUDE_CODE_USE_" + backend: "1",
                "CLAUDE_CODE_USE_FOUNDRY": "false",
            }):
                result = hooks._sanitized_env("claude")
                self.assertEqual(required, credentials.keys() & result.keys())

    def test_conflicting_cloud_families_do_not_launch_a_peer(self):
        with patch.dict(os.environ, {"CLAUDE_CODE_USE_BEDROCK": "1", "CLAUDE_CODE_USE_VERTEX": "1"}):
            with patch.object(panel, "detect_cli", return_value="/fake/claude"):
                self.assertEqual("ERROR", panel.probe("claude", gate=True)[0])
            result = {}
            with contextlib.redirect_stderr(io.StringIO()):
                hooks._review_one("claude", "fixture", None, "", str(self.root), 5, result)
            self.assertTrue(result["claude"].startswith("__ERROR__"))

    def test_general_probe_keeps_custom_provider_auth_separate_from_gate_probe(self):
        stub = self.root / "codex-provider-stub.py"
        stub.write_text(
            "import os,sys\n"
            "text=sys.stdin.read()\n"
            "if 'AWS_BEARER_TOKEN_BEDROCK' not in os.environ:\n"
            "    print('Unauthorized: missing fixture credential',file=sys.stderr);sys.exit(1)\n"
            "print(text.strip())\n")
        def launch(argv, *args, **kwargs):
            self.assertEqual([sys.executable, str(stub)], argv[:2])
            return self.real_popen(argv, *args, **kwargs)
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ, {
                "CO_AGENT_HOST": "claude", "AWS_BEARER_TOKEN_BEDROCK": "fixture",
            }))
            spec = panel.ADAPTERS["codex"]
            stack.enter_context(patch.dict(panel.ADAPTERS, {
                "codex": {**spec, "argv": [sys.executable, str(stub), *spec["argv"][1:]]}}))
            stack.enter_context(patch.object(panel, "detect_cli", return_value=str(stub)))
            stack.enter_context(patch.object(panel, "detect_plugin", return_value=False))
            stack.enter_context(patch.object(subprocess, "Popen", side_effect=launch))
            entry = panel._peer_entry("codex", str(self.root))
            self.assertEqual("READY", entry["status"])
            self.assertNotEqual("READY", panel.probe("codex", gate=True)[0])
            panel._atomic_write_json(panel._summary_path(str(self.root)), {
                "peers": {"codex": entry}, "host": "claude",
            })
            self.assertTrue(panel.gate_eligible(str(self.root), "codex"))


if __name__ == "__main__":
    unittest.main()
