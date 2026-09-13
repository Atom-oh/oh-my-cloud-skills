# Required PR review

This repository has two separate checks. Both must pass for the latest PR HEAD
before an authorized merge. The workflow files and validators are executable truth
about their implementation; ADR-021 records the current review/documentation policy.

| Check | Execution boundary | Required result |
|---|---|---|
| AI Code Review | Trusted-base code on the review runner; PR content is data | Complete configured peer coverage and no active Critical/Major |
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
4. The workflow creates one FULL prompt for every configured peer. The complete
   diff arrives on stdin or as embedded text; Kiro receives no file tools. Base facts
   describe base, so a proposed head change may intentionally update them.
5. `run-panel.sh` records expected/responded cells, failures and truncation evidence.
   `synthesize.sh` supplies the same verified context, diff and peer reports to the
   chair. The primary can read base files; the fallback has no file tools. Neither
   may execute PR instructions. Review prose and generated diagnostics are English.
6. `review_gate.py` validates the final Issues structure and required coverage. The
   final comment is bound to the current HEAD/run; a failed/error gate fails the job.

## Decision contract

- `PENDING`: review is not complete. A previous result does not approve this HEAD.
- `PASSED`: final Critical/Major sections are explicitly empty, the chair completed
  successfully, and every configured required review cell/input is complete.
- `BLOCKED`: an active Critical/Major remains, the chair rejects the change, or L1
  validation found a defect. A PASS token beside an active Major cannot pass.
- `ERROR`: required evidence or infrastructure is missing, failed, malformed or
  incomplete. This is not proof of a code defect and is never an implicit approval.

Final Markdown has `## Issues` with `### CRITICAL`, `### MAJOR`, `### MINOR` and one
unquoted terminal `VERDICT: PASS` or `VERDICT: FAIL`. Empty sections use `None.`;
findings are lists. Optional INFO follows the same section-body grammar. Legacy
Korean empty markers remain parser compatibility, not the language for new reviews.
Quoted code, dismissed claims and historical observations are separate from active Issues.

A claim needs a concrete trigger, affected path and verified consequence. Shared or
previously shipped code is not exempt if the PR exposes a real defect. Source skills,
commands, agents, Codex entries and CI cells are different populations. An absent diff
hunk does not prove a base file is missing. A reviewer without evidence should label
an assumption unverified rather than claim it reproduced a failure.

## Configuration and bounds

`pr-review.defaults.json` defines the committed roster; `panel_config.py` validates it.
The local override is `.claude/pr-review.local.json`, not a co-agent user-scope file.
The production workflow has one FULL lens; helper tests may use multiple lenses.
Do not infer active membership from old ADR examples or a fixed model-count label.
Codex's model comes from runner configuration; Kiro model IDs come from the panel
configuration. Provider catalogs are independent and their strings need not match.

The workflow's region/endpoint and chair configuration, `run-panel.sh` deadline/input
limits, and `synthesize.sh` output/timeout limits are authoritative. Do not restate
an old regional or model guarantee as current. Inspect configured identities and
masked errors, never credential values.

The existing diff, output and deadline caps remain enforced. Exceeding one requires
reducing/splitting input or diagnosing the failed provider; never raise/disable a cap
merely to turn incomplete coverage green. Every enabled required reviewer must finish.
Intentional roster changes need owner-approved configuration review; do not drop Kiro
Opus or another cell just to avoid a finding. A single remaining vendor cannot satisfy
the current independent-coverage gate.

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
