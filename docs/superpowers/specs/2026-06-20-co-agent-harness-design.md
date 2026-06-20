# co-agent:harness — Design Spec

**Status:** Draft (pending co-agent panel re-orientation + user review)
**Date:** 2026-06-20
**Author:** Junseok Oh (with Claude)
**Plugin:** `co-agent` (oh-my-cloud-skills marketplace)

## 1. Summary

`co-agent:harness` is an autonomous **design → implement → review** orchestrator that
separates roles across AI providers. The **host** (the AI CLI running the skill —
Claude in Claude Code, Codex in Codex) owns the **design, the verification spec (tests),
and every commit**. A **cross-provider peer implementer** writes the code, but only
inside an **isolated git worktree** it can never escape. The existing co-agent
**consensus gate** reviews both the plan and the resulting code.

This extends the cross-provider rationale already proven for review ("a model misses its
own bug patterns") to *implementation*: the model that designs is never the model that
implements, and neither is the sole reviewer.

## 2. Goals / Non-Goals

**Goals**
- Decorrelate design and implementation blind spots via provider separation.
- Let a strong code-generation model implement while the host orchestrates and judges.
- Preserve the co-agent trust model: only the host writes to the working branch.
- Reuse the consensus pipeline's infrastructure rather than duplicating it.
- Run as a **durable relay**: each stage leaves an on-disk artifact and only advances when
  that artifact validates (output gate), so runs resume, verify, and debug from disk.
- Keep the skill body lean (repo token-economy value); delegate heavy rules to references.

**Non-Goals**
- Replacing the current host-implements consensus pipeline (harness is opt-in, additive).
- Letting any external AI commit, push, or mutate the live working tree.
- Building the #1 adversarial-round / #2 escalation gate upgrades (separate work;
  referenced here as prerequisites of the gate harness calls).
- Multi-implementer tournaments (possible future mode; out of scope now).

## 3. Roles & Provider Mapping

| Role | Who | Notes |
|------|-----|-------|
| Chair / Designer / Committer | **host** | Claude Code → Claude; Codex → Codex (`CO_AGENT_HOST`) |
| Implementer | **peer-host counterpart** (default) | host=claude → codex; host=codex → claude(opus). Overridable via `harness.implementer`. |
| Review panel | Kiro + peer host CLI + Agy (Gemini fallback) | the existing host-aware consensus panel |

By construction the implementer ≠ designer ≠ sole reviewer. `harness.implementer` may be
set to any installed peer (`codex`/`claude`/`agy`); `null` resolves to the counterpart.

## 4. Flow

```
/co-agent:harness <adr|spec|plan|task>
 H0  Detect host(chair) · panel · implementer → consent + cost matrix → require clean tree
 H1  DESIGN (host)   : plan present → LOAD (parse_plan); else generate TDD plan from ADR/spec (consensus P1)
 H2  PLAN GATE        : panel reviews the plan → iterate to no CRITICAL/MAJOR (consensus gate; depends on #1/#2)
 H3  DELEGATED IMPLEMENT (per task — the new core)
     a) host writes the failing test (red)              # verification spec stays host-owned
     b) create an isolated git worktree at the base commit
     c) invoke implementer peer in WRITE mode inside the worktree, scoped to the task's file set
     d) host pulls the worktree diff → scope_guard (revert out-of-scope) → run tests (green?)
        └ not green / out-of-scope → feedback → bounded fix loop ≤ harness.max_fix_rounds
                                              → exhausted → task-abort + escalate
     e) host applies the validated diff to the working branch — SOLE committer, one commit/task
     f) write tasks/<idx>/result.json; consensus_state task-done; remove the worktree
 H4  CODE GATE         : consensus gate on the cumulative diff (consensus P4) → fix loop → escalate if unresolved
 H5  REPORT            : consensus_state report + implementer attribution; assert all worktrees removed
```

Every stage **emits an artifact to the run directory** (§12) and **only advances when that
artifact exists and validates** (output gate). This makes the relay durable: resume,
verification, and debugging all read from disk rather than re-deriving.

## 5. Trust Boundary (the crux)

