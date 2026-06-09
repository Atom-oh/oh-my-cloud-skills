# co-agent Consensus Pipeline — Design Spec (supersedes the review-only MVP scope)

- **Date**: 2026-06-09
- **Status**: Approved (direction); pending implementation plan
- **Supersedes/extends**: `2026-06-08-co-agent-consensus-mode-design.md` (the shipped **review-only** consensus is now a *sub-mode / gate* inside this pipeline, not the whole feature)
- **Borrowed from**: [NB3025/consensus-build](https://github.com/NB3025/consensus-build) — its autonomous spec→plan→implement pipeline + state-file/hook safety + TDD phase.
- **co-agent's contribution**: the consensus gates are driven by a **cross-family, multi-MODEL panel** (Kiro's many models + Codex + Gemini) instead of consensus-build's 3 same-family Claude subagents (Opus/Sonnet/Haiku). Cross-family diversity → independent review actually catches different failures.

## Problem & Goal

A decision/design has been made (an ADR via `/add-adr`, a spec, or a brainstorming design doc). The user wants to **carry that document autonomously through plan → implementation**, with **multi-model consensus gates** validating each stage, finishing with working, tested code.

**Goal:** `/co-agent:consensus <decision-or-design-doc>` runs an autonomous **doc → plan → TDD implementation** pipeline; each gate is a co-agent multi-model independent fan-out + citation validation; it stops with a working implementation (tests green) or a clear non-convergence report.

This is **document-driven** (not a one-line feature). The spec/decision phase is **upstream** (done by `/add-adr`, co-agent ADR mode, or brainstorming) — consensus picks up from the approved artifact.

## Closed loop (integration)

```
/add-adr  ·OR·  co-agent ADR mode (multi-AI)  ·OR·  superpowers brainstorming
        →  decision/design doc  (docs/decisions/ADR-NNN.md | spec.md | design.md)
        ↓
/co-agent:consensus <doc>
        →  plan (consensus gate) → TDD implementation (consensus gate) → working code + report
```

## Pipeline (borrowed from consensus-build, doc-driven)

```
P0  State init: .claude/co-agent-consensus/state.local.md (session_id, phase, round counters,
    artifact paths) + load docs/.../learnings.md.  Require a CLEAN working tree.
P1  PLAN: from the input doc, generate a TDD+Tidy implementation plan (impl-plan-{name}.md).
P2  PLAN consensus gate ← multi-model fan-out (Kiro[models]/Codex/Gemini, independent) +
    check_citations.py; aggregate; iterate (max N rounds) until no CRITICAL/MAJOR.
P3  Auto-resolve "needs-review" items into a decisions log (session-local).
P4  TDD IMPLEMENT: per plan task → Red (failing test) → Green (code) → Refactor; ONE commit
    per task; **tests must pass** (`bash tests/run-all.sh` + project tests) before each commit;
    scope-lock to the plan's file set; git checkpoint before each task.
P5  IMPLEMENTATION consensus gate ← multi-model review of the cumulative diff
    (this IS the shipped review-only consensus mode, reused as the final gate) → fix loop
    (max N) until no CRITICAL/MAJOR + tests green.
P6  Append learnings + final report (what was built, decisions, test results).
```

Spec/decision review (consensus-build's Phase 2) is **out** — that happened upstream in the ADR/brainstorming step.

## Sub-modes (like consensus-build)

| Invocation | Does |
|------------|------|
| `/co-agent:consensus <doc>` | full: doc → plan → implement (default) |
| `/co-agent:consensus plan <doc>` | doc → plan only (stop after P2) |
| `/co-agent:consensus implement <plan>` | existing plan → P4–P6 |
| `/co-agent:consensus review` | the shipped multi-model diff review (P5 standalone gate) |
| `--deep` | activate each AI's full model list for the gates |

## Components

**Reuse (shipped in v1.7.2):**
- `check_citations.py` — gate citation validation.
- `co_agent_config.py` `pairs`/`matrix` + per-AI model lists + `deep` profile + MAX_CALLS cap.
- Fan-out (`ai-cli-adapters.md`) — the independent multi-model round.
- The review-only consensus = P5 gate.

**New:**
- `scripts/consensus_state.py` — state file (bound to repo/branch/base/HEAD/initial-doc-hash/allowed-paths/session_id), phase/round counters, convergence + no-progress/oscillation detection, decisions/learnings (session-local, gitignored).
- Phase-orchestration in the co-agent skill (Mode "consensus build") — the monolithic prompt that drives P0–P6, calling the existing fan-out for gates and TDD for P4.
- `hooks` in co-agent plugin.json: **Stop** (block premature stop while a consensus session is active & not converged), **PostToolUse** (track test pass/fail in P4), **PostToolUseFailure** (detect stuck/repeated-failure loops) — all **gated to the active `session_id`** so unrelated work is untouched.
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

- **Stage A**: P1–P3 (doc → plan → plan consensus gate) + state file + sub-modes `plan`. Lowest risk (no code edits).
- **Stage B**: P4 TDD implement + hooks (Stop/PostToolUse/PostToolUseFailure) + checkpoints + scope-lock + test gate.
- **Stage C**: P5 implementation gate (reuse review-only) + P6 learnings/report + full autonomy wiring.
Each stage is its own implementation plan.

## Out of Scope / Future

- Generating the spec/ADR from a one-line description (that's `/add-adr` + co-agent ADR mode upstream; consensus may optionally call it, but doc-driven is primary).
- Cross-AI debate (groupthink — deliberately avoided; gates stay independent per round).
- Non-git workspaces.
