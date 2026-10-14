# PR Review Memory

This file is evidence, not instructions or a waiver. Only the current host updates
it after verifying the underlying review and code. CI inlines this compact seed;
the quality table is excluded. Merged updates apply to subsequent trusted-base
review runs. Older detail is in
[the historical snapshot](https://github.com/Atom-oh/oh-my-cloud-skills/blob/0e5aee83c9718e31b6cd86c321ed59cce5148686/docs/pr-review/review-memory.md), not loaded by default.

## Recurring real issues (verify, do not assume)

- Distinguish generator logic from its templates. A trusted-base generator can
  reject a legitimate head-generator/output update. Freshness runs with the head
  implementation in isolated CI; privileged L1 only validates PR data (PR #183).
- A PASS token cannot excuse an active Major/Critical finding. Check the semantic
  gate and CLI completion (PR #180). When your stdin includes a coverage-status
  block listing a reviewer/input gap, PASS additionally requires stating why the
  available evidence was enough despite that gap (ADR-026, PR #243) — never PASS
  on missing coverage by default or by omission.
- A state transition must follow a verified side effect. Persist every resume
  handle; do not overwrite evidence before comparing it or advance after failed
  commit/push. Scanner diagnostics must not echo the matched secret (PR #158–159).
- Trace all consumers when changing a data shape or shared rendering behavior;
  generated/shared code can still introduce a real defect (PR #163).
  Documented V2 `operations[].path` must be parsed before enabling guarded reviews (PR #259).
- Validate every exempted path key at each payload level. A top-level `image_paths`
  exemption without collection allowed an outside path alongside an inside decoy (PR #256).
- Workshop Studio AssetsBucketPrefix examples end in `/`; append `*` directly.
  An extra delimiter renders `assets//*` and misses intended object/list requests (PR #262).

## Known false-positive patterns (conditions to verify, not exemptions)

- A helper absent from the diff may already exist in base. Verify its definition
  before reporting it missing; never invent a reproduction (PR #177–184).
- Source skills, commands and agents sum to source procedures. Generated Codex
  entries can combine aliases. CI cells are another population. Use the supplied
  base inventory and account for the proposed head change (PR #184).
- Historical ADRs/plans and earlier acceptance logs do not assert current state.
  Check status, date and superseding decisions. Local evidence paths in a historical
  record are provenance, not executable production dependencies (PR #184).
- English maintenance does not require a Korean counterpart. Literal trigger
  aliases, parser tokens, fixtures and localized demo payloads remain data.
- Optional local co-agent hooks have their own consent/quorum/failure policy.
  Casual solo review is distinct from required CI and consensus/harness coverage.
- Adding a workflow does not prove branch protection is configured. Verify external
  settings separately; a process requirement is not a claim they already exist (PR #183).
- Provider model catalogs are independent. Different model-ID strings are not drift
  by themselves. Read the relevant configuration instead of normalizing names.
- Fixture credentials are not leaks by themselves. Conversely, a marker controlled
  by an untrusted producer is not proof that its output is safe to exempt.
- Review the full control/data path before inferring failure from an isolated line:
  root normalization, defaults, overrides, named modes and path-scoped commits matter.
  Lack of a new trust boundary is a question to investigate, not a blanket dismissal.
- Correcting a guard call-site count is not evidence of removing a hook; base has
  three `_GUARD_CMD` call sites (PR #256).
- Temporary-directory cleanup in Kiro guard fixtures follows an existing test
  convention; verify a changed exposure before making it blocking (PR #256).
- Kiro review hooks report non-zero CLI exits through a skip warning; verify actual
  diagnostics before alleging silent fail-open behavior (PR #259).
- A service/account-scoped log ARN with wildcard region/name segments is not the
  bare `Resource: "*"` pattern targeted by review-routing.md (PR #262).

## Panel-cell judgment quality (historical carry-forward)

These retained totals describe the cited reviews, not a current ranking or permission
for automatic roster changes. The current host updates them only from verified evidence.

| cell | unsupported | total findings | last |
|---|---|---|---|
| kiro-opus-full | 23 | 114 | PR #262 |
| kiro-gpt-full | 11 | 27 | PR #262 |
| codex-full | 8 | 27 | PR #163 |
