#!/usr/bin/env python3
"""co-agent panel-readiness preflight: detect + probe + report per peer.

Usage:
  check_panel.py classify --sentinel S --exit N --timeout 0|1   # stdin = candidate stdout
  check_panel.py report [--root DIR] [--json]
  check_panel.py status <peer> [--root DIR]
  check_panel.py access <peer> [--root DIR]
"""
import sys
import os
import re

_AUTH_RE = re.compile(r"not logged in|unauthenticated|please (log|sign) in|run .*login|401|auth", re.I)


def classify(sentinel, stdout, stderr, returncode, timed_out):
    """Pure: map a probe result to (status, reason)."""
    if timed_out:
        return "TIMEOUT", "probe exceeded the per-CLI timeout"
    text = (stdout or "")
    if returncode == 0 and sentinel and sentinel in text.strip().split():
        return "READY", ""
    blob = f"{stdout}\n{stderr}"
    if _AUTH_RE.search(blob):
        return "AUTH", "authentication required"
    if returncode == 0:
        return "NO_INGEST", "ran but did not echo the sentinel (input channel not consumed)"
    return "ERROR", f"exit {returncode}"


def _cmd_classify(argv):
    def opt(name, default=None):
        return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else default
    sentinel = opt("--sentinel", "")
    rc = int(opt("--exit", "0"))
    timed_out = opt("--timeout", "0") in ("1", "true", "yes")
    stdout = sys.stdin.read()
    status, _reason = classify(sentinel, stdout, "", rc, timed_out)
    print(status)
    return 0


def main():
    argv = sys.argv[1:]
    if not argv:
        print(__doc__)
        return 2
    if argv[0] == "classify":
        return _cmd_classify(argv[1:])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
