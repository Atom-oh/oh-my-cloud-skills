"""Execute the skill's state/observation snippets against local fixtures."""
import json
import hashlib
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
            "REPO": "example/repository",
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
                self.assert_refused("command -v jq")

    def test_invalid_numeric_bounds_are_rejected(self):
        for field, value in (("phase", ["poll"]), ("max_iter", 1.5), ("await_deadline", "later"),
                             ("iteration", -1), ("max_iter", 10**30)):
            with self.subTest(field=field):
                self.initialize()
                state = self.read()
                state[field] = value
                self.write(state)
                self.assert_refused("command -v jq")

    def test_scope_change_does_not_extend_invocation_deadline(self):
        self.initialize()
        self.record()
        self.run_snippet("NOW=$(date")
        before = self.read()
        observation = before["review"]
        observation["head"] = "d" * 40
        observation["sources"]["ai"]["head"] = "d" * 40
        observation["diff_sha256"] = "e" * 64
        (self.directory / "review-observation.tmp.json").write_text(json.dumps(observation))
        self.run_snippet("jq --slurpfile record")
        self.assertEqual(before["await_deadline"], self.read()["await_deadline"])

    def test_checkpoint_rejects_bound_source_from_another_head(self):
        for verdict in ("PASSED", "BLOCKED", "ERROR", "PENDING"):
            with self.subTest(verdict=verdict):
                self.initialize()
                observation = self.record(verdict)
                observation["sources"]["ai"]["head"] = "d" * 40
                (self.directory / "review-observation.tmp.json").write_text(json.dumps(observation))
                self.assert_refused("jq --slurpfile record")

    def prepare_clean(self):
        self.initialize()
        self.record("PASSED")
        state = self.read()
        state["phase"] = "checking_review"
        state["review"]["sources"]["ai"]["coverage_complete"] = True
        state["review"]["diff_sha256"] = hashlib.sha256(b"fixture diff\n").hexdigest()
        self.write(state)
        live = {
            "number": 17, "state": "OPEN", "headRefOid": "a" * 40, "headRefName": "fixture",
            "baseRefOid": "b" * 40, "baseRefName": "main",
            "reviewDecision": "APPROVED", "mergeStateStatus": "CLEAN",
            "mergeable": "MERGEABLE",
        }
        self.live_path = self.directory / "live-pr.json"
        self.live_path.write_text(json.dumps(live))
        self.env["TEST_LIVE_PR"] = str(self.live_path)
        fake = self.directory / "bin"
        fake.mkdir(exist_ok=True)
        gh = fake / "gh"
        gh.write_text("""#!/usr/bin/env python3
import json, os, pathlib, sys
path = pathlib.Path(os.environ["TEST_LIVE_PR"])
if pathlib.Path(sys.argv[0]).name == "git":
    if sys.argv[1:] == ["symbolic-ref", "--quiet", "--short", "HEAD"]:
        if os.environ.get("TEST_BRANCH") == "DETACHED": sys.exit(1)
        print(os.environ.get("TEST_BRANCH", "fixture"))
    elif sys.argv[1:] == ["rev-parse", "--verify", "HEAD"]:
        print(os.environ.get("TEST_LOCAL_HEAD", "a" * 40))
    else: sys.exit(2)
elif sys.argv[1:3] == ["repo", "view"]:
    print("example/repository")
elif sys.argv[1:3] == ["pr", "diff"]:
    if os.environ.get("TEST_DIFF_FAIL"):
        sys.exit(1)
    print(os.environ.get("TEST_DIFF", "fixture diff"))
    if os.environ.get("TEST_HEAD_RACE"):
        data = json.loads(path.read_text())
        data["headRefOid"] = "d" * 40
        path.write_text(json.dumps(data))
elif sys.argv[1:3] == ["pr", "view"]:
    if os.environ.get("TEST_QUERY_FAIL"):
        sys.exit(1)
    data = json.loads(path.read_text())
    if "--jq" not in sys.argv:
        print(path.read_text())
    else:
        query = sys.argv[sys.argv.index("--jq") + 1]
        if query == "[.state,.headRefName]|@tsv":
            print(data["state"] + "\\t" + data["headRefName"])
        elif query in (".baseRefName", ".headRefOid", ".headRefName"):
            print(data[query[1:]])
        else:
            sys.exit(2)
elif sys.argv[1:3] == ["pr", "checks"]:
    error = os.environ.get("TEST_CHECK_ERROR")
    if error:
        print(error, file=sys.stderr)
        sys.exit(1)
    print(os.environ.get("TEST_CHECKS", '[{"name":"CI","bucket":"pass","state":"SUCCESS"}]'))
else:
    sys.exit(2)
""")
        gh.chmod(0o755)
        if not (fake / "git").exists():
            (fake / "git").symlink_to("gh")
        self.env["PATH"] = str(fake) + os.pathsep + os.environ["PATH"]
        return state, live

    def assert_refused(self, needle='.stop_reason = "clean"'):
        original = self.state.read_bytes()
        result = subprocess.run(
            ["bash", "-euo", "pipefail", "-c", self.snippet(needle)],
            env=self.env, cwd=self.directory, capture_output=True, text=True,
        )
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(original, self.state.read_bytes())

    def test_clean_accepts_complete_current_head_evidence(self):
        self.prepare_clean()
        self.run_snippet('.stop_reason = "clean"')
        self.assertEqual(("stop", "clean"), (self.read()["phase"], self.read()["stop_reason"]))

    def test_entry_refuses_wrong_branch_closed_pr_and_detached_head(self):
        for branch, status in (("other", "OPEN"), ("fixture", "CLOSED"),
                               ("fixture", "MERGED"), ("DETACHED", "OPEN")):
            with self.subTest(branch=branch, status=status):
                _, live = self.prepare_clean()
                live["state"] = status
                self.live_path.write_text(json.dumps(live))
                self.env["TEST_BRANCH"] = branch
                self.assert_refused("REPO=$(gh repo view")

    def test_entry_preserves_gate_and_committing_state(self):
        for phase in ("gate", "committing"):
            with self.subTest(phase=phase):
                state, _ = self.prepare_clean()
                state["phase"] = phase
                self.write(state)
                self.run_snippet("REPO=$(gh repo view")
                self.run_snippet("command -v jq")
                self.assertEqual(state, self.read())

    def test_clean_refuses_missing_stale_partial_or_blocked_evidence(self):
        for invalid in ("null", "empty", "pending", "error", "unbound", "stale",
                        "coverage", "finding", "optional_block", "array_verdict", "blank_basis",
                        "stop_reason", "invalid_phase", "exemption"):
            with self.subTest(invalid=invalid):
                state, _ = self.prepare_clean()
                source = state["review"]["sources"]["ai"]
                if invalid in ("null", "empty"):
                    state["review"] = None if invalid == "null" else {}
                elif invalid in ("pending", "error", "unbound"):
                    source["verdict"] = invalid.upper()
                elif invalid == "stale":
                    source["head"] = "d" * 40
                elif invalid == "coverage":
                    source["coverage_complete"] = False
                elif invalid == "finding":
                    source["blocking_findings"] = ["unresolved Major"]
                elif invalid == "optional_block":
                    state["review"]["requirements"]["ai"]["required"] = False
                    source["verdict"] = "BLOCKED"
                elif invalid == "array_verdict":
                    state["review"]["requirements"]["ai"]["required"] = False
                    source["verdict"] = ["BLOCKED"]
                elif invalid == "blank_basis":
                    state["review"]["requirements"]["ai"]["basis"] = " \n "
                elif invalid == "stop_reason":
                    state["stop_reason"] = "review_unavailable"
                elif invalid == "invalid_phase":
                    state["phase"] = "committing"
                else:
                    source["verdict"] = "NOT_REQUIRED"
                self.write(state)
                self.assert_refused()

    def test_clean_rechecks_live_scope_and_effective_protection(self):
        for field, value in (
            ("number", 18), ("headRefOid", "d" * 40),
            ("baseRefName", "release"), ("state", "MERGED"),
            ("reviewDecision", "CHANGES_REQUESTED"), ("reviewDecision", "REVIEW_REQUIRED"),
            ("mergeStateStatus", "BLOCKED"), ("mergeStateStatus", "UNKNOWN"),
            ("mergeStateStatus", "BEHIND"),
            ("mergeable", "CONFLICTING"),
        ):
            with self.subTest(field=field, value=value):
                _, live = self.prepare_clean()
                live[field] = value
                self.live_path.write_text(json.dumps(live))
                self.assert_refused()

    def test_clean_refuses_query_failure_diff_drift_and_racing_push(self):
        for variable, value in (("TEST_QUERY_FAIL", "1"), ("TEST_DIFF_FAIL", "1"),
                                ("TEST_DIFF", "different diff"), ("TEST_HEAD_RACE", "1"),
                                ("TEST_LOCAL_HEAD", "d" * 40)):
            with self.subTest(variable=variable):
                self.prepare_clean()
                self.env[variable] = value
                self.assert_refused()
                del self.env[variable]

    def test_clean_allows_optional_failure_and_unchanged_diff_after_base_advance(self):
        for merge_state in ("CLEAN", "UNSTABLE", "HAS_HOOKS"):
            with self.subTest(merge_state=merge_state):
                _, live = self.prepare_clean()
                live.update(baseRefOid="e" * 40, mergeStateStatus=merge_state)
                self.live_path.write_text(json.dumps(live))
                self.run_snippet('.stop_reason = "clean"')
                self.assertEqual("b" * 40, self.read()["review"]["base_sha"])

    def test_required_check_lookup_and_results_cannot_fail_open(self):
        for variable, value in (
            ("TEST_CHECK_ERROR", "HTTP 403"), ("TEST_CHECK_ERROR", "unknown flag: --required"),
            ("TEST_CHECKS", "null"), ("TEST_CHECKS", "{}"),
            ("TEST_CHECKS", '[{"name":"CI","bucket":"fail","state":"FAILURE"}]'),
            ("TEST_CHECKS", '[{"name":"CI","bucket":"pending","state":"PENDING"}]'),
        ):
            with self.subTest(value=value):
                self.prepare_clean()
                self.env[variable] = value
                self.assert_refused()
                del self.env[variable]
        self.prepare_clean()
        self.env["TEST_CHECK_ERROR"] = "no required checks reported on the 'fixture' branch"
        self.run_snippet('.stop_reason = "clean"')

    def test_invalid_exemption_and_multiple_documents_are_rejected(self):
        for mode in ("exemption", "multi"):
            with self.subTest(mode=mode):
                self.initialize()
                observation = self.record()
                if mode == "exemption":
                    observation["sources"]["ai"]["verdict"] = "NOT_REQUIRED"
                    text = json.dumps(observation)
                else:
                    text = "{}\n" + json.dumps(observation)
                (self.directory / "review-observation.tmp.json").write_text(text)
                self.assert_refused("jq --slurpfile record")

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
        self.assert_refused("NOW=$(date")

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
