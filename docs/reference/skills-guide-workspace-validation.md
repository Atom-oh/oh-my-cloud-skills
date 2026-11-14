# Dense guide workspace validation — 2026-11-14

This revision responds to the user's feedback that the initial deployment looked
sparse. The user prioritized dense functionality and practical exercises and
explicitly approved source and PR publication. Source is published through PR #307.

## Delivered behavior

The React home has 28 curated exercises across six plugins. Desktop shows a plugin
navigator, searchable task list and selected exercise together; mobile uses a
list/detail flow. Each exercise has prerequisites, a copyable request, expected
output, verification and a current reference. Search, plugin and task state are
encoded in the URL and restored by reload/history navigation.

Real archived screenshots open fully contained in a dialog. Separate links open
the full image or interactive archive; current controls remain documented in the
maintained reference. Codex dashboard text procedures remain distinct from Claude
Code panes. Practice checkmarks record the user's own comparison for this session.
The assistant preserves a conversation across tasks/searches in the same plugin
and clears it when the plugin scope changes.

The HTTP body budget is derived from the same character/history limits as parsed
validation, allowing the complete Korean and escaped-Unicode request contract.
Oversized requests receive a safe 400 response. Retrieval preserves fenced and
inline syntax, and packaging rejects source citations without a built page.

## Verification

| Check | Result |
|---|---|
| Repository TAP | 1,194 passed, zero failures |
| TypeScript | Passed after review fixes |
| Site regression tests | 133 passed in the final package build |
| Bilingual coverage | 100 page pairs and four catalogs passed |
| Server regressions | 14 passed, including real HTTP listeners |
| Claude and Codex manifest validators | Both passed |
| Generated package freshness | 9,289 files checked |
| Skill evaluation | 21 PASS, zero REVIEW/FAIL |
| Production package | Both locales built; 271 indexed excerpts |
| Browser acceptance | Passed at 1440px, 768px and 390px |

The initial sandboxed build stopped in the locale test file without a detailed
assertion report. An isolated rerun and subsequent full package builds outside
that sandbox passed without suppressing a test.

Final browser acceptance completed at **2026-11-14 11:19:52 UTC**. It exercised all
28 task references, copying, manual checks, filters/search/empty state, shared
search reload/history, the contained preview, an independently opened archived
example and its presenter window, contextual assistant, English deep links,
native theme toggle and mobile back navigation. Zero page errors and failed local
requests were recorded. Desktop, tablet, mobile and preview captures were inspected.

A separate browser test with explicitly mocked auth/model responses confirmed
same-plugin conversation retention and different-plugin reset at 11:19:45 UTC.
This is client-state evidence, not a live provider claim. The earlier production
Cognito/Haiku/Luna smoke belongs to the initial release record.

## Review findings and fixes

The first independent public-source review of `27bb0e13` returned **83/90 REVIEW**:
one Major and four additional warning-tier findings. Its 90-point scale exempted
independent MCP Visual Testing while inspecting supplied browser captures.

- The cropped default iframe preview was replaced by a contained real image with
  full-size and interactive-archive links. The complete output is visible.
- Presenter mode now runs from the standalone archive. Browser verification opened
  and closed the archive's actual presenter window successfully.
- The current presenter shortcut was corrected from S to N in both English and
  Korean, including shared learning-path metadata. Archives retain their own keys.
- Search is serialized as `q` and restored with the selected plugin/task.
- Small UI typography remains a disclosed rubric warning; it is not silently waived.

GitHub CI's review of `27bb0e13` identified the HTTP byte/character mismatch. The
new regression reproduced rejection of a valid maximum Korean history, then passed
for both raw UTF-8 and escaped JSON after the shared-budget fix. An additional
oversized-body case verifies a 400 response rather than a dropped connection.
The corpus and same-plugin conversation-reset advisories were also reproduced and
fixed. The corpus regression covers nested fences, tildes and inline placeholders.

The CI claim that the domain was not deployed conflicts with the initial release's
recorded 2026-11-14 09:35 UTC production smoke. That first release is live; the dense
revision is separately gated. Quota intentionally counts accepted requests before
provider execution because partial/failed provider attempts may incur work. It is
not an answered-question counter. Required CI remains the merge gate; no merge is
claimed from local review or degraded CI coverage.

## Deployment preparation and publication

ZIP SHA-256:
`6a8bb704e980f14190a82729d0fb28b3f9fc5f19652b67a4a819dad4ab1452a8`.
The uncompressed package is 82,541,398 bytes. It is staged as an immutable version
in the existing private bucket, with a new CloudFormation update change set.
Superseded unexecuted change sets were removed; the previous deployed source
version is retained.

Direct changes replace the immutable Web Function revision and update endpoint
weights. CloudFront and DNS updates arise from dynamic attribute references; no
replacement of those resources is required. Authentication, quotas, IAM and model
configuration are unchanged.

Automatic approval initially rejected transmitting unpublished source to a review
service. After the explicitly approved GitHub publication, the exact public commit
and clean checkout were verified. A restricted review of that published source
was then approved and completed. No unpublished source or private configuration
was sent through an alternate service.

Production activation awaits the final independent review of the fixes, followed
by cache invalidation and a new public-site/authenticated-provider smoke test.
