#!/usr/bin/env python3
"""kiro plugin setup helpers: probe kiro-cli usability, list its models, and write the
two `.kiro/agents/*.json` custom agents the delegate/review paths invoke headlessly.

Usage:
  kiro_setup.py probe [--timeout N]                  # READY | AUTH | NO_INGEST | TIMEOUT | ERROR | ABSENT
  kiro_setup.py list-models                          # one model id per line (best-effort)
  kiro_setup.py write-agents [--root DIR] [--force]  # write .kiro/agents/kiro-{implementer,reviewer}.json

probe() statuses:
  READY      — kiro-cli echoed the sentinel; usable headlessly.
  AUTH       — an auth-required message was detected; run `kiro-cli` interactively to
               log in, or set KIRO_API_KEY, then re-probe.
  NO_INGEST  — kiro-cli exited 0 but did NOT echo the sentinel back (it ran, but its
               input channel wasn't actually consumed the way the probe expects — e.g.
               a CLI build/flag combination that silently drops the argv prompt). Treat
               the same as not-yet-usable; report it to the user rather than assuming
               READY from a zero exit code alone.
  TIMEOUT    — the probe exceeded its timeout (cold-start CLIs can be slow on first call
               — retrying once is reasonable before treating this as a real failure).
  ERROR      — kiro-cli exited non-zero for a reason other than AUTH.
  ABSENT     — kiro-cli is not on PATH.
"""
import sys
import os
import re
import json
import shutil
import subprocess
import tempfile

_AUTH_RE = re.compile(
    r"not logged in|unauthenticated|invalid credentials|access denied|"
    r"token expired|expired token|please (log|sign) in|run .*login|\b401\b|\b403\b|"
    r"unauthorized|forbidden", re.I)

_IMPLEMENTER_AGENT = {
    "name": "kiro-implementer",
    "description": "Implements tasks handed off by the /kiro:delegate pipeline, inside a "
                    "throwaway git worktree the host controls.",
    "prompt": "You implement exactly the task described in the prompt you're given, using "
              "the requirements/design/tasks spec files as context (read them with "
              "fs_read). Make the minimal change that satisfies the task. Do not touch "
              "files outside the task's declared file set. Do not run git commit — the "
              "host commits after review.",
    "tools": ["fs_read", "fs_write", "execute_bash"],
    "allowedTools": ["fs_read", "fs_write", "execute_bash"],
    "hooks": {
        "preToolUse": [
            {
                "matcher": "fs_write",
                "hooks": [
                    {
                        "type": "runCommand",
                        # Defense-in-depth on top of the host's worktree.py capture-diff +
                        # scope_guard.py (the load-bearing guarantee — see
                        # references/kiro-headless.md): refuse a write outside the cwd the
                        # implementer was launched in (the worktree). `..`/absolute-path
                        # escapes still can't reach the main tree since the host only ever
                        # applies the CAPTURED, scope-guarded diff — this hook just narrows
                        # the blast radius earlier.
                        "command": "python3 -c \"import json,sys,os; d=json.load(sys.stdin); p=(d.get('tool_input') or {}).get('path',''); sys.exit(2 if (p.startswith('/') or '..' in p.split(os.sep)) else 0)\""
                    }
                ]
            }
        ]
    }
}

_REVIEWER_AGENT = {
    "name": "kiro-reviewer",
    "description": "Reviews a diff for the /kiro:review command and the pre-commit hook. "
                    "Read-only — never writes.",
    "prompt": "You are a strict but fair code reviewer. Read the diff you're pointed to "
              "with fs_read and report findings as instructed in the prompt. Never modify "
              "any file.",
    "tools": ["fs_read"],
    "allowedTools": ["fs_read"]
}


def probe(timeout=90):
    if not shutil.which("kiro-cli"):
        return "ABSENT", "command not found"
    sentinel = "KIRO_SETUP_PROBE"
    argv = ["kiro-cli", "chat", f"Reply with exactly this token and nothing else: {sentinel}",
            "--v3", "--mode", "default", "--no-interactive", "--trust-tools=fs_read", "--wrap", "never"]
    with tempfile.TemporaryDirectory() as cwd:
        outp, errp = os.path.join(cwd, ".out"), os.path.join(cwd, ".err")
        try:
            # Capture to FILES, not PIPEs — kiro-cli's acp-callback auth refresh happens
            # over the host fds it was launched with; a pipe severs that and hangs to the
            # full timeout (see co-agent's check_panel.py probe(), same root cause).
            with open(outp, "w") as of, open(errp, "w") as ef:
                r = subprocess.run(argv, cwd=cwd, stdin=subprocess.DEVNULL, stdout=of,
                                    stderr=ef, timeout=timeout)
            with open(outp, encoding="utf-8", errors="replace") as f:
                out = f.read()
            with open(errp, encoding="utf-8", errors="replace") as f:
                err = f.read()
        except subprocess.TimeoutExpired:
            return "TIMEOUT", "probe exceeded the timeout"
        except OSError as e:
            return "ERROR", str(e)[:200]
        if r.returncode == 0 and sentinel in out.strip().split():
            return "READY", ""
        if _AUTH_RE.search(f"{out}\n{err}"):
            return "AUTH", "authentication required — run `kiro-cli` interactively to log in, or set KIRO_API_KEY"
        if r.returncode == 0:
            return "NO_INGEST", "ran but did not echo the sentinel"
        return "ERROR", f"exit {r.returncode}: {err.strip()[:200] or out.strip()[:200]}"


