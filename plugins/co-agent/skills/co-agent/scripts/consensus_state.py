#!/usr/bin/env python3
"""co-agent consensus pipeline — session state + input-document detection.

State lives at <root>/.claude/co-agent-consensus/state.local.md as a human-readable
header plus a ```json fenced block. It binds a run to the repo/branch/base/HEAD, the
sha of each input doc, the allowed file set, a session_id, the current phase, and the
current task index — so the autonomous pipeline is resumable and so session-gated hooks
(Stage B) can no-op on unrelated work.

Commands:
  consensus_state.py init <root> --docs a.md,b.md [--base main] [--allowed f1,f2]
  consensus_state.py get <root> [key]
  consensus_state.py set <root> <key> <value>        # key in: phase, task_index
  consensus_state.py detect <root> <path>...         # classify docs → "path<TAB>kind"
  consensus_state.py verify <root>                   # exit 0 if clean tree + HEAD matches
Exit 0 ok / 1 verify-fail / 2 usage.
"""
import sys
import os
import re
import json
import uuid
import hashlib
import subprocess

STATE_REL = os.path.join(".claude", "co-agent-consensus", "state.local.md")
SET_KEYS = ("phase", "task_index", "status")


def _git(root, *args):
    try:
        out = subprocess.run(["git", "-C", root, *args], capture_output=True,
                             text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def _sha12(path):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:12]
    except OSError:
        return ""


def state_path(root):
    return os.path.join(root, STATE_REL)


def read_state(root):
    p = state_path(root)
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def write_state(root, state):
    p = state_path(root)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    body = json.dumps(state, indent=2, ensure_ascii=False)
    with open(p, "w", encoding="utf-8") as f:
        f.write("<!-- co-agent-consensus session state — managed by consensus_state.py; "
                "DO NOT edit by hand. Ephemeral (gitignored). -->\n\n")
        f.write(f"# Consensus session `{state.get('session_id','')}`\n\n")
        f.write(f"phase: **{state.get('phase')}** · task: {state.get('task_index')} · "
                f"branch: {state.get('branch') or '?'}\n\n")
        f.write("```json\n" + body + "\n```\n")


def classify(path):
    """adr / spec / plan / unknown — by location then content."""
    low = path.replace("\\", "/").lower()
    base = os.path.basename(low)
    if "/docs/decisions/" in low or re.match(r"adr-\d", base):
        return "adr"
    try:
        with open(path, encoding="utf-8") as f:
            head = f.read(8000)
    except (OSError, UnicodeDecodeError):
        head = ""
    # a writing-plans plan: bite-sized checkbox tasks
    if ("/plans/" in low) or ("- [ ]" in head and re.search(r"^#{2,3}\s+Task\s", head, re.M)):
        return "plan"
    if "/specs/" in low or "design" in base or "spec" in base or "## Non-Goals" in head:
        return "spec"
    return "unknown"


def cmd_init(root, docs, base, allowed):
    state = {
        "session_id": uuid.uuid4().hex[:16],
        "phase": "P0",
        "task_index": 0,
        "status": "running",
        "autonomous": False,
        "tasks": {},
        "rounds": {},
        "repo_root": os.path.abspath(root),
        "branch": _git(root, "rev-parse", "--abbrev-ref", "HEAD"),
        "base": base or "main",
        "head": _git(root, "rev-parse", "HEAD"),
        "docs": [{"path": d, "kind": classify(d), "sha": _sha12(d)} for d in docs],
        "allowed_paths": allowed,
    }
    write_state(root, state)
    print(f"session {state['session_id']} · phase P0 · "
          f"{len(docs)} doc(s): " + ", ".join(f"{d['kind']}:{os.path.basename(d['path'])}" for d in state["docs"]))
    return 0


def cmd_get(root, key):
    s = read_state(root)
    if s is None:
        print("no active consensus session (run init)", file=sys.stderr)
        return 2
    if key:
        v = s.get(key)
        print(json.dumps(v) if isinstance(v, (dict, list)) else (v if v is not None else ""))
    else:
        print(json.dumps(s, indent=2, ensure_ascii=False))
    return 0


def cmd_set(root, key, value):
    if key not in SET_KEYS:
        print(f"set key must be one of: {', '.join(SET_KEYS)}", file=sys.stderr)
        return 2
    s = read_state(root)
    if s is None:
        print("no active consensus session (run init)", file=sys.stderr)
        return 2
    if key == "task_index":
        if not value.isdigit():
            print("task_index must be a non-negative integer", file=sys.stderr)
            return 2
        s[key] = int(value)
    elif key == "status":
        if value not in ("running", "done", "aborted"):
            print("status must be running|done|aborted", file=sys.stderr)
            return 2
        s[key] = value
    else:
        s[key] = value
    write_state(root, s)
    print(f"{key} = {s[key]}")
    return 0


def cmd_detect(root, paths):
    for p in paths:
        print(f"{p}\t{classify(p)}")
    return 0


