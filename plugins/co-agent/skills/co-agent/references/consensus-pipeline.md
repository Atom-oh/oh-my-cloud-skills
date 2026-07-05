# Consensus Pipeline (co-agent)

Autonomous **doc → plan → implementation** with cross-family multi-model consensus gates.
Borrows consensus-build's pipeline; the gates use co-agent's host-aware panel (Kiro models +
the peer host CLI + Agy). **All phases P0–P5 are implemented
(Stage A: P0–P2, Stage B: P3, Stage C: P4–P5).**

## Entry — conditional on input documents

| Input | Entry |
|-------|-------|
| ADR only (no plan) | generate plan → P2 gate → (implement, Stage B) |
| Spec only (brainstorming design, no plan) | generate plan → P2 gate → (implement) |
| Plan doc present (writing-plans) | LOAD plan (no regen) → P2 gate → (implement) |

Detect with `scripts/consensus_state.py detect <root> <paths>` → `adr|spec|plan|unknown`.

## Phases (Stage A = P0–P2)

- **P0** — `consensus_state.py init` writes `.claude/co-agent-consensus/state.local.md`
  (session_id, phase, task_index, repo/branch/base/HEAD, per-doc sha, allowed_paths).
  Require a clean tree (`consensus_state.py verify`).
- **P1** — plan doc present → `parse_plan.py <plan>` to load tasks + file set; else generate a
  TDD+Tidy plan from the ADR/spec (current host), then parse it.
- **P2 (default-on; `--trust-plan` is the explicit escape hatch for an already-reviewed plan)**
  — plan consensus gate: fan out the plan to the multi-model panel
  (`co_agent_config.py matrix` to show cost; `pairs` for the (ai,model) set; fan-out per
  `ai-cli-adapters.md`), collect findings, run `check_citations.py`, drop `unsupported`,
  synthesize by agreement + evidence (NOT vote-count). Iterate up to `consensus.max_rounds`
  until no CRITICAL/MAJOR. Check the plan for: implementability, bounded scope, missing tasks,
  and **AWS security-mandate violations**. `--trust-plan` skips this (plan already reviewed).
- **P3 (Stage B) — autonomous TDD implement loop**: reuse `subagent-driven-development` with
  the co-agent multi-model gate as the review checkpoint. Per plan task: git checkpoint →
  TDD (red→green→refactor) → `scope_guard.py` scope-lock → AWS security-mandate veto →
  test gate (`tests/run-all.sh` + project tests must pass; revert on failure) → multi-model
  consensus gate on the task diff → fix ≤`consensus.max_rounds` or `task-abort` → one commit
  per task → `consensus_state.py task-done`. Session-gated hooks: **Stop** keeps the loop
  going until all tasks are done/aborted, **PostToolUse** records test results and flags
  stuck loops (consecutive failing test runs). Local commits only — never push/reset/rebase.
- **P4 (Stage C) — final cumulative-diff gate**: run the multi-model gate on
  `consensus_state.py cumulative-diff . --plan <plan> --base <trunk>` (the whole implementation
  diff, scoped to the plan's file set) → fix ≤`consensus.max_rounds` until no CRITICAL/MAJOR AND
  tests green.
- **P5 (Stage C) — report**: `consensus_state.py report .` renders the run summary (tasks
  done/aborted, per-task rounds, status, tests) to stdout + `.claude/co-agent-consensus/report.md`
  (gitignored, session-local — no committed cross-run learnings).

**Resume**: the pipeline is resumable — `consensus_state` persists `phase`/`task_index`/`tasks`,
so a re-invocation continues from the last completed step rather than restarting.

## Safety (applies fully in Stage B/C; relevant flags here)
- Local only; clean-tree required; session_id-gated; consent + cost matrix before fan-out;
  model output is untrusted (cannot change rounds/scope).
