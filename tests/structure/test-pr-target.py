"""Bind bare git push to a PR using real repositories and no network."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "plugins/co-agent/skills/pr-autofix"
HELPER = SKILL / "scripts/check_pr_target.py"
DEFAULT_METADATA = object()


class PrTargetTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="pr target ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
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

    def entry(self, allowed=True, gh_status="0"):
        bindir = self.root / "bin"
        bindir.mkdir(exist_ok=True)
        gh = bindir / "gh"
        gh.write_text("""#!/usr/bin/env python3
import json, os, sys
data = json.loads(os.environ["FIXTURE_PR"])
if sys.argv[1:3] == ["repo", "view"]:
    print("Upstream/Repo")
elif sys.argv[1:3] == ["pr", "view"]:
    if "--jq" in sys.argv:
        print(data["state"] + "\\t" + data["headRefName"])
    else:
        print(json.dumps(data))
    sys.exit(int(os.environ["FIXTURE_GH_STATUS"]))
else:
    sys.exit(2)
""")
        gh.chmod(0o755)
        step = SKILL.joinpath("SKILL.md").read_text().split("### 1. Identify the PR", 1)[1]
        snippet = re.search(r"```bash\n(.*?)\n```", step, re.S)[1]
        env = {**self.env, "PR_NUMBER": "171", "FIXTURE_PR": json.dumps(self.metadata),
               "FIXTURE_GH_STATUS": gh_status, "CLAUDE_PLUGIN_ROOT": str(SKILL.parents[1]),
               "PATH": str(bindir) + os.pathsep + self.env["PATH"]}
        result = subprocess.run(["bash", "-c", snippet], cwd=self.repo, env=env,
                                text=True, capture_output=True)
        if allowed:
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        else:
            self.assertNotEqual(0, result.returncode, "Step 1 accepted an unsafe target")

    def test_step_one_rejects_wrong_fork_then_accepts_push_remote(self):
        self.fork()
        self.entry(False)
        self.git("config", "branch.topic.pushRemote", "fork")
        self.entry()

    def test_step_one_preserves_gh_failure_even_with_valid_json(self):
        self.entry(False, gh_status="1")


if __name__ == "__main__":
    unittest.main()
