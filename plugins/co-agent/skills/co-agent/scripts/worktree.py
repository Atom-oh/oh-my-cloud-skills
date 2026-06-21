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
import sys
import subprocess


def git(cwd, *args):
    return subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True)


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
        base = argv[argv.index("--base") + 1] if "--base" in argv else "HEAD"
        r = git(root, "worktree", "add", wt, base)
        sys.stderr.write(r.stderr)
        return r.returncode

    if cmd == "capture-diff":
        if len(argv) < 2:
            print("usage: worktree.py capture-diff <wt_path>", file=sys.stderr)
            return 2
        wt = argv[1]
        git(wt, "add", "-A")              # respects .gitignore — ignored files not staged
        r = git(wt, "diff", "--cached")
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
