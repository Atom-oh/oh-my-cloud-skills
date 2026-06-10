# co-agent Consensus Pipeline — Stage B Implementation Plan (P3 autonomous TDD loop)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Stage B (P3) — autonomously implement a reviewed plan's tasks via TDD, gated by the co-agent multi-model consensus gate, with hard safety rails (scope-lock, test-gate, checkpoint, security veto, session-gated hooks).

**Architecture:** Stage B reuses the `superpowers:subagent-driven-development` pattern but swaps its *human* review checkpoint for the *co-agent multi-model* gate. Per plan task: checkpoint → TDD implementer → test gate → multi-model gate → fix loop (≤`consensus.max_rounds`) or abort → one commit → advance state. New deterministic helpers: `scope_guard.py` (file-set lock), `consensus_hooks.py` (session-gated Stop/PostToolUse/PostToolUseFailure decision logic), and `consensus_state.py` P3-progress fields. Orchestration itself is skill/command prose.

**Tech Stack:** Python 3 (stdlib only), Bash hooks (in `plugin.json`, session-gated), Markdown command/skill/reference, TAP tests sourced by `tests/run-all.sh`.

**Spec:** `docs/superpowers/specs/2026-06-09-co-agent-consensus-pipeline-design.md` (Stage B = P3).

**Reuse (already on main, Stage A):** `consensus_state.py` (init/get/set/detect/verify, `task_index`), `parse_plan.py` (`--files`/`--count`/tasks), the multi-model fan-out (`ai-cli-adapters.md` + `co_agent_config.py` `pairs`/`matrix`), `check_citations.py`, `references/consensus-pipeline.md`, `references/consensus-mode.md` (gate mechanics), `/co-agent:consensus` command, SKILL Mode 5.

**Out of scope (Stage C, separate plan):** P4 final cumulative-diff gate, P5 learnings/report, full-autonomy default wiring. Do NOT build those here.

---

## File Structure

| File | Responsibility |
|------|----------------|
| `plugins/co-agent/skills/co-agent/scripts/scope_guard.py` (NEW) | Given a plan `.md` + candidate path(s), exit 0 if every path is within the plan's declared file set (via `parse_plan`), else exit 1 listing the out-of-scope paths. The scope-lock primitive. |
| `plugins/co-agent/skills/co-agent/scripts/consensus_hooks.py` (NEW) | Session-gated hook decision logic for `stop`/`post-tooluse`/`post-tooluse-failure`. No-ops (exit 0, silent) unless an active consensus session (`consensus_state`) is in phase P3 with `autonomous: true`. Centralizes logic so the bash hook lines stay tiny. |
| `plugins/co-agent/skills/co-agent/scripts/consensus_state.py` (MODIFY) | Add P3 progress: top-level `status` (`running`/`done`/`aborted`) + `autonomous` bool + per-task `tasks` map (`{idx: {status, rounds}}`); commands `task-start`/`task-done`/`task-abort`/`task-round`/`autonomous`. |
| `plugins/co-agent/.claude-plugin/plugin.json` (MODIFY) | Add `Stop`, `PostToolUse`, `PostToolUseFailure` hooks delegating to `consensus_hooks.py` (session-gated). |
| `plugins/co-agent/commands/consensus.md` (MODIFY) | `implement <plan>` sub-mode: reserved → working (the P3 workflow). |
| `plugins/co-agent/skills/co-agent/SKILL.md` (MODIFY) | Mode 5: add the P3 implement workflow (reuse-subagent-driven + multi-model gate). |
| `plugins/co-agent/skills/co-agent/references/consensus-pipeline.md` (MODIFY) | Expand the P3 section (per-task loop + safety rails). |
| `tests/structure/test-co-agent-consensus-stage-b.sh` (NEW) | scope_guard (in/out), consensus_hooks session-gating (no-op when inactive; acts when active P3), state progress commands. |

`.gitignore` already excludes `.claude/co-agent-consensus/`.

---

## Task 1: `scope_guard.py` — scope-lock primitive

**Files:**
- Create: `plugins/co-agent/skills/co-agent/scripts/scope_guard.py`
- Test: locked by Task 7

- [ ] **Step 1: Write the script**

