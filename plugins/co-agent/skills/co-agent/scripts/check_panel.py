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

PEERS = ("kiro-cli", "claude", "codex", "agy")
PEER_PLUGINS = {"codex": "openai/codex-plugin-cc"}   # peer → official Claude Code plugin repo


def detect_cli(peer):
    return shutil.which(peer)


def detect_plugin(peer, plugins_root):
    """True if the peer's official plugin appears installed under the plugin cache.

    Two independent signals, either is sufficient: (1) a directory whose exact basename
    matches the official repo's own name (e.g. "codex-plugin-cc") — the literal repo-name
    convention; (2) a `marketplace.json` under plugins_root that declares a plugin entry
    named after the peer's own CLI name ("codex") *and* whose "source" directory actually
    exists on disk — the convention actually observed on a real install, where Claude Code
    names the on-disk marketplace dir after marketplace.json's own "name" field
    ("openai-codex", not the git repo's name "codex-plugin-cc") and nests the plugin itself
    under plugins/<plugin-name> ("codex"). (1) alone silently missed that genuinely-installed
    official plugin and kept prompting to (re)install it; requiring the source directory to
    exist for (2) avoids treating a bare entry name (e.g. leftover/partial metadata) as proof
    of an actual install. Malformed marketplace.json — wrong top-level type, a non-list/scalar
    "plugins" value, non-dict entries, or a non-string "source" (including the object-form
    source Claude Code marketplaces legitimately use for git-hosted plugins) — is skipped, not
    raised: this walk covers every marketplace under plugins_root, including ones this peer
    doesn't own, so one bad or differently-shaped file must not take down the whole probe.
    """
    repo = PEER_PLUGINS.get(peer)
    if not repo or not plugins_root or not os.path.isdir(plugins_root):
        return False
    needle = repo.split("/")[-1]   # e.g. "codex-plugin-cc"
    for dirpath, dirnames, filenames in os.walk(plugins_root):
        if os.path.basename(dirpath) == needle or needle in dirnames:
            return True
        if os.path.basename(dirpath) == ".claude-plugin" and "marketplace.json" in filenames:
            try:
                with open(os.path.join(dirpath, "marketplace.json"), encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(data, dict):
                continue
            marketplace_root = os.path.dirname(dirpath)
            plugins = data.get("plugins")
            if not isinstance(plugins, list):
                continue
            for entry in plugins:
                if not isinstance(entry, dict) or entry.get("name") != peer:
                    continue
                source = entry.get("source")
                if isinstance(source, str) and source and os.path.isdir(os.path.join(marketplace_root, source)):
                    return True
    return False


def decide_access(peer, has_cli, has_plugin):
    if has_plugin:
        return "plugin", False
    if has_cli:
        return "raw", peer in PEER_PLUGINS   # suggest installing the official plugin if one exists
    return "none", False

# AUTH vs ERROR only affects the diagnostic label on an already-failing (non-READY) probe —
# both are non-READY, so the gate behaves identically. We keep bare 401/403 (catches
# "got 401 from server", "server returned 403") and accept the rare cosmetic false-positive
# (e.g. "Processed 401 items") rather than miss real auth failures.
_AUTH_RE = re.compile(
    r"not logged in|unauthenticated|invalid credentials|access denied|"
    r"token expired|expired token|expiredtoken|"
    r"please (log|sign) in|run .*login|\b401\b|\b403\b|unauthorized|forbidden",
    re.I,
)


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
# NOTE: the probe runs each CLI in an isolated temp dir (not a git repo). codex exec refuses to
# run outside a trusted/git dir, so the probe — and ONLY the probe — passes --skip-git-repo-check.
# The real fan-out runs in the repo root (a git repo) and builds its command from the skill /
# ai-cli-adapters.md, not from this dict, so the flag stays probe-local.
ADAPTERS = {
    "codex":    {"argv": ["codex", "exec", "-s", "read-only", "--skip-git-repo-check", "{P}"], "channel": "stdin"},
    "agy":      {"argv": ["agy", "-p", "{P}", "--sandbox"], "channel": "stdin"},
    "claude":   {"argv": ["claude", "-p", "{P}", "--permission-mode", "plan", "--output-format", "text"], "channel": "stdin"},
    "kiro-cli": {"argv": ["kiro-cli", "chat", "{I}", "--v3", "--mode", "default",
                          "--no-interactive", "--trust-tools=fs_read", "--wrap", "never"],
                 "channel": "argv"},
}
_CAP = 64 * 1024   # output-size cap


def _kill_proc(p):
    """Kill a probe child, whole process group on POSIX. os.killpg/getpgid don't exist on
    Windows — fall back to p.kill() there instead of raising AttributeError (which the callers'
    broad excepts would swallow, leaving the child alive)."""
    try:
        if hasattr(os, "killpg") and hasattr(os, "getpgid"):
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
        else:
            p.kill()
    except Exception:
        try:
            p.kill()
        except Exception:
            pass


def probe(peer, timeout=90, nonce="STATIC"):
    # 90s, not 20s: cold-start CLIs blow far past 20s on first run — kiro auth-refresh + MCP init,
    # codex reasoning + MCP init, and agy especially (12-24s warm but a cold model load can exceed
    # 80s). 20s produced spurious TIMEOUTs on warm-usable peers. report() probes sequentially, and
    # absent peers cost nothing, so the realistic ceiling is one cold peer's load, not 5×90s. A
    # peer whose backend is mid-cold-load can still flap to TIMEOUT — re-run setup once it's warm.
    if peer not in ADAPTERS:
        return "ERROR", f"unknown peer {peer}"
    if not detect_cli(peer):
        return "ABSENT", "command not found"
    sentinel = f"COAGENT_PROBE_{nonce}"
    spec = ADAPTERS[peer]
    if spec["channel"] == "stdin":
        # Wording matters here, not just for agy's UX — "read ... on/from stdin" phrases the
        # instruction as an explicit read-action on stdin. agy's agent then appears to try to
        # actually invoke a second, literal read of stdin as a tool call; that second read hits
        # an already-fully-consumed pipe (communicate() already wrote+closed it) and hangs to the
        # full timeout every time (reproduced 7/7, deterministic, independent of stdin content —
        # confirmed via direct agy invocation outside this probe). Rephrasing as "the text you
        # received via stdin" (preposition, not a read-verb object) reproduced READY 3/3 with no
        # code change elsewhere. codex is unaffected either way (verified) — this covers both.
        prompt = "Reply with exactly the text you received via stdin, and nothing else."
        argv = [a.replace("{P}", prompt) for a in spec["argv"]]
        stdin_data = sentinel + "\n"
    else:  # argv
        inp = f"Reply with exactly this token and nothing else: {sentinel}"
        argv = [a.replace("{I}", inp) for a in spec["argv"]]
        stdin_data = ""
    with tempfile.TemporaryDirectory() as cwd:
        # Capture stdout/stderr to FILES, not PIPEs. Some peers refresh auth over the host fds
        # they were launched with (kiro here runs --auth=acp-callback host-mediated refresh);
        # replacing stdout with our own *pipe* severs that callback and the refresh hangs to the
        # full timeout (kiro: 5s with a file, TIMEOUT with a pipe). File redirection leaves no
        # reader on the other end and the auth path survives. stdin still uses a PIPE so we can
        # feed the sentinel to stdin-channel peers (codex/agy); argv-channel peers (kiro) get "".
        outp = os.path.join(cwd, ".probe_out")
        errp = os.path.join(cwd, ".probe_err")
        p = None
        try:
            with open(outp, "w") as of, open(errp, "w") as ef:
                p = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.PIPE, stdout=of,
                                     stderr=ef, text=True, start_new_session=True)
                try:
                    p.communicate(input=stdin_data, timeout=timeout)
                    timed_out = False
                except subprocess.TimeoutExpired:
                    _kill_proc(p)
                    # No pipes to drain — output is already in the files; just reap the corpse.
                    try:
                        p.communicate(timeout=5)
                    except subprocess.TimeoutExpired:
                        pass
                    timed_out = True
            with open(outp, encoding="utf-8", errors="replace") as f:
                out = f.read(_CAP)
            with open(errp, encoding="utf-8", errors="replace") as f:
                err = f.read(_CAP)
            return classify(sentinel, out, err, p.returncode, timed_out)
        except FileNotFoundError:
            return "ABSENT", "command not found"
        except Exception as e:  # never hard-fail a probe
            return "ERROR", str(e)[:200]
        finally:
            # Ensure no detached child survives an error path other than TimeoutExpired
            # (e.g. communicate raising mid-read) — Windows-safe kill (see _kill_proc).
            if p is not None and p.poll() is None:
                _kill_proc(p)


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


