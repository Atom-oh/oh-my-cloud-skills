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
import hashlib

# Neutralize system/global git config when reading an untrusted worktree.
# os.devnull (not a hard-coded "/dev/null") so this also holds on Windows.
# GIT_PAGER=cat defuses a peer-planted core.pager/pager.<cmd> command (git would otherwise
# exec the pager on some operations).
_CLEAN_ENV = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
              "GIT_ATTR_NOSYSTEM": "1", "GIT_PAGER": "cat", "GIT_OPTIONAL_LOCKS": "0"}


def git(cwd, *args, env=None):
    return subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, env=env)


# `capture-diff` must survive the peer committing inside the worktree (workspace-write
# implementers can run `git commit` via bash). Diffing "index vs current HEAD" goes silently
# empty once HEAD has moved past the SHA the worktree was created from — the peer's whole
# change is dropped with exit 0. Fix: `add` resolves --base to an absolute SHA and records it
# HOST-side, in the MAIN repo's git-dir (never the worktree's own private admin subdir, e.g.
# `.git/worktrees/<name>/`, and never inside the working tree). The peer's sandbox is scoped
# to the worktree's working directory — a marker living one level up, in the worktree's own
# admin area, is still reachable via `git -C <wt> rev-parse --git-dir` and we don't provably
# assert the sandbox blocks writing there (see the module docstring); putting it in the HOST's
# git-dir instead means "reachable from inside the worktree" is no longer the question — it's
# simply not on any path the worktree resolves to. `capture-diff` then diffs the index against
# that recorded base, not implicit HEAD, so it captures everything since creation whether the
# peer committed, left it uncommitted, or both. Keyed by a hash of the worktree's absolute
# path so concurrent worktrees don't collide.
_BASE_MARKER_DIR = "co-agent-worktree-bases"


def _base_marker_path(root, wt):
    gd = git(root, "rev-parse", "--git-dir", env=_CLEAN_ENV)
    if gd.returncode != 0:
        return None
    d = gd.stdout.strip()
    d = d if os.path.isabs(d) else os.path.join(root, d)
    key = hashlib.sha256(os.path.abspath(wt).encode()).hexdigest()[:16]
    return os.path.join(d, _BASE_MARKER_DIR, f"{key}.sha")


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
        # Resolve --base to an absolute SHA BEFORE checkout, from the main repo (root) — "HEAD"
        # is relative to whichever tree resolves it, and once the worktree exists its own HEAD
        # is what we're trying to pin down, not what we'd get by re-resolving "HEAD" there.
        rp = git(root, "rev-parse", "--verify", base, env=_CLEAN_ENV)
        if rp.returncode != 0:
            sys.stderr.write(rp.stderr)
            return rp.returncode
        base_sha = rp.stdout.strip()
        # Neutralize core.hooksPath/fsmonitor (+ clean env) so a post-checkout hook or fsmonitor
        # command a peer planted via shared repo/global config can't execute at checkout time.
        r = git(root, "-c", f"core.hooksPath={os.devnull}", "-c", "core.fsmonitor=",
                "worktree", "add", wt, base_sha, env=_CLEAN_ENV)
        sys.stderr.write(r.stderr)
        if r.returncode != 0:
            return r.returncode
        marker = _base_marker_path(root, wt)
        if marker:
            try:
                os.makedirs(os.path.dirname(marker), exist_ok=True)
                with open(marker, "w", encoding="utf-8") as f:
                    f.write(base_sha + "\n")
            except OSError as e:
                sys.stderr.write(f"warning: could not record base SHA for capture-diff: {e}\n")
        return 0

    if cmd == "capture-diff":
        if len(argv) < 2:
            print("usage: worktree.py capture-diff <wt_path>", file=sys.stderr)
            return 2
        wt = argv[1]
        # Diff against the SHA recorded at `add` time, not implicit HEAD — HEAD may have moved
        # if the peer committed inside the worktree (see _BASE_MARKER note above). Missing
        # marker (worktree predates this fix, or the write failed) falls back to the old
        # HEAD-relative behavior — surfaced on stderr since it can silently miss peer commits.
        base_ref = "HEAD"
        marker = _base_marker_path(root, wt)
        if marker and os.path.isfile(marker):
            with open(marker, encoding="utf-8") as f:
                base_ref = f.read().strip() or "HEAD"
        else:
            sys.stderr.write("warning: no recorded base SHA for this worktree — diffing "
                              "against HEAD, which misses any peer commit inside the worktree\n")
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
        # Unstage tracked-but-ignored files — reset to base_ref, NOT bare HEAD. A bare
        # `git reset -- <path>` restores the INDEX to current HEAD's version of that path,
        # which still carries it forward if the peer committed (or modified) an ignored file
        # AFTER base_ref: HEAD then has content base_ref never did, and resetting to HEAD
        # keeps exactly that content staged, so the final `diff --cached base_ref` still
        # shows it. Resetting to base_ref instead removes the path from the index entirely
        # when base_ref never had it (git's `reset <commit> -- <path>` behavior for a path
        # absent from <commit>), so it can never appear in the base_ref-relative diff.
        ig = git(wt, "ls-files", "--cached", "-i", "--exclude-standard", env=_CLEAN_ENV)
        ignored = [p for p in ig.stdout.splitlines() if p]
        if ignored:
            git(wt, "reset", "-q", base_ref, "--", *ignored, env=_CLEAN_ENV)
        # --no-ext-diff blocks external diff *command* drivers; --no-textconv blocks textconv
        # (NOT covered by --no-ext-diff); attributesFile=/dev/null + clean env + neutralizers
        # drop all remaining config/attribute influence.
        r = git(wt, "-c", f"core.attributesFile={os.devnull}", *nf,
                "diff", "--cached", base_ref, "--no-ext-diff", "--no-textconv", "--binary", env=_CLEAN_ENV)
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
        # Marker lives host-side (see _base_marker_path) — the worktree's own removal never
        # cleans it up; do it here so these don't accumulate across the harness's lifetime.
        marker = _base_marker_path(root, wt)
        if marker and os.path.isfile(marker):
            try:
                os.remove(marker)
            except OSError:
                pass
        return r.returncode

    if cmd == "prune":
        git(root, "worktree", "prune")
        return 0

    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
