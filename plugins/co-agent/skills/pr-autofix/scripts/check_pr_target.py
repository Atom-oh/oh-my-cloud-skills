#!/usr/bin/env python3
"""Read gh PR JSON on stdin; bind bare git push using local Git metadata only."""
import json
import os
import re
import subprocess
import sys
from urllib.parse import urlsplit


class TargetError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise TargetError(message)


def git(*args):
    result = subprocess.run(["git", *args], capture_output=True, text=True, timeout=10)
    # Git errors can contain credential-bearing URLs/config keys. Never relay them.
    require(result.returncode == 0,
            "cannot resolve local Git configuration; use an attached branch and a named push remote.")
    return result.stdout


class Config:
    def __init__(self):
        self.values = {}
        for record in git("config", "--null", "--list").split("\0"):
            if record:
                key, separator, value = record.partition("\n")
                self.values.setdefault(key, []).append(value if separator else None)

    def all(self, key):
        return self.values.get(key, [])

    def last(self, key, default=None):
        values = self.all(key)
        return values[-1] if values else default

    def boolean(self, key):
        if key not in self.values:
            return False
        return git("config", "--type=bool", "--get", key).strip() == "true"


def repository_path(path):
    require(isinstance(path, str) and
            re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", path) is not None and
            all(part not in (".", "..") for part in path.split("/")),
            "repository identity must be an explicit owner/repository.")
    return path.lower()


def url_identity(raw, *, pr=False):
    require(isinstance(raw, str) and raw and
            not any(character.isspace() or ord(character) < 32 for character in raw),
            "invalid repository URL; configure a canonical HTTPS or SSH URL.")
    if "://" in raw:
        parsed = urlsplit(raw)
        require(parsed.scheme in (("https",) if pr else ("https", "ssh")) and
                parsed.hostname and not parsed.query and not parsed.fragment,
                "use a canonical HTTPS/SSH host and repository path, without URL options.")
        require(parsed.port in (None, 443 if parsed.scheme == "https" else 22),
                "custom transport ports cannot be bound locally; use a canonical remote URL.")
        if pr:
            require(parsed.username is None and parsed.password is None,
                    "PR metadata must contain a canonical web URL.")
        if parsed.scheme == "ssh":
            require(parsed.username == "git" and parsed.password is None,
                    "SSH remotes must use the canonical git user.")
        host, path = parsed.hostname.lower(), parsed.path
        require(path.startswith("/"), "repository URL has no absolute path.")
        path = path[1:]
    else:
        match = re.fullmatch(r"git@([A-Za-z0-9.-]+):/?(.+)", raw)
        require(not pr and match is not None,
                "unsupported remote route; use canonical HTTPS or git@host:owner/repository.git.")
        host, path = match.group(1).lower(), match.group(2)
    require(re.fullmatch(r"[A-Za-z0-9.-]+", host) is not None,
            "unresolvable host; SSH aliases are not expanded by this guard.")
    if pr:
        match = re.fullmatch(r"(.+)/pull/[1-9][0-9]*", path)
        require(match is not None, "PR metadata must contain a canonical pull-request URL.")
        path = match.group(1)
    elif path.endswith(".git"):
        path = path[:-4]
    return host, repository_path(path)


