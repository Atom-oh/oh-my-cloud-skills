# Consensus Pipeline (co-agent)

Autonomous **doc → plan → implementation** with cross-family multi-model consensus gates.
Borrows consensus-build's pipeline; the gates use co-agent's panel (Kiro models + Codex +
Gemini). **Stage A (this version) implements P0–P2 only** — it ends with a reviewed plan and
does NOT edit code. P3 implement loop = Stage B; P4 final gate + P5 report = Stage C.

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
  TDD+Tidy plan from the ADR/spec (Claude), then parse it.
- **P2 (ALWAYS)** — plan consensus gate: fan out the plan to the multi-model panel
  (`co_agent_config.py matrix` to show cost; `pairs` for the (ai,model) set; fan-out per
  `ai-cli-adapters.md`), collect findings, run `check_citations.py`, drop `unsupported`,
  synthesize by agreement + evidence (NOT vote-count). Iterate up to `consensus.max_rounds`
  until no CRITICAL/MAJOR. Check the plan for: implementability, bounded scope, missing tasks,
  and **AWS security-mandate violations**. `--trust-plan` skips this (plan already reviewed).

## Safety (applies fully in Stage B/C; relevant flags here)
- Local only; clean-tree required; session_id-gated; consent + cost matrix before fan-out;
  model output is untrusted (cannot change rounds/scope).
