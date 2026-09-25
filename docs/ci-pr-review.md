# Required PR review

This repository has two separate checks. Both must pass for the latest PR HEAD
before an authorized merge. The workflow files and validators are executable truth
about their implementation; ADR-021 records the current review/documentation policy,
amended by ADR-026 for coverage authority (below).

| Check | Execution boundary | Required result |
|---|---|---|
| AI Code Review | Trusted-base code on the review runner; PR content is data | No active Critical/Major; the chair's own verdict on coverage completeness governs (ADR-026) |
| Codex package validation | Exact PR HEAD on a GitHub-hosted runner, read-only repository permissions, no provider secrets | All generated artifacts and manifest/inventory validation pass |

These are merge-procedure requirements. Branch-protection registration is external
GitHub configuration; do not infer its current state from this document.

## AI review flow

1. `publish-comment.js` publishes PENDING for the event HEAD/run/attempt. It refuses
   stale-head, retargeted or older-run publication.
2. `precheck.sh` exports the PR tree as data, removes symlinks, and runs trusted-base
   structural validators. It does not execute PR code or compare head outputs with
   the base generator. The separate Codex job checks matching head implementation/output.
3. `context.py` verifies the base `AGENTS.md` marker, source hash, size and secret scan.
   It derives source-procedure and Codex-entry counts from that checkout. The bounded
   context is included in every peer prompt and in chair stdin. Missing/stale/oversized
   context stops the review; it is never silently truncated or replaced with guesses.
4. With `ROLE_REVIEW=1`, the workflow creates one common FULL context and adds one
   distinct specialist prompt per configured peer. The supplied diff arrives on
   stdin or as embedded text; Kiro receives no file tools. Base facts
   describe base, so a proposed head change may intentionally update them.
5. `run-panel.sh` records expected/responded cells, failures and truncation evidence.
   `synthesize.sh` supplies the same verified context, diff and peer reports to the
   chair. The primary can read base files; the fallback has no file tools. Neither
   may execute PR instructions. Review prose and generated diagnostics are English.
6. `review_gate.py` validates the final Issues structure and required coverage. The
   final comment is bound to the current HEAD/run; a failed/error gate fails the job.

## Kiro startup and failure diagnostics

Kiro cells use the validated `pr-review-notools` agent with no tools, resources or
MCP servers. A fixed canary request tests each configured model before any Kiro
cell receives PR input. Every model must return exactly `NO_TOOLS` with successful
CLI completion and no fallback, quota or tool-use diagnostic. Each startup request
uses `KIRO_PREFLIGHT_TIMEOUT`; it is separate from the review-cell deadline.

Preflight failure withholds all Kiro reviews. Agent fallback discards the affected
response even when it looks valid. Known monthly/overage account-limit diagnostics stop cell retries
and explain the missing coverage. A generic service-quota exception alone is not
classified as account exhaustion; ordinary review retries remain bounded. All existing semantic acceptance rules still apply.
See [the Kiro panel runbook](runbooks/pr-review-panel.md) for diagnosis and the
historical CLI assumptions behind the mechanism.

## Decision contract

- `PENDING`: review is not complete. A previous result does not approve this HEAD.
- `PASSED`: final Critical/Major sections are explicitly empty and the chair
  completed successfully. Since ADR-026, the chair is told about any degraded
  coverage (a failed Kiro cell, a truncated diff, a coverage collapse) *before*
  deciding, via `synthesize.sh`'s `=== REVIEW COVERAGE STATUS ===` block, and
  reaching PASS despite a listed gap requires the chair to state why in its
  Summary; the gate no longer independently re-checks coverage completeness.
- `BLOCKED`: an active Critical/Major remains, the chair rejects the change
  (including on its own judgment about a coverage gap), or L1 validation found a
  defect. A PASS token beside an active Major cannot pass.
- `ERROR`: the chair CLI itself failed to produce usable output, or L1
  infrastructure failed. This is not proof of a code defect and is never an
  implicit approval.