def list_models():
    if not shutil.which("kiro-cli"):
        print("kiro-cli not found on PATH", file=sys.stderr)
        return 2
    argv = ["kiro-cli", "chat", "--list-models", "--format", "json"]
    with tempfile.TemporaryDirectory() as cwd:
        outp, errp = os.path.join(cwd, ".out"), os.path.join(cwd, ".err")
        try:
            # Capture to FILES, not PIPEs — same reason as probe()/kiro_review.py:
            # kiro-cli's acp-callback auth refresh happens over the host fds it was
            # launched with, and a PIPE severs that, hanging this call to the full
            # timeout even when authenticated. A prior version of this function used
            # capture_output=True (a PIPE) and reintroduced exactly that bug.
            with open(outp, "w") as of, open(errp, "w") as ef:
                r = subprocess.run(argv, cwd=cwd, stdin=subprocess.DEVNULL, stdout=of,
                                    stderr=ef, timeout=30)
            with open(outp, encoding="utf-8", errors="replace") as f:
                out = f.read()
            with open(errp, encoding="utf-8", errors="replace") as f:
                err = f.read()
        except subprocess.TimeoutExpired:
            print("could not list models: kiro-cli --list-models timed out", file=sys.stderr)
            return 2
        except OSError as e:
            print(f"could not list models: {e}", file=sys.stderr)
            return 2
    if r.returncode != 0:
        print(f"kiro-cli --list-models exited {r.returncode}: {err.strip()[:300]}", file=sys.stderr)
        return 2
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        # Not every kiro-cli build supports --format json for this flag — fall back to
        # printing raw stdout so the caller (a human running /kiro:setup) can still read it.
        print(out)
        return 0
    ids = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, str):
                ids.append(item)
            elif isinstance(item, dict):
                ids.append(str(item.get("id") or item.get("model") or item.get("name") or item))
    elif isinstance(data, dict):
        for item in data.get("models", []):
            if isinstance(item, str):
                ids.append(item)
            elif isinstance(item, dict):
                ids.append(str(item.get("id") or item.get("model") or item.get("name") or item))
    for m in ids:
        print(m)
    return 0


def write_agents(root, force=False):
    d = os.path.join(root, ".kiro", "agents")
    os.makedirs(d, exist_ok=True)
    written = []
    for name, spec in (("kiro-implementer.json", _IMPLEMENTER_AGENT),
                        ("kiro-reviewer.json", _REVIEWER_AGENT)):
        p = os.path.join(d, name)
        if os.path.isfile(p) and not force:
            print(f"skip (exists): {p} — pass --force to overwrite")
            continue
        with open(p, "w", encoding="utf-8") as f:
            json.dump(spec, f, indent=2)
            f.write("\n")
        written.append(p)
    for p in written:
        print(f"wrote {p}")
    return 0


def main():
    argv = sys.argv[1:]
    root = "."
    if "--root" in argv:
        i = argv.index("--root")
        if i + 1 >= len(argv):
            print("--root requires a value", file=sys.stderr)
            return 2
        root = argv[i + 1]
        del argv[i:i + 2]
    if not argv:
        print(__doc__)
        return 2
    cmd = argv[0]
    if cmd == "probe":
        if "--timeout" in argv:
            i = argv.index("--timeout")
            if i + 1 >= len(argv) or not argv[i + 1].isdigit():
                print("--timeout requires a positive integer value", file=sys.stderr)
                return 2
            timeout = int(argv[i + 1])
        else:
            timeout = 90
        status, reason = probe(timeout)
        print(status + (f"\t{reason}" if reason else ""))
        return 0
    if cmd == "list-models":
        return list_models()
    if cmd == "write-agents":
        return write_agents(root, force="--force" in argv)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
