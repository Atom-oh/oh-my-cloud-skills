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
