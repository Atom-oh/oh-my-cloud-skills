# ADR-017: PR-Review — Disable `kiro-glm` (`glm-5`) in the Panel Roster

## Status

Accepted (2026-08-14) — narrows the Kiro roster set by ADR-012/ADR-014; those decisions'
rationale (why a 3rd/4th vendor slot, why `--v3` is dropped, the `gpt-5.5`→`gpt-5.6-terra`
bump) is unaffected and remains historical record.

## Context

The sibling `AWS-Demo-Platform` repo — which runs a bash-array port of this repo's
lens×model PR-review panel — found in its own PR #88 that the `kiro-glm` cell (model
`glm-5`) alone produced 4 false-positive findings in a single review round, with the
other panel members (`codex`, `kiro-opus`, `kiro-gpt`) producing zero false positives on
the same diff in the same round. That repo recorded the decision to drop `glm-5` from its
roster in its own `ADR-015-pr-review-per-model-parallel-jobs.md`. This repo is the
de-facto upstream reference implementation for the harness design (config-driven roster
via `panel_config.py` + `pr-review.defaults.json`, rather than a bash array), so the same
false-positive complaint applies here identically — this repo's `kiro-glm` cell wraps the
same `glm-5` model via the same `kiro-cli chat` invocation path.

`glm-5` was originally added to diversify vendor coverage (Claude/OpenAI/Zhipu families —
ADR-011) and survived the `gpt-5.5`-deprecation bump in ADR-014 unchanged. Its
false-positive rate is a quality problem independent of the model-string/vendor-catalog
issues those ADRs addressed.

## Decision

- Disable the `kiro-glm` cell by setting `"enabled": false` in
  `scripts/pr-review/pr-review.defaults.json`, **without deleting the key**.
  `panel_config.py`'s `validate_shape()` requires every member of `ALL_CELLS`
  (`codex`, `kiro-opus`, `kiro-gpt`, `kiro-glm`) to stay present in the config regardless
  of its `enabled` value (22nd review MAJOR, guarded in `validate_shape` around
  `panel_config.py:106-108`) — deleting the key instead of disabling it would make
  `panel_config.py effective`/`kiro-cells` raise `ConfigError` and `cmd_kiro_cells` exit 1,
  which `run-panel.sh`'s own check (~line 69-72) treats as "refusing to run with an
  unverified roster," failing the whole panel closed rather than just dropping one cell.
  `KIRO_CELLS = ("kiro-opus", "kiro-gpt", "kiro-glm")` at `panel_config.py:34` — the
  known-cell allowlist — is unchanged; `kiro-glm` stays a valid, just-disabled, cell name.
- Effective roster: `codex` + `kiro-opus` + `kiro-gpt` (2 Kiro cells, not 3) × 4 lenses
  (L2–L5) = 12 cells (was 16), of which 8 are Kiro calls (was 12).
- Tests updated to match the new default (`enabled: false`) rather than the old default
  (`enabled: true`): `tests/pr-review/test-panel-config.sh` case (a)'s exact-string
  roster assertion now expects the 2-cell default; case (b) — the "disabling a cell"
  code-path test — is re-pointed at `kiro-gpt` instead of `kiro-glm`, since disabling an
  already-disabled cell would no longer exercise that path; case (l)'s invalid-model
  fixture now explicitly re-enables `kiro-glm` in its override (`{"enabled": true, "model":
  ""}`) so the invalid-model check still fires instead of short-circuiting on the
  now-default-disabled cell. `tests/pr-review/test-run-panel.sh` case (a)'s cell/responded
  counts move from 8/2-lens×4-models to 6/2-lens×3-models; case (f)'s degraded-tag
  assertion drops `kiro-glm` from the expected sorted list; case (m) — the dedicated
  "disabling a cell via config" test — is re-pointed at `kiro-gpt` for the same reason as
  panel-config's case (b), with `responded=4` (codex + kiro-opus only, since kiro-glm is
  now off by default *and* kiro-gpt is off via this test's override). Cases (o)/(p),
  which explicitly disable all three Kiro cells (or already only test that a repo-root
  override is honored from a non-root cwd), were left as-is — disabling an
  already-disabled `kiro-glm` there is redundant but harmless, not incorrect.
  `tests/pr-review/test-synthesize.sh`'s hand-written `degraded-models.txt` fixtures are
  independent of the live config and were left unchanged.