```python
#!/usr/bin/env python3
"""Scope-lock for the consensus P3 implement loop: a candidate file path is allowed
only if it is in the plan's declared file set (the union of every task's Create/Modify/
Test paths, via parse_plan). Used before any autonomous edit so the loop can't sprawl
beyond the reviewed plan.

Usage:
  scope_guard.py --plan <plan.md> <path>...   # exit 0 if ALL paths in scope, else 1
  scope_guard.py --plan <plan.md> --list      # print the allowed file set
Exit 0 = all in scope / list ok · 1 = at least one out of scope · 2 = usage/read error.
"""
import sys
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import parse_plan  # sibling module (Stage A)


def allowed_set(plan_path):
    with open(plan_path, encoding="utf-8") as f:
        tasks = parse_plan.parse(f.read())
    files = []
    for t in tasks:
        for fp in t["files"]:
            n = fp.strip().lstrip("./")
            if n and n not in files:
                files.append(n)
    return files


def _norm(p):
    return p.strip().lstrip("./").replace("\\", "/")


def main():
    args = sys.argv[1:]
    if "--plan" not in args:
        print(__doc__)
        return 2
    plan = args[args.index("--plan") + 1] if args.index("--plan") + 1 < len(args) else None
    if not plan:
        print("--plan requires a path", file=sys.stderr)
        return 2
    try:
        allowed = allowed_set(plan)
    except (OSError, UnicodeDecodeError) as e:
        print(f"❌ cannot read plan {plan}: {e}", file=sys.stderr)
        return 2

    if "--list" in args:
        print("\n".join(allowed))
        return 0

    paths = [a for a in args if a != "--plan" and a != plan and not a.startswith("--")]
    if not paths:
        print("no candidate paths given", file=sys.stderr)
        return 2
    allowed_norm = {_norm(a) for a in allowed}
    out = [p for p in paths if _norm(p) not in allowed_norm]
    if out:
        print("❌ out of plan scope (not in the reviewed plan's file set):", file=sys.stderr)
        for p in out:
            print(f"   • {p}", file=sys.stderr)
        return 1
    print(f"✅ all {len(paths)} path(s) within plan scope")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: chmod + syntax**

Run: `chmod +x plugins/co-agent/skills/co-agent/scripts/scope_guard.py && python3 -c "import ast; ast.parse(open('plugins/co-agent/skills/co-agent/scripts/scope_guard.py').read()); print('ok')"`
Expected: `ok`

- [ ] **Step 3: Manual smoke test**

```bash
cd /home/ec2-user/oh-my-cloud-skills
P=$(mktemp /tmp/plan.XXXXXX.md)
printf '### Task 1: a\n**Files:**\n- Create: `src/a.py`\n- Test: `tests/a.sh`\n- [ ] x\n' > "$P"
S=plugins/co-agent/skills/co-agent/scripts/scope_guard.py
python3 "$S" --plan "$P" --list                          # → src/a.py, tests/a.sh
python3 "$S" --plan "$P" src/a.py; echo "in=$?"          # → 0
python3 "$S" --plan "$P" src/evil.py; echo "out=$?"      # → 1
python3 "$S" --plan "$P" src/a.py src/evil.py; echo "mixed=$?"  # → 1
rm -f "$P"
```
Expected: `--list` prints both paths; in-scope → 0; out-of-scope → 1; mixed → 1.

- [ ] **Step 4: Commit**

```bash
git add plugins/co-agent/skills/co-agent/scripts/scope_guard.py
git commit -m "feat(co-agent): scope_guard.py — plan file-set lock for P3 implement loop"
```

---

## Task 2: `consensus_state.py` — P3 progress fields & commands

**Files:**
- Modify: `plugins/co-agent/skills/co-agent/scripts/consensus_state.py`
- Test: locked by Task 7

Stage A's `consensus_state.py` has `init` (writes state w/ `phase`, `task_index`, `rounds={}`), `get`, `set` (keys `phase`/`task_index`), `detect`, `verify`. Add P3 progress without breaking those.

- [ ] **Step 1: Add `status` + `autonomous` to the init state + `SET_KEYS`**

In `cmd_init`, add two keys to the `state` dict (after `task_index`):

```python
        "status": "running",
        "autonomous": False,
        "tasks": {},
