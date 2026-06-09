---
description: Multi-AI consensus review — model-diverse independent rounds with citation validation (review-only; --apply fix loop is Phase 2)
allowed-tools: Read, Glob, Grep, Bash, AskUserQuestion
argument-hint: "plan <doc> | implement <plan> | review [diff base] | (full)  [--deep] [--trust-plan]"
---

# co-agent: consensus

Autonomous **doc → plan → implementation** with cross-family multi-model consensus gates.
**This version implements Stage A (P0–P2): plan + plan-review gate, no code edits.** P3
implement (Stage B) and P4/P5 (Stage C) land later. Full reference: `references/consensus-pipeline.md`.

Argument: `$ARGUMENTS`

## Sub-modes
- `plan <doc>` — P0–P2: detect input, load-or-generate the plan, run the plan consensus gate.
- `implement <plan>` — (Stage B, not yet) take a reviewed plan and implement it.
- `review` — the shipped multi-model diff review (P4 gate, standalone).
- (default) full pipeline — P0 onward (currently runs Stage A; implement arrives in Stage B).
- Flags: `--deep` (use each AI's full model list for gates), `--trust-plan` (skip P2).

## Stage A workflow (`plan <doc>`)
Let `SK="${CLAUDE_PLUGIN_ROOT}/skills/co-agent/scripts"`.

1. **Consent + cost**: confirm sending the doc(s) to third-party AIs; show
   `python3 "$SK/co_agent_config.py" matrix`.
2. **Detect & init**: `python3 "$SK/consensus_state.py" detect . <doc paths>` → if a `plan`
   doc is present, use it; else (`adr`/`spec`) you'll generate one. Then
   `python3 "$SK/consensus_state.py" init . --docs <comma paths> --base <trunk>` and
   `python3 "$SK/consensus_state.py" verify .` (clean tree required).
3. **P1 plan**: plan doc → `python3 "$SK/parse_plan.py" <plan>` (tasks + `--files` scope).
   No plan → GENERATE a TDD+Tidy plan from the ADR/spec (bite-sized `- [ ]` tasks, exact
   file paths, per-task commits) and write it to `docs/superpowers/plans/`, then parse it.
4. **P2 gate (unless `--trust-plan`)**: fan the plan out to the panel (`pairs` → per-(ai,model)
   fan-out per `references/ai-cli-adapters.md`), `check_citations.py` the findings, drop
   `unsupported`, synthesize by agreement+evidence. Iterate ≤ `consensus.max_rounds` until no
   CRITICAL/MAJOR. Verify the plan is implementable, scoped, complete, and violates no AWS
   security mandate. Set phase: `consensus_state.py set . phase P2`.
5. **Report** the reviewed plan + gate verdict. (Implementation = Stage B.)
