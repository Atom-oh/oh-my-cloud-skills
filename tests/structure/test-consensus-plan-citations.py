"""Offline regressions for plan/diff citation boundaries."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "plugins/co-agent/skills/co-agent/scripts/check_citations.py"
DIFF = """diff --git a/service.py b/service.py
--- a/service.py
+++ b/service.py
@@ -1 +1,2 @@
 keep()
+delete_all()
"""


class CitationTests(unittest.TestCase):
    def run_check(self, artifact, findings):
        with tempfile.TemporaryDirectory(prefix="consensus-citations-") as directory:
            root = Path(directory)
            diff = root / "artifact"
            data = root / "findings.json"
            diff.write_text(artifact, encoding="utf-8")
            serialized = json.dumps(findings)
            data.write_text(serialized, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-B", str(SCRIPT), str(diff), str(data), "--json"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(data.read_text(encoding="utf-8"), serialized)
            return result

    def test_plan_major_and_fabricated_quote_remain_for_chair(self):
        plan = "# Deployment Plan\n\n## Task 1\nDisable authentication before deployment.\n"
        findings = [
            {"severity": "MAJOR", "file": "plan.md", "line": 4,
             "snippet": "Disable authentication before deployment.", "issue": "unsafe step"},
            {"severity": "MAJOR", "file": "plan.md", "line": 4,
             "snippet": "Publish administrator credentials.", "issue": "fabricated quotation"},
        ]
        # The chair can confirm/refute these against the actual plan. The diff
        # helper must never replace that check with all-unsupported classification.
        self.assertIn(findings[0]["snippet"], plan)
        self.assertNotIn(findings[1]["snippet"], plan)
        result = self.run_check(plan, findings)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("check plan citations manually", result.stderr)
        self.assertIn("findings still require chair review", result.stderr)

    def test_normal_diff_citations(self):
        findings = [
            {"severity": "MAJOR", "file": "service.py", "line": 2, "snippet": "delete_all()"},
            {"file": "service.py", "line": 2, "snippet": "fabricated()"},
            {"file": "missing.py", "line": 1},
            {"file": "service.py", "line": "invalid"},
        ]
        result = self.run_check(DIFF, findings)
        self.assertEqual(result.returncode, 0, result.stderr)
        classified = json.loads(result.stdout)
        self.assertEqual([f["citation"] for f in classified],
                         ["supported", "needs-review", "unsupported", "needs-review"])
        self.assertEqual(classified[0]["severity"], "MAJOR")

    def test_deletion_only_diff_preserves_old_path(self):
        artifact = """diff --git a/service.py b/service.py
deleted file mode 100644
--- a/service.py
+++ /dev/null
@@ -1,2 +0,0 @@
-keep()
-authenticate()
"""
        result = self.run_check(artifact, [{"severity": "MAJOR", "file": "service.py", "line": 2}])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)[0]["citation"], "needs-review")

    def test_empty_diff_with_no_findings_is_valid(self):
        result = self.run_check("", [])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [])

    def test_mode_only_rename_and_binary_diffs_are_valid(self):
        artifacts = [
            "diff --git a/service.py b/service.py\nold mode 100644\nnew mode 100755\n",
            "diff --git a/old.py b/new.py\nsimilarity index 100%\nrename from old.py\nrename to new.py\n",
            "diff --git a/image.png b/image.png\nindex 123..456 100644\n"
            "Binary files a/image.png and b/image.png differ\n",
        ]
        for artifact in artifacts:
            with self.subTest(artifact=artifact):
                result = self.run_check(artifact, [])
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_malformed_artifacts_cannot_produce_classification(self):
        artifacts = [
            "fatal: ambiguous argument HEAD\n",
            "--- a/service.py\n+++ b/service.py\n",
            "diff --git a/service.py b/service.py\n",
            DIFF.replace("@@ -1 +1,2 @@", "@@ broken @@"),
            DIFF.replace("@@ -1 +1,2 @@", "@@ -1,2 +1,2 @@"),
            DIFF + "unexpected prose\n",
        ]
        for artifact in artifacts:
            with self.subTest(artifact=artifact):
                result = self.run_check(artifact, [{"severity": "MAJOR", "file": "service.py"}])
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertIn("findings still require chair review", result.stderr)

    def test_malformed_findings_are_rejected(self):
        for findings in ({}, [None], ["claim"], [{"file": 7}], [{"snippet": []}]):
            with self.subTest(findings=findings):
                result = self.run_check(DIFF, findings)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")

    def test_ambiguous_basename_is_needs_review(self):
        artifact = DIFF.replace("service.py", "one/service.py")
        artifact += DIFF.replace("service.py", "two/service.py")
        result = self.run_check(artifact, [{"file": "service.py", "line": 2}])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)[0]["citation"], "needs-review")

    def test_git_quoted_unicode_and_unquoted_spaces(self):
        cases = [
            (DIFF.replace("service.py", "service name.py"), "service name.py"),
            (DIFF.replace("a/service.py", '"a/\\354\\225\\204.py"')
             .replace("b/service.py", '"b/\\354\\225\\204.py"'), "아.py"),
        ]
        for artifact, filename in cases:
            with self.subTest(filename=filename):
                result = self.run_check(artifact, [{"file": filename, "line": 2}])
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)[0]["citation"], "supported")


if __name__ == "__main__":
    unittest.main()