```

Extend `SET_KEYS` to allow `status`:

```python
SET_KEYS = ("phase", "task_index", "status")
```

In `cmd_set`, allow `status` only from a fixed set (place inside the existing logic that already int-casts `task_index`):

```python
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
```

- [ ] **Step 2: Add `autonomous` + per-task commands**

Add these functions (after `cmd_verify`):

```python
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
```

- [ ] **Step 3: Route the new commands in `main()`**

Add next to the existing `if cmd == ...` lines:

```python
    if cmd == "autonomous":
        return cmd_autonomous(root, rest[1]) if len(rest) >= 2 else 2
    if cmd in ("task-start", "task-done", "task-abort", "task-round"):
        return cmd_task(root, cmd, rest[1]) if len(rest) >= 2 else 2
```

- [ ] **Step 4: Manual checks**

```bash
cd /home/ec2-user/oh-my-cloud-skills
python3 -c "import ast; ast.parse(open('plugins/co-agent/skills/co-agent/scripts/consensus_state.py').read()); print('ok')"
T=$(mktemp -d); S=plugins/co-agent/skills/co-agent/scripts/consensus_state.py
printf '# Plan\n### Task 1: a\n- [ ] x\n' > "$T/plan.md"
python3 "$S" init "$T" --docs "$T/plan.md" >/dev/null
python3 "$S" autonomous "$T" on
python3 "$S" task-start "$T" 0
python3 "$S" task-round "$T" 0
python3 "$S" task-done "$T" 0
python3 "$S" set "$T" status done
python3 "$S" get "$T" status         # → done
rm -rf "$T"
```
Expected: `autonomous = True`; `task 0: in_progress (rounds 0)` → `... (rounds 1)` → `task 0: done (rounds 1)`; `status` → `done`. Existing `bash tests/run-all.sh` still green.

- [ ] **Step 5: Commit**

```bash
git add plugins/co-agent/skills/co-agent/scripts/consensus_state.py
git commit -m "feat(co-agent): consensus_state P3 progress (status/autonomous/per-task)"
```

---

## Task 3: `consensus_hooks.py` — session-gated hook decision logic

**Files:**
- Create: `plugins/co-agent/skills/co-agent/scripts/consensus_hooks.py`
- Test: locked by Task 7

- [ ] **Step 1: Write the script**

```python
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
```

- [ ] **Step 2: chmod + syntax**

Run: `chmod +x plugins/co-agent/skills/co-agent/scripts/consensus_hooks.py && python3 -c "import ast; ast.parse(open('plugins/co-agent/skills/co-agent/scripts/consensus_hooks.py').read()); print('ok')"`
Expected: `ok`

- [ ] **Step 3: Manual smoke test — no-op when inactive, blocks when active P3**

```bash
cd /home/ec2-user/oh-my-cloud-skills
T=$(mktemp -d); S=plugins/co-agent/skills/co-agent/scripts
printf '# Plan\n### Task 1: a\n- [ ] x\n' > "$T/plan.md"
python3 "$S/consensus_state.py" init "$T" --docs "$T/plan.md" >/dev/null
# inactive (phase P0, not autonomous) → stop is a no-op (no output)
echo '{}' | python3 "$S/consensus_hooks.py" stop --root "$T"; echo "inactive-stop-rc=$?"
# activate P3 autonomous with a pending task → stop should emit a block JSON
python3 "$S/consensus_state.py" set "$T" phase P3 >/dev/null
python3 "$S/consensus_state.py" autonomous "$T" on >/dev/null
python3 "$S/consensus_state.py" task-start "$T" 0 >/dev/null
echo '{}' | python3 "$S/consensus_hooks.py" stop --root "$T" | python3 -c "import json,sys; d=json.load(sys.stdin); print('decision='+d['decision'])"
# mark done → stop allows (no output)
python3 "$S/consensus_state.py" task-done "$T" 0 >/dev/null
echo '{}' | python3 "$S/consensus_hooks.py" stop --root "$T"; echo "alldone-stop-rc=$?"
rm -rf "$T"
```
Expected: inactive stop → no output, rc 0; active P3 w/ pending task → `decision=block`; all-done → no output, rc 0.

- [ ] **Step 4: Commit**

```bash
git add plugins/co-agent/skills/co-agent/scripts/consensus_hooks.py
git commit -m "feat(co-agent): consensus_hooks.py — session-gated P3 Stop/PostToolUse logic"
```

---

## Task 4: Wire the hooks into `plugin.json`

**Files:**
- Modify: `plugins/co-agent/.claude-plugin/plugin.json`

co-agent's `plugin.json` already has a `hooks` object (PostToolUse on `Edit|Write` for CLAUDE.md, SessionStart). Add the three P3 hooks. They call `consensus_hooks.py` which itself no-ops unless a session is active — so they are safe globally.

- [ ] **Step 1: Read the current hooks block, then add the three events**

Inside `"hooks": { ... }`, add (alongside the existing `PostToolUse`/`SessionStart`):

```json
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/skills/co-agent/scripts/consensus_hooks.py\" stop --root . 2>/dev/null" }
        ]
      }
    ],
    "PostToolUseFailure": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/skills/co-agent/scripts/consensus_hooks.py\" post-tooluse-failure --root . 2>/dev/null" }
        ]
      }
    ]
