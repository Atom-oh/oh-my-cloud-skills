#!/usr/bin/env python3
"""co-agent panel-readiness preflight: detect + probe + report per peer.

Usage:
  check_panel.py classify --sentinel S --exit N --timeout 0|1   # stdin = candidate stdout
  check_panel.py report [--root DIR] [--json]
  check_panel.py status <peer> [--root DIR]
  check_panel.py access <peer> [--root DIR]
  check_panel.py gate-eligible <peer> [--root DIR]   # exit 0 + "true" iff READY AND raw_cli
  check_panel.py fresh [--root DIR]                  # exit 0 iff summary config_hash matches current
"""
import sys
import os
import re
import shutil
import subprocess
import tempfile
import signal
import json
import datetime
import hashlib

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
try:
    import co_agent_config  # sibling — for config_hash
except Exception:
    co_agent_config = None

SCHEMA_VERSION = 1

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
        if os.path.basename(dirpath) == needle or needle in dirnames:
            return True
    return False


def decide_access(peer, has_cli, has_plugin):
    if has_plugin:
        return "plugin", False
    if has_cli:
        return "raw", peer in PEER_PLUGINS   # suggest installing the official plugin if one exists
    return "none", False

_AUTH_RE = re.compile(r"not logged in|unauthenticated|please (log|sign) in|run .*login|\b401\b|\b403\b|forbidden", re.I)


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
    "claude":   {"argv": ["claude", "-p", "{P}", "--permission-mode", "plan", "--output-format", "text"], "channel": "stdin"},
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


def _config_hash(root):
    if co_agent_config is None:
        return ""
    try:
        blob = json.dumps(co_agent_config.effective(root), sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()[:16]
    except Exception:
        return ""


def _summary_path(root):
    return os.path.join(root, ".claude", "co-agent-panel.local.json")


def _atomic_write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def report(root, plugins_root, as_json=False):
    peers = {}
    for peer in PEERS:
        cli = detect_cli(peer)
        has_plugin = detect_plugin(peer, plugins_root)
        access, suggest = decide_access(peer, bool(cli), has_plugin)
        # raw_cli is recorded independently of access so a peer that has BOTH the official
        # plugin AND a raw CLI stays implementer-eligible (the implementer gate needs a raw
        # write-mode CLI, which access=="plugin" alone would otherwise hide).
        entry = {"access": access, "raw_cli": bool(cli)}
        if access == "plugin":
            entry["plugin"] = PEER_PLUGINS.get(peer)
            if cli:
                # also has a raw CLI → probe it so its raw usability (implementer gate) is known
                status, reason = probe(peer)
                entry["status"] = status
                entry["cli_path"] = cli
                if reason:
                    entry["reason"] = reason
            else:
                entry["status"] = "READY"   # plugin-only: the plugin handles ingestion
        elif access == "raw":
            status, reason = probe(peer)
            entry["status"] = status
            entry["cli_path"] = cli
            if reason:
                entry["reason"] = reason
            if suggest:
                entry["suggest_install"] = PEER_PLUGINS.get(peer)
        else:
            entry["status"] = "ABSENT"
        peers[peer] = entry
    summary = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.datetime.now().astimezone().isoformat(),
        "config_hash": _config_hash(root),
        "peers": peers,
    }
    _atomic_write_json(_summary_path(root), summary)
    if as_json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(f"{'peer':10} {'access':7} {'status':10} note")
        for peer, e in peers.items():
            note = e.get("suggest_install") or e.get("reason") or e.get("plugin") or ""
            print(f"{peer:10} {e['access']:7} {e['status']:10} {note}")
    return 0


def _read_summary(root):
    p = _summary_path(root)
    if not os.path.isfile(p):
        return None
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _reader(root, peer, field, default):
    s = _read_summary(root)
    if not s:
        return default
    return s.get("peers", {}).get(peer, {}).get(field, default)


def is_fresh(root):
    """True iff the saved summary's config_hash still matches the current effective config.

    The summary records config_hash but nothing consumed it, so a config/host/auth change
    could leave a stale READY in place. Callers run `fresh` before trusting readiness and
    re-run `/co-agent:setup` (re-probe) on a mismatch.
    """
    s = _read_summary(root)
    if not s:
        return False
    saved = s.get("config_hash", "")
    cur = _config_hash(root)
    # If we can't compute a current hash (config module unavailable), don't force churn.
    return (not cur) or saved == cur


def gate_eligible(root, peer):
    """A peer can produce panel/gate output only if it is READY AND has a raw CLI.

    The bash fan-out invokes raw CLIs only (Tier-1 plugin routing is not wired), so a
    plugin-only peer (status READY, raw_cli false) would contribute zero output — counting
    it toward a non-degraded gate is the 'plugin-only READY but silent' bug. Both
    consensus and harness must share this single predicate.
    """
    s = _read_summary(root)
    if not s:
        return False
    e = s.get("peers", {}).get(peer, {})
    return e.get("status") == "READY" and bool(e.get("raw_cli"))


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
    if argv[0] == "report":
        root = argv[argv.index("--root") + 1] if "--root" in argv else "."
        proot = argv[argv.index("--plugins-root") + 1] if "--plugins-root" in argv else os.path.expanduser("~/.claude/plugins")
        return report(root, proot, as_json="--json" in argv)
    if argv[0] in ("status", "access"):
        peer = argv[1]
        root = argv[argv.index("--root") + 1] if "--root" in argv else "."
        default = "ABSENT" if argv[0] == "status" else "none"
        print(_reader(root, peer, argv[0], default))
        return 0
    if argv[0] == "gate-eligible":
        peer = argv[1]
        root = argv[argv.index("--root") + 1] if "--root" in argv else "."
        ok = gate_eligible(root, peer)
        print("true" if ok else "false")
        return 0 if ok else 1
    if argv[0] == "fresh":
        root = argv[argv.index("--root") + 1] if "--root" in argv else "."
        ok = is_fresh(root)
        print("fresh" if ok else "stale")
        return 0 if ok else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
