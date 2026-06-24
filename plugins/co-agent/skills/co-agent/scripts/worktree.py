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
# os.devnull (not a hard-coded "/dev/null") so this also holds on Windows.
# GIT_PAGER=cat defuses a peer-planted core.pager/pager.<cmd> command (git would otherwise
# exec the pager on some operations).
_CLEAN_ENV = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
              "GIT_ATTR_NOSYSTEM": "1", "GIT_PAGER": "cat", "GIT_OPTIONAL_LOCKS": "0"}


def git(cwd, *args, env=None):
    return subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, env=env)


def _capture_neutralizers(wt):
    """`-c` overrides that defuse EVERY git-config code-execution surface a peer could plant
    via in-tree `.gitattributes` + shared repo config: clean/smudge/process filters (run at
    `git add`) AND diff textconv/command drivers (run at `git diff`). We can't ignore in-tree
    `.gitattributes`, so each driver command is overridden to a pass-through / empty. Pair with
    `--no-ext-diff --no-textconv` on the diff itself. Also point `core.hooksPath` at an empty
    dir so no hook a peer planted via shared repo config can fire on any capture-stage git call.
    Also blanks `core.fsmonitor`/`core.pager` (both can name a command git would exec)."""
    ov = ["-c", f"core.hooksPath={os.devnull}", "-c", "core.fsmonitor=", "-c", "core.pager=cat"]
    for prefix, keys in (("filter", ("clean", "smudge", "process")), ("diff", ("textconv", "command"))):
        r = git(wt, "config", "--name-only", "--get-regexp", rf"^{prefix}\.", env=_CLEAN_ENV)
        names = set()
        for line in r.stdout.splitlines():
            parts = line.split(".")
            if len(parts) >= 3:                   # <prefix>.<name>.<key>; <name> may contain dots
                names.add(".".join(parts[1:-1]))
        for n in names:
            for k in keys:
                ov += ["-c", f"{prefix}.{n}.{k}=" + ("cat" if k in ("clean", "smudge") else "")]
    return ov


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
        # Neutralize core.hooksPath/fsmonitor (+ clean env) so a post-checkout hook or fsmonitor
        # command a peer planted via shared repo/global config can't execute at checkout time.
        r = git(root, "-c", f"core.hooksPath={os.devnull}", "-c", "core.fsmonitor=",
                "worktree", "add", wt, base, env=_CLEAN_ENV)
        sys.stderr.write(r.stderr)
        return r.returncode

    if cmd == "capture-diff":
        if len(argv) < 2:
            print("usage: worktree.py capture-diff <wt_path>", file=sys.stderr)
            return 2
        wt = argv[1]
        # Defuse every git-config exec surface (filters at add-time, textconv/diff drivers at
        # diff-time) BEFORE staging — both are RCE-bearing stages, not just ext-diff.
        nf = _capture_neutralizers(wt)
        # Reset the index first so a peer's pre-staged `git add -f <ignored>` can't sneak in.
        rst = git(wt, "reset", "-q", env=_CLEAN_ENV)
        if rst.returncode != 0:
            sys.stderr.write(rst.stderr)
            return rst.returncode
        add = git(wt, *nf, "add", "-A", env=_CLEAN_ENV)   # respects .gitignore for untracked
        if add.returncode != 0:                      # surface failures — never emit a stale diff
            sys.stderr.write(add.stderr)
            return add.returncode
        # Unstage tracked-but-ignored files (committed before being gitignored).
        ig = git(wt, "ls-files", "--cached", "-i", "--exclude-standard", env=_CLEAN_ENV)
        ignored = [p for p in ig.stdout.splitlines() if p]
        if ignored:
            git(wt, "reset", "-q", "--", *ignored, env=_CLEAN_ENV)
        # --no-ext-diff blocks external diff *command* drivers; --no-textconv blocks textconv
        # (NOT covered by --no-ext-diff); attributesFile=/dev/null + clean env + neutralizers
        # drop all remaining config/attribute influence.
        r = git(wt, "-c", f"core.attributesFile={os.devnull}", *nf,
                "diff", "--cached", "--no-ext-diff", "--no-textconv", "--binary", env=_CLEAN_ENV)
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
