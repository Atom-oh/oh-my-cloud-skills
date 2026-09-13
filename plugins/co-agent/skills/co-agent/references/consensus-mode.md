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
   profile activates each AI's full model list). Derive the roster and cap from
   `matrix`/`pairs` for the current host, rounds and phases; do not reuse an old
   default pair count.
   `pairs` emits the supported panel key in the first column —
   these are the supported binary names, so invoke
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
- The `default` profile selects one model per AI; `deep` uses each AI's `models`
  list. Read `co-agent.defaults.json` and effective configuration for the chosen profile.
- Cap: `rounds × pairs ≤ max_calls`; trim same-family (round-robin) first, then warn.
- Same provider *family* (e.g. two variants from one direct provider) = diminishing returns; the matrix warns.
  Kiro can route models from different families, so `matrix` treats its multi-model
  list separately. Confirm the actual model families rather than assuming distinct
  CLI names imply diversity.
- The interactive co-agent roster and repository PR CI roster are independent.
  Historical roster decisions do not supply current model IDs or waive required
  coverage. Consensus/harness require READY raw-CLI peers; report missing evidence.

## Where the gate is used
- **`/co-agent:consensus review`** — the gate, standalone, on a git diff (shipped v1.7.2).
- **Pipeline P2** — the gate on a plan document (Stage A).
- **Pipeline P4** — the gate on the cumulative implementation diff (Stage C).

> Roadmap/terminology is **Stage A (P0–P2) · Stage B (P3 implement) · Stage C (P4–P5)** —
> see `references/consensus-pipeline.md`. (The earlier "Phase 2 / `--apply`" wording is retired.)
