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
import subprocess
import tempfile
import signal

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


# Read-only adapters, mirroring references/ai-cli-adapters.md. "{P}" = prompt, "{I}" = INPUT (prompt+sentinel).
ADAPTERS = {
    "codex":    {"argv": ["codex", "exec", "-s", "read-only", "{P}"], "channel": "stdin"},
    "agy":      {"argv": ["agy", "-p", "{P}", "--sandbox"], "channel": "stdin"},
    "gemini":   {"argv": ["gemini", "-p", "{P}", "-o", "text"], "channel": "stdin"},
    "kiro-cli": {"argv": ["kiro-cli", "chat", "{I}", "--v3", "--mode", "default",
                          "--no-interactive", "--trust-tools=fs_read", "--wrap", "never"],
                 "channel": "argv"},
}
_CAP = 64 * 1024   # output-size cap


def probe(peer, timeout=20, nonce="STATIC"):
    if peer not in ADAPTERS:
        return "ERROR", f"unknown peer {peer}"
    if not detect_cli(peer):
        return "ABSENT", "command not found"
    sentinel = f"COAGENT_PROBE_{nonce}"
    spec = ADAPTERS[peer]
    if spec["channel"] == "stdin":
        prompt = "Read the single token provided on stdin and reply with exactly that token, nothing else."
        argv = [a.replace("{P}", prompt) for a in spec["argv"]]
        stdin_data = sentinel + "\n"
    else:  # argv
        inp = f"Reply with exactly this token and nothing else: {sentinel}"
        argv = [a.replace("{I}", inp) for a in spec["argv"]]
        stdin_data = ""
    with tempfile.TemporaryDirectory() as cwd:
        try:
            p = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, start_new_session=True)
            try:
                out, err = p.communicate(input=stdin_data, timeout=timeout)
                timed_out = False
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(p.pid), signal.SIGKILL)
                out, err = p.communicate()
                timed_out = True
            return classify(sentinel, out[:_CAP], (err or "")[:_CAP], p.returncode, timed_out)
        except FileNotFoundError:
            return "ABSENT", "command not found"
        except Exception as e:  # never hard-fail a probe
            return "ERROR", str(e)[:200]


def main():
    argv = sys.argv[1:]
    if not argv:
        print(__doc__)
        return 2
    if argv[0] == "classify":
        return _cmd_classify(argv[1:])
    if argv[0] == "probe":
        peer = argv[1]
        timeout = int(argv[argv.index("--timeout") + 1]) if "--timeout" in argv else 20
        status, _ = probe(peer, timeout=timeout)
        print(status)
        return 0
    if argv[0] == "--selftest-access":
        peer, hc, hp = argv[1], argv[2] == "1", argv[3] == "1"
        access, suggest = decide_access(peer, hc, hp)
        print(f"{access} {1 if suggest else 0}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
