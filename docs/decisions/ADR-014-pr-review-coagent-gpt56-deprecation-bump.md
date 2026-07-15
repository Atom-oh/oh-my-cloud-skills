# ADR-014: PR-Review + co-agent — `gpt-5.5` Deprecated, Bump to `gpt-5.6` Variants

## Status

Accepted (2026-07-15) — amends the Kiro roster set by ADR-012 and co-agent's default
codex model set by PR #112; both decisions' rationale (why a 3rd/4th vendor slot, why
`--v3` is dropped) is unaffected and remains historical record.

## Context

`gpt-5.5` was deprecated upstream. Two independent call sites in this repo pin a
`gpt-5.5`-family model string:

- `scripts/pr-review/pr-review.defaults.json` (`kiro-gpt` cell) → passed to `kiro-cli
  chat --model` for the pr-review CI panel.
- `plugins/co-agent/skills/co-agent/co-agent.defaults.json` (`codex` panel entry) →
  passed to `codex exec -c model=...` for co-agent's interactive fan-out.

Each call site resolves through a different vendor-side routing path (Kiro's cross-vendor
router vs. Codex's own model catalog on Bedrock-mantle), so the replacement model string
differs per site rather than being a single global find/replace.

## Decision

- `kiro-gpt` cell: `gpt-5.5` → `gpt-5.6-terra`.
- co-agent's `codex` panel model: `openai.gpt-5.5` → `openai.gpt-5.6-sol`.
- Both changes are config-only (`pr-review.defaults.json`, `co-agent.defaults.json`) — no
  code path changes; `run-panel.sh`'s Codex cell has never hardcoded a model (it's fixed
  via the runner image's `~/.codex/config.toml`, out of scope for this ADR in this repo).
  Comments/docs referencing the old model string as a live value were updated alongside
  (`run-panel.sh`, `.github/workflows/pr-review.yml`, `ai-cli-adapters.md`,
  `consensus-mode.md`, `configure.md`, `docs/ci-pr-review.md`,
  `docs/ci-pr-review-runbook.md`, `doc-sites/docs/co-agent/*`); historical ADRs (ADR-009,
  ADR-011, ADR-012) are left untouched per the decisions/CLAUDE.md convention (never
  retro-edit an accepted ADR's rationale).
- Scope: **this repo only**. Sibling repos running the same ported CI design
  (`multi-region-architecture`, `ttobak`, `aws-fsi-demo`, `cc-on-bedrock`,
  `claude-code-usage-dashboard`, `security-ops`) each need the same swap applied
  independently via their own PRs — `AWS-Demo-Platform` was excluded from this pass (a
  concurrent session was already applying the identical swap there).

## Consequences

- Kiro roster retains 3-vendor diversity (Claude/OpenAI/Zhipu families) — only the
  OpenAI-family model string changed, not the roster composition.
- co-agent's codex panel entry keeps the same `effort: high` tiering; only the model id
  changed.
- Tests updated in lockstep: `tests/pr-review/test-panel-config.sh`'s assertions that
  encode the *live default* (`kiro-cells` default-roster output) now expect
  `gpt-5.6-terra:kiro-gpt`; assertions using `gpt-5.5` as an arbitrary/synthetic test value
  (unrelated to the real roster) were left as-is.

## References

- `scripts/pr-review/pr-review.defaults.json`, `plugins/co-agent/skills/co-agent/co-agent.defaults.json`
- ADR-012 (original `kimi-k2.5` → `gpt-5.5` roster swap, rationale unaffected)
- PR #112 (co-agent default panel models, codex → `openai.gpt-5.5`, rationale unaffected)
