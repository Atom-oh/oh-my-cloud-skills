# co-agent Consensus Pipeline — Design Spec (supersedes the review-only MVP scope)

- **Date**: 2026-06-09
- **Status**: Approved (direction); pending implementation plan
- **Supersedes/extends**: `2026-06-08-co-agent-consensus-mode-design.md` (the shipped **review-only** consensus is now a *sub-mode / gate* inside this pipeline, not the whole feature)
- **Borrowed from**: [NB3025/consensus-build](https://github.com/NB3025/consensus-build) — its autonomous spec→plan→implement pipeline + state-file/hook safety + TDD phase.
- **co-agent's contribution**: the consensus gates are driven by a **cross-family, multi-MODEL panel** (Kiro's many models + Codex + Gemini) instead of consensus-build's 3 same-family Claude subagents (Opus/Sonnet/Haiku). Cross-family diversity → independent review actually catches different failures.

## Problem & Goal

The **design and the plan already exist as written documents** — produced upstream by the superpowers pipeline (brainstorming → spec doc; writing-plans → implementation plan doc) and/or `/add-adr` (decision). The user wants co-agent to **take that document set and autonomously IMPLEMENT it**, with **multi-model consensus gates** validating the work, finishing with working, tested code.

**Goal:** `/co-agent:consensus` reads the input **document set (ADR + spec + writing-plans plan)** and autonomously executes the plan's tasks via TDD, with each gate being a co-agent **cross-family multi-model** independent fan-out + citation validation. It stops with a working implementation (tests green) or a clear non-convergence report.

**Entry depends on which documents are present** (a decision tree, not a one-line desc):

| Input docs | Entry point |
|------------|-------------|
| **ADR only** (no plan) | **generate the plan** → plan consensus gate → implement |
| **Spec only** (brainstorming design, no plan) | **generate the plan** → plan consensus gate → implement |
| **Plan doc present** (writing-plans output) | **review the existing plan** (consensus gate) → implement (no regeneration) |

So **plan generation is a normal path** (for ADR/spec inputs that have no plan), and the **plan consensus gate ALWAYS runs** before implementation — a freshly-generated plan especially needs multi-model review; a supplied plan is reviewed before it's trusted. consensus is the autonomous executor: an autonomous sibling to `subagent-driven-development`/`executing-plans`, except the cross-family multi-model panel (not Claude-only subagents + a human) is the gate.

## Closed loop (integration with the superpowers pipeline)

```
superpowers:brainstorming → docs/superpowers/specs/<date>-<topic>-design.md
superpowers:writing-plans → docs/superpowers/plans/<date>-<feature>.md   (bite-sized TDD tasks)
(optional) /add-adr        → docs/decisions/ADR-NNN.md
        ↓  (input = this document set)
/co-agent:consensus            (reads spec + plan [+ ADR])
        →  validate plan (consensus gate) → autonomous TDD implementation of the plan's tasks
           (per-task multi-model gate) → working code + report
```

> consensus consumes the SAME plan format `writing-plans` emits (checkbox `- [ ]` TDD steps,
> exact file paths, per-task commits), so the two compose directly.

## Pipeline (plan is an INPUT; implementation is the core)

```
P0  Detect & load the input doc set (ADR? spec? plan?); init state file
    .claude/co-agent-consensus/state.local.md (session_id, phase, current task index, round
    counters, artifact paths) + load learnings. Require a CLEAN working tree.
P1  PLAN (conditional on inputs):
      - plan doc present  → LOAD it as-is (no regeneration).
      - ADR/spec only (no plan) → GENERATE a TDD+Tidy plan from the decision/design.
    Either way, parse the plan into bite-sized tasks (checkbox `- [ ]` TDD steps + file paths).
P2  PLAN consensus gate (ALWAYS): multi-model fan-out (Kiro[models]/Codex/Gemini, independent)
    + check_citations.py — review the plan (generated or supplied) for implementability,
    bounded scope, missing tasks, and security-mandate violations; iterate (max rounds) until
    no CRITICAL/MAJOR. A generated plan especially must clear this before any code is written.
P3  Per-task loop over the plan's tasks (the heart of the feature):
      checkpoint → TDD: Red (write failing test) → Green (code) → Refactor →
      run gate: `bash tests/run-all.sh` + project tests MUST pass →
      multi-model consensus gate on the task's diff (Kiro[models]/Codex/Gemini independent +
        check_citations.py) → if CRITICAL/MAJOR: fix within round budget, else abort →
      ONE commit per task → advance task index in state (resumable).
    scope-lock to the plan's declared file set throughout.
P4  Final IMPLEMENTATION consensus gate ← multi-model review of the cumulative diff
    (this IS the shipped review-only consensus mode, reused) → fix loop until clean + tests green.
P5  Append learnings + final report (tasks done, decisions, test results, any aborted tasks).
```

Spec/decision authoring AND plan authoring happen **upstream** (brainstorming + writing-plans + ADR). consensus's job is faithful, gated, autonomous **execution** of that plan.

## Sub-modes (like consensus-build)

