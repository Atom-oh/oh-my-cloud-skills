"""Execute the skill's state/observation snippets against local fixtures."""
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SKILL = Path(os.environ.get("PR_AUTOFIX_SKILL_UNDER_TEST",
                           str(ROOT / "plugins/co-agent/skills/pr-autofix")))


class ReviewStateTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="pr review state ")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.state = self.directory / "state.json"
        self.env = {
            **os.environ, "STATE": str(self.state), "STATE_DIR": str(self.directory),
            "PR_NUMBER": "17", "BASE_REF": "main", "GIT_ITER": "2",
            "CLAUDE_PLUGIN_ROOT": str(ROOT / "plugins/co-agent"),
            "CO_AGENT_USER_CONFIG": str(self.directory / "no-user-config"),
            "PR_AUTOFIX_WAIT_SECONDS": "60",
        }

    def snippet(self, needle):
        files = [SKILL / "SKILL.md", SKILL / "references/review-state.md",
                 SKILL / "references/review-evidence.md"]
        for path in files:
            if path.is_file():
                for block in re.findall(r"```bash\n(.*?)\n```", path.read_text(), re.S):
                    if needle in block:
                        return block
        self.fail(f"Missing executable state contract: {needle}")

    def run_snippet(self, needle):
        result = subprocess.run(["bash", "-euo", "pipefail", "-c", self.snippet(needle)],
                                env=self.env, cwd=self.directory,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def write(self, data):
        self.state.write_text(json.dumps(data))

    def read(self):
        return json.loads(self.state.read_text())

    def initialize(self):
        self.write({"pr": 17, "base_ref": "main", "iteration": 2, "max_iter": 5,
                    "phase": "poll", "run_dir": "preserved", "sig": "signature",
                    "ld_sha": "script-hash"})
        self.run_snippet("command -v jq")

    def record(self, verdict="PENDING"):
        observation = {
            "head": "a" * 40, "base_sha": "b" * 40, "diff_sha256": "c" * 64,
            "handles": [{"provider": "github-actions", "id": "run-123"}],
            "requirements": {"ai": {"required": True, "basis": "fixture project policy"}},
            "sources": {"ai": {"verdict": verdict, "head": "a" * 40,
                               "coverage_complete": False, "blocking_findings": []}},
        }
        (self.directory / "review-observation.tmp.json").write_text(json.dumps(observation))
        self.run_snippet("jq --slurpfile record")
        return observation

    def test_legacy_state_migrates_without_losing_iteration_or_delta(self):
        self.initialize()
        state = self.read()
        self.assertIn("review", state)
        self.assertEqual(60, state["await_limit_seconds"])
        self.assertEqual((2, "preserved", "signature", "script-hash"),
                         (state["iteration"], state["run_dir"], state["sig"], state["ld_sha"]))

    def test_absent_state_initializes_with_bounded_wait(self):
        self.assertFalse(self.state.exists())
        self.run_snippet("command -v jq")
        state = self.read()
        self.assertEqual((17, 2, 60), (state["pr"], state["iteration"], state["await_limit_seconds"]))
        self.assertIsNone(state["review"])
        self.assertEqual("poll", state["phase"])

    def test_checkpoint_persists_scope_handles_and_machine_verdict(self):
        self.initialize()
        observation = self.record("BLOCKED")
        self.assertEqual(observation, self.read()["review"])
        self.assertFalse((self.directory / "review-observation.tmp.json").exists())

    def test_wait_budget_preserves_pending_remote_handle(self):
        self.initialize()
        self.record()
        self.run_snippet("NOW=$(date")
        state = self.read()
        self.assertEqual("awaiting_review", state["phase"])
        self.assertGreater(state["await_deadline"], state["await_started_at"])
        state["await_deadline"] = 0
        self.write(state)
        self.run_snippet("NOW=$(date")
        state = self.read()
        self.assertEqual(("stop", "review_unavailable"), (state["phase"], state["stop_reason"]))
        self.assertEqual("run-123", state["review"]["handles"][0]["id"])
        self.assertEqual("PENDING", state["review"]["sources"]["ai"]["verdict"])
        self.assertEqual(2, state["iteration"])

    def test_resume_preserves_handles_and_renews_only_local_budget(self):
        self.initialize()
        self.record()
        state = self.read()
        state.update(phase="stop", stop_reason="review_unavailable",
                     await_started_at=1, await_deadline=2, run_dir=None)
        self.write(state)
        self.run_snippet("command -v jq")
        state = self.read()
        self.assertEqual(2, state["iteration"])
        self.assertEqual("run-123", state["review"]["handles"][0]["id"])
        self.assertIsNone(state["await_deadline"])

    def test_native_verdict_tokens_do_not_silently_pass(self):
        path = self.directory / "comment.json"
        self.env["REVIEW_COMMENT"] = str(path)
        for verdict in ("PASSED", "BLOCKED", "ERROR"):
            with self.subTest(verdict=verdict):
                path.write_text(json.dumps({"body": "**Status: " + verdict + "**\nreport"}))
                result = self.run_snippet("AI_VERDICT=")
                self.assertEqual(verdict, result.stdout.strip())
        path.write_text(json.dumps({"body": "no machine verdict"}))
        self.assertEqual("UNBOUND", self.run_snippet("AI_VERDICT=").stdout.strip())

    def test_corrupt_existing_state_is_preserved(self):
        for corrupt in (
            b"", b"{broken",
            json.dumps({"pr": 17, "base_ref": "main", "iteration": "2", "max_iter": 5,
                        "phase": "awaiting_review", "review": {"handles": ["live"]},
                        "run_dir": "recovery", "sig": "keep", "ld_sha": "keep"}).encode(),
        ):
            with self.subTest(corrupt=corrupt[:30]):
                self.state.write_bytes(corrupt)
                result = subprocess.run(
                    ["bash", "-euo", "pipefail", "-c", self.snippet("command -v jq")],
                    env=self.env, cwd=self.directory, capture_output=True, text=True,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(corrupt, self.state.read_bytes())

    def test_invalid_numeric_bounds_are_rejected(self):
        for field, value in (("max_iter", 1.5), ("await_deadline", "later"),
                             ("iteration", -1), ("max_iter", 10**30)):
            with self.subTest(field=field):
                self.initialize()
                state = self.read()
                state[field] = value
                self.write(state)
                original = self.state.read_bytes()
                result = subprocess.run(
                    ["bash", "-euo", "pipefail", "-c", self.snippet("command -v jq")],
                    env=self.env, cwd=self.directory, capture_output=True, text=True,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(original, self.state.read_bytes())

    def test_scope_change_does_not_extend_invocation_deadline(self):
        self.initialize()
        self.record()
        self.run_snippet("NOW=$(date")
        before = self.read()
        observation = before["review"]
        observation["head"] = "d" * 40
        observation["diff_sha256"] = "e" * 64
        (self.directory / "review-observation.tmp.json").write_text(json.dumps(observation))
        self.run_snippet("jq --slurpfile record")
        self.assertEqual(before["await_deadline"], self.read()["await_deadline"])

    def test_invalid_exemption_and_multiple_documents_are_rejected(self):
        for mode in ("exemption", "multi"):
            with self.subTest(mode=mode):
                self.initialize()
                observation = self.record()
                original = self.state.read_bytes()
                if mode == "exemption":
                    observation["sources"]["ai"]["verdict"] = "NOT_REQUIRED"
                    text = json.dumps(observation)
                else:
                    text = "{}\n" + json.dumps(observation)
                (self.directory / "review-observation.tmp.json").write_text(text)
                result = subprocess.run(
                    ["bash", "-euo", "pipefail", "-c", self.snippet("jq --slurpfile record")],
                    env=self.env, cwd=self.directory, capture_output=True, text=True,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(original, self.state.read_bytes())

    def test_justified_optional_source_is_preserved(self):
        self.initialize()
        observation = self.record()
        observation["requirements"]["ai"] = {
            "required": False, "basis": "human-only task; no AI requirement or configured AI review",
        }
        observation["sources"]["ai"]["verdict"] = "NOT_REQUIRED"
        (self.directory / "review-observation.tmp.json").write_text(json.dumps(observation))
        self.run_snippet("jq --slurpfile record")
        self.assertEqual("NOT_REQUIRED", self.read()["review"]["sources"]["ai"]["verdict"])

    def test_bad_deadline_does_not_mutate_state_in_wait_branch(self):
        self.initialize()
        self.record()
        state = self.read()
        state["await_deadline"] = "later"
        self.write(state)
        original = self.state.read_bytes()
        result = subprocess.run(
            ["bash", "-euo", "pipefail", "-c", self.snippet("NOW=$(date")],
            env=self.env, cwd=self.directory, capture_output=True, text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(original, self.state.read_bytes())

    def test_quoted_and_fenced_tokens_do_not_override_native_verdict(self):
        path = self.directory / "comment.json"
        self.env["REVIEW_COMMENT"] = str(path)
        for body, expected in (
            ("Example: `**Status: PASSED**`\n**Status: BLOCKED**", "BLOCKED"),
            ("> **Status: PASSED**\n**Status: ERROR**", "ERROR"),
            ("```markdown\n**Status: PASSED**\n```\n**Status: BLOCKED**", "BLOCKED"),
            ("~~~~\n**Status: PASSED**\n~~~~\n**Status: ERROR**", "ERROR"),
        ):
            with self.subTest(body=body):
                path.write_text(json.dumps({"body": body}))
                self.assertEqual(expected, self.run_snippet("AI_VERDICT=").stdout.strip())


if __name__ == "__main__":
    unittest.main()
