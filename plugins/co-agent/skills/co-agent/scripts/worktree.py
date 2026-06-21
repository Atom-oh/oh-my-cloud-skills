#!/usr/bin/env python3
"""Isolated git-worktree helper for the co-agent:harness delegated-implement path.

A worktree isolates the git working tree but is NOT a security sandbox; combine it
with a workspace-write CLI sandbox (see `co_agent_config.py impl-flags`). `capture-diff`
stages only non-ignored changes (`git add -A` respects `.gitignore`) so a `.gitignore`'d
file a peer creates can never be carried into the main tree.

Usage:
  worktree.py add <wt_path> --base <ref> [--root DIR]
  worktree.py capture-diff <wt_path>
  worktree.py remove <wt_path> [--root DIR]
  worktree.py prune [--root DIR]

Exit: 0 ok · 2 usage error · git's return code on failure.
"""
import os
import sys
import subprocess

# Neutralize system/global git config when reading an untrusted worktree.
_CLEAN_ENV = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null"}


def git(cwd, *args, env=None):
    return subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, env=env)


def main():
    argv = sys.argv[1:]
    root = "."
    if "--root" in argv:
        i = argv.index("--root")
        root = argv[i + 1]
        del argv[i:i + 2]
    if not argv:
        print(__doc__)
        return 2
    cmd = argv[0]

    if cmd == "add":
        if len(argv) < 2:
            print("usage: worktree.py add <wt_path> --base <ref>", file=sys.stderr)
            return 2
        wt = argv[1]
        base = "HEAD"
        if "--base" in argv:
            bi = argv.index("--base") + 1
            if bi >= len(argv):
                print("usage: worktree.py add <wt_path> --base <ref>", file=sys.stderr)
                return 2
            base = argv[bi]
        r = git(root, "worktree", "add", wt, base)
        sys.stderr.write(r.stderr)
        return r.returncode

    if cmd == "capture-diff":
        if len(argv) < 2:
            print("usage: worktree.py capture-diff <wt_path>", file=sys.stderr)
            return 2
        wt = argv[1]
        # Reset the index first so a peer's pre-staged `git add -f <ignored>` can't sneak in.
        rst = git(wt, "reset", "-q", env=_CLEAN_ENV)
        if rst.returncode != 0:
            sys.stderr.write(rst.stderr)
            return rst.returncode
        add = git(wt, "add", "-A", env=_CLEAN_ENV)   # respects .gitignore for untracked
        if add.returncode != 0:                      # surface failures — never emit a stale diff
            sys.stderr.write(add.stderr)
            return add.returncode
        # Unstage tracked-but-ignored files (committed before being gitignored).
        ig = git(wt, "ls-files", "--cached", "-i", "--exclude-standard", env=_CLEAN_ENV)
        ignored = [p for p in ig.stdout.splitlines() if p]
        if ignored:
            git(wt, "reset", "-q", "--", *ignored, env=_CLEAN_ENV)
        # --no-ext-diff blocks external diff drivers (.gitattributes / diff.external RCE);
        # attributesFile=/dev/null + clean env drop system/global influence.
        r = git(wt, "-c", "core.attributesFile=/dev/null",
                "diff", "--cached", "--no-ext-diff", "--binary", env=_CLEAN_ENV)
        sys.stdout.write(r.stdout)
        return r.returncode

    if cmd == "remove":
        if len(argv) < 2:
            print("usage: worktree.py remove <wt_path>", file=sys.stderr)
            return 2
        wt = argv[1]
        r = git(root, "worktree", "remove", "--force", wt)
        git(root, "worktree", "prune")
        sys.stderr.write(r.stderr)
        return r.returncode

    if cmd == "prune":
        git(root, "worktree", "prune")
        return 0

    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