Final Markdown has `## Issues` with `### CRITICAL`, `### MAJOR`, `### MINOR` and one
unquoted terminal `VERDICT: PASS` or `VERDICT: FAIL`. Empty sections use `None.`;
findings are lists. Optional INFO follows the same section-body grammar. Legacy
Korean empty markers remain parser compatibility, not the language for new reviews.
Quoted code, dismissed claims and historical observations are separate from active Issues.

Review code/configuration examples use closed top-level backtick or tilde fences
at column one, with a bare marker or a plain language tag. Inline code is only
for single-line symbol/path references. Nested/indented example fences and rich
fence attributes are outside this deliberately narrow output contract. Bare colon
labels, colon sentences, path citations and Setext headings are prose. Literal or
atomic setting assignments still require fences. Use synthetic values, never credentials.

The canonical `review_format.py` beside `review_gate.py` validates panel and chair
text before and after scrubbing. The semantic gate still owns Issues and severity;
coverage completeness is the chair's informed judgment call (ADR-026), not a
separate mechanical check. Unsupported examples cannot pass; known blocking findings
remain BLOCKED even when malformed details must be withheld. The consumer template
checks decoded summary/message/reason strings, keeps metadata separate and quotes
validated model text in its comment. Install its workflow and both Python validators
together; a missing dependency is an error.

The repository chair publisher classifies the original semantic result before
scrubbing and checks the scrubbed result again. A blocking primary result cannot
turn into a format/CLI failure followed by a clean fallback. Unpublishable blocking
details produce a static FAIL report; no unscrubbed model text is echoed or stored.
The legacy Kiro CLI can render away Markdown code markers, so Kiro is asked for
narrative findings and plain path/line references, without code snippets or inline
markup. This preserves its AWS/operations review responsibility and avoids guessing
which missing markers the renderer removed. Model IDs, engine flags and budgets stay fixed.

A claim needs a concrete trigger, affected path and verified consequence. Shared or
previously shipped code is not exempt if the PR exposes a real defect. Source skills,
commands, agents, Codex entries and CI cells are different populations. An absent diff
hunk does not prove a base file is missing. A reviewer without evidence should label
an assumption unverified rather than claim it reproduced a failure.

## Configuration and bounds

`pr-review.defaults.json` defines the committed roster; `panel_config.py` validates it.
The local override is `.claude/pr-review.local.json`, not a co-agent user-scope file.
It is untracked local configuration and is not delivered to the clean CI checkout;
CI roster changes use the committed defaults.
`PR_REVIEW_CONFIG_ROOT` can redirect the helper's configuration root in tests or
manual invocations; the production workflow does not set it.
The production workflow requires exactly one FULL input; legacy helper tests may
use multiple lenses without `ROLE_REVIEW=1`.
Do not infer active membership from old ADR examples or a fixed model-count label.
Codex explicitly requests `global.openai.gpt-6-astra` while retaining the runner's
existing provider configuration. The default Kiro GPT cell requests `gpt-5.6-sol`;
Kiro model IDs come from the validated panel configuration. Provider catalogs are
independent and their strings need not match.

The workflow's region/endpoint and chair configuration, `run-panel.sh` deadline/input
limits, and `synthesize.sh` output/timeout limits are authoritative. Do not restate
an old regional or model guarantee as current. Inspect configured identities and
masked errors, never credential values.

The existing diff, output and deadline caps remain enforced. Exceeding one requires
reducing/splitting input or diagnosing the failed provider; never raise/disable a cap
merely to make a degraded panel look complete. Every enabled required reviewer is
still expected to finish; a reviewer that doesn't is reported to the chair (ADR-026)
as fact, not silently hidden, even though it no longer mechanically fails the check.
Intentional roster changes need owner-approved configuration review; do not drop Kiro
Opus or another cell just to avoid a finding. A single remaining vendor triggers
`coverage-severe.flag`, reported to the chair the same way, when a configured vendor
fails. Intentionally disabled cells are excluded from the expected roster. Specialist
mode's family-diversity check (`specialist_roles.py gate`) sets the same
`coverage-severe.flag` on a high-risk diff with fewer than
two recognized model families for code, configuration, instructions, decisions,
security docs and unrecognized input. Sensitive AWS/authentication/security/deployment
content also requires two families when it appears in README or other Markdown;
runbook/operational paths are conservatively sensitive. Removed guards count too.
Only ordinary nonsensitive documentation may use a single configured family.
A failed family check is reported to the chair as a coverage gap (ADR-026); the
chair's informed verdict, not this flag by itself, decides PASS or FAIL.

