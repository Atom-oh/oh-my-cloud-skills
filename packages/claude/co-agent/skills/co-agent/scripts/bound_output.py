#!/usr/bin/env python3
"""Bound each peer's fan-out response before it reaches the host's context.

The input-side budget machinery (`fits`/`max_calls`/`context_limit`) already caps what
goes OUT to each peer. Nothing capped what came BACK — every `$RUN/<ai>-<n>.md` file was
read in full for synthesis, unbounded. This applies each AI's `response_limit`
(`co_agent_config.py set <ai> response_limit <n>`, lines; 0/unset = no check) the same
way `fits` applies `context_limit`: advisory, never a hard truncation the peer CLI
itself is told to apply — the CLI already ran and wrote its file before this runs.

A response within budget is printed in full. One over budget is excerpted (head + tail,
so a lede AND a conclusion survive) with the full file's path named, so the host reads
the long form only when it actually needs it — never invented, never silently dropped.

Usage:
  bound_output.py <run_dir> [--host <claude|codex>] [--root <repo>]
    Scans <run_dir> for "<ai>-*.md"/"<ai>-*.txt" slot files (the fan-out's own naming
    convention, see references/ai-cli-adapters.md), applies each ai's response_limit,
    and prints one bounded section per file, in filename order.
  bound_output.py --file <path> --ai <ai> [--host ...] [--root ...]
    Bound a single file explicitly (same output, for a caller that names its own files).

Exit 0 on normal output (including "nothing to bound" — an empty run_dir prints
nothing and exits 0, matching the fan-out's "empty/skipped" convention). Exit 2 on
usage error. Never exits non-zero over a peer's response shape — an unreadable slot
file is reported and skipped, not fatal to the others.
"""
import argparse
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
from co_agent_host import ACTIVE_PEERS, detect_host  # noqa: E402
import co_agent_config as cfg_mod  # noqa: E402



def ai_for_filename(name):
    """Longest ACTIVE_PEERS id that is a prefix of `name` up to a following '-' or '.'
    — the fan-out names slots "<ai>-<n>.<ext>" (e.g. "kiro-cli-1.md"); "kiro-cli" itself
    contains a hyphen, so a naive split on the first '-' would misparse it as "kiro"."""
    best = None
    for ai in ACTIVE_PEERS:
        if name == ai or name.startswith(ai + "-") or name.startswith(ai + "."):
            if best is None or len(ai) > len(best):
                best = ai
    return best


def response_limit(root, host, ai):
    try:
        return int(cfg_mod.effective(root)["panel"].get(ai, {}).get("response_limit", 0) or 0)
    except (OSError, ValueError, TypeError):
        return 0  # unreadable/malformed config → advisory check never blocks


def bound_text(text, limit):
    """(bounded_text, was_excerpted). limit<=0 means no check. The excerpt itself is
    sized FROM the limit (2/3 head, 1/3 tail, each at least 1 line) — a fixed head/tail
    size regardless of `limit` would let a small budget's "excerpt" exceed the budget
    it exists to enforce."""
    lines = text.splitlines()
    if limit <= 0 or len(lines) <= limit:
        return text, False
    head_n = max(1, limit * 2 // 3)
    tail_n = max(1, limit - head_n)
    head = lines[:head_n]
    tail = lines[-tail_n:] if tail_n < len(lines) - head_n else []
    excerpt = head + [f"… {len(lines) - len(head) - len(tail)} lines omitted …"] + tail
    return "\n".join(excerpt), True


def bound_file(path, ai, root, host):
    limit = response_limit(root, host, ai)
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError as exc:
        print(f"=== {ai} ({os.path.basename(path)}): unreadable ({exc}); skipped ===")
        return
    bounded, excerpted = bound_text(text, limit)
    lines = text.count("\n") + 1 if text else 0
    if excerpted:
        print(f"=== {ai} ({os.path.basename(path)}, {lines} lines > {limit}-line budget "
              f"— excerpted; full text: {path}) ===")
    else:
        print(f"=== {ai} ({os.path.basename(path)}, {lines} lines) ===")
    print(bounded)
    print()


def main():
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("run_dir", nargs="?")
    p.add_argument("--file")
    p.add_argument("--ai")
    p.add_argument("--host")
    p.add_argument("--root", default=os.getcwd())
    args, unknown = p.parse_known_args()
    if unknown:
        print(f"unrecognized arguments: {' '.join(unknown)}", file=sys.stderr)
        return 2
    host = detect_host(args.host)

    if args.file:
        if not args.ai:
            print("--file requires --ai", file=sys.stderr)
            return 2
        bound_file(args.file, args.ai, args.root, host)
        return 0

    if not args.run_dir:
        print(__doc__, file=sys.stderr)
        return 2
    if not os.path.isdir(args.run_dir):
        print(f"not a directory: {args.run_dir}", file=sys.stderr)
        return 2
    for name in sorted(os.listdir(args.run_dir)):
        if not (name.endswith(".md") or name.endswith(".txt")):
            continue
        ai = ai_for_filename(name)
        if ai is None:
            continue  # not a peer slot file (e.g. a synthesized digest) — leave it alone
        bound_file(os.path.join(args.run_dir, name), ai, args.root, host)
    return 0


if __name__ == "__main__":
    sys.exit(main())
