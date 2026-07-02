---
description: Autonomous doc→plan→implementation pipeline with cross-family multi-model consensus gates. All stages shipped — Stage A (P0–P2 plan gate), Stage B (P3 autonomous implement), Stage C (P4 final gate + P5 report); full-pipeline default with resume.
allowed-tools: Read, Glob, Grep, Bash, AskUserQuestion
argument-hint: "plan <doc...> | review [diff base] | implement <plan> | (full)  [--deep] [--trust-plan]"
---

# co-agent: consensus

Autonomous **doc → plan → implementation** with cross-family multi-model consensus gates.
**All stages are implemented** — Stage A (P0–P2: plan + plan-review gate), Stage B (P3:
autonomous implement), Stage C (P4 final gate + P5 report). Full reference: `references/consensus-pipeline.md`.

> **The host itself writes the code here** (TDD loop, main tree). Want a cross-provider peer
> to write it instead, sandboxed in a worktree, while the host stays the gatekeeper? Use
> `/co-agent:harness`. Side-by-side comparison: `SKILL.md` → "Consensus vs harness".

Argument: `$ARGUMENTS`

## Sub-modes
- `plan <doc...>` — P0–P2: detect input(s), load-or-generate the plan, run the plan consensus gate. **(available — Stage A)**
- `review [diff base]` — standalone multi-model diff review (the consensus gate run on its own). **(available — shipped v1.7.2)**
- `implement <plan>` — autonomously implement a reviewed plan (P3 TDD loop, multi-model gated). **(available — Stage B)**
- (default, no sub-mode) — runs the **full pipeline P0→P5** end-to-end: detect inputs → load/generate plan → P2 plan gate → P3 implement → P4 final gate → P5 report. **Resumable** — re-running reads `consensus_state` (phase/task_index) and continues.
- Flags: `--deep` (use each AI's full model list for the gates), `--trust-plan` (skip the P2 plan gate when the plan was already reviewed upstream). Round/call limits come from `consensus.max_rounds`/`consensus.max_calls` (config) — there is no `--apply`/`--max-rounds` flag.

## Stage A workflow (`plan <doc>`)
Let `SK="${CLAUDE_PLUGIN_ROOT}/skills/co-agent/scripts"`.

1. **Consent + cost**: confirm sending the doc(s) to third-party AIs; show
   `python3 "$SK/co_agent_config.py" matrix`.
1a. **Consult readiness** (`.claude/co-agent-panel.local.json` from `/co-agent:setup`):
   `check_panel.py fresh` (re-run `/co-agent:setup` if `stale`), then `check_panel.py
   gate-eligible <peer>` per peer — keep only `true` (`status==READY` **and** `raw_cli`).
   `gate-eligible`, **not** bare `status`: the fan-out calls raw CLIs only, so a plugin-only
   peer (READY, `raw_cli:false`) yields zero output yet would falsely satisfy the gate.
   consensus is **non-degraded**: with **no gate-eligible peer**, do **not** solo — **block**
   and tell the user to run `/co-agent:setup`. Absent summary → run `/co-agent:setup` first.
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
