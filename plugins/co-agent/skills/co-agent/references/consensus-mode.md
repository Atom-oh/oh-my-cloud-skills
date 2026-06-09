# Consensus Mode (co-agent)

Review-only higher-confidence review. (The `--apply` autonomous fix loop is Phase 2 — see
the design spec; not implemented in this version.)

## Why
- **Model diversity** (different families catch different bugs) > intra-family duplication.
- **Citation validation** turns "verify, don't vote-count" into a mechanical filter.

## Flow (review-only)
1. Consent + scope; print `co_agent_config.py matrix` (provider·model·ctx + max calls).
2. One **independent** round over `(ai,model)` pairs (`pairs` command; `deep` profile for
   the full per-AI model lists; capped by `consensus.max_calls`, default 12).
3. `check_citations.py` classifies findings → drop `unsupported`, flag `needs-review`.
4. Chair synthesis: **raw agreement + evidence strength**, attribute dissent. No confidence
   weighting (contradicts the chair principle).
5. **Quorum guard**: ≤1 usable pair → single-opinion review, not "consensus".

## Multi-model rules
- Default = one model per AI. `deep` profile activates each AI's `models` list.
- Cap: `rounds × pairs ≤ max_calls`; trim same-family duplicates first, then warn.
- Same provider family (e.g. two Claude variants) = diminishing returns; the matrix warns.

## NOT in this version (Phase 2)
- `--apply` fix loop, scope-lock, test gate, security veto, checkpoint patch, clean-tree,
  no-progress/oscillation stop. See `docs/superpowers/specs/2026-06-08-co-agent-consensus-mode-design.md`.
