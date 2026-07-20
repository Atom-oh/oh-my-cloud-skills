# Kiro spec format + task file-scoping

`/kiro:delegate`'s Plan stage writes a **Kiro-native spec** to
`.kiro/specs/<name>/` — the same format Kiro's own spec-driven workflow uses (so a user
can also finish the work by hand in Kiro IDE if delegation ever needs to stop mid-way):

```
.kiro/specs/<name>/
├── requirements.md   # user stories + acceptance criteria (or bugfix.md for a fix spec)
├── design.md          # architecture, data flow, sequence diagrams, key decisions
└── tasks.md           # the implementation plan, in a format this plugin's own scripts parse
```

## `requirements.md`

Plain prose + a list of user stories, each with acceptance criteria:

```markdown
# Requirements: <feature name>

## User Story 1: <short title>
As a <role>, I want <capability>, so that <benefit>.

**Acceptance criteria:**
- [ ] <testable criterion>
- [ ] <testable criterion>
```

## `design.md`

Architecture and key decisions — whatever level of detail the change warrants (a
one-paragraph design for a small change is fine). Cover: approach, affected
components/files, data flow, error handling, and anything a reviewer would ask about.

## `tasks.md` — MUST match `parse_plan.py`'s format

This plugin reuses co-agent's `parse_plan.py`/`scope_guard.py` verbatim (copied into
`scripts/`), so `tasks.md` must use the **exact** task-block format those scripts parse:

```markdown
## Task 1: <short title>

**Files:**
- Create: `path/to/new_file.py`
- Modify: `path/to/existing_file.py`
- Test: `path/to/existing_file_test.py`

- [ ] <step 1>
- [ ] <step 2>
```

Rules that matter (the parser is regex-based, not lenient):

- The task heading MUST be `## Task N: <title>` or `### Task N: <title>` — the number is
  required and must be sequential-enough for `parse_plan.py --count`/ordering to make sense.
- File paths **MUST be backtick-wrapped** (`` `path` ``) directly after
  `Create:`/`Modify:`/`Test:` — a bare (non-backtick) path is silently ignored, which
  yields an *empty* allowed-file-set for that task and makes `scope_guard.py` reject
  every edit Kiro makes for it. This is the single most common authoring mistake — always
  backtick every path.
- Every file Kiro is expected to touch for a task MUST appear in that task's `**Files:**`
  block. `scope_guard.py` checks against the **plan-wide union of every task's declared
  paths** (it has no per-task filter — verbatim copy of co-agent's script), so it alone
  cannot stop Task A's implementer run from touching a path Task B declared. Per-task
  isolation instead comes from wave-planning only ever grouping tasks with
  pairwise-**disjoint** file sets into the same wave (see "Wave planning" below) — write
  tasks with non-overlapping file sets whenever they're meant to run independently.
- Steps are plain `- [ ]` checkboxes; `/kiro:delegate` checks them off as tasks complete
  (mirrors Kiro IDE's own task-list UI, so the file stays meaningful if a user opens it
  there).

## Wave planning (parallel tasks)

`/kiro:delegate` groups tasks into **waves** of pairwise-disjoint file sets (same
algorithm as co-agent's `delegated-implement.md` "Parallel waves"), capped by
`delegate.parallel_tasks` (default 3). Two tasks whose `**Files:**` blocks share a path
never run in the same wave — write tasks so file sets are disjoint where the work is
genuinely independent; a plan that's inherently sequential will naturally collapse to
1-task waves, which is correct, not a bug.

## Why reuse Kiro's own spec format instead of a generic plan.md

1. **Kiro reads it as context** — pointing `kiro-cli chat` at `requirements.md`/`design.md`
   via `fs_read` gives the implementer the same context a human working the spec in Kiro
   IDE would have.
2. **Escape hatch** — if delegation stalls (Kiro's fix loop keeps failing and the user
   wants to intervene), the spec is already in the shape Kiro IDE expects; a user can open
   the project in Kiro and continue the remaining tasks natively instead of through this
   plugin.
3. **No format the user has to learn twice** — Kiro's own docs already teach this
   requirements/design/tasks shape.