- Docs updated to the new cell/call counts and roster list: `docs/ci-pr-review.md` (matrix
  description, 16→12 max cells, Kiro-call count in the data-residency section, roster
  list in "설정") and `docs/ci-pr-review-runbook.md` (cell-tag example, 16→12 max tags,
  Kiro call count 12→8). `.github/workflows/pr-review.yml` has no `strategy:`/`matrix:`
  block and no stale cell-count prose to fix — the fan-out lives entirely in the scripts
  this ADR's config change already covers.
- Scope: **this repo only**. Sibling repos running the same ported CI design
  (`AWS-Demo-Platform`, `ai-trader-web`, `aws-fsi-demo`, `awsops`, `cc-on-bedrock`,
  `claude-code-usage-dashboard`, `multi-region-architecture`, `nfm-dashboard`,
  `security-ops`, `ttobak`) each need the same roster change applied independently via
  their own PRs — this repo is upstream for the harness *design*, not a source of synced
  config, and `AWS-Demo-Platform` (where the false-positive finding originated) has
  already made this exact change in its own ADR-015.
- Separately, the `co-agent` plugin (`plugins/co-agent/`) has its own, unrelated model
  roster (`co-agent.defaults.json`'s `models` array) that also listed `glm-5` — dropped
  from that array and every doc that echoes it
  (`plugins/co-agent/commands/configure.md`,
  `plugins/co-agent/skills/co-agent/references/{consensus-mode,relay-chain-gate,
  ai-cli-adapters}.md`, `doc-sites/docs/co-agent/overview.md`) for the same underlying
  complaint (glm-5 false positives), even though co-agent's roster and pr-review's panel
  are independent features that happen to have both included this model.

## Consequences

- Panel loses one vendor's worth of redundant find-coverage per lens, but drops the one
  cell with a demonstrated false-positive problem; the remaining roster
  (Claude/OpenAI/OpenAI-via-Kiro) still has cross-vendor diversity via `codex` vs.
  `kiro-opus`/`kiro-gpt`, per ADR-011's original rationale.
- Coverage-floor logic (`run-panel.sh`'s `ALL_TAGS`/`CODEX_ENABLED`) already treats a
  disabled cell as intentionally out-of-roster, not degraded — no change needed there;
  this ADR only changes which cells start disabled by default.
- `glm-5` remains available to any operator who wants it back: `python3
  scripts/pr-review/panel_config.py set kiro-glm enabled true --root .` (or a committed
  edit to `pr-review.defaults.json`, per `docs/ci-pr-review.md`'s "경로 A") re-enables it
  with that one command, no code change — the disabled entry keeps `model: glm-5` (only
  `enabled` flips to `false`), so `validate_shape()`'s enabled-cell model check never
  trips on re-enable.

## References

- `scripts/pr-review/pr-review.defaults.json`, `scripts/pr-review/panel_config.py`
- AWS-Demo-Platform PR #88 (4 false positives from `glm-5` alone in one review round)
- AWS-Demo-Platform `docs/decisions/ADR-015-pr-review-per-model-parallel-jobs.md` (the
  precedent this ADR follows for the same underlying complaint)
- ADR-011 (original lens×model matrix design, 3-vendor Kiro roster)
- ADR-012 (`kimi-k2.5` → `gpt-5.5` roster swap, rationale unaffected)
- ADR-014 (`gpt-5.5` → `gpt-5.6` deprecation bump, rationale unaffected)
