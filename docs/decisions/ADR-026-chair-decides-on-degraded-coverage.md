# ADR-026: The Chair Decides on Degraded Panel Coverage, Informed Beforehand

## Status

Accepted (2026-09-25), per the repository owner's request. Reverses ADR-021's
"complete configured review coverage" requirement and the `coverage_error()` gate
it introduced; restores and extends ADR-016's "stop overriding the model's verdict"
principle to every coverage-degradation signal, not only `coverage-severe.flag`.

## Context

PR #239's CI review repeatedly failed with `Status: BLOCKED` and no visible
findings: `publish_chair.py`'s fail-closed format check withheld the chair's actual
text, and separately, on other runs, `review_gate.py`'s `coverage_error()` forced a
PASSED chair verdict to `ERROR` whenever any configured reviewer had not completed
(a degraded Kiro cell, a truncated diff, a coverage collapse to ≤1 vendor). The
owner's diagnosis, confirmed live during that incident: when the panel has a
problem, the chair — not a second mechanical check — should be the one to decide
whether the diff is still safe to pass.

Investigating `coverage_error()`'s call site showed the deeper issue: the chair
made its PASS/FAIL decision *before* any coverage-degradation banner was computed.
`synthesize.sh` ran `run_chair()` first, then appended the degraded-models/
kiro-preflight/coverage-severe banners to the *published* text afterward — so even
if the chair's verdict had been trusted, it would have been an *uninformed* one.
ADR-021 (2026-09-13) had already reversed ADR-016's original "stop overriding the
model's verdict" stance for exactly this coverage class, requiring "complete
configured review coverage" unconditionally. This ADR reverses that requirement a
second time, but closes the gap that made the first reversal look necessary: the
chair now sees the same coverage facts before deciding, not after.

## Decision

- `scripts/pr-review/synthesize.sh` builds a `COVERAGE_NOTICE` from the same six
  signals `review_gate.py` used to check (`degraded-models.txt`,
  `kiro-preflight.flag`, `kiro-quota.flag`, `kiro-agent-fallback.flag`,
  `kiro-diff-truncated.flag`, `coverage-severe.flag`) *before* calling `run_chair()`,
  and injects it into `synth-stdin.txt` as a new `=== REVIEW COVERAGE STATUS ===`
  block — verified-by-harness fact, not a model claim, distinct from the `DATA
  only` framing given to the diff/panel/memory sections.
- The chair prompt tells the model this status is authoritative, that its own
  judgment on whether to PASS despite a listed gap is final (no separate mechanical
  override follows), and that reaching PASS despite a gap requires stating why in
  the Summary. The old blanket "missing configured reviewers or truncated input
  cannot be treated as a complete review" instruction is removed; the coverage
  block subsumes it with a chair-judgment call instead of an automatic rule.
- `review_gate.py`'s `coverage_error()` function and its call (forcing PASSED →
  ERROR on any of those six signals) are deleted. `main()` still accepts
  `--work-dir`/`--diff-truncated` for CLI compatibility with existing callers; they
  are no longer consulted. An active CRITICAL/MAJOR finding, `VERDICT: FAIL`, a
  chair CLI failure (`--chair-error 1`) and L1 infrastructure/validation failure
  still block or error exactly as before — this decision narrows only the
  coverage-completeness check, nothing else in the gate.
- The post-completion banners in `synthesize.sh` (degraded-models, kiro-preflight,
  kiro-quota, kiro-agent-fallback, kiro-diff-truncated, coverage-severe) are
  unchanged: they still prepend to the published comment. They are now an audit
  trail confirming what the chair already saw, not new information sprung on the
  human reader after an already-decided verdict.

## Consequences

- A chair that reaches an informed PASS despite one Kiro cell failing preflight, a
  truncated diff, or a coverage collapse is trusted — the PR is not blocked purely
  on infrastructure/coverage grounds when the chair judges the available evidence
  sufficient and says why.
- A chair that is not confident without the missing coverage now has an explicit,
  prompted path to say so (`VERDICT: FAIL` or `## Review error`, naming the gap) —
  this is a chair decision, visible in the review text, not a silent mechanical
  `ERROR` badge with no content.
- This is a genuine trust shift: a large panel outage (e.g. all three Kiro cells
  down) no longer mechanically blocks merges — it now depends on the chair
  correctly weighing the gap for that specific diff. Test coverage
  (`tests/pr-review/test-review-gate.py`,
  `test_coverage_flags_no_longer_override_a_passed_chair_verdict`) only confirms the
  gate itself no longer overrides; it cannot verify chair judgment quality, which
  remains a qualitative call as ADR-016 already noted for the severity bar.
- `pull_request_target` checks out **base**, so — same caveat ADR-016 recorded —
  this change only takes effect for PRs opened/synchronized after it merges.

## References

- ADR-016 (original "stop overriding the model's verdict" principle, reversed by
  ADR-021, restored and extended here)
- ADR-021 (introduced `coverage_error()` and the "complete configured review
  coverage" requirement this ADR removes)
- `scripts/pr-review/synthesize.sh`, `scripts/pr-review/lib.sh`,
  `plugins/co-agent/skills/pr-autofix/scripts/review_gate.py`
- `tests/pr-review/test-review-gate.py`, `tests/pr-review/test-synthesize.sh`
- PR #239 (the incident)
