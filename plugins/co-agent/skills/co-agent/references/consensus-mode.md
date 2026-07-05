# Consensus Gate Mechanics (co-agent)

> **Scope:** this file defines the **multi-model consensus GATE** — the independent
> fan-out + citation-validation + synthesis step. The gate is used both by the standalone
> `/co-agent:consensus review` and as a phase gate inside the pipeline (P2 plan gate, and
> P4 implementation gate in Stage C). **The end-to-end pipeline is authoritative in
> `references/consensus-pipeline.md`** — this file is just the reusable gate rules.

## Why
- **Model diversity** (different families catch different bugs) > intra-family duplication.
- **Citation validation** turns "verify, don't vote-count" into a mechanical filter.

## The gate (one round)
1. Consent + scope; print `co_agent_config.py matrix` (provider·model·ctx + max calls).
2. One **independent** round over `(ai,model)` pairs (`co_agent_config.py pairs`; `deep`
   profile activates each AI's full model list; capped by `consensus.max_calls`, default 24 — sized so the committed deep profile's 5 pairs survive even the hybrid gate's 2-phase split, 24 // 2 rounds // 2 phases = 6 ≥ 5).
   `pairs` emits the panel key in the first column (`kiro-cli`, `claude`, `codex`, `agy`) —
   these ARE the binary names (the old `kiro`/`antigravity` aliases were removed), so invoke
   each directly via the `references/ai-cli-adapters.md` fan-out `case "$ai"` block, which
   maps every key to its exact command line. (Note the Kiro binary is `kiro-cli`, never a
   bare `kiro`.)
3. `check_citations.py` classifies findings → drop `unsupported`, flag `needs-review`.
4. Chair synthesis: **raw agreement + evidence strength**, attribute dissent. No confidence
   weighting (contradicts the chair principle).
5. **Quorum guard**: ≤1 usable pair → single-opinion review, not "consensus".

A **gate loop** repeats this round up to `consensus.max_rounds` (default 2) until no
CRITICAL/MAJOR finding remains (also stop on no-progress / oscillation).

## Multi-model rules
- Default profile = one model per AI. The committed default is `deep`, which activates
  each AI's `models` list — Kiro's mainstay panel is **opus / kimi-k2.5 / glm-5**.
- Cap: `rounds × pairs ≤ max_calls`; trim same-family (round-robin) first, then warn.
- Same provider *family* (e.g. two Agy-routed variants) = diminishing returns; the matrix warns.
  **Kiro is the exception** — it's a cross-vendor router (Claude / Moonshot / Zhipu), so
  multiple Kiro models are genuine cross-family diversity (matrix notes it, no warning).
- **`kimi-k2.5` is an `[Internal]` preview** in `kiro-cli --list-models`. If an account
  can't access it, the fan-out *skips* that pair (Kiro drops to 2 models) — it does not
  auto-substitute. The designated fallback is **`claude-sonnet-4.6`** (stable, 1M ctx):
  `python3 scripts/co_agent_config.py set kiro-cli models claude-opus-4.8,claude-sonnet-4.6,glm-5`
  (write to `.claude/co-agent.local.json` to keep it personal, or edit `co-agent.defaults.json`).

## Where the gate is used
- **`/co-agent:consensus review`** — the gate, standalone, on a git diff (shipped v1.7.2).
- **Pipeline P2** — the gate on a plan document (Stage A).
- **Pipeline P4** — the gate on the cumulative implementation diff (Stage C).

> Roadmap/terminology is **Stage A (P0–P2) · Stage B (P3 implement) · Stage C (P4–P5)** —
> see `references/consensus-pipeline.md`. (The earlier "Phase 2 / `--apply`" wording is retired.)