- **Quarantined writes.** The peer writes *only* inside an ephemeral worktree, never the
  live tree or branch. The worktree is created at the base commit, scoped to the task,
  and removed (`trap … EXIT`, plus explicit removal in H3f) including on abort.
- **Quarantined write-mode adapters.** The write variants (`codex exec` without
  `-s read-only`; `claude -p` without `--permission-mode plan`; `agy -p` without
  `--sandbox`) exist **only** on the harness implement path and are clearly marked as
  such. Every other co-agent path (review, decide, ADR, plan/code gates) stays
  read-only/advisory. This is the single place in the plugin where an external AI may write.
- **Host owns verification + commits.** Host writes the red test, runs `scope_guard` +
  the test gate + the consensus review gate, and is the only committer to the working branch.
- **Model output is untrusted.** The implementer cannot change scope, round counts, or
  commit. Out-of-scope paths are reverted. A passing self-claim is never trusted — only
  the host-run test gate decides green.
- **Decorrelation.** Designer, implementer, and the review panel are distinct providers.

## 6. Components

**New**
- `/co-agent:harness` skill + command (orchestration steps H0–H5).
- `references/delegated-implement.md` — lean reference for the worktree lifecycle,
  write-mode adapters, the host-owns-red-test rule, and the fix loop. (The only new doc.)
- Worktree lifecycle helper (create-at-base / scoped / pull-diff / remove). Implemented in
  bash within the reference, or a small `scripts/worktree.py` if logic warrants — decided
  in the implementation plan.
- `scripts/stage_result.py` — write/validate a stage `result.json` against a shared schema
  and append a row to `stage_wall.tsv`; gates call it and exit non-zero on missing/failing
  artifacts (the output-gate mechanism, §11).
- `co_agent_config.py` additions: `harness.implementer`, `harness.max_fix_rounds`, and
  write-mode flag plumbing for the implementer adapter.

**Reused (unchanged)**
- `parse_plan.py`, `scope_guard.py`, `consensus_state.py` (init / verify / task /
  cumulative-diff / report), `check_citations.py`, `co_agent_config.py`
  (panel / pairs / matrix / flags / host).
- The consensus gate (`references/consensus-mode.md`) for H2 and H4.
- consent + cost-matrix discipline, clean-tree requirement, `session_id` gating,
  gitignored session state.

## 7. Configuration

Added to `co-agent.defaults.json` (overridable in `.claude/co-agent.local.json` via
`/co-agent:configure`):

```jsonc
"harness": {
  "implementer": null,        // ai id | null → peer-host counterpart
  "max_fix_rounds": null      // int | null → inherit consensus.max_rounds
}
```

- `harness.implementer` validated against the installed-AI charset rules already in
  `co_agent_config.py`; rejected if it equals the current host.
- Resolution helper `co_agent_config.py implementer --host <h>` prints the effective
  implementer (counterpart when null), mirroring `panel`/`pairs`.

## 8. Error Handling

| Condition | Behavior |
|-----------|----------|
| Implementer CLI missing / errors / timeout | **Fall back to host-implement** for that task, note it. Never blocks. |
| Worktree creation fails | Abort the harness run with a clear message. Never silently write to the live tree. |
| Out-of-scope path in worktree diff | Revert those paths, feed back to the implementer. |
| Fix loop exhausted (still red / still flagged) | `task-abort` + escalate (verdict REVIEW); continue or stop per state policy. |
| Dirty working tree at H0 | Refuse to start (clean-tree required, same as consensus). |
| Plan gate (H2) unresolved after max_rounds | Escalate (REVIEW); do not enter implement. |

## 9. Testing

`tests/structure/test-co-agent-harness.sh`:
- Implementer resolution: default = counterpart per host (claude↔codex); explicit override
  respected; host-as-implementer rejected.
- Write-mode adapter flags built correctly per AI; read-only/advisory paths unaffected
  (regression guard that review/gate adapters still carry `-s read-only` / `plan` / `--sandbox`).
- `scope_guard` rejects an out-of-scope worktree path.
- **Host-only-commit invariant**: simulate an implementer writing in a worktree → assert no
  commit is attributable to the peer and the host performs the single commit.
