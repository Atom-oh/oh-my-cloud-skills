#!/usr/bin/env python3
"""Print how co-agent's push gate classifies a few commands, for test-push-gate.sh.

Redirected pushes must not be reviewed against the wrong root; ref deletions
have no content to review.
Loaded by path because consensus_hooks.py lives outside any importable package.
"""
import importlib.util
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_spec = importlib.util.spec_from_file_location(
    "ch", os.path.join(_ROOT, "plugins", "co-agent", "skills", "co-agent", "scripts",
                       "consensus_hooks.py"))
ch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ch)


def classify(cmd):
    """Mirror ev_pre_push_gate's skip logic, without running the gate itself. Checks
    ALL `git push` occurrences (via `_push_gate_skip_reason`, same as the real
    function — folds in the per-occurrence bypass check too) — a compound command is
    only classified as skipped if EVERY push invocation in it is itself either
    bypassed or unreviewable; a single reviewable, non-bypassed occurrence anywhere
    makes the whole command GATED."""
    detect = re.sub(r"'[^']*'|\"[^\"]*\"", lambda mm: " " * len(mm.group()), cmd)
    gms = list(ch._GIT_PUSH_CMD_RE.finditer(detect))
    if not gms:
        return "not-a-push"
    reasons = [ch._push_gate_skip_reason(detect, gm) for gm in gms]
    if not all(reasons):
        return "GATED"
    r = reasons[0]
    if "redirect" in r or "WRONG repository" in r:
        return "skip:redirect"
    if "ref-deletion" in r:
        return "skip:delete"
    if "refs the gate's range does not describe" in r:
        return "skip:refspec"
    if "dry-run" in r:
        return "skip:dry-run"
    if "bypassed" in r:
        return "skip:bypass"
    return "skip:other"


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    normalized = args and args[0] == "--normalized"
    for cmd in (args[1:] if normalized else args):
        result = classify(cmd)
        print("skip" if normalized and result.startswith("skip") else result)
