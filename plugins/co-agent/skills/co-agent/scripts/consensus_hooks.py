#!/usr/bin/env python3
"""Session-gated decision logic for the consensus P3 hooks. The bash hooks in
plugin.json delegate here so their inline logic stays trivial. EVERY event is a
NO-OP (exit 0, no output) unless there is an ACTIVE autonomous consensus session
(consensus_state: status==running, phase==P3, autonomous==True) — so unrelated work
is never affected.

Events:
  stop                 — while an autonomous P3 session has tasks left, emit a JSON
                         block decision so the agent keeps going instead of stopping.
  post-tooluse         — record the last test result (pass/fail) into the state when a
                         test command ran, so the loop can read it.
  post-tooluse-failure — increment a consecutive-failure counter; if it crosses
                         STUCK_LIMIT, emit a 'stuck — abort' notice.

Usage (bash hook pipes the hook JSON on stdin):
  consensus_hooks.py stop --root .
  consensus_hooks.py post-tooluse --root .
  consensus_hooks.py post-tooluse-failure --root .
Always exits 0 (a hook must never hard-fail the session). Prints either nothing
(no-op) or a hook-control JSON / advisory line.
"""
import sys
import os
import json

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import consensus_state as cs

STUCK_LIMIT = 3


def _active(root):
    """Return the state dict iff an autonomous P3 session is running, else None."""
    s = cs.read_state(root)
    if not s:
        return None
    if s.get("status") == "running" and s.get("phase") == "P3" and s.get("autonomous"):
        return s
    return None


def _stdin_json():
    try:
        data = sys.stdin.read()
        return json.loads(data) if data.strip() else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _tasks_remaining(s):
    tasks = s.get("tasks", {})
    return [i for i, t in tasks.items() if t.get("status") not in ("done", "aborted")]


def ev_stop(root):
    s = _active(root)
    if not s:
        return 0  # no-op
    remaining = _tasks_remaining(s)
    if not remaining:
        return 0  # all done → allow stop
    # Block the stop so the autonomous loop continues to the next task.
    print(json.dumps({
        "decision": "block",
        "reason": f"co-agent consensus P3 active: {len(remaining)} task(s) not yet done/aborted "
                  f"(task_index {s.get('task_index')}). Continue the implement loop, or run "
                  f"`consensus_state.py set . status aborted` to stop."
    }))
    return 0


def ev_post_tooluse(root):
    s = _active(root)
    if not s:
        return 0
    payload = _stdin_json()
    cmd = (payload.get("tool_input", {}) or {}).get("command", "")
    if "run-all.sh" in cmd or "test-plugins.py" in cmd or "pytest" in cmd:
        # record a coarse pass/fail signal from the tool result if present
        out = json.dumps(payload.get("tool_response", payload.get("tool_result", "")))
        s["last_test_pass"] = ("ALL TESTS PASSED" in out) or ("passed" in out and "failed" not in out)
        cs.write_state(root, s)
    return 0


def ev_post_tooluse_failure(root):
    s = _active(root)
    if not s:
        return 0
    n = int(s.get("consec_failures", 0)) + 1
    s["consec_failures"] = n
    cs.write_state(root, s)
    if n >= STUCK_LIMIT:
        print(f"[co-agent consensus] {n} consecutive tool failures — the P3 loop looks STUCK. "
              f"Revert to the last checkpoint and abort this task "
              f"(`consensus_state.py task-abort . {s.get('task_index')}`).")
    return 0


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 0
    event = a[0]
    root = a[a.index("--root") + 1] if "--root" in a and a.index("--root") + 1 < len(a) else "."
    if event == "stop":
        return ev_stop(root)
    if event == "post-tooluse":
        return ev_post_tooluse(root)
    if event == "post-tooluse-failure":
        return ev_post_tooluse_failure(root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
