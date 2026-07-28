#!/usr/bin/env python3
"""Run-telemetry helpers for the `/kiro:delegate` pipeline — the two things the delegate
loop needs from a finished kiro-cli call that the CLI won't hand back structurally.

kiro-cli headless has no `--output-format json` (upstream: kiro#5423) and no headless
session-id/credit JSON (kiro#9066), so both of these read what IS available today: the
`--list-sessions --format json` store, and the human-readable log the caller already
redirects to a file (mandatory — a pipe severs kiro's `--auth=acp-callback` refresh).

Usage:
  kiro_run.py session-id <dir>      # newest sessionId kiro-cli recorded for cwd=<dir>,
                                    # or nothing (exit 1) if there is none. Feed it to
                                    # `kiro-cli chat --resume-id <id>` so a fix round
                                    # continues the SAME conversation instead of
                                    # re-reading the whole task from scratch.
  kiro_run.py credits <log>...      # sum the `Credits: <n>` figures kiro-cli prints in
                                    # its own turn footer across one or more captured
                                    # logs; prints the total (2 dp) or nothing.
                                    # Best-effort telemetry for the delegation-rate
                                    # report — exit 1 with no output if the footer
                                    # format changed, never an error.
"""
import sys
import os
import re
import json
import shutil
import subprocess
import tempfile

# kiro-cli colorizes its turn footer even when stdout is a redirected file, so strip
# escapes before matching (same reason kiro_review.py strips them before JSON-scanning).
_ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b[@-Z\\-_]")
# The footer looks like `▸ Credits: 0.27 • Time: 3s` (observed on 2.11.1). Matching only
# the labelled number keeps this from picking up prose in the model's own output.
_CREDITS = re.compile(r"\bCredits:\s*([0-9]+(?:\.[0-9]+)?)")


def session_id(directory):
    """Newest sessionId kiro-cli recorded for cwd=`directory`. Each delegate task runs in
    its own worktree, so the cwd→session mapping is unambiguous — no upstream session-id
    JSON needed. Prints the id and exits 0, or prints nothing and exits 1 (caller must
    then just start a fresh conversation, never fail the task over this)."""
    if not shutil.which("kiro-cli"):
        return 1
    real = os.path.realpath(directory)
    with tempfile.TemporaryDirectory() as td:
        outp = os.path.join(td, ".out")
        try:
            # `--list-sessions` reports sessions for the CWD IT RUNS IN, and its JSON is
            # keyed by cwd — run it in `directory` and still match the key, so a build
            # that only ever reports its own cwd and one that reports all cwds both work.
            # Capture to a FILE, not a pipe (auth-callback, see the module docstring).
            with open(outp, "w") as of:
                r = subprocess.run(["kiro-cli", "chat", "--list-sessions", "--format", "json"],
                                    cwd=directory, stdin=subprocess.DEVNULL, stdout=of,
                                    stderr=subprocess.DEVNULL, timeout=30)
            with open(outp, encoding="utf-8", errors="replace") as f:
                data = json.loads(_ANSI.sub("", f.read()))
        except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError, ValueError):
            return 1
        if r.returncode != 0 or not isinstance(data, list):
            return 1
    best = None
    for group in data:
        if not isinstance(group, dict):
            continue
        if os.path.realpath(str(group.get("cwd", ""))) != real:
            continue
        for s in group.get("sessions") or []:
            if not isinstance(s, dict) or not s.get("sessionId"):
                continue
            # Sort by updatedAt (ISO-8601 UTC, so lexicographic == chronological); a
            # session with no timestamp loses to any that has one rather than winning by
            # arriving last in the list.
            key = str(s.get("updatedAt") or "")
            if best is None or key > best[0]:
                best = (key, str(s["sessionId"]))
    if best is None:
        return 1
    print(best[1])
    return 0


def credits(paths):
    """Sum every `Credits: <n>` in the given captured logs. Best-effort by contract: the
    delegation-rate report omits the figure rather than claiming a wrong one, so an
    unreadable log or a changed footer format is exit 1 with no output, never a crash."""
    total = 0.0
    found = False
    for p in paths:
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                text = _ANSI.sub("", f.read())
        except OSError:
            continue
        for m in _CREDITS.finditer(text):
            try:
                total += float(m.group(1))
                found = True
            except ValueError:
                continue
    if not found:
        return 1
    print(f"{total:.2f}")
    return 0


def main():
    argv = sys.argv[1:]
    if len(argv) >= 2 and argv[0] == "session-id":
        return session_id(argv[1])
    if len(argv) >= 2 and argv[0] == "credits":
        return credits(argv[1:])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