def _peer_entry(peer, plugins_root):
    """Build one peer's readiness entry (the probe is the slow part). Pure per-peer — safe to
    run concurrently across peers."""
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
    return entry


def report(root, plugins_root, as_json=False):
    # Probe peers SEQUENTIALLY, not concurrently. Peers commonly share one model backend (e.g.
    # codex/kiro/agy all on amazon-bedrock here); firing all probes at once throttles that backend
    # and pushes every call past its timeout — peers that pass alone (kiro ~5s, agy ~24s) all
    # flapped to TIMEOUT when probed in parallel. Sequential gives each probe the full backend.
    # Absent peers return instantly (no CLI), so the realistic cost is the sum of installed peers'
    # actual response times (~tens of seconds), not 5×timeout.
    peers = {peer: _peer_entry(peer, plugins_root) for peer in PEERS}
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
    """True iff the saved summary's config_hash matches the current effective config; callers
    re-run `/co-agent:setup` on a mismatch. Catches CONFIG drift only — not PATH/auth/install
    (a full `report` re-probe catches those; config_hash can't see them)."""
    s = _read_summary(root)
    if not s:
        return False
    cur = _config_hash(root)
    # Can't compute current hash (config module unavailable) → don't force churn.
    return (not cur) or s.get("config_hash", "") == cur


def gate_eligible(root, peer):
    """A peer produces panel/gate output only if READY AND has a raw CLI. The fan-out calls
    raw CLIs only, so a plugin-only peer (READY, raw_cli false) is silent — the 'plugin-only
    READY but silent' bug. consensus and harness share this single predicate."""
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
