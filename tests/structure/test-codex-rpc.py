"""Regression for a notification and response arriving in one pipe write."""
import importlib.util
from pathlib import Path
import selectors
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("runtime_smoke", ROOT / "scripts/test-codex-runtime.py")
RUNTIME = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNTIME)


class RpcTests(unittest.TestCase):
    def test_fixture_flattens_namespace_tools(self):
        declared = [{"type": "namespace", "name": "functions", "tools": [
            {"type": "custom", "name": "apply_patch"}, {"type": "function", "name": "exec_command"}]}]
        tools = RUNTIME.response_tools({"tools": declared})
        self.assertEqual("custom", RUNTIME.response_tool(tools, "apply_patch")["type"])

    def test_fixture_reuses_only_an_explicit_known_response_catalog(self):
        tools = [{"type": "custom", "name": "apply_patch"}]
        self.assertEqual(tools, RUNTIME.response_tools({"previous_response_id": "known"}, tools))
        for request, previous in (({}, tools), ({"previous_response_id": "unknown"}, None)):
            with self.assertRaisesRegex(RuntimeError, "no tools declaration"):
                RUNTIME.response_tools(request, previous)
        self.assertEqual([], RUNTIME.response_tools({"tools": [], "previous_response_id": "known"}, tools))

    def test_fixture_reports_missing_or_ambiguous_patch_support(self):
        with self.assertRaisesRegex(RuntimeError, "found 0.*exec_command"):
            RUNTIME.response_tool([{"type": "function", "name": "exec_command"}], "apply_patch")
        with self.assertRaisesRegex(RuntimeError, "found 2"):
            RUNTIME.response_tool([{"name": "apply_patch"}, {"name": "apply_patch"}], "apply_patch")
        for payload in ({"tools": {}}, {"tools": ["invalid"]},
                        {"tools": [{"type": "namespace", "tools": {}}]}):
            with self.assertRaises(RuntimeError):
                RUNTIME.response_tools(payload)

    def test_coalesced_notification_does_not_hide_the_response(self):
        code = (
            "import os,sys\n"
            "sys.stdin.readline()\n"
            "os.write(1,b'{\"method\":\"changed\"}\\n{\"id\":1,\"result\":{\"ok\":true}}\\n')\n"
            "sys.stdin.readline()\n"
        )
        process = subprocess.Popen([sys.executable, "-u", "-c", code],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True)
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)
        try:
            try:
                result = RUNTIME.request(process, selector, 1, "probe", {})
            except RuntimeError as exc:
                self.fail(f"A valid response was already available: {exc}")
            self.assertEqual({"ok": True}, result)
        finally:
            selector.close()
            process.terminate()
            process.wait(timeout=5)
            process.stdin.close()
            process.stdout.close()
            process.stderr.close()


if __name__ == "__main__":
    unittest.main()