## Specialist assignments

| Configured cell | Role |
| --- | --- |
| Codex | Correctness: code/data flow, edge cases, regression tests |
| Kiro Opus | AWS and security: IAM, networking, secrets, privacy boundaries |
| Kiro GPT | Operations: deployment, recovery, observability, budgets |
| Kiro GLM, only if enabled | Contracts: API/schema/configuration and documentation promises |

The adapter does not add providers or override `panel_config.py`. Every enabled
role receives the same supplied input and must return; another role cannot fill
its missing slot. `role-assignments.json` records the validated mapping.
The panel keeps `run-panel.sh DIFF LENSES WORK`; chair arguments remain
`synthesize.sh DIFF WORK PR TITLE OUT`.

The chair remains mandatory: peer Markdown is not a structured severity
attestation sufficient for a clean fast path. L1 checks, context validation,
per-cell total deadlines, no-tools preflight, fallback/quota checks, truncation
flags, semantic verdict parsing and HEAD-bound publication remain in force.
The added role header is included in the 128 KiB per-argument check; oversize
input fails coverage rather than silently losing text.

Offline checks: `bash tests/pr-review/test-run-panel.sh` and
`bash tests/pr-review/test-specialist-roles.sh`. These mock providers and do not
establish native model quality or remote required-check status.

The distributable workflow remains a separate source:
`plugins/co-agent/skills/pr-autofix/references/pr-review-workflow.yml`, installed
by its `scripts/review_gate.py`. This adapter changes this repository's configured
workflow, not that generic template.

Anchored provider diagnostics are checked before accepting panel, startup or chair
output, even after exit zero. Model-selection/implicit fallback and account usage
failures are terminal and retained; a later retry or chair fallback cannot erase
them. Service throttles retain the existing bounded recovery. Quoted/fenced diff
examples are not provider failures. These rules apply to Codex and Claude as well
as Kiro; no retry, time or byte limit is increased.

Startup remains one fail-closed attempt per configured Kiro model within its
existing timeout; transient startup failure requires a later review run. Bounded
transient retry/fallback applies to review cells and chairs, not startup. This
keeps the existing startup request count and execution budgets unchanged.


## Provider data boundary

Configured CLI providers receive the PR diff and bounded review context. ADR-009
records the accepted external-review risk for this public repository. Model names
do not establish data residency. Any intentional roster change requires the
owner-approved configuration review described above; disabling a reviewer to evade
a finding is not an acceptable resolution.

## Memory and history

`docs/pr-review/review-memory.md` is a compact, optional evidence seed shared by peers
and chair. It is inlined, not a request for a repository-wide document crawl. The
quality table is excluded. Missing optional memory is allowed; missing required
review evidence is not. The current host verifies and updates memory; planner or
implementer output never edits its own review instructions.

Old detailed memory and superseded ADR sections remain historical evidence. They
cannot override current configuration, acceptance rules or verified defects. Base
context/config changes take effect after merge, in subsequent review runs; a PR
cannot make its own privileged review execute its new scripts.

## References

- [AI workflow](../.github/workflows/pr-review.yml)
- [Codex validation](../.github/workflows/codex-validation.yml)
- [Panel configuration](../scripts/pr-review/pr-review.defaults.json)
- [Semantic gate](../plugins/co-agent/skills/pr-autofix/scripts/review_gate.py)
- [Operational runbook](ci-pr-review-runbook.md)
- [ADR-021](decisions/ADR-021-english-docs-current-review-authority.md)