```

And add a Bash matcher entry to the EXISTING `PostToolUse` array (append, do not remove the CLAUDE.md one):

```json
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/skills/co-agent/scripts/consensus_hooks.py\" post-tooluse --root . 2>/dev/null" }
        ]
      }
```

- [ ] **Step 2: Validate JSON + refs + plugin tests**

Run: `python3 -c "import json; json.load(open('plugins/co-agent/.claude-plugin/plugin.json')); print('json ok')" && python3 scripts/test-plugins.py 2>&1 | tail -3`
Expected: `json ok` and `ALL TESTS PASSED`.

- [ ] **Step 3: Behavior smoke test (hook is a global no-op when no session)**

```bash
cd /home/ec2-user/oh-my-cloud-skills
CLAUDE_PLUGIN_ROOT=plugins/co-agent echo '{}' | python3 plugins/co-agent/skills/co-agent/scripts/consensus_hooks.py stop --root .; echo "no-session-rc=$?"
```
Expected: no output, rc 0 (no `.claude/co-agent-consensus/state.local.md` in repo root → no-op). Confirms the hooks won't disturb ordinary sessions.

- [ ] **Step 4: Commit**

```bash
git add plugins/co-agent/.claude-plugin/plugin.json
git commit -m "feat(co-agent): wire session-gated P3 hooks (Stop/PostToolUse/PostToolUseFailure)"
```

---

## Task 5: `implement` sub-mode → working (command + skill + reference)

**Files:**
- Modify: `plugins/co-agent/commands/consensus.md`
- Modify: `plugins/co-agent/skills/co-agent/SKILL.md`
- Modify: `plugins/co-agent/skills/co-agent/references/consensus-pipeline.md`

- [ ] **Step 1: `consensus.md` — make `implement` working + add the P3 workflow**

In the sub-modes list, change the `implement` line and the `argument-hint` (remove "reserved"):

```markdown
- `implement <plan>` — autonomously implement a reviewed plan (P3 TDD loop, multi-model gated). **(available — Stage B)**
```

Add a new section after the Stage A workflow:

```markdown
## Stage B workflow (`implement <plan>`)
Reuses the `subagent-driven-development` pattern with the **co-agent multi-model gate** as
the review checkpoint. Requires a clean tree; commits locally only (never push/reset/rebase).

0. **Init/resume**: `consensus_state.py verify .` (clean tree); if no session, `init` it from
   the plan; set `phase P3` and `autonomous on`. Tasks come from `parse_plan.py <plan>`;
   allowed file set from `parse_plan.py <plan> --files` (enforced by `scope_guard.py`).
1. **Per task** (advance `consensus_state.py task-start . <i>`):
   a. **Checkpoint**: `git stash create`/tag or a WIP commit you can reset to.
   b. **Implement (TDD)**: write the failing test → minimal code → refactor. Every file you
      touch MUST pass `scope_guard.py --plan <plan> <path>` (else stop — out of scope).
   c. **Security veto**: reject any change violating the AWS mandates (0.0.0.0/0, Principal:"*",
      secrets in env, …) before applying.
   d. **Test gate**: `bash tests/run-all.sh` (+ project tests) MUST pass; on failure, revert to
      the checkpoint and either fix within `consensus.max_rounds` or `task-abort`.
   e. **Multi-model gate**: run the consensus gate (references/consensus-mode.md) on the task's
      diff; drop `unsupported` findings; if CRITICAL/MAJOR remain, fix (≤ max_rounds) or abort.
   f. **Commit** the single task (explicit paths) and `consensus_state.py task-done . <i>`.
