---
description: Autonomous doc→plan→implementation pipeline with cross-family multi-model consensus gates. Current Stage A runs P0–P2 (load/generate a plan + plan-review gate, no code edits); implementation is Stage B.
allowed-tools: Read, Glob, Grep, Bash, AskUserQuestion
argument-hint: "plan <doc...> | review [diff base] | (full)  [--deep] [--trust-plan]   (implement = Stage B, reserved)"
---

# co-agent: consensus

Autonomous **doc → plan → implementation** with cross-family multi-model consensus gates.
**This version implements Stage A (P0–P2): plan + plan-review gate, no code edits.** P3
implement (Stage B) and P4/P5 (Stage C) land later. Full reference: `references/consensus-pipeline.md`.

Argument: `$ARGUMENTS`

## Sub-modes
- `plan <doc...>` — P0–P2: detect input(s), load-or-generate the plan, run the plan consensus gate. **(available — Stage A)**
- `review [diff base]` — standalone multi-model diff review (the consensus gate run on its own). **(available — shipped v1.7.2)**
- `implement <plan>` — autonomously implement a reviewed plan (P3 TDD loop). **(Stage B — reserved, not yet)**
- (default, no sub-mode) — runs the full pipeline; **currently an alias for Stage A (P0–P2)** until Stage B/C land.
- Flags: `--deep` (use each AI's full model list for the gates), `--trust-plan` (skip the P2 plan gate when the plan was already reviewed upstream). Round/call limits come from `consensus.max_rounds`/`consensus.max_calls` (config) — there is no `--apply`/`--max-rounds` flag.

## Stage A workflow (`plan <doc>`)
Let `SK="${CLAUDE_PLUGIN_ROOT}/skills/co-agent/scripts"`.

1. **Consent + cost**: confirm sending the doc(s) to third-party AIs; show
   `python3 "$SK/co_agent_config.py" matrix`.
2. **Detect & init**: `python3 "$SK/consensus_state.py" detect . <doc...>` → if a `plan`
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
