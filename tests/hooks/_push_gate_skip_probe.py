#!/usr/bin/env python3
"""Print how co-agent's push gate classifies a few commands, for test-push-gate.sh.

The two hooks that intercept `git push` (co-agent's push_gate, kiro's pre-push-review)
must agree on what they cannot review: a push redirected at another repo/work tree would
be reviewed against the WRONG root, and a ref-deletion push has no content to review.
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
    """Mirror ev_pre_push_gate's skip ordering, without running the gate itself."""
    detect = re.sub(r"'[^']*'|\"[^\"]*\"", lambda mm: " " * len(mm.group()), cmd)
    m = ch._GIT_PUSH_CMD_RE.search(detect)
    if not m:
        return "not-a-push"
    if ch._PUSH_REDIRECT_RE.search(m.group()):
        return "skip:redirect"
    rest = re.split(r"[;&|\n]", detect[m.end():], 1)[0]
    if ch._PUSH_DELETE_RE.search(rest):
        return "skip:delete"
    return "GATED"


if __name__ == "__main__":
    import sys
    for cmd in sys.argv[1:]:
        print(classify(cmd))
