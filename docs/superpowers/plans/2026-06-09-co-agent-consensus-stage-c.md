# co-agent Consensus Pipeline — Stage C Implementation Plan (P4 final gate + P5 report + full-autonomy wiring)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the consensus pipeline — a final cumulative-diff multi-model gate (P4), a deterministic session report (P5), and wiring so the default `/co-agent:consensus <doc>` runs P0→P5 end-to-end and resumes from saved state.

**Architecture:** Two small deterministic helpers on `consensus_state.py` — `report` (render a markdown summary from session state) and `cumulative-diff` (emit `git diff <base>...HEAD` filtered to the plan's allowed file set, the input to the P4 gate). P4 itself reuses the existing multi-model gate (`references/consensus-mode.md` + the fan-out + `check_citations.py`); P5/wiring/resume are orchestration prose in the command + SKILL + reference. No new autonomous machinery — Stage B's hooks/scope-lock/state already provide the rails.

**Tech Stack:** Python 3 (stdlib only), Bash TAP tests sourced by `tests/run-all.sh`, Markdown command/skill/reference, `git`.

**Spec:** `docs/superpowers/specs/2026-06-09-co-agent-consensus-pipeline-design.md` (Stage C = P4 + P5 + wiring + resume).

**Reuse (on main, Stage A+B):** `consensus_state.py` (phase/task_index/status/tasks/autonomous/last_test_pass), `parse_plan.py` (`--files`), the fan-out (`ai-cli-adapters.md` + `co_agent_config.py` `pairs`/`matrix`), `check_citations.py`, `scope_guard.py`, `consensus_hooks.py`, `references/consensus-pipeline.md`, `references/consensus-mode.md` (gate mechanics), `/co-agent:consensus` command, SKILL Mode 5.

**Out of scope:** a committed persistent cross-run `learnings.md` (panel cut it — keep learnings session-local/gitignored). The 1.8.0 release is a follow-up, not part of this plan.

---

## File Structure

| File | Responsibility |
|------|----------------|
| `plugins/co-agent/skills/co-agent/scripts/consensus_state.py` (MODIFY) | Add `report` (render final markdown summary from state → stdout, and write it to the session artifact dir) and `cumulative-diff` (print `git diff <base>...HEAD` limited to the plan's allowed file set) commands. |
| `plugins/co-agent/commands/consensus.md` (MODIFY) | Default (no sub-mode) = full P0→P5 pipeline; add the P4 gate + P5 report steps; document resume. |
| `plugins/co-agent/skills/co-agent/SKILL.md` (MODIFY) | Mode 5: add P4 (final gate) + P5 (report) + "default runs the full pipeline / resumes from state". |
| `plugins/co-agent/skills/co-agent/references/consensus-pipeline.md` (MODIFY) | Expand P4/P5 bullets; mark Stage C done; describe resume. |
| `tests/structure/test-co-agent-consensus-stage-c.sh` (NEW) | `report` (renders tasks/status), `cumulative-diff` scope filter, resume (phase/task_index round-trip). |

`.gitignore` already excludes `.claude/co-agent-consensus/`.

---

## Task 1: `consensus_state.py` — `report` command

**Files:**
- Modify: `plugins/co-agent/skills/co-agent/scripts/consensus_state.py`
- Test: locked by Task 4

`consensus_state.py` already has `read_state`, `write_state`, `state_path`, and routes commands in `main()`. Add a `report` command that renders a markdown summary and also writes it next to the state file.

- [ ] **Step 1: Add the `cmd_report` function**

Add after the existing `cmd_task` function:

```python
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
```

- [ ] **Step 2: Route `report` in `main()`**

Add next to the other `if cmd == ...` lines (e.g. after the `task-*` routing):

```python
    if cmd == "report":
        return cmd_report(root)
```

- [ ] **Step 3: Syntax + manual check**

```bash
cd /home/ec2-user/oh-my-cloud-skills
python3 -c "import ast; ast.parse(open('plugins/co-agent/skills/co-agent/scripts/consensus_state.py').read()); print('ok')"
T=$(mktemp -d); S=plugins/co-agent/skills/co-agent/scripts/consensus_state.py
printf '# Plan\n### Task 1: a\n- [ ] x\n' > "$T/plan.md"
python3 "$S" init "$T" --docs "$T/plan.md" >/dev/null
python3 "$S" task-start "$T" 0 >/dev/null; python3 "$S" task-done "$T" 0 >/dev/null
python3 "$S" set "$T" status done >/dev/null
python3 "$S" report "$T" | head -8
test -f "$T/.claude/co-agent-consensus/report.md" && echo "report.md written"
rm -rf "$T"
```
Expected: a markdown report with `status: done`, `tasks: 1 done, 0 aborted, 1 total`, a task table row `| 0 | done | 0 |`; `report.md written`.

- [ ] **Step 4: Commit**

```bash
git add plugins/co-agent/skills/co-agent/scripts/consensus_state.py
git commit -m "feat(co-agent): consensus_state report command (P5 final report)"
```

---

## Task 2: `consensus_state.py` — `cumulative-diff` command (P4 input)

**Files:**
- Modify: `plugins/co-agent/skills/co-agent/scripts/consensus_state.py`
- Test: locked by Task 4

The P4 gate reviews the WHOLE implementation diff, limited to the plan's allowed file set so noise/unrelated files don't enter the gate. Provide a command that emits exactly that diff.

- [ ] **Step 1: Add `cmd_cumulative_diff`**

Add after `cmd_report`. It reuses `_git` (already in the file) and `parse_plan` (sibling module) for the allowed file set:

```python
def cmd_cumulative_diff(root, plan_path, base):
    """Print `git diff <base>...HEAD` limited to the plan's declared file set (P4 input)."""
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import parse_plan
    try:
        with open(plan_path, encoding="utf-8") as f:
            tasks = parse_plan.parse(f.read())
    except (OSError, UnicodeDecodeError) as e:
        print(f"❌ cannot read plan {plan_path}: {e}", file=sys.stderr)
        return 2
    files = []
    for t in tasks:
        for fp in t.get("files", []):
            n = fp.strip().lstrip("./")
            if n and n not in files:
                files.append(n)
    if not files:
        print("❌ plan declares no files — nothing to diff", file=sys.stderr)
        return 2
    diff = _git(root, "diff", f"{base}...HEAD", "--", *files)
    sys.stdout.write(diff + ("\n" if diff and not diff.endswith("\n") else ""))
    return 0
```

- [ ] **Step 2: Route it in `main()`**

```python
    if cmd == "cumulative-diff":
        plan = opt_after(rest, "--plan")
        base = opt_after(rest, "--base") or "main"
        return cmd_cumulative_diff(root, plan, base) if plan else 2
```

Add this small arg helper near the top of `main()` (before the routing), if not already present:

```python
    def opt_after(seq, flag):
        return seq[seq.index(flag) + 1] if flag in seq and seq.index(flag) + 1 < len(seq) else None
```

- [ ] **Step 3: Syntax + manual check**

```bash
cd /home/ec2-user/oh-my-cloud-skills
python3 -c "import ast; ast.parse(open('plugins/co-agent/skills/co-agent/scripts/consensus_state.py').read()); print('ok')"
S=plugins/co-agent/skills/co-agent/scripts/consensus_state.py
P=$(mktemp /tmp/p.XXXXXX.md)
printf '### Task 1: a\n**Files:**\n- Modify: `README.md`\n- [ ] x\n' > "$P"
# diff README.md only between main and HEAD (may be empty if unchanged — exit 0 either way)
python3 "$S" cumulative-diff . --plan "$P" --base main >/dev/null; echo "rc=$?"
# missing --plan → usage error
python3 "$S" cumulative-diff . --base main >/dev/null 2>&1; echo "noplan-rc=$?"
rm -f "$P"
```
Expected: `rc=0`; `noplan-rc=2`.

- [ ] **Step 4: Commit**

```bash
git add plugins/co-agent/skills/co-agent/scripts/consensus_state.py
git commit -m "feat(co-agent): consensus_state cumulative-diff command (P4 gate input, scoped)"
```

---

## Task 3: Orchestration prose — P4/P5 + full-pipeline default + resume

**Files:**
- Modify: `plugins/co-agent/commands/consensus.md`
- Modify: `plugins/co-agent/skills/co-agent/SKILL.md`
- Modify: `plugins/co-agent/skills/co-agent/references/consensus-pipeline.md`

- [ ] **Step 1: `consensus.md` — default = full pipeline + add P4/P5 + resume**

In the sub-modes list, change the default line:

```markdown
- (default, no sub-mode) — runs the **full pipeline P0→P5** end-to-end: detect inputs → load/generate plan → P2 plan gate → P3 implement → P4 final gate → P5 report. **Resumable** — re-running reads `consensus_state` (phase/task_index) and continues.
```

Add a section after the Stage B workflow:

```markdown
## Stage C — final gate + report (`P4`, `P5`) and full-pipeline default
1. **P4 final gate**: capture the cumulative implementation diff, scoped to the plan's files —
   `python3 "$SK/consensus_state.py" cumulative-diff . --plan <plan> --base <trunk>` — and run the
   multi-model consensus gate on it (references/consensus-mode.md). Drop `unsupported` findings;
   if CRITICAL/MAJOR remain, fix (≤ `consensus.max_rounds`) and re-run; require tests green.
2. **P5 report**: `python3 "$SK/consensus_state.py" set . status done` then
   `python3 "$SK/consensus_state.py" report .` — emits the run summary (tasks done/aborted, rounds,
   tests) to stdout and `.claude/co-agent-consensus/report.md` (gitignored). Present it to the user.
3. **Full pipeline / resume**: the default invocation chains P0→P5. On re-invocation, read
   `consensus_state.py get . phase` + `get . task_index` and continue from there (don't restart);
   the Stop hook keeps the loop going until `status` is `done`/`aborted`.
```

- [ ] **Step 2: `SKILL.md` Mode 5 — add P4/P5/resume**

After the Stage-B implement paragraph in Mode 5, add:

```markdown
**Final gate + report (Stage C, P4/P5)**: when all tasks are done, run the consensus gate once
more on the **cumulative** diff (`consensus_state.py cumulative-diff . --plan <plan> --base <trunk>`
→ gate) until clean + tests green, then `consensus_state.py set . status done` and
`consensus_state.py report .` (writes `.claude/co-agent-consensus/report.md`, gitignored).
The **default** `/co-agent:consensus <doc>` runs the full P0→P5 pipeline and is **resumable** —
re-running reads `phase`/`task_index` from state and continues.
```

- [ ] **Step 3: `consensus-pipeline.md` — expand P4/P5 + resume + mark Stage C done**

Replace the P4 and P5 bullets with:

```markdown
- **P4 (Stage C) — final cumulative-diff gate**: run the multi-model gate on
  `consensus_state.py cumulative-diff . --plan <plan> --base <trunk>` (the whole implementation
  diff, scoped to the plan's file set) → fix ≤`consensus.max_rounds` until no CRITICAL/MAJOR AND
  tests green.
- **P5 (Stage C) — report**: `consensus_state.py report .` renders the run summary (tasks
  done/aborted, per-task rounds, status, tests) to stdout + `.claude/co-agent-consensus/report.md`
  (gitignored, session-local — no committed cross-run learnings).

**Resume**: the pipeline is resumable — `consensus_state` persists `phase`/`task_index`/`tasks`,
so a re-invocation continues from the last completed step rather than restarting.
```

And update the intro line so it no longer says "Stage A implements P0–P2 only" — change to:

```markdown
Borrows consensus-build's pipeline; the gates use co-agent's panel (Kiro models + Codex +
Gemini). **All phases P0–P5 are implemented (Stage A: P0–P2, Stage B: P3, Stage C: P4–P5).**
```

- [ ] **Step 4: Validate + commit (explicit paths)**

Run: `python3 scripts/test-plugins.py 2>&1 | tail -2`
Expected: ALL TESTS PASSED.

```bash
git add plugins/co-agent/commands/consensus.md plugins/co-agent/skills/co-agent/SKILL.md plugins/co-agent/skills/co-agent/references/consensus-pipeline.md
git commit -m "docs(co-agent): consensus P4/P5 + full-pipeline default + resume (Stage C)"
```

---

## Task 4: Tests — `tests/structure/test-co-agent-consensus-stage-c.sh`

**Files:**
- Create: `tests/structure/test-co-agent-consensus-stage-c.sh`

- [ ] **Step 1: Write the test (sourced — no shebang exec, no `exit`)**

```bash
#!/usr/bin/env bash
# Stage C: consensus_state `report` + `cumulative-diff` + resume (phase/task_index round-trip).

CO="plugins/co-agent/skills/co-agent"
ST="$CO/scripts/consensus_state.py"

D=$(mktemp -d "${TMPDIR:-/tmp}/csc.XXXXXX")
printf '# Plan\n### Task 1: a\n**Files:**\n- Modify: `README.md`\n- [ ] x\n' > "$D/plan.md"
python3 "$ST" init "$D" --docs "$D/plan.md" >/dev/null 2>&1

# --- report ---
python3 "$ST" task-start "$D" 0 >/dev/null 2>&1
python3 "$ST" task-round "$D" 0 >/dev/null 2>&1
python3 "$ST" task-done "$D" 0 >/dev/null 2>&1
python3 "$ST" set "$D" status done >/dev/null 2>&1
REP=$(python3 "$ST" report "$D" 2>&1)
assert_contains "$REP" "Consensus run report" "report has a title"
assert_contains "$REP" "1 done" "report counts done tasks"
assert_contains "$REP" "status**: done" "report shows status"
assert_file_exists "$D/.claude/co-agent-consensus/report.md" "report.md written to session dir"
# report with no session → exit 2
E=$(mktemp -d "${TMPDIR:-/tmp}/cscx.XXXXXX")
python3 "$ST" report "$E" >/dev/null 2>&1 && RR=0 || RR=$?
assert_eq "2" "$RR" "report with no session → exit 2"
rm -rf "$E"

# --- cumulative-diff: missing --plan → usage err; with --plan → rc 0 ---
python3 "$ST" cumulative-diff "$D" --base main >/dev/null 2>&1 && CD=0 || CD=$?
assert_eq "2" "$CD" "cumulative-diff without --plan → exit 2"
python3 "$ST" cumulative-diff "$D" --plan "$D/plan.md" --base main >/dev/null 2>&1 && CD2=0 || CD2=$?
assert_eq "0" "$CD2" "cumulative-diff with --plan → exit 0"

# --- resume: phase/task_index persist and round-trip ---
python3 "$ST" set "$D" phase P3 >/dev/null 2>&1
python3 "$ST" set "$D" task_index 2 >/dev/null 2>&1
assert_eq "P3" "$(python3 "$ST" get "$D" phase 2>&1)" "resume: phase persisted"
assert_eq "2" "$(python3 "$ST" get "$D" task_index 2>&1)" "resume: task_index persisted"

rm -rf "$D"
```

- [ ] **Step 2: Run the suite**

Run: `bash tests/run-all.sh 2>&1 | tail -3`
Expected: `ALL TESTS PASSED`, 0 failed, total up.

- [ ] **Step 3: Commit**

```bash
git add tests/structure/test-co-agent-consensus-stage-c.sh
git commit -m "test(co-agent): consensus Stage C — report + cumulative-diff + resume"
```

---

## Task 5: Final validation gate

- [ ] **Step 1: Full gate**

Run: `bash tests/run-all.sh 2>&1 | tail -2 && python3 scripts/test-plugins.py 2>&1 | tail -2 && python3 scripts/test-codex-plugins.py 2>&1 | tail -2`
Expected: all report all-passed.

- [ ] **Step 2: Confirm the pipeline is documented end-to-end (no "Stage A only" leftovers)**

Run: `grep -rn "Stage A implements P0–P2 only\|implement loop = Stage B\|P4 final gate + P5 report = Stage C" plugins/co-agent/skills/co-agent/references/consensus-pipeline.md || echo "pipeline marked complete"`
Expected: the old "Stage A only / lands later" phrasing is gone (P4/P5 now implemented).

- [ ] **Step 3: Scope-clean check (only Stage C files)**

Run: `git diff --name-only main..HEAD | grep -vE '^(plugins/co-agent/(skills/co-agent/(scripts/consensus_state\.py|SKILL\.md|references/consensus-pipeline\.md)|commands/consensus\.md)|tests/structure/test-co-agent-consensus-stage-c\.sh|docs/superpowers/)' || echo "scope clean — only Stage C files"`
Expected: `scope clean — only Stage C files`.

---

## Self-Review

- **Spec coverage (Stage C = P4 + P5 + wiring + resume):** P4 cumulative-diff gate → Task 2 (`cumulative-diff`) + Task 3 prose (reuse the gate); P5 report → Task 1 (`report`, session-local/gitignored, NO committed learnings) + Task 3 prose; full-pipeline default → Task 3 (command/SKILL); resume → Task 1/2 state + Task 3 prose + Task 4 round-trip test; tests → Task 4; final gate → Task 5. ✅
- **Placeholder scan:** full code in Tasks 1, 2, 4; concrete markdown in Task 3; exact commands + expected output in every run step. None.
- **Type/name consistency:** `cmd_report`/`cmd_cumulative_diff` added to `consensus_state.py` and routed as `report`/`cumulative-diff` (Tasks 1–2), consumed in Task 3 prose + Task 4 tests with the same flags (`--plan`/`--base`); report writes `.claude/co-agent-consensus/report.md` everywhere; `cumulative-diff` reuses the existing `_git` helper and the `parse_plan.parse` → `t["files"]` shape (matches Stage A/B). The `opt_after` helper is defined in `main()` (Task 2) before its use.
