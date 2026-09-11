"""Bind bare git push to a PR using real repositories and no network."""
import json
import os
from pathlib import Path
import re
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "plugins/co-agent/skills/pr-autofix"
HELPER = SKILL / "scripts/check_pr_target.py"
DEFAULT_METADATA = object()


class PrTargetTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="pr target ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.repo = self.root / "consumer repo"
        self.repo.mkdir()
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        self.env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="/dev/null")
        self.git("init", "-q", "--template=", "-b", "topic")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "--allow-empty", "-qm", "initial")
        self.git("remote", "add", "origin", "https://github.com/Upstream/Repo.git")
        self.git("config", "branch.topic.remote", "origin")
        self.git("config", "branch.topic.merge", "refs/heads/topic")
        self.metadata = {
            "state": "OPEN", "headRefName": "topic",
            "headRepository": {"nameWithOwner": "Upstream/Repo"},
            "url": "https://github.com/Upstream/Repo/pull/171",
        }
        self.state = self.repo / ".claude/co-agent-consensus/pr-autofix/pr-171/state.json"

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, env=self.env,
                              text=True, capture_output=True, check=True).stdout.strip()

    def check(self, allowed=True, metadata=DEFAULT_METADATA):
        before = (self.repo / ".git/config").read_bytes()
        head = self.git("for-each-ref", "--format=%(refname) %(objectname)")
        result = subprocess.run(
            [sys.executable, "-B", str(HELPER)], cwd=self.repo, env=self.env,
            input=json.dumps(self.metadata if metadata is DEFAULT_METADATA else metadata),
            text=True, capture_output=True,
        )
        self.assertEqual(before, (self.repo / ".git/config").read_bytes())
        self.assertEqual(head, self.git("for-each-ref", "--format=%(refname) %(objectname)"))
        self.assertEqual("", result.stdout)
        if allowed:
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("", result.stderr)
        else:
            self.assertNotEqual(0, result.returncode)
            self.assertTrue(result.stderr.startswith("PR target:"), result.stderr)
        return result

    def fork(self):
        self.metadata["headRepository"]["nameWithOwner"] = "Contributor/Repo"
        self.git("remote", "add", "fork", "git@github.com:Contributor/Repo.git")

    def test_same_repository_default_simple_and_pending_local_commit(self):
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "--allow-empty", "-qm", "pending fix")
        self.check()

    def test_owner_name_schema_with_and_without_name_with_owner(self):
        self.metadata["headRepositoryOwner"] = {"login": "Upstream"}
        for repository in ({"id": "fixture-id", "name": "Repo"},
                           {"name": "Repo", "nameWithOwner": "Upstream/Repo"}):
            self.metadata["headRepository"] = repository
            self.check()
            self.entry()
        self.metadata["headRepository"]["nameWithOwner"] = "Other/Repo"
        self.check(False)
        self.metadata["headRepository"] = {"name": "Repo"}
        self.metadata["headRepositoryOwner"] = None
        self.check(False)

    def test_fork_owner_name_schema_binds_push_remote(self):
        self.fork()
        self.metadata["headRepository"] = {"name": "Repo"}
        self.metadata["headRepositoryOwner"] = {"login": "Contributor"}
        self.check(False)
        self.git("config", "branch.topic.pushRemote", "fork")
        self.check()
        self.entry()

    def test_wrong_origin_for_fork_is_rejected(self):
        self.fork()
        self.check(False)

    def test_correct_fork_push_remote_overrides_base_upstream(self):
        self.fork()
        self.git("config", "branch.topic.pushRemote", "fork")
        self.check()

    def test_remote_push_default_and_branch_override_precedence(self):
        self.fork()
        self.git("config", "remote.pushDefault", "fork")
        self.check()
        self.git("config", "branch.topic.pushRemote", "origin")
        self.check(False)

    def test_fork_origin_with_base_repository_upstream(self):
        self.fork()
        self.git("remote", "set-url", "origin", "https://github.com/Contributor/Repo.git")
        self.check()

    def test_push_modes_and_simple_upstream_name(self):
        for mode in ("simple", "current", "upstream"):
            with self.subTest(mode=mode):
                self.git("config", "push.default", mode)
                self.check()
        self.git("config", "branch.topic.merge", "refs/heads/main")
        for mode in ("simple", "upstream"):
            self.git("config", "push.default", mode)
            self.check(False)
        self.git("config", "push.default", "current")
        self.check()

    def test_triangular_simple_does_not_require_matching_fetch_branch(self):
        self.fork()
        self.git("config", "branch.topic.merge", "refs/heads/main")
        self.git("config", "branch.topic.pushRemote", "fork")
        self.check()
        self.git("config", "push.default", "upstream")
        self.check(False)

    def test_missing_upstream_needs_current_or_auto_setup(self):
        self.git("config", "--unset", "branch.topic.merge")
        self.check(False)
        self.git("config", "push.autoSetupRemote", "true")
        self.check()
        self.git("config", "--unset", "push.autoSetupRemote")
        self.git("config", "push.default", "current")
        self.check()

    def test_sole_remote_and_ambiguous_remote_fallback(self):
        self.git("config", "--remove-section", "branch.topic")
        self.git("remote", "rename", "origin", "only")
        self.git("config", "push.default", "current")
        self.check()
        self.git("remote", "add", "other", "https://github.com/Other/Repo.git")
        self.check(False)

    def test_real_bare_push_uses_the_sole_non_origin_remote(self):
        self.git("config", "--remove-section", "branch.topic")
        self.git("remote", "rename", "origin", "only")
        self.git("config", "push.default", "current")
        self.check()
        bare = self.root / "only.git"
        self.git("init", "-q", "--bare", "--template=", str(bare))
        self.git("remote", "set-url", "only", str(bare))
        self.git("push")  # Local file transport only; no network.
        self.assertEqual(self.git("rev-parse", "HEAD"),
                         self.git("--git-dir", str(bare), "rev-parse", "refs/heads/topic"))

    def test_git_config_override_disagrees_with_actual_push_and_is_rejected(self):
        alternate = self.root / "alternate.config"
        alternate.write_bytes((self.repo / ".git/config").read_bytes())
        bare = self.root / "actual.git"
        self.git("init", "-q", "--bare", "--template=", str(bare))
        self.git("remote", "set-url", "origin", str(bare))
        self.env["GIT_CONFIG"] = str(alternate)
        self.assertEqual("https://github.com/Upstream/Repo.git",
                         self.git("config", "--get", "remote.origin.url"))
        self.git("push")  # GIT_CONFIG is ignored here: only the local bare repo is contacted.
        self.assertEqual(self.git("rev-parse", "HEAD"),
                         self.git("--git-dir", str(bare), "rev-parse", "refs/heads/topic"))
        result = self.check(False)
        self.assertIn("GIT_CONFIG", result.stderr)
        self.assertNotIn(str(alternate), result.stderr)
        self.entry(False)

    def test_branch_closed_merged_detached_and_missing_repository(self):
        for patch in ({"state": "CLOSED"}, {"state": "MERGED"},
                      {"headRefName": "other"}, {"headRepository": None},
                      {"headRepository": {"nameWithOwner": "invalid"}}):
            self.check(False, {**self.metadata, **patch})
        self.git("checkout", "--detach", "-q")
        self.check(False)

    def test_explicit_single_head_refspec(self):
        for spec in ("HEAD:refs/heads/topic", "refs/heads/topic:refs/heads/topic",
                     "refs/heads/topic"):
            self.git("config", "remote.origin.push", spec)
            self.check()

    def test_misdirected_ambiguous_forced_and_bulk_refspecs(self):
        for spec in ("HEAD:refs/heads/main", "+HEAD:refs/heads/topic", ":",
                     "refs/heads/*:refs/heads/*", ":refs/heads/topic",
                     "HEAD:refs/tags/topic", "other:refs/heads/topic", "topic:topic"):
            with self.subTest(spec=spec):
                self.git("config", "remote.origin.push", spec)
                self.check(False)
        self.git("config", "remote.origin.push", "HEAD:refs/heads/topic")
        self.git("config", "--add", "remote.origin.push", "HEAD:refs/heads/other")
        self.check(False)

    def test_matching_mirror_follow_tags_and_submodule_push_rejected(self):
        for key, value in (("push.default", "matching"), ("push.default", "nothing"),
                           ("remote.origin.mirror", "true"), ("push.followTags", "true"),
                           ("push.recurseSubmodules", "on-demand"),
                           ("push.recurseSubmodules", "only")):
            with self.subTest(key=key, value=value):
                self.git("config", key, value)
                self.check(False)
                self.git("config", "--unset", key)
        self.git("config", "push.followTags", "false")
        self.git("config", "remote.origin.mirror", "false")
        self.check()

    def test_submodule_recurse_is_rejected_in_both_config_orders(self):
        original = (self.repo / ".git/config").read_bytes()
        for settings in (
            (("submodule.recurse", "true"),),
            (("submodule.recurse", "true"), ("push.recurseSubmodules", "no")),
            (("push.recurseSubmodules", "no"), ("submodule.recurse", "true")),
            (("submodule.recurse", "false"), ("submodule.recurse", "true")),
        ):
            with self.subTest(settings=settings):
                (self.repo / ".git/config").write_bytes(original)
                for key, value in settings:
                    self.git("config", "--add", key, value)
                self.check(False)
        self.git("config", "--add", "submodule.recurse", "false")
        self.check()

    def test_push_url_not_fetch_url_and_multiple_destinations(self):
        self.fork()
        self.git("config", "remote.origin.pushurl", "https://github.com/Contributor/Repo.git")
        self.check()
        self.git("config", "--add", "remote.origin.pushurl", "https://github.com/Other/Repo.git")
        self.check(False)
        self.git("config", "--unset-all", "remote.origin.pushurl")
        self.git("config", "--add", "remote.origin.url", "https://github.com/Contributor/Repo.git")
        self.check(False)

    def test_standard_ssh_https_and_case_insensitive_repository_identity(self):
        for url in ("git@github.com:Upstream/Repo.git",
                    "ssh://git@github.com/Upstream/Repo.git",
                    "ssh://git@github.com:22/Upstream/Repo.git",
                    "https://github.com/upstream/repo",
                    "https://github.com:443/Upstream/Repo.git"):
            with self.subTest(url=url):
                self.git("config", "remote.origin.url", url)
                self.check()

    def test_wrong_host_ssh_alias_custom_port_transport_and_path_rejected(self):
        for url in ("git@my-github-alias:Upstream/Repo.git",
                    "https://github.com.evil.invalid/Upstream/Repo",
                    "ssh://git@github.com:2222/Upstream/Repo.git",
                    "ssh://other@github.com/Upstream/Repo.git",
                    "ext::command", "/local/repo", "https://github.com/Upstream/Repo/extra",
                    "https://github.com/Upstream/Repo?route=Other/Repo",
                    "https://github.com/Upstream/%52epo"):
            with self.subTest(url=url):
                self.git("config", "remote.origin.url", url)
                self.check(False)

    def test_raw_url_scheme_must_match_git_transport_case(self):
        for url in ("HTTPS://github.com/Upstream/Repo.git", "SSH://git@github.com/Upstream/Repo.git"):
            with self.subTest(url=url):
                self.git("config", "remote.origin.url", url)
                self.check(False)

    def test_url_credentials_never_appear_in_diagnostics(self):
        secret = "fixture-token-never-log"
        self.git("config", "remote.origin.url",
                 f"https://fixture-user:{secret}@github.com/Other/Repo.git")
        result = self.check(False)
        self.assertNotIn(secret, result.stderr)
        self.assertNotIn("fixture-user", result.stderr)
        self.git("config", "remote.origin.url",
                 f"https://fixture-user:{secret}@github.com/Upstream/Repo.git")
        self.check()

    def test_url_rewrites_and_custom_receive_pack_fail_closed(self):
        for key, value in (("url.https://github.com/Other/.pushInsteadOf",
                            "https://github.com/Upstream/"),
                           ("url.git@alias:.insteadOf", "https://github.com/"),
                           ("remote.origin.receivepack", "custom-receiver"),
                           ("remote.origin.vcs", "custom-helper")):
            self.git("config", key, value)
            self.check(False)
            self.git("config", "--unset", key)

    def test_bad_json_is_rejected_without_echoing_input(self):
        for value in ([], None, {"state": ["OPEN"]}, {**self.metadata, "url": "not-a-url"}):
            self.check(False, value)
        result = subprocess.run([sys.executable, "-B", str(HELPER)], cwd=self.repo,
                                env=self.env, input="fixture-secret{", text=True,
                                capture_output=True)
        self.assertNotEqual(0, result.returncode)
        self.assertNotIn("fixture-secret", result.stderr)

    def entry(self, allowed=True, gh_status="0", supplied=None, initialize=False):
        bindir = self.root / "bin"
        bindir.mkdir(exist_ok=True)
        gh = bindir / "gh"
        gh.write_text("""#!/usr/bin/env python3
import json, os, sys
data = json.loads(os.environ["FIXTURE_PR"])
with open(os.environ["FIXTURE_GH_LOG"], "a") as log:
    log.write(json.dumps(sys.argv[1:]) + "\\n")
if sys.argv[1:3] == ["repo", "view"]:
    print("Upstream/Repo")
elif sys.argv[1:3] == ["pr", "view"]:
    fields = sys.argv[sys.argv.index("--json") + 1].split(",")
    print(json.dumps({key: value for key, value in data.items() if key in fields}))
    sys.exit(int(os.environ["FIXTURE_GH_STATUS"]))
elif sys.argv[1:3] == ["pr", "list"]:
    print('[{"number": 171}]')
else:
    sys.exit(2)
""")
        gh.chmod(0o755)
        reference = SKILL.joinpath("references/review-state.md").read_text()
        snippet = next(block for block in re.findall(r"```bash\n(.*?)\n```", reference, re.S)
                       if "STATE_BINDING=" in block)
        env = {**self.env, "PR_NUMBER": "171", "FIXTURE_PR": json.dumps(self.metadata),
               "FIXTURE_GH_STATUS": gh_status, "CLAUDE_PLUGIN_ROOT": str(SKILL.parents[1]),
               "FIXTURE_GH_LOG": str(self.root / "gh.log"),
               "PATH": str(bindir) + os.pathsep + self.env["PATH"]}
        for key, value in (supplied or {}).items():
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value
        snippet += '\nprintf "\\nresolved-pr=%s\\n" "$PR_NUMBER"\n'
        if initialize:
            model = SKILL.joinpath("SKILL.md").read_text().split("## State model", 1)[1]
            snippet += re.search(r"```bash\n(.*?)\n```", model, re.S)[1] + "\n"
            reference = SKILL.joinpath("references/review-state.md").read_text()
            snippet += next(block for block in re.findall(r"```bash\n(.*?)\n```", reference, re.S)
                            if "command -v jq" in block)
            snippet += '\nprintf "\\nresolved-state=%s\\n" "$STATE"\n'
            env.update(BASE_REF="main", GIT_ITER="2", PR_AUTOFIX_WAIT_SECONDS="60",
                       CO_AGENT_USER_CONFIG=str(self.root / "no-user-config"))
        result = subprocess.run(["bash", "-c", snippet], cwd=self.repo, env=env,
                                text=True, capture_output=True)
        if allowed:
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        else:
            self.assertNotEqual(0, result.returncode, "Step 1 accepted an unsafe target")
        return result

    def saved_state(self, phase="gate"):
        data = {"pr": 171, "base_ref": "main", "iteration": 2, "max_iter": 5,
                "phase": phase, "run_dir": "pending-delta", "sig": "signature",
                "ld_sha": "script-hash", "review": None, "stop_detail": None,
                "await_started_at": None, "await_deadline": None, "await_limit_seconds": 60}
        self.state.parent.mkdir(parents=True, exist_ok=True)
        self.state.write_text(json.dumps(data))
        return data

    def test_state_only_resume_preserves_gate_and_committing_without_discovery(self):
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "--allow-empty", "-qm", "pending fix")
        for phase in ("gate", "committing"):
            with self.subTest(phase=phase):
                data = self.saved_state(phase)
                result = self.entry(supplied={"STATE": str(self.state), "PR_NUMBER": None},
                                    initialize=True)
                self.assertIn("resolved-pr=171", result.stdout)
                self.assertIn("resolved-state=" + str(self.state), result.stdout)
                self.assertEqual(data, json.loads(self.state.read_text()))
                calls = [json.loads(line) for line in (self.root / "gh.log").read_text().splitlines()]
                self.assertFalse(any(call[:2] == ["pr", "list"] for call in calls))

    def test_reported_binding_is_consumed_in_a_separate_shell(self):
        for phase in (None, "gate", "committing"):
            with self.subTest(phase=phase):
                if self.state.exists():
                    self.state.unlink()
                saved = self.saved_state(phase) if phase else None
                result = self.entry(supplied={"STATE": str(self.state) if phase else None})
                binding = json.loads(result.stdout.splitlines()[0])
                self.assertEqual({"pr": 171, "state": str(self.state)}, binding)
                model = SKILL.joinpath("SKILL.md").read_text().split("## State model", 1)[1]
                script = re.search(r"```bash\n(.*?)\n```", model, re.S)[1]
                reference = SKILL.joinpath("references/review-state.md").read_text()
                script += "\n" + next(block for block in re.findall(r"```bash\n(.*?)\n```", reference, re.S)
                                     if "command -v jq" in block)
                env = {**self.env, "STATE_BINDING": json.dumps(binding), "BASE_REF": "main", "GIT_ITER": "2",
                       "PR_AUTOFIX_WAIT_SECONDS": "60", "CLAUDE_PLUGIN_ROOT": str(SKILL.parents[1]),
                       "CO_AGENT_USER_CONFIG": str(self.root / "no-user-config")}
                for key in ("STATE", "STATE_DIR", "PR_NUMBER"):
                    env.pop(key, None)
                consumed = subprocess.run(["bash", "-euo", "pipefail", "-c", script],
                                          cwd=self.repo, env=env, capture_output=True, text=True)
                self.assertEqual(0, consumed.returncode, consumed.stderr)
                state = json.loads(self.state.read_text())
                self.assertEqual(saved, state) if saved else self.assertEqual(171, state["pr"])

    def test_logical_workspace_ancestor_resolves_to_the_same_state(self):
        saved = self.saved_state()
        alias = self.root / "workspace alias"
        alias.symlink_to(self.repo, target_is_directory=True)
        logical = alias / self.state.relative_to(self.repo)
        result = self.entry(supplied={"STATE": str(logical), "PR_NUMBER": None}, initialize=True)
        self.assertIn("resolved-state=" + str(self.state), result.stdout)
        self.assertEqual(saved, json.loads(self.state.read_text()))

    def test_internal_alias_to_canonical_state_is_rejected(self):
        self.saved_state()
        alias = self.repo / "state-alias"
        alias.symlink_to(self.state.parent, target_is_directory=True)
        self.entry(False, supplied={"STATE": str(alias / "state.json"), "PR_NUMBER": None})

    def test_foreign_state_is_rejected_before_reading_its_contents(self):
        self.saved_state()
        foreign = self.root / "foreign/.claude/co-agent-consensus/pr-autofix/pr-171/state.json"
        foreign.parent.mkdir(parents=True)
        foreign.write_bytes(self.state.read_bytes())
        module = runpy.run_path(str(SKILL / "scripts/resolve_pr_state.py"))
        resolver = module["resolve"]
        def unexpected_read(_):
            self.fail("Foreign state contents were opened before path rejection")
        with patch.dict(resolver.__globals__, {"read_state": unexpected_read}):
            with self.assertRaises(module["StateError"]):
                resolver(self.repo, state=str(foreign))

    def test_explicit_number_must_match_state_before_querying(self):
        self.saved_state()
        before = self.state.read_bytes()
        self.entry(False, supplied={"STATE": str(self.state), "PR_NUMBER": "172"})
        self.assertEqual(before, self.state.read_bytes())
        self.assertFalse((self.root / "gh.log").exists())

    def test_foreign_state_with_same_number_is_not_adopted(self):
        self.saved_state()
        foreign = self.root / "foreign repo/.claude/co-agent-consensus/pr-autofix/pr-171/state.json"
        foreign.parent.mkdir(parents=True)
        foreign.write_bytes(self.state.read_bytes())
        before = foreign.read_bytes()
        self.entry(False, supplied={"STATE": str(foreign), "PR_NUMBER": None}, initialize=True)
        self.assertEqual(before, foreign.read_bytes())
        self.assertFalse((self.root / "gh.log").exists())

    def test_supplied_missing_empty_malformed_and_multidocument_state_never_resets(self):
        self.state.parent.mkdir(parents=True)
        for contents in (None, b"", b"{broken", b"{}{}", b'{"pr":171}', b'{"pr":0}'):
            with self.subTest(contents=contents):
                if contents is not None:
                    self.state.write_bytes(contents)
                self.entry(False, supplied={"STATE": str(self.state), "PR_NUMBER": None},
                           initialize=True)
                if contents is None:
                    self.assertFalse(self.state.exists())
                else:
                    self.assertEqual(contents, self.state.read_bytes())
                self.assertFalse((self.root / "gh.log").exists())
        self.entry(False, supplied={"STATE": ""})

    def test_symlink_state_and_parent_directory_are_rejected(self):
        self.saved_state()
        backup = self.root / "saved.json"
        self.state.rename(backup)
        self.state.symlink_to(backup)
        self.entry(False, supplied={"STATE": str(self.state)})
        self.state.unlink()
        backup.rename(self.state)
        directory = self.state.parent
        directory.rename(self.root / "saved directory")
        directory.symlink_to(self.root / "saved directory", target_is_directory=True)
        self.entry(False, supplied={"STATE": str(self.state)})

    def test_branch_discovery_only_without_supplied_number_or_state(self):
        result = self.entry(supplied={"PR_NUMBER": None, "STATE": None}, initialize=True)
        self.assertIn("resolved-pr=171", result.stdout)
        self.assertEqual(171, json.loads(self.state.read_text())["pr"])
        calls = [json.loads(line) for line in (self.root / "gh.log").read_text().splitlines()]
        self.assertTrue(any(call[:2] == ["pr", "list"] for call in calls))

    def test_empty_pr_number_allows_discovery(self):
        result = self.entry(supplied={"PR_NUMBER": "", "STATE": None}, initialize=True)
        self.assertIn("resolved-pr=171", result.stdout)
        self.assertEqual(171, json.loads(self.state.read_text())["pr"])

    def test_derived_existing_state_pr_mismatch_is_not_reset(self):
        self.saved_state()
        data = json.loads(self.state.read_text())
        data["pr"] = 172
        self.state.write_text(json.dumps(data))
        before = self.state.read_bytes()
        self.entry(False, initialize=True)
        self.assertEqual(before, self.state.read_bytes())

    def test_relative_canonical_state_keeps_same_file(self):
        before = self.saved_state()
        result = self.entry(supplied={"STATE": str(self.state.relative_to(self.repo)),
                                     "PR_NUMBER": None}, initialize=True)
        self.assertIn("resolved-state=" + str(self.state), result.stdout)
        self.assertEqual(before, json.loads(self.state.read_text()))

    def test_step_one_rejects_wrong_fork_then_accepts_push_remote(self):
        self.fork()
        self.entry(False)
        self.git("config", "branch.topic.pushRemote", "fork")
        self.entry()

    def test_step_one_preserves_gh_failure_even_with_valid_json(self):
        self.entry(False, gh_status="1")


if __name__ == "__main__":
    unittest.main()