def validate(pr):
    require(isinstance(pr, dict) and pr.get("state") == "OPEN",
            "require an OPEN PR before fixes or pushes.")
    branch = pr.get("headRefName")
    require(isinstance(branch, str) and branch, "PR head branch is missing.")
    head_repository = pr.get("headRepository")
    require(isinstance(head_repository, dict), "PR head repository is missing or deleted.")
    owner_repo = repository_path(head_repository.get("nameWithOwner"))
    host, _ = url_identity(pr.get("url"), pr=True)

    config = Config()
    fields = ("HEAD", "refname", "push:remotename", "push:remoteref",
              "upstream:remotename", "upstream:remoteref")
    rows = git("for-each-ref", "--format=" + "%00".join("%(" + f + ")" for f in fields),
               "refs/heads/").splitlines()
    attached = [row.split("\0") for row in rows if row.startswith("*\0")]
    require(len(attached) == 1 and len(attached[0]) == len(fields),
            "detached or unborn HEAD; check out the PR head branch.")
    _, ref, native_remote, native_ref, upstream_remote, upstream_ref = attached[0]
    require(ref == "refs/heads/" + branch,
            "attached branch does not match the PR head; select the intended checkout.")

    prefix = "branch." + branch
    remotes = {match.group(1) for key in config.values
               if (match := re.fullmatch(r"remote\.(.+)\.[^.]+", key))}
    fallback = next(iter(remotes)) if len(remotes) == 1 else "origin"
    fetch_remote = config.last(prefix + ".remote", fallback)
    remote = config.last(prefix + ".pushremote",
                         config.last("remote.pushdefault", fetch_remote))
    require(remote in remotes and remote != "." and
            re.fullmatch(r"[A-Za-z0-9_./-]+", remote) is not None,
            "cannot resolve the push remote; configure branch.<name>.pushRemote to a named remote.")
    require(not native_remote or native_remote == remote,
            "Git push remote disagrees with configuration; resolve the local route before retrying.")
    remote_prefix = "remote." + remote
    require(not config.boolean(remote_prefix + ".mirror") and
            not config.boolean("push.followtags"),
            "mirror/followTags may push unrelated refs; disable them before entering this loop.")
    require(config.last("push.recursesubmodules", "no") in ("no", "false", "off", "0", "check"),
            "submodule pushes may change other repositories; disable recursive pushes.")
    require(not config.all(remote_prefix + ".vcs") and
            not config.all(remote_prefix + ".receivepack"),
            "custom remote helpers/receive-pack cannot be bound; use the standard Git transport.")

    mode = config.last("push.default", "simple")
    require(mode in ("simple", "current", "upstream"),
            "use push.default=simple, current or upstream; matching/bulk pushes are not allowed.")
    refspecs = config.all(remote_prefix + ".push")
    if refspecs:
        require(len(refspecs) == 1 and refspecs[0] in (ref, ref + ":" + ref, "HEAD:" + ref),
                "push refspec must update only HEAD to the fully qualified PR head ref, without force.")
    elif mode == "upstream" or (mode == "simple" and remote == fetch_remote):
        require(remote == fetch_remote,
                "upstream mode cannot push to a different remote; use simple/current for a fork.")
        merges = config.all(prefix + ".merge")
        require((not merges and config.boolean("push.autosetupremote")) or
                (merges == [ref] and upstream_remote == remote and upstream_ref == ref),
                "upstream must be the same PR head ref; configure tracking or use push.default=current.")
    require(not native_ref or native_ref == ref,
            "Git push ref differs from the PR head ref; correct the push refspec.")

    push_urls = config.all(remote_prefix + ".pushurl")
    urls = push_urls or config.all(remote_prefix + ".url")
    require(len(urls) == 1 and isinstance(urls[0], str) and urls[0],
            "require exactly one push URL; multiple destinations or legacy remote files are unsupported.")
    url = urls[0]
    for key, values in config.values.items():
        if key.startswith("url.") and (
            key.endswith(".insteadof") or (not push_urls and key.endswith(".pushinsteadof"))
        ):
            require(not any(value is None or url.startswith(value) for value in values),
                    "push URL rewrite prevents binding; configure an explicit canonical push URL.")
    if url.startswith(("git@", "ssh://")):
        require(not config.all("core.sshcommand") and
                not any(os.environ.get(key) for key in ("GIT_SSH", "GIT_SSH_COMMAND")),
                "custom SSH command cannot be resolved locally; use the standard SSH transport.")
    destination = url_identity(url)
    require(destination == (host, owner_repo),
            "bare git push targets another repository/host; set pushRemote or pushurl to the PR head repository.")


def main():
    try:
        validate(json.load(sys.stdin))
    except TargetError as error:
        print("PR target: " + str(error), file=sys.stderr)
        return 1
    except (ValueError, OSError, subprocess.TimeoutExpired):
        print("PR target: invalid metadata/URL or unavailable local Git; no target was verified.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