2. When all tasks are done, set `status done` (the Stop hook then allows stopping). Report.
```

- [ ] **Step 2: `SKILL.md` Mode 5 — add the P3 line**

In Mode 5, after the plan-gate paragraph, add:

```markdown
**Implement (Stage B, `implement <plan>`)**: once the plan passes the gate, autonomously
implement it — reuse the `subagent-driven-development` loop but with the **multi-model gate**
as the review checkpoint. Per task: checkpoint → TDD → `scope_guard.py` (stay in the plan's
file set) → security-mandate veto → test gate (`tests/run-all.sh` must pass) → multi-model
gate → one commit → `consensus_state.py task-done`. Session-gated hooks (Stop/PostToolUse/
PostToolUseFailure) keep the loop going and catch stuck states. Local commits only.
```

- [ ] **Step 3: `consensus-pipeline.md` — expand the P3 section**

Replace the existing short P3 bullet with:

```markdown
- **P3 (Stage B) — autonomous TDD implement loop**: reuse `subagent-driven-development` with
  the co-agent multi-model gate as the review checkpoint. Per plan task: git checkpoint →
  TDD (red→green→refactor) → `scope_guard.py` scope-lock → AWS security-mandate veto →
  test gate (`tests/run-all.sh` + project tests must pass; revert on failure) → multi-model
  consensus gate on the task diff → fix ≤`consensus.max_rounds` or `task-abort` → one commit
  per task → `consensus_state.py task-done`. Session-gated hooks: **Stop** keeps the loop
  going until all tasks are done/aborted, **PostToolUse** records test results,
  **PostToolUseFailure** flags stuck loops. Local commits only — never push/reset/rebase.
```

- [ ] **Step 4: Validate + commit (explicit paths)**

Run: `python3 scripts/test-plugins.py 2>&1 | tail -2`
Expected: PASS.

```bash
git add plugins/co-agent/commands/consensus.md plugins/co-agent/skills/co-agent/SKILL.md plugins/co-agent/skills/co-agent/references/consensus-pipeline.md
git commit -m "docs(co-agent): consensus implement sub-mode (Stage B P3 workflow)"
```

---

## Task 6: Tests — `tests/structure/test-co-agent-consensus-stage-b.sh`

**Files:**
- Create: `tests/structure/test-co-agent-consensus-stage-b.sh`

- [ ] **Step 1: Write the test (sourced — no shebang exec, no `exit`)**

```bash
#!/usr/bin/env bash
# Stage B: scope_guard + consensus_hooks session-gating + consensus_state P3 progress.

CO="plugins/co-agent/skills/co-agent"
SG="$CO/scripts/scope_guard.py"
HK="$CO/scripts/consensus_hooks.py"
ST="$CO/scripts/consensus_state.py"

assert_file_exists "$SG" "scope_guard.py exists"
assert_file_executable "$SG" "scope_guard.py is executable"
assert_file_exists "$HK" "consensus_hooks.py exists"

# --- scope_guard ---
P=$(mktemp "${TMPDIR:-/tmp}/sgplan.XXXXXX.md")
printf '### Task 1: a\n**Files:**\n- Create: `src/a.py`\n- Test: `tests/a.sh`\n- [ ] x\n' > "$P"
python3 "$SG" --plan "$P" src/a.py >/dev/null 2>&1 && IN=0 || IN=$?
assert_eq "0" "$IN" "scope_guard: in-scope path allowed"
python3 "$SG" --plan "$P" src/evil.py >/dev/null 2>&1 && OUT=0 || OUT=$?
assert_eq "1" "$OUT" "scope_guard: out-of-scope path rejected"
assert_contains "$(python3 "$SG" --plan "$P" --list 2>&1)" "src/a.py" "scope_guard --list shows allowed set"
rm -f "$P"

# --- consensus_hooks session-gating ---
D=$(mktemp -d "${TMPDIR:-/tmp}/csb.XXXXXX")
printf '# Plan\n### Task 1: a\n- [ ] x\n' > "$D/plan.md"
python3 "$ST" init "$D" --docs "$D/plan.md" >/dev/null 2>&1
# inactive (P0, not autonomous) → stop hook no-op (empty output)
OUT0=$(echo '{}' | python3 "$HK" stop --root "$D" 2>&1)
assert_eq "" "$OUT0" "stop hook is a no-op when no active P3 session"
# activate P3 autonomous + pending task → stop emits block decision
python3 "$ST" set "$D" phase P3 >/dev/null 2>&1
python3 "$ST" autonomous "$D" on >/dev/null 2>&1
python3 "$ST" task-start "$D" 0 >/dev/null 2>&1
assert_contains "$(echo '{}' | python3 "$HK" stop --root "$D" 2>&1)" "block" "stop hook blocks while P3 task pending"
# task done → stop allows again (no-op)
python3 "$ST" task-done "$D" 0 >/dev/null 2>&1
OUT1=$(echo '{}' | python3 "$HK" stop --root "$D" 2>&1)
assert_eq "" "$OUT1" "stop hook allows stop once all tasks done"

