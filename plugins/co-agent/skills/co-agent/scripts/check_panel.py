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
import shutil

PEERS = ("kiro-cli", "claude", "codex", "agy", "gemini")
PEER_PLUGINS = {"codex": "openai/codex-plugin-cc"}   # peer → official Claude Code plugin repo


def detect_cli(peer):
    return shutil.which(peer)


def detect_plugin(peer, plugins_root):
    """True if the peer's official plugin appears installed under the plugin cache."""
    repo = PEER_PLUGINS.get(peer)
    if not repo or not plugins_root or not os.path.isdir(plugins_root):
        return False
    needle = repo.split("/")[-1]   # e.g. "codex-plugin-cc"
    for dirpath, dirnames, _files in os.walk(plugins_root):
        if needle in os.path.basename(dirpath) or needle in dirnames:
            return True
    return False


def decide_access(peer, has_cli, has_plugin):
    if has_plugin:
        return "plugin", False
    if has_cli:
        return "raw", peer in PEER_PLUGINS   # suggest installing the official plugin if one exists
    return "none", False

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
    if argv[0] == "--selftest-access":
        peer, hc, hp = argv[1], argv[2] == "1", argv[3] == "1"
        access, suggest = decide_access(peer, hc, hp)
        print(f"{access} {1 if suggest else 0}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
