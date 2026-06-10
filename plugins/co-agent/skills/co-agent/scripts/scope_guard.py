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

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import parse_plan  # sibling module (Stage A)


def allowed_set(plan_path):
    with open(plan_path, encoding="utf-8") as f:
        tasks = parse_plan.parse(f.read())
    files = []
    for t in tasks:
        for fp in t["files"]:
            n = fp.strip().lstrip("./")
            if n and n not in files:
                files.append(n)
    return files


def _norm(p):
    return p.strip().lstrip("./").replace("\\", "/")


def main():
    args = sys.argv[1:]
    if "--plan" not in args:
        print(__doc__)
        return 2
    plan = args[args.index("--plan") + 1] if args.index("--plan") + 1 < len(args) else None
    if not plan:
        print("--plan requires a path", file=sys.stderr)
        return 2
    try:
        allowed = allowed_set(plan)
    except (OSError, UnicodeDecodeError) as e:
        print(f"❌ cannot read plan {plan}: {e}", file=sys.stderr)
        return 2

    if "--list" in args:
        print("\n".join(allowed))
        return 0

    paths = [a for a in args if a != "--plan" and a != plan and not a.startswith("--")]
    if not paths:
        print("no candidate paths given", file=sys.stderr)
        return 2
    allowed_norm = {_norm(a) for a in allowed}
    out = [p for p in paths if _norm(p) not in allowed_norm]
    if out:
        print("❌ out of plan scope (not in the reviewed plan's file set):", file=sys.stderr)
        for p in out:
            print(f"   • {p}", file=sys.stderr)
        return 1
    print(f"✅ all {len(paths)} path(s) within plan scope")
    return 0


if __name__ == "__main__":
    sys.exit(main())