# --- state progress ---
python3 "$ST" task-round "$D" 0 >/dev/null 2>&1
assert_contains "$(python3 "$ST" get "$D" tasks 2>&1)" "rounds" "task-round records per-task rounds"
python3 "$ST" set "$D" status bogus >/dev/null 2>&1 && SB=0 || SB=$?
assert_eq "2" "$SB" "status rejects invalid value"
rm -rf "$D"
```

- [ ] **Step 2: Run the suite**

Run: `bash tests/run-all.sh 2>&1 | tail -3`
Expected: `ALL TESTS PASSED`, 0 failed.

- [ ] **Step 3: Commit**

```bash
git add tests/structure/test-co-agent-consensus-stage-b.sh
git commit -m "test(co-agent): consensus Stage B — scope_guard + hook gating + state progress"
```

---

## Task 7: Final validation gate

- [ ] **Step 1: Full gate**

Run: `bash tests/run-all.sh 2>&1 | tail -2 && python3 scripts/test-plugins.py 2>&1 | tail -2 && python3 scripts/test-codex-plugins.py 2>&1 | tail -2`
Expected: all report all-passed.

- [ ] **Step 2: Hook safety check (no consensus session ⇒ hooks invisible)**

Run: `rm -rf .claude/co-agent-consensus 2>/dev/null; CLAUDE_PLUGIN_ROOT=plugins/co-agent bash -c 'echo "{}" | python3 plugins/co-agent/skills/co-agent/scripts/consensus_hooks.py stop --root . && echo "{}" | python3 plugins/co-agent/skills/co-agent/scripts/consensus_hooks.py post-tooluse --root .'; echo "rc=$?"`
Expected: no output, `rc=0` — the new hooks do nothing outside an active consensus session.

- [ ] **Step 3: Scope-clean check (only Stage B files)**

Run: `git diff --name-only main..HEAD | grep -vE '^(plugins/co-agent/(skills/co-agent/(scripts/(scope_guard|consensus_hooks|consensus_state)\.py|SKILL\.md|references/consensus-pipeline\.md)|commands/consensus\.md|\.claude-plugin/plugin\.json)|tests/structure/test-co-agent-consensus-stage-b\.sh|docs/superpowers/)' || echo "scope clean — only Stage B files"`
Expected: `scope clean — only Stage B files`.

---

## Self-Review

- **Spec coverage (Stage B = P3):** per-task TDD loop (Task 5 prose + hooks) ✅; checkpoint/scope-lock (`scope_guard.py` Task 1 + prose) ✅; test-gate-before-commit (prose Task 5) ✅; multi-model gate reuse (prose, reuses consensus-mode.md) ✅; security-mandate veto (prose) ✅; session-gated hooks Stop/PostToolUse/PostToolUseFailure (Tasks 3–4) ✅; resumable progress (`consensus_state` Task 2) ✅; local-only commits (prose) ✅. Stage C (P4/P5) excluded ✅.
- **Placeholder scan:** full code in Tasks 1–3, 6; concrete JSON/markdown in Tasks 4–5; exact commands + expected output in every run step. None.
- **Type/name consistency:** `scope_guard.py` imports `parse_plan.parse` (Stage A) and uses its `t["files"]`; `consensus_hooks.py` imports `consensus_state` and calls `read_state`/`write_state` (Stage A names) + reads `status`/`phase`/`autonomous`/`tasks`/`task_index`/`consec_failures`; `consensus_state.py` new commands (`autonomous`, `task-start|done|abort|round`) + `SET_KEYS=("phase","task_index","status")` are used consistently across Tasks 2/3/5/6. Hook event names `stop`/`post-tooluse`/`post-tooluse-failure` match between `consensus_hooks.py` (Task 3) and `plugin.json` (Task 4) and the test (Task 6).
