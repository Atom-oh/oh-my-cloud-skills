# Dense guide workspace release — 2026-11-14

The 28-exercise React workspace is deployed at `skills.atomai.click`, with the
Cognito-authenticated Haiku/Luna guide assistant. Source commit:
`5e2a2a8ae75597fb5682329f41bb7eb3922cf8fe` (merged main, including PR #307).
The CloudFormation stack reached `UPDATE_COMPLETE`, its source object version
matched the verified package, and CloudFront invalidation completed.

Release ZIP SHA-256:
`ea408c58bd8362d7f8b93a747c3c3b0c408c8c19eb230e9f5a2c88e2cafeb86e`.
Uncompressed size: 82,362,493 bytes. The prior versioned source remains available
for rollback. Deployment changes replaced the immutable Web Function revision
and updated its endpoint reference; authentication, quotas, IAM and model settings
were preserved.

## User-visible behavior

The desktop workspace keeps plugin filters, a searchable task catalog and the
selected exercise together. Mobile uses a list/detail flow. All 28 exercises
across six plugins provide prerequisites, a concrete request, expected output,
verification and a current reference. Search, plugin and task state are shareable
in the URL. English and Korean guides cover 97 paired pages from current main.

Real archived screenshots open fully contained in a dialog; separate links open
the image or interactive archive. Practice checkmarks explicitly record the user's
own comparison in the current session. Claude Code panes and Codex text-status
procedures retain their host-specific descriptions.

## Validation

| Check | Result |
|---|---|
| TypeScript and both locale builds | Passed on the release source |
| Site regression tests | 133 passed |
| Server regressions | 15 passed, including real TCP listeners |
| Locale coverage | 97 English/Korean pairs and four catalogs passed |
| Claude/Codex manifest validation | Both passed |
| Generated freshness | 9,273 files checked across all plugins |
| Skill evaluation | 21 PASS, zero REVIEW/FAIL |
| Public retrieval corpus | 265 indexed excerpts; citation paths checked against built pages |
| Repository TAP | 1,194 passed on the integrated PR tree at `34ed0441` |
| Independent content review | 88.5/90 PASS; one typography warning |
| Final PR #307 checks | AI review, Codex validation and documentation validation passed |

The TAP run covers the integrated PR tree before the unrelated presentation-tool
changes in PR #308. Deployed app implementation, dependencies, infrastructure and
UI translations were verified unchanged; the final release build and guide
coverage checks include the updated main documentation. No failed check was waived.

The initial sandboxed locale-test run failed without a detailed assertion report.
An isolated rerun and subsequent complete builds outside that sandbox passed
without suppressing tests.

## Production verification

The authenticated smoke completed at **2026-11-14 12:35:11 UTC**:

- Homepage, configuration and health endpoints returned 200.
- Unauthenticated chat returned 401; direct unauthenticated origin access returned 403.
- The legacy prefix redirected with its query intact.
- A temporary account completed actual Cognito managed login and returned to English.
- A real co-agent Haiku specialist and Luna synthesis returned a non-degraded,
  816-character answer with three verified, reachable English source links.
- The conversation remained available when selecting another task in the same plugin.
- The temporary account was deleted. No invitation was sent, and its password and
  access token were neither printed nor written to persistent output files.

This verifies existing-account login, not delivery of a new user's confirmation
email. Pool/client identifiers were checked against the dedicated stack before
creating the temporary account.

Public browser acceptance completed at **12:35:20 UTC**. All 28 task references,
clipboard actions, manual checks, filters/search/empty state, shared-search reload
and history, contained image preview, standalone archive/presenter windows,
contextual assistant, English deep links, native theme toggle and 1440/768/390px
layouts passed. It recorded zero page errors and zero unexpected failed requests.
Production desktop, mobile and preview captures were inspected.

## Review corrections and provenance

The implementation fixed the cropped iframe preview, denied presenter popup,
incorrect S shortcut (current guidance now uses N), omitted search URL state,
same-plugin task/search conversation resets, invalid command citation paths and
angle-bracket syntax loss in the retrieval corpus.

The HTTP byte cap now derives from the shared character/history contract and
accounts for escaped JSON. A subsequent review found that resuming an oversized
request before iterator cleanup left it paused. The corrected code resumes after
cleanup. Its regression reproduced the failure, then verified that a delayed
1 MiB remainder drains and the next request on the connection receives 200 after
the initial 400. The user explicitly approved the test-file execution-surface
exception, and the fix was landed through the hashed, isolated `land_delta.sh`
pipeline in `dc69e8d0` (iteration 1/5). The optional push gate was configured off.

PR #307's final review at `ea1cfab0` passed under ADR-026: the chair disclosed the
single peer and truncated prompt, recovered the complete head files from the
harness `pr-tree`, and supplied its own second-vendor full-scope read. This was the
chair's explicit acceptance, not a mechanical waiver. Another session merged
PR #307 at **12:16:10 UTC** as `a772bcfd`; this session did not perform that merge.
The temporary foundation PR #309 became redundant and was closed without merging.

Small UI typography remains the content rubric's single warning. The five-minute
token/re-authentication behavior, a possible conversation reset when returning
from a reference page, legacy asset redirects and other nonblocking advisories
remain described in the final PR review. Quota counts accepted attempts, including
provider attempts that later fail.
