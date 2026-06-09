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
SET_KEYS = ("phase", "task_index")


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
    s[key] = int(value) if key == "task_index" and value.isdigit() else value
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
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
