# PR review runbook

Use this runbook with [the current review contract](ci-pr-review.md). Do not use an
old ADR's model roster, region, lexical PASS rule or warning-only coverage behavior
as current instructions. Inspect the exact PR HEAD, both CI checks and the latest
bot comment before deciding what failed.

## Inspect a review

```bash
gh pr view <number> --json headRefOid,baseRefName,state,statusCheckRollup
gh api repos/Atom-oh/oh-my-cloud-skills/issues/<number>/comments
gh api repos/Atom-oh/oh-my-cloud-skills/pulls/<number>/comments
gh run view <run-id> --log-failed
```

Never paste credential values from a log into chat, issues or commits. Use masked
error excerpts. The canonical comment must match the current HEAD/run; an old
PASSED comment or PENDING review is not approval. Read final Issues and inline
comments even when a check is green.

## Failure classification

| Observation | Meaning and next action |
|---|---|
| `L1 validation failed` | Read the named manifest/version/inventory error. Fix the source and run both validators locally. |
| `L1 infrastructure failed` | Fetch/archive failed before validators started. Inspect runner/Git access; do not guess a manifest defect. |
| `Review context unavailable` or missing base context | Restore/regenerate base AGENTS.md from CLAUDE.md and verify provenance, size and secret checks. |
| BLOCKED, active Critical/Major | Verify the finding against code, fix a real defect, test and push; obtain a fresh full review. |
| `Review coverage incomplete` | At least one configured cell failed or returned no usable result. Diagnose that provider/CLI; all required cells must complete. |
| `Kiro preflight failed` | No PR input was sent to Kiro. Diagnose startup response, CLI completion and tool-use/fallback signals. |
| `Kiro no-tools contract violated` | Default-agent fallback was detected; responses were discarded. Revalidate the CLI/agent configuration. |
| `Kiro request quota exhausted` | Known account-limit evidence explains missing Kiro coverage; do not spend retries on the same exhausted monthly allowance or overage cap. |
| `Kiro diff truncated` or output-cap evidence | The reviewed input/output is partial. Reduce/split the PR or output; do not call it complete. |
| `Insufficient independent coverage` | Required vendor diversity was not available. The semantic gate rejects it, regardless of the chair's text. |
| `Review generation failed` | Neither chair attempt completed with valid structured output. Inspect CLI/format errors; retry only after identifying the cause. |
| Codex package validation failed | Use the PR's generator and manifests together. Regenerate, then rerun `--check`; a base-generator comparison is not a substitute. |

A transient provider error may justify a bounded retry. The same oversized input or
malformed structure needs correction, not an unbounded rerun loop. Missing optional
memory does not block review, but it does not replace required context or coverage.

## Withheld chair details

A blocking decision survives publication failures. The publisher no longer replaces
hidden findings with empty Issues sections: its diagnostic report is explicitly not
a finding-free review. A failed or incomplete nonblocking response remains ERROR.
Neither case can pass merely because details are unavailable.

Find the single JSON record prefixed with `chair-publication:` in the synthesis
step log. Withheld reports include the same metadata in the PR comment. It contains
fixed codes, byte counts and parsed issue-item counts, never source text or
scrubber/exception messages. Publication diagnostics do not establish provider
completion or required peer coverage; the existing gate checks those separately.

| Reason | Next action |
|---|---|
| `source_format_rejected` / `scrubbed_format_rejected` | Inspect `format_diagnostic.rule`; correct the named presentation rule while preserving findings and severity. |
| `input_too_large` / `scrubbed_output_too_large` | Compare byte counts with `byte_limit` and obtain a concise complete report. |
| `source_review_incomplete` / `scrubbed_review_incomplete` | Obtain a complete canonical review; do not treat missing evidence as empty Issues. |
| `scrubber_failed` / `publisher_error` | Check the indicated processing stage and the trusted helper/dependency installation. Raw exception text is intentionally omitted. |
| `blocking_evidence_removed` | The source blocker did not survive sanitization; recover a publishable blocking review before resolving it. |
| `invalid_utf8` | Correct the provider output encoding before retrying. |

`source_decision` distinguishes an active Critical/Major item from an explicit FAIL
verdict. `issue_item_counts` counts parsed visible list items, not verified defects;
`null` means missing or ambiguous, not zero. `format_diagnostic.line` is a one-based
line in the review text at the indicated stage, not a repository source location.
A null line means the check cannot safely map its reconstructed prose to the source.
Models, fallback rules, acceptance conditions and the 50,000-byte cap are unchanged.
Trusted-base CI picks up publisher changes only after they merge.

## Local reproduction

Run in the checkout under review:

```bash
python3 scripts/test-plugins.py
python3 scripts/test-codex-plugins.py
python3 scripts/sync-codex-plugins.py --check
bash tests/run-all.sh
```

After changing a maintained source/template, regenerate the affected Codex outputs
before freshness validation. A generator logic change and its output belong in one
PR; the isolated head CI checks them together.

For base-context diagnosis, run from the trusted checkout:

```bash
python3 plugins/co-agent/skills/co-agent/scripts/check_ai_context.py . --verify AGENTS.md
python3 scripts/pr-review/context.py --root . --output /var/tmp/base-review-context.md
```

The context builder checks the generated marker/hash and rejects outside paths.
AGENTS.md is capped at 6,144 bytes; the complete context is capped at 8,192 bytes.
The isolated PR-head CI validates the real assembled context before merge. It derives inventory populations from repository data.
It does not execute scripts from a supplied PR tree or load every historical doc.

## Roster, model and authentication diagnosis

```bash
python3 scripts/pr-review/panel_config.py show --root .
```

Compare with committed `pr-review.defaults.json` and the workflow configuration.
A gitignored local override normally disappears during clean CI checkout. A change
to base configuration takes effect after it merges; it cannot retroactively change
the trusted scripts used to review that same PR.

Check CLI availability, the configured provider/model and the actual masked error.
The workflow supplies the chair's region/endpoint pair; Codex uses its runner CLI
configuration and Kiro uses its own catalog. Do not infer equivalence or residency
from similar model names. A Kiro quota error is not evidence that a different
provider's credentials failed. Do not print environment variables containing keys.

No automatic model exclusion is authorized by judgment-quality statistics. Verify
unsupported findings against current code, distinguish them from provider failures,
and obtain an explicit owner-approved roster change when warranted. Keep genuine
blocking findings and all required coverage; do not weaken gates to make a PR green.

For these Kiro-specific failures, use [the panel runbook](runbooks/pr-review-panel.md).
It separates configuration, startup and quota failures without weakening the review gate.

## Completion

Require both CI checks, complete configured peer responses, no unresolved current
Critical/Major, and a comment bound to the latest HEAD. Recheck HEAD, target branch
and prerequisite PRs immediately before authorized merge. Retain the merge commit
and relevant verification results; temporary local evidence is not a portable
artifact link unless it was actually published.
