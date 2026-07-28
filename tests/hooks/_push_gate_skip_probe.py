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
    if ch._PUSH_MULTIREF_RE.search(rest) or ch._push_has_explicit_refspec(rest):
        return "skip:refspec"
    return "GATED"


def kiro_classify(cmd):
    """kiro's equivalent predicate — the two gates must agree on every case."""
    _hspec = importlib.util.spec_from_file_location(
        "hm", os.path.join(_ROOT, "plugins", "kiro", "skills", "kiro-delegate", "scripts",
                           "hook_match.py"))
    hm = importlib.util.module_from_spec(_hspec)
    _hspec.loader.exec_module(hm)
    return "skip" if hm.is_push_scope_mismatch(cmd) else "GATED"


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    both = args and args[0] == "--both"
    for cmd in (args[1:] if both else args):
        c = classify(cmd)
        if both:
            # normalize: any skip reason is a skip, so the two gates are comparable
            print(f"{'skip' if c.startswith('skip') else c} {kiro_classify(cmd)}")
        else:
            print(c)
