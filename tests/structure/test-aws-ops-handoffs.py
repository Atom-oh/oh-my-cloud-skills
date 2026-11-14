"""Offline regression checks for AWS Ops handoffs and documented diagnostics."""
import json
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]
OPS = ROOT / "plugins/aws-ops-plugin"


def read(path):
    return path.read_text(encoding="utf-8")


class HandoffTests(unittest.TestCase):
    def test_companion_preflight_is_shared_and_host_aware(self):
        guard = OPS / "references/companion-skills.md"
        self.assertTrue(guard.is_file(), "canonical companion preflight missing")
        text = read(guard)
        for phrase in ("active session", "not bundled", "stop", "trust", "cache"):
            self.assertIn(phrase, text)
        for plugin in ("aws-core", "aws-agents", "aws-agents-for-devsecops",
                       "aws-data-analytics", "databases-on-aws", "aws-serverless"):
            self.assertIn(plugin, text)
        for path in (OPS / "CLAUDE.md", ROOT / "scripts/codex/aws-ops-plugin.md",
                     OPS / "skills/ops-security-audit/SKILL.md",
                     OPS / "skills/ops-observability/references/aws-devops-agent.md"):
            with self.subTest(path=path):
                self.assertIn("companion-skills.md", read(path))

    def test_security_metadata_describes_handoff(self):
        frontmatter = read(OPS / "skills/ops-security-audit/SKILL.md").split("---")[1]
        self.assertIn("aws-agents-for-devsecops", frontmatter)
        self.assertNotIn("plus AWS Security Agent", frontmatter)
        self.assertNotIn('Principal:\\"*\\" or Resource:', frontmatter)

    def test_webhook_secret_uses_approved_store(self):
        text = read(OPS / "skills/ops-observability/references/aws-devops-agent.md")
        self.assertNotIn("secret in the Lambda env", text)
        self.assertIn("Secrets Manager", text)
        self.assertIn("SSM Parameter Store", text)
        self.assertIn("never print", text)

    def test_cni_cross_reference_resolves(self):
        path = OPS / "skills/ops-troubleshoot/references/common-errors.md"
        match = re.search(r"\[[^\]]*\]\(([^)]+vpc-cni-troubleshooting\.md)\)", read(path))
        self.assertIsNotNone(match, "CNI must use a relative Markdown link")
        self.assertTrue((path.parent / match[1]).is_file())

    def test_mixed_authentication_consults_both_sources(self):
        for path in (OPS / "agents/iam-agent.md",
                     OPS / "skills/ops-security-audit/references/iam-audit.md",
                     OPS / "skills/ops-troubleshoot/references/common-errors.md"):
            with self.subTest(path=path):
                text = read(path)
                self.assertIn("API_AND_CONFIG_MAP", text)
                self.assertIn("takes precedence", text)
                self.assertNotIn("aws-auth only in `CONFIG_MAP`", text)

    def test_capability_retention_is_configuration_not_delete_flag(self):
        text = read(OPS / "agents/eks-agent.md")
        self.assertNotIn("delete only with `--delete-propagation-policy RETAIN`", text)
        self.assertIn("configured `deletePropagationPolicy`", text)
        self.assertIn("create-capability", text)
        self.assertIn("explicit user approval", text)

    def test_running_not_ready_filters_use_pod_condition(self):
        # Evaluate the actual jq expressions copied from the procedures, not a
        # reimplementation of their intended logic. All data is local fixtures.
        def pod(name, phase, ready, container_ready):
            status = {"phase": phase,
                      "containerStatuses": [{"ready": container_ready}]}
            if ready is not None:
                status["conditions"] = [{"type": "Ready", "status": ready}]
            return {"metadata": {"namespace": "fixture", "name": name}, "status": status}

        fixtures = {"items": [
            pod("ready", "Running", "True", True),
            pod("container-unready", "Running", "False", False),
            pod("readiness-gated", "Running", "False", True),
            pod("missing-condition", "Running", None, True),
            pod("pending", "Pending", "False", False),
            pod("completed-job", "Succeeded", "False", False),
            pod("failed-job", "Failed", "False", False),
        ]}
        expected = {"fixture/container-unready", "fixture/readiness-gated",
                    "fixture/missing-condition"}
        for path in (OPS / "agents/eks-agent.md", OPS / "skills/ops-troubleshoot/SKILL.md"):
            with self.subTest(path=path):
                filters = re.findall(r"kubectl get pods -A -o json \| jq -r '([^']+)'", read(path))
                self.assertEqual(1, len(filters))
                result = subprocess.run(["jq", "-r", filters[0]], input=json.dumps(fixtures),
                                        text=True, capture_output=True, check=True)
                self.assertEqual(expected, set(result.stdout.splitlines()))


if __name__ == "__main__":
    unittest.main()
