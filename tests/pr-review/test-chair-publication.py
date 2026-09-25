"""Verify content-free publication diagnostics without relaxing the review gate."""
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
PUBLISHER_PATH = ROOT / "scripts/pr-review/publish_chair.py"
PUBLISHER = runpy.run_path(str(PUBLISHER_PATH))
GATE = runpy.run_path(str(ROOT / "plugins/co-agent/skills/pr-autofix/scripts/review_gate.py"))
FORMAT = runpy.run_path(str(ROOT / "plugins/co-agent/skills/pr-autofix/scripts/review_format.py"))


def review(summary="Synthetic review.", major="- Confirmed synthetic defect.", verdict="FAIL"):
    return (
        f"## Summary\n{summary}\n\n## Issues\n### CRITICAL\nNone.\n"
        f"### MAJOR\n{major}\n### MINOR\nNone.\n\n## Verdict\nVERDICT: {verdict}\n"
    )


class PublicationTests(unittest.TestCase):
    def publish(self, text):
        return PUBLISHER["publish_with_diagnostics"](text)

    def assert_blocked(self, body):
        self.assertEqual("BLOCKED", GATE["markdown_review"](body)["status"])
        self.assertNotIn("### MAJOR\nNone.", body)
        self.assertNotIn("### CRITICAL\nNone.", body)

    def test_inline_failure_reports_rule_and_source_counts_without_details(self):
        source = review("Run `printf fixture-private-value`.")
        body, diagnostics = self.publish(source)
        self.assert_blocked(body)
        self.assertEqual("source_format_rejected", diagnostics["reason"])
        self.assertEqual("source_validation", diagnostics["stage"])
        self.assertEqual("active_major", diagnostics["source_decision"])
        self.assertEqual({"CRITICAL": 0, "MAJOR": 1, "MINOR": 0, "INFO": None},
                         diagnostics["issue_item_counts"])
        self.assertEqual({"code": "unsupported_review_format",
                          "rule": "invalid_inline_reference", "line": 2},
                         diagnostics["format_diagnostic"])
        self.assertNotIn("fixture-private-value", body + json.dumps(diagnostics))
        self.assertNotIn("Confirmed synthetic defect", body)

    def test_oversized_source_has_distinct_reason_and_remains_blocked(self):
        source = review("é" * 25001)
        body, diagnostics = self.publish(source)
        self.assert_blocked(body)
        self.assertEqual("input_too_large", diagnostics["reason"])
        self.assertEqual(len(source.encode()), diagnostics["input_bytes"])
        self.assertEqual(50000, diagnostics["byte_limit"])
        self.assertIsNone(diagnostics["format_diagnostic"])
        self.assertLess(len(body.encode()), 50000)

    def test_explicit_fail_is_not_invented_as_a_major_finding(self):
        body, diagnostics = self.publish(review("Invalid `--trust-tools=`.", major="None."))
        self.assert_blocked(body)
        self.assertEqual("explicit_fail", diagnostics["source_decision"])
        self.assertEqual(0, diagnostics["issue_item_counts"]["MAJOR"])

    def test_ambiguous_and_missing_sections_have_unknown_counts(self):
        sources = [
            "Invalid `--trust-tools=`.\nVERDICT: FAIL\n",
            review("Invalid `--trust-tools=`.").replace(
                "### MAJOR", "### MAJOR\n- First item.\n### MAJOR"),
            review("Invalid `--trust-tools=`.") + "\n```text\nUnclosed",
        ]
        for source in sources:
            with self.subTest(source=source):
                _, diagnostics = self.publish(source)
                self.assertTrue(all(value is None for value in diagnostics["issue_item_counts"].values()))

    def test_quoted_and_dismissed_findings_are_not_counted(self):
        quoted = "```text\n## Issues\n### CRITICAL\n- Not active.\n```"
        source = review(quoted, major="None.", verdict="PASS")
        source = source.replace("## Verdict", "## Dismissed findings\n- MAJOR example.\n## Verdict")
        body, diagnostics = self.publish(source)
        self.assertEqual(source, body)
        self.assertEqual(0, diagnostics["issue_item_counts"]["CRITICAL"])
        self.assertEqual(0, diagnostics["issue_item_counts"]["MAJOR"])

    def test_incomplete_and_nonblocking_invalid_reports_stay_errors(self):
        for source in (review("Invalid `--trust-tools=`.", major="None.", verdict="PASS"),
                       "## Review error\nCould not complete.\nVERDICT: FAIL\n"):
            with self.subTest(source=source):
                body, diagnostics = self.publish(source)
                self.assertEqual("ERROR", GATE["markdown_review"](body)["status"])
                self.assertEqual("ERROR", diagnostics["published_status"])

    def test_scrubber_failure_is_reported_without_stderr(self):
        failure = subprocess.CompletedProcess([], 2, "", "fixture-private-value")
        with mock.patch.object(PUBLISHER["subprocess"], "run", return_value=failure):
            body, diagnostics = self.publish(review())
        self.assert_blocked(body)
        self.assertEqual("scrubber_failed", diagnostics["reason"])
        self.assertNotIn("fixture-private-value", body + json.dumps(diagnostics))

    def test_scrub_expansion_and_post_scrub_format_have_distinct_diagnostics(self):
        cases = (
            ("x" * 50001, "scrubbed_output_too_large"),
            (review("Invalid `--trust-tools=`."), "scrubbed_format_rejected"),
        )
        for output, reason in cases:
            with self.subTest(reason=reason), mock.patch.object(
                PUBLISHER["subprocess"], "run", return_value=subprocess.CompletedProcess([], 0, output, "")
            ):
                body, diagnostics = self.publish(review())
            self.assert_blocked(body)
            self.assertEqual(reason, diagnostics["reason"])
            self.assertEqual(len(output.encode()), diagnostics["scrubbed_bytes"])

    def test_scrubbing_cannot_clear_a_source_blocker(self):
        filtered = review(major="None.", verdict="PASS")
        with mock.patch.object(PUBLISHER["subprocess"], "run",
                               return_value=subprocess.CompletedProcess([], 0, filtered, "")):
            body, diagnostics = self.publish(review(verdict="PASS"))
        self.assert_blocked(body)
        self.assertEqual("blocking_evidence_removed", diagnostics["reason"])
        self.assertEqual(1, diagnostics["issue_item_counts"]["MAJOR"])

    def test_publisher_exception_does_not_disclose_exception_text(self):
        with mock.patch.object(PUBLISHER["subprocess"], "run", side_effect=OSError("fixture-private-value")):
            body, diagnostics = self.publish(review())
        self.assert_blocked(body)
        self.assertEqual("publisher_error", diagnostics["reason"])
        self.assertNotIn("fixture-private-value", body + json.dumps(diagnostics))

    def test_missing_formatter_cannot_erase_a_known_source_blocker(self):
        original = PUBLISHER["runpy"].run_path

        def load(path):
            if Path(path).name == "review_format.py":
                raise FileNotFoundError("fixture-private-value")
            return original(path)

        with mock.patch.object(PUBLISHER["runpy"], "run_path", side_effect=load):
            body, diagnostics = self.publish(review())
        self.assert_blocked(body)
        self.assertEqual("publisher_error", diagnostics["reason"])
        self.assertEqual("source_validation", diagnostics["stage"])
        self.assertNotIn("fixture-private-value", body + json.dumps(diagnostics))

    def test_synthesis_logs_diagnostics_without_replacing_primary_blocker(self):
        with tempfile.TemporaryDirectory(prefix="chair publication ") as temporary:
            root = Path(temporary)
            work, binary = root / "work", root / "bin"
            work.mkdir()
            binary.mkdir()
            (work / "slot").mkdir()
            (work / "base-context.md").write_text("Trusted synthetic context.")
            (work / "diff.txt").write_text("Synthetic diff.")
            labels = "codex/FULL\nkiro-opus/FULL\nkiro-gpt/FULL\n"
            for name in ("responded.txt", "expected.txt"):
                (work / name).write_text(labels)
            for cell in labels.splitlines():
                (work / "slot" / (cell.replace("/", "-") + ".md")).write_text("Complete synthetic review.")
            source = root / "source.md"
            source.write_text(review("Run `printf fixture-private-value`."))
            fallback = root / "fallback-called"
            fake = binary / "claude"
            fake.write_text(
                "#!/usr/bin/env python3\n"
                "import os\nfrom pathlib import Path\n"
                "if os.environ['ANTHROPIC_MODEL'] != 'test-primary':\n"
                "    Path(os.environ['TEST_CHAIR_FALLBACK']).touch()\n"
                "print(Path(os.environ['TEST_CHAIR_SOURCE']).read_text())\n"
            )
            fake.chmod(0o755)
            environment = {
                **os.environ, "PATH": str(binary) + os.pathsep + os.environ["PATH"],
                "ANTHROPIC_MODEL": "test-primary", "CHAIR_FALLBACK_MODEL": "test-fallback",
                "TEST_CHAIR_FALLBACK": str(fallback), "TEST_CHAIR_SOURCE": str(source),
                "GITHUB_ENV": str(work / "environment"),
            }
            result = subprocess.run(
                ["bash", str(ROOT / "scripts/pr-review/synthesize.sh"), str(work / "diff.txt"),
                 str(work), "999", "Synthetic review", str(work / "review.md")],
                cwd=ROOT, env=environment, capture_output=True, text=True, check=True,
            )
            body = (work / "review.md").read_text()
            self.assert_blocked(body)
            self.assertFalse(fallback.exists())
            self.assertIn("chair-publication:", result.stderr)
            self.assertIn("source_format_rejected", result.stderr)
            self.assertIn("chair_error=0", (work / "environment").read_text())
            self.assertNotIn("fixture-private-value", result.stdout + result.stderr + body)

    def test_cli_emits_safe_json_diagnostics_on_stderr(self):
        source = review("Run `printf fixture-private-value`.")
        result = subprocess.run([sys.executable, str(PUBLISHER_PATH)], input=source,
                                text=True, capture_output=True, cwd=ROOT, check=True)
        self.assert_blocked(result.stdout)
        prefix = "chair-publication: "
        self.assertTrue(result.stderr.startswith(prefix))
        diagnostics = json.loads(result.stderr[len(prefix):])
        self.assertEqual("source_format_rejected", diagnostics["reason"])
        self.assertNotIn("fixture-private-value", result.stdout + result.stderr)

    def test_invalid_utf8_remains_error_with_content_free_diagnostic(self):
        result = subprocess.run([sys.executable, str(PUBLISHER_PATH)],
                                input=b"fixture-private-value\xff", capture_output=True, cwd=ROOT, check=True)
        self.assertEqual("ERROR", GATE["markdown_review"](result.stdout.decode())["status"])
        diagnostics = json.loads(result.stderr.decode().split(": ", 1)[1])
        self.assertEqual("invalid_utf8", diagnostics["reason"])
        self.assertNotIn(b"fixture-private-value", result.stdout + result.stderr)

    def test_format_diagnostics_preserve_the_existing_failure_code(self):
        cases = (
            ("Run `printf example`.", "invalid_inline_reference", 1),
            ("```python args\nvalue\n```", "invalid_fence_info", 1),
            ("- ```text\nvalue\n```", "nested_or_indented_fence", 1),
            ("Text `unfinished", "unpaired_inline_delimiter", 1),
            ("Text ``item`", "mismatched_inline_delimiter", 1),
            ("Safe.\n```text\nunfinished", "unclosed_fence", 2),
            ("Set `api_key` = fixture.", "unfenced_sensitive_assignment", 1),
            ("api_key=fixture", "unfenced_sensitive_assignment", None),
        )
        for text, rule, line in cases:
            with self.subTest(rule=rule):
                self.assertEqual({"code": "unsupported_review_format", "rule": rule, "line": line},
                                 FORMAT["format_diagnostic"](text))
                self.assertEqual("unsupported_review_format", FORMAT["format_violation"](text))
        self.assertIsNone(FORMAT["format_diagnostic"]("See `src/module.py`."))


if __name__ == "__main__":
    unittest.main()
