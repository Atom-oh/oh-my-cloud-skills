#!/usr/bin/env python3
"""Execute the maintained IAM pod diagnostic against a local kubectl shim."""

import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
AGENT = ROOT / "plugins/aws-ops-plugin/agents/iam-agent.md"


class DiagnosticTests(unittest.TestCase):
    def setUp(self):
        source = AGENT.read_text()
        match = re.search(r"^kubectl exec <pod> -- sh -c '\n.*?^  done'",
                          source, flags=re.MULTILINE | re.DOTALL)
        self.assertIsNotNone(match, "maintained presence-only diagnostic is missing")
        self.command = match.group(0).replace("<pod>", "fixture-pod")
        self.temporary = tempfile.TemporaryDirectory(prefix="iam-diagnostic-test-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        shim = self.base / "kubectl"
        shim.write_text(
            f"#!{sys.executable}\n"
            "import os, subprocess, sys\n"
            "if sys.argv[1:5] != ['exec', 'fixture-pod', '--', 'sh']:\n"
            "    sys.exit('unexpected kubectl fixture arguments')\n"
            "if sys.argv[5] != '-c' or len(sys.argv) != 7:\n"
            "    sys.exit('diagnostic must filter inside the pod shell')\n"
            "env = {k: v for k, v in os.environ.items() if not k.startswith('AWS_')}\n"
            "env.update({\n"
            " 'AWS_ACCESS_KEY_ID': 'SYNTHETIC_ACCESS_KEY_VALUE',\n"
            " 'AWS_SECRET_ACCESS_KEY': 'SYNTHETIC_SECRET_KEY_VALUE',\n"
            " 'AWS_SESSION_TOKEN': 'SYNTHETIC_TOKEN_VALUE\\nAWS_FORGED_VALUE=secret',\n"
            " 'AWS_CONTAINER_AUTHORIZATION_TOKEN': 'SYNTHETIC_CONTAINER_SECRET',\n"
            " 'AWS_WEB_IDENTITY_TOKEN_FILE': '/synthetic/private/token',\n"
            " 'AWS_REGION': '',\n"
            " 'AWS_UNKNOWN_SECRET': 'SYNTHETIC_UNKNOWN_SECRET',\n"
            "})\n"
            "sys.exit(subprocess.run(sys.argv[4:], env=env).returncode)\n"
        )
        shim.chmod(0o700)

    def test_actual_documented_command_outputs_only_fixed_names_and_presence(self):
        result = subprocess.run(
            ["sh", "-c", self.command],
            env={**os.environ, "PATH": str(self.base) + os.pathsep + os.environ["PATH"]},
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, b"")
        combined = result.stdout + result.stderr
        for value in (b"SYNTHETIC_ACCESS_KEY_VALUE", b"SYNTHETIC_SECRET_KEY_VALUE",
                      b"SYNTHETIC_TOKEN_VALUE", b"AWS_FORGED_VALUE", b"secret",
                      b"SYNTHETIC_CONTAINER_SECRET", b"/synthetic/private/token",
                      b"SYNTHETIC_UNKNOWN_SECRET"):
            self.assertNotIn(value, combined)
        lines = result.stdout.decode().splitlines()
        self.assertGreaterEqual(len(lines), 10)
        for line in lines:
            self.assertRegex(line, r"^AWS_[A-Z_]+=(present|absent)$")
        for name in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN",
                     "AWS_CONTAINER_AUTHORIZATION_TOKEN", "AWS_WEB_IDENTITY_TOKEN_FILE",
                     "AWS_REGION"):
            self.assertIn(f"{name}=present", lines)
        self.assertIn("AWS_DEFAULT_REGION=absent", lines)
        self.assertIn("AWS_CONTAINER_CREDENTIALS_FULL_URI=absent", lines)
        self.assertNotIn("AWS_UNKNOWN_SECRET=present", lines)

    def test_identity_diagnostic_is_retained_and_raw_environment_dump_is_absent(self):
        source = AGENT.read_text()
        self.assertIn("kubectl exec -it <pod> -- aws sts get-caller-identity", source)
        self.assertNotRegex(source, r"kubectl exec[^\n]*-- env")


if __name__ == "__main__":
    unittest.main(verbosity=2)