def cmd_verify(root):
    """exit 0 if the working tree is clean AND HEAD still matches the recorded state."""
    s = read_state(root)
    if s is None:
        print("no active consensus session", file=sys.stderr)
        return 1
    dirty = _git(root, "status", "--porcelain")
    if dirty:
        print("❌ working tree not clean — consensus needs a clean tree", file=sys.stderr)
        return 1
    head = _git(root, "rev-parse", "HEAD")
    if s.get("head") and head and head != s["head"]:
        print(f"❌ HEAD drifted ({s['head'][:8]} → {head[:8]}) — unrelated changes mid-run", file=sys.stderr)
        return 1
    print("✅ clean tree, HEAD matches session")
    return 0


def _load_or_die(root):
    s = read_state(root)
    if s is None:
        print("no active consensus session (run init)", file=sys.stderr)
    return s


def cmd_autonomous(root, value):
    s = _load_or_die(root)
    if s is None:
        return 2
    if value.lower() not in ("on", "off", "true", "false", "1", "0"):
        print("usage: autonomous <on|off>", file=sys.stderr)
        return 2
    s["autonomous"] = value.lower() in ("on", "true", "1")
    write_state(root, s)
    print(f"autonomous = {s['autonomous']}")
    return 0


def cmd_task(root, action, idx):
    """task-start/done/abort/round <idx> — track per-task progress in state['tasks']."""
    s = _load_or_die(root)
    if s is None:
        return 2
    if not idx.isdigit():
        print("task index must be a non-negative integer", file=sys.stderr)
        return 2
    t = s.setdefault("tasks", {}).setdefault(idx, {"status": "pending", "rounds": 0})
    if action == "task-start":
        t["status"] = "in_progress"
        s["task_index"] = int(idx)
    elif action == "task-done":
        t["status"] = "done"
    elif action == "task-abort":
        t["status"] = "aborted"
        s["status"] = "aborted"
    elif action == "task-round":
        t["rounds"] = int(t.get("rounds", 0)) + 1
    else:
        print(f"unknown task action '{action}'", file=sys.stderr)
        return 2
    write_state(root, s)
    print(f"task {idx}: {t['status']} (rounds {t['rounds']})")
    return 0


def cmd_report(root):
    """Render a final markdown report from session state → stdout, and write it to
    <root>/.claude/co-agent-consensus/report.md (gitignored, session-local)."""
    s = read_state(root)
    if s is None:
        print("no active consensus session (run init)", file=sys.stderr)
        return 2
    tasks = s.get("tasks", {})
    if not isinstance(tasks, dict):
        tasks = {}
    done = [i for i, t in tasks.items() if isinstance(t, dict) and t.get("status") == "done"]
    aborted = [i for i, t in tasks.items() if isinstance(t, dict) and t.get("status") == "aborted"]
    lines = []
    lines.append(f"# Consensus run report — session `{s.get('session_id', '')}`")
    lines.append("")
    lines.append(f"- **status**: {s.get('status', '?')}")
    lines.append(f"- **phase**: {s.get('phase', '?')}")
    lines.append(f"- **branch**: {s.get('branch') or '?'}  (base {s.get('base') or '?'})")
    lines.append(f"- **tasks**: {len(done)} done, {len(aborted)} aborted, {len(tasks)} total")
    lines.append(f"- **tests**: {'PASS' if s.get('last_test_pass') else 'unknown/fail'}")
    docs = s.get("docs", [])
    if docs:
        lines.append(f"- **inputs**: " + ", ".join(
            f"{d.get('kind')}:{os.path.basename(d.get('path', ''))}" for d in docs if isinstance(d, dict)))
    lines.append("")
    lines.append("| task | status | rounds |")
    lines.append("|------|--------|--------|")
    for i in sorted(tasks, key=lambda k: int(k) if str(k).isdigit() else 0):
        t = tasks[i] if isinstance(tasks[i], dict) else {}
        lines.append(f"| {i} | {t.get('status', '?')} | {t.get('rounds', 0)} |")
    report = "\n".join(lines) + "\n"

    out_path = os.path.join(root, ".claude", "co-agent-consensus", "report.md")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)
    sys.stdout.write(report)
    return 0


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 2
    cmd, rest = a[0], a[1:]
    root = rest[0] if rest and not rest[0].startswith("--") else "."

    def opt(flag):
        return rest[rest.index(flag) + 1] if flag in rest and rest.index(flag) + 1 < len(rest) else None

    if cmd == "init":
        docs = [d for d in (opt("--docs") or "").split(",") if d]
        allowed = [p for p in (opt("--allowed") or "").split(",") if p]
        return cmd_init(root, docs, opt("--base"), allowed)
    if cmd == "get":
        key = rest[1] if len(rest) > 1 and not rest[1].startswith("--") else None
        return cmd_get(root, key)
    if cmd == "set":
        return cmd_set(root, rest[1], rest[2]) if len(rest) >= 3 else 2
    if cmd == "detect":
        paths = [p for p in rest[1:] if not p.startswith("--")]
        return cmd_detect(root, paths) if paths else 2
    if cmd == "verify":
        return cmd_verify(root)
    if cmd == "autonomous":
        return cmd_autonomous(root, rest[1]) if len(rest) >= 2 else 2
    if cmd in ("task-start", "task-done", "task-abort", "task-round"):
        return cmd_task(root, cmd, rest[1]) if len(rest) >= 2 else 2
    if cmd == "report":
        return cmd_report(root)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
