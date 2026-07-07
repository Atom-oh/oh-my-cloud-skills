# ADR-012: PR-Review Kiro Roster — `kimi-k2.5` → `gpt-5.5`, Drop `--v3`

## Status

Accepted (2026-07-06) — amends the Kiro roster set by ADR-009; ADR-009's chair model
(Claude Opus 4.8) is unaffected and remains historical record (superseded in practice by
the separate Fable 5 chair swap, tracked only in `docs/ci-pr-review.md`/runbook, not an ADR).

## Context

`kimi-k2.5` was one of ADR-009's three Kiro roster models. Production evidence accumulated
against it on two independent axes:

- **Coverage degradation**: `kimi-k2.5` produced zero responses across all lenses in 2/2
  observed production runs (`coverage-severe`-adjacent — see `docs/ci-pr-review-runbook.md`).
- **False positives**: 7 dismissed panel findings traced to `kimi-k2.5` hallucinations
  (diff-unsupported claims), vs. 0 for `kiro-opus`, `kiro-glm`, and `codex` over the same
  observation window (see chat history distilled into the runbook's rationale section).

The user's explicit priority for this panel: false negatives (missed issues) are
acceptable, false positives are not — they inflate review latency/cost and erode trust in
the gate. `kimi-k2.5` was the only roster member with negative evidence on either axis.

`gpt-5.5` was initially believed unavailable via `kiro-cli` (looked callable per
`--list-models`, but a `--v3` flag inherited from an unrelated earlier fix routed calls to
a narrower-catalog backend that rejected it with `HTTP 400 INVALID_MODEL_ID`). Direct testing
confirmed `gpt-5.5` works fine via `kiro-cli chat --model gpt-5.5 ...` once `--v3` is
dropped; `--v3` was originally added to work around a stdin-delivery bug and an invalid
`--trust-tools` name, both already fixed independently via argv delivery and the correct
`fs_read` tool name — `--v3` itself was never load-bearing for either.

## Options Considered

1. **Keep `kimi-k2.5`** — rejected; the only roster member with observed coverage and
   false-positive risk on this CI's specific priority (minimize false positives).
2. **`kimi-k2.5` → `minimax-m2.5`** — tested clean, briefly adopted, then superseded by
   option 3 per explicit user preference (perceived lower reliability of minimax).
3. **`kimi-k2.5` → `gpt-5.5`, drop `--v3`** — (adopted) restores model diversity
   (Claude/OpenAI/Zhipu-family coverage instead of a second Claude-family slot) once the
   real blocker (`--v3`) is understood and removed.

## Decision

- `scripts/pr-review/run-panel.sh`: `KIRO_MODELS=("claude-opus-4.8:kiro-opus"
  "gpt-5.5:kiro-gpt" "glm-5:kiro-glm")`.
- All `kiro-cli chat` invocations in this repo's `scripts/pr-review/*.sh` drop `--v3`
  (kept `--mode default --no-interactive --trust-tools=fs_read --wrap never`).
- Scope: **CI pr-review only**. `co-agent`'s own Kiro roster (`minimax-m2.5` alongside
  `claude-opus-4.8`/`glm-5`) and its `--v3`-bearing adapters (`ai-cli-adapters.md`,
  `check_panel.py`, `consensus_hooks.py`) are **not** changed by this ADR — co-agent's
  fan-out is interactive/on-demand, not a fail-closed CI gate, and `--v3`'s catalog
  restriction has not been shown to affect co-agent's own model set (kimi/glm/opus only).
  A future ADR should revisit `--v3` there if co-agent's roster ever needs `gpt-5.5`.

## Consequences

- Kiro roster restores 3-vendor diversity in the lens×model matrix (previously 2 Claude-
  family + 1 Zhipu after the interim minimax step).
- `gpt-5.5` now occupies 2 of 4 model-rows per lens (shared with `codex`), a diversity
  trade-off explicitly accepted — see `docs/ci-pr-review.md` for the tracked backlog item
  to re-evaluate a 4th distinct model.
- Sibling repos running the same ported CI design (multi-region-architecture, ttobak,
  aws-fsi-demo, cc-on-bedrock, awsops, AWS-Demo-Platform, security-ops) received the same
  roster + `--v3` fix; two (AWS-Demo-Platform, security-ops) intentionally were NOT moved
  to the Fable-5 chair in the same pass — see their own workflow comments for account-
  specific constraints (data retention / IAM scope) unrelated to this roster decision.

## References

- `docs/ci-pr-review.md`, `docs/ci-pr-review-runbook.md` (detailed rationale, live config)
- ADR-009 (original panel decision — chair + initial roster, left as historical record)
- ADR-011 (lens×model matrix design this roster plugs into)
- PR #108 (this change), PR #103/#104 (lens-matrix rollout)
