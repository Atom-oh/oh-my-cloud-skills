#!/usr/bin/env python3
"""Scope-lock for the consensus P3 implement loop: a candidate file path is allowed
only if it is in the plan's declared file set (the union of every task's Create/Modify/
Test paths, via parse_plan). Used before any autonomous edit so the loop can't sprawl
beyond the reviewed plan.

Usage:
  scope_guard.py --plan <plan.md> <path>...   # exit 0 if ALL paths in scope, else 1
  scope_guard.py --plan <plan.md> --list      # print the allowed file set
Exit 0 = all in scope / list ok · 1 = at least one out of scope · 2 = usage/read error.
"""
import sys
import os
import posixpath

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import parse_plan  # sibling module (Stage A)


def _norm(p):
    """Normalize a path for scope comparison. Uses posixpath.normpath (which correctly
    collapses interior './' and '../' segments) instead of a blind lstrip("./") — lstrip
    strips *any* run of '.' and '/' characters, so "../../src/foo.py" was collapsing to
    "src/foo.py" and matching a plan that never declared it. normpath leaves a genuine
    escape (leading '..') intact so callers can detect and reject it."""
    p = p.strip().replace("\\", "/")
    if not p:
        return p
    return posixpath.normpath(p)


def allowed_set(plan_path):
    with open(plan_path, encoding="utf-8") as f:
        tasks = parse_plan.parse(f.read())
    files = []
    for t in tasks:
        for fp in t["files"]:
            n = _norm(fp)
            if n and n not in files:
                files.append(n)
    return files


def main():
    args = sys.argv[1:]
    if "--plan" not in args:
        print(__doc__)
        return 2
    plan_flag = args.index("--plan")
    plan = args[plan_flag + 1] if plan_flag + 1 < len(args) else None
    if not plan:
        print("--plan requires a path", file=sys.stderr)
        return 2
    try:
        allowed = allowed_set(plan)
    except (OSError, UnicodeDecodeError) as e:
        print(f"❌ cannot read plan {plan}: {e}", file=sys.stderr)
        return 2

    # Only `--plan <value>` is a real option here; every other arg is a candidate path.
    # Remove exactly the two tokens `--plan <value>` BY POSITION, not by value — a
    # value-based filter (`a != plan`) also dropped any CANDIDATE whose path happened to
    # equal the plan path, silently excluding it from the scope check. A candidate that
    # itself starts with `--` (e.g. a file literally named "--foo.py") must be REJECTED
    # as out-of-scope, not silently dropped — dropping it would bypass the gate entirely.
    rest = [a for i, a in enumerate(args) if i not in (plan_flag, plan_flag + 1)]

    # `--list` is list-mode ONLY when it's the sole remaining argument. A bare
    # `"--list" in args` checked before candidate validation let a candidate path
    # literally named "--list" flip the whole invocation into list mode and exit 0 —
    # skipping the scope check for EVERY other candidate in the same call (a real gate
    # bypass, not just an odd filename: exit 0 is read as "all in scope").
    if rest == ["--list"]:
        print("\n".join(allowed))
        return 0
    dashed = [a for a in rest if a.startswith("--")]
    paths = [a for a in rest if not a.startswith("--")]
    if not paths and not dashed:
        print("no candidate paths given", file=sys.stderr)
        return 2
    if dashed:
        print("❌ out of plan scope (option-like paths are rejected, not scope-checked):",
              file=sys.stderr)
        for p in dashed:
            print(f"   • {p}", file=sys.stderr)
        return 1
    allowed_norm = {_norm(a) for a in allowed}

    def in_scope(c):
        cn = _norm(c)
        # Fail closed on any path that still escapes upward after normalization — never
        # fall through to the suffix match below for these ("../../src/foo.py" must not
        # sneak in just because it happens to end with an allowed entry).
        if cn.startswith(".."):
            return False
        # The suffix match below exists ONLY so an ABSOLUTE candidate (e.g. git handing us
        # "/repo/src/foo.py") still matches a relative plan entry "src/foo.py". A RELATIVE
        # candidate must match exactly — otherwise "attacker/src/foo.py" would pass just
        # because it ends with an allowed "src/foo.py", letting a worktree-generated path
        # outside the plan's declared set through (the exact guarantee this gate makes).
        is_abs = c.strip().replace("\\", "/").startswith("/")
        for a in allowed_norm:
            if cn == a:
                return True
            # Absolute-candidate-only suffix match. Only when the allowed entry HAS a
            # directory component — a bare filename (e.g. "Makefile") must match exactly,
            # or "/anything/Makefile" would match too.
            if is_abs and "/" in a and cn.endswith("/" + a):
                return True
        return False
    out = [p for p in paths if not in_scope(p)]
    if out:
        print("❌ out of plan scope (not in the reviewed plan's file set):", file=sys.stderr)
        for p in out:
            print(f"   • {p}", file=sys.stderr)
        return 1
    print(f"✅ all {len(paths)} path(s) within plan scope")
    return 0


if __name__ == "__main__":
    sys.exit(main())