- Live-tree-untouched invariant: during a simulated implement step the live tree stays clean.
- Graceful fallback to host-implement when the implementer CLI is absent.
- `harness.*` config round-trip (set/get/show) and host-equals-implementer rejection.
- **Output gates**: a stage with a missing/invalid `result.json` blocks advancement
  (e.g. no `plan.md` → H2 refused; task `result.json` with `green=false` → no commit).
- `stage_result.py` schema validation: well-formed result accepted, malformed rejected;
  `stage_wall.tsv` gets one row per stage.
- Resume skips a stage whose valid artifact already exists in the run directory.
- Run directory is gitignored (no session artifacts leak into commits).

## 10. Relationship to consensus & Token Economy

`harness` is the **orchestration layer** (design → implement → review); `consensus` is the
**gate** it calls for H2/H4 and remains usable standalone. The skill body stays lean —
orchestration steps only — with gate mechanics delegated to `consensus-mode.md` and CLI
details to `ai-cli-adapters.md`. The harness depends on the agreed gate upgrades
(#1 adversarial cross-critique round, #2 explicit disagreement/escalation protocol) being
present in the consensus gate; those are tracked as separate prerequisite work.

## 11. Stage artifacts, relay & output gates

The harness runs as a **durable relay** (dev host → peer artifact → host improvement),
not an in-memory synthesis. Every stage writes its output to disk, and a stage is
considered passed **only when its artifact exists and validates** — this is the output
gate. The state machine in `consensus_state.py` advances on artifact presence, which is
what makes the pipeline resumable, auditable, and debuggable.

**Run directory** (`.claude/co-agent-consensus/runs/<session_id>/`, gitignored —
session-local, never committed):

```
runs/<session_id>/
  plan.md                         # H1 design output (or a copy of the loaded plan)
  plan-gate/
    review-<ai>-<round>.md        # raw per-AI plan review
    findings.json                 # parsed + citation-validated findings
    result.json                   # { verdict, criticals, majors, rounds }
  tasks/<idx>/
    red.diff                      # H3a host-authored failing test
    task.diff                     # H3d validated implementer worktree diff
    review-<ai>.md                # per-AI task review
    result.json                   # { green, in_scope, verdict, rounds, implementer }
  code-gate/
    review-<ai>.md
    result.json                   # { verdict, criticals, majors, rounds }
  stage_wall.tsv                  # one row per stage: stage \t start \t end \t status (timing/debug)
  report.md                       # H5 human summary (rendered by consensus_state report)
```

**Output gate rules**
- **H1 → H2**: a `plan.md` must exist and parse (`parse_plan`); otherwise the run cannot
  enter the plan gate.
- **H2 → H3**: `plan-gate/result.json` must exist with `verdict != FAIL` and no unresolved
  CRITICAL/MAJOR; otherwise escalate (REVIEW), do not implement.
- **per task (H3)**: `tasks/<idx>/result.json` must record `green=true` and `in_scope=true`
  before `consensus_state task-done`. A missing/red/out-of-scope result blocks the commit.
- **H4 → H5**: `code-gate/result.json` must show no unresolved CRITICAL/MAJOR and tests green.

`result.json` files use a small shared schema so gates are **machine-checkable** rather
than prose-parsed. A new helper `scripts/stage_result.py` (write/validate a result.json
against the schema, and append to `stage_wall.tsv`) keeps this mechanical; gate scripts
exit non-zero on a missing or failing artifact.

**Resume** reads `consensus_state` *and* the run directory: a stage whose valid artifact
already exists is skipped, so re-invocation continues exactly where it stopped.

## 12. Open Questions (to resolve in the plan)

- Worktree helper as inline bash vs a small `scripts/worktree.py` (lean vs testable).
- Whether H3a (host red test) is mandatory for *every* task or skippable for pure-refactor
  tasks that already have coverage.
- Escalation surface: a `needs-human` status in `consensus_state` is the leading option,
  recorded alongside the failing `result.json` verdict (REVIEW) — confirm in the plan.
- Whether `stage_result.py` is its own script or folded into `consensus_state.py`.