| Invocation | Does |
|------------|------|
| `/co-agent:consensus <doc>` | full pipeline P0–P5: detect inputs → plan (load or generate) → plan gate → implement → final gate → report (default) |
| `/co-agent:consensus plan <doc>` | P0–P2 only: plan (load/generate) + plan consensus gate, then stop |
| `/co-agent:consensus implement <plan>` | P0–P1(load)–P2(gate)→P3–P5: take an existing plan and implement it |
| `/co-agent:consensus review` | the shipped multi-model diff review (P4 standalone gate) |
| `--deep` | activate each AI's full model list for the gates |
| `--trust-plan` | skip the P2 plan gate (only sensible when the plan was already reviewed upstream) |

## Components

**Reuse (shipped in v1.7.2):**
- `check_citations.py` — gate citation validation.
- `co_agent_config.py` `pairs`/`matrix` + per-AI model lists + `deep` profile + MAX_CALLS cap.
- Fan-out (`ai-cli-adapters.md`) — the independent multi-model round.
- The review-only consensus = P4 final implementation gate (and the per-task gate in P3).

**New:**
- `scripts/consensus_state.py` — state file (bound to repo/branch/base/HEAD/initial-doc-hash/allowed-paths/session_id), phase/round counters, convergence + no-progress/oscillation detection, decisions/learnings (session-local, gitignored).
- Phase-orchestration in the co-agent skill (Mode "consensus build") — the monolithic prompt that drives P0–P5, calling the existing fan-out for gates and TDD for the P3 per-task loop.
- `hooks` in co-agent plugin.json: **Stop** (block premature stop while a consensus session is active & not converged), **PostToolUse** (track test pass/fail during P3), **PostToolUseFailure** (detect stuck/repeated-failure loops) — all **gated to the active `session_id`** so unrelated work is untouched.
- `commands/consensus.md` extended with the sub-modes + doc argument.
- `references/consensus-pipeline.md` — phase reference + safety.

## Convergence & stop criteria (per gate, and overall)

- **Gate converged**: 0 Claude-verified CRITICAL/MAJOR findings AND (for P5) tests green AND diff within scope.
- **Stop a gate loop**: `consensus.max_rounds` rounds (the existing config key, default 2); OR round R findings ⊇ R-1 (no-progress); OR oscillation (same hunk toggled).
- **Stop the pipeline (abort)**: tests regress and can't be fixed within the round budget; cumulative diff touches files outside the plan's declared set, or exceeds 2× the plan's estimated line count; unrelated working-tree change detected; quorum degrades (≤1 usable model output).

## Safety (panel concerns + consensus-build mitigations)

- **session_id state guard** — hooks no-op unless the active consensus session matches (unrelated work unaffected).
- **Clean working tree required**; **git checkpoint** (stash/tag) before each P4 task → trivial rollback.
- **Tests must pass** before every task commit (`tests/run-all.sh` + project tests); a failing build aborts rather than letting the panel review broken code.
- **Scope-lock**: edits restricted to the plan's declared file set.
- **AWS security-mandate veto**: a proposed change violating the global rules (`0.0.0.0/0`, `Principal:"*"`, secrets in env, …) is rejected before apply.
- **Local only**: never commit to protected branches, never push/reset/rebase/force, never touch cloud resources.
- **Prompt-injection hardening**: model output is untrusted data — cannot alter rounds, scope, or inject commands.
- **Consent + cost**: print the `(ai,model)` matrix + estimated calls before the first fan-out; confirm scope (the doc + repo) is OK to send to third-party AIs.
- **Confidence aggregation** (reintroduced from consensus-build) is **secondary to citation validation**: evidence (verified citation) is the primary filter; agreement count is a tiebreaker, never the deciding vote (honors "verify, don't vote-count").

## Error Handling

- Missing/oversized/errored `(ai,model)` pair → skip, note, continue (size guard + graceful degradation). Quorum guard if ≤1 remains.
- Input doc missing/unreadable → stop with a clear message (nothing to build from).
- P4 test failure → revert to checkpoint, attempt fix within round budget, else abort with the failing output.
- Crash/interrupt mid-run → state file lets a re-invocation resume from the last completed phase.

## Testing

- `consensus_state.py` unit tests (state bind/round tally/convergence/no-progress/oscillation/abort conditions) in `tests/structure/`.
- Hook guard tests: Stop/PostToolUse no-op when session_id inactive; active-session behavior.
- Gate integration (lightweight, mocked CLIs): multi-model fan-out → citation filter → converge/stop.
- Full suite (`run-all.sh` + `test-plugins.py` + `test-codex-plugins.py`) stays green.

## Phasing (implementation)

- **Stage A**: P0–P2 (detect inputs → plan load/generate → plan consensus gate) + state file + `plan` sub-mode. Lowest risk — no code edits, ends with a reviewed plan.
- **Stage B**: P3 per-task TDD implement loop + hooks (Stop/PostToolUse/PostToolUseFailure) + checkpoints + scope-lock + per-task test gate.
- **Stage C**: P4 final implementation gate (reuse review-only) + P5 learnings/report + full autonomy wiring + resume-from-state.
Each stage is its own implementation plan (writing-plans).

## Out of Scope / Future

- Generating the spec/ADR from a one-line description (that's `/add-adr` + co-agent ADR mode upstream; consensus may optionally call it, but doc-driven is primary).
- Cross-AI debate (groupthink — deliberately avoided; gates stay independent per round).
- Non-git workspaces.
