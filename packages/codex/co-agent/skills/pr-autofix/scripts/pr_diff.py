#!/usr/bin/env python3
"""Capture a pinned PR diff without GitHub's diff API file-count limit."""

import argparse
import os
from pathlib import Path
import re
import subprocess
import tempfile


class DiffError(RuntimeError):
    pass


def git(repo, *args, stdout=None):
    # Do not inherit an alternate Git directory or an external diff command.
    env = {key: value for key, value in os.environ.items()
           if key not in {
               "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",
               "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
               "GIT_NAMESPACE", "GIT_EXTERNAL_DIFF", "GIT_DIFF_OPTS",
               "GIT_CONFIG", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT",
           } and not re.fullmatch(r"GIT_CONFIG_(?:KEY|VALUE)_\d+", key)}
    result = subprocess.run(
        ["git", "--no-pager", "-c", "core.hooksPath=/dev/null",
         "-c", "core.fsmonitor=false", "-c", "core.attributesFile=/dev/null",
         "-c", "protocol.ext.allow=never", "-C", str(repo), *args],
        stdout=stdout if stdout is not None else subprocess.PIPE,
        stderr=subprocess.PIPE, env=env, check=False,
    )
    if result.returncode:
        # A remote's diagnostic can contain its URL; never echo credentials.
        raise DiffError(f"git {args[0]} failed (exit {result.returncode})")
    return result.stdout.decode("utf-8").strip() if stdout is None else None


def capture(repo, base, head, output, verify_base_checkout=False):
    if not all(re.fullmatch(r"[0-9a-f]{40}", sha) for sha in (base, head)):
        raise DiffError("base and head must be full lowercase commit SHAs")
    repo = Path(repo).resolve()
    output = Path(output)
    if output.is_symlink():
        raise DiffError("output must not be a symlink")
    checkout = git(repo, "rev-parse", "--verify", "HEAD")
    if verify_base_checkout and checkout != base:
        raise DiffError("trusted checkout does not match the requested base")
    fetch = ["fetch", "--quiet", "--no-tags"]
    if git(repo, "rev-parse", "--is-shallow-repository") == "true":
        fetch.append("--unshallow")
    # Fetch objects only. No PR checkout, hooks, external diff or textconv runs.
    git(repo, *fetch, "origin", base, head)
    for sha in (base, head):
        if git(repo, "rev-parse", "--verify", sha + "^{commit}") != sha:
            raise DiffError("requested SHA does not identify a commit")
    git(repo, "merge-base", base, head)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
                dir=output.parent, prefix=".pr-diff-", delete=False) as stream:
            temporary = Path(stream.name)
            git(repo, "diff", "--no-ext-diff", "--no-textconv", "--no-color",
                "--full-index", "--no-renames", "--submodule=short",
                "--src-prefix=a/", "--dst-prefix=b/",
                f"{base}...{head}", "--", stdout=stream)
        if git(repo, "rev-parse", "--verify", "HEAD") != checkout:
            raise DiffError("checkout changed while capturing the diff")
        temporary.replace(output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--verify-base-checkout", action="store_true")
    args = parser.parse_args()
    try:
        capture(args.repo, args.base, args.head, args.output,
                args.verify_base_checkout)
    except (DiffError, OSError) as error:
        parser.exit(1, f"PR diff capture failed: {error}\n")


if __name__ == "__main__":
    main()
