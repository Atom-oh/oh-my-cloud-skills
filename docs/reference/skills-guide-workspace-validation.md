# Dense guide workspace validation — 2026-11-14

This revision responds to the user's feedback that the initial deployment looked
sparse. The user prioritized dense functionality and practical exercises and
approved GitHub source and PR publication.

## Behavior

The React home now has 28 curated exercises across six registered plugins.
Desktop shows a plugin navigator, searchable task list and selected exercise
together. Mobile uses a task list/detail flow. Each exercise has prerequisites,
a copyable request, expected output, a verification step and a current reference.
Actual archived examples open in a labeled dialog. Checkmarks explicitly record
the user's own comparison in the current session; they do not claim execution.

Host selection keeps Codex dashboard text procedures distinct from Claude Code
panes. Task URLs, English/Korean content and contextual chat remain available.
Selecting a search result preserves the query. The corpus now resolves command
guide URLs correctly and refuses to package a citation without a built page.

## Current verification

| Check | Result |
|---|---|
| Repository TAP | 1,194 passed, zero failures |
| TypeScript | Passed |
| Site regression tests | 133 passed |
| Isolated locale regression rerun | 126 passed |
| Bilingual coverage | 100 page pairs and four catalogs passed |
| Server regression tests | 12 passed, including real local HTTP listeners |
| Claude and Codex manifest validators | Both passed |
| Generated package freshness | 9,289 files checked |
| Skill evaluation | 21 PASS, zero REVIEW/FAIL |
| Production package | Both locales built; 265 indexed guide excerpts |
| Browser acceptance | Passed at 1440px, 768px and 390px |

The initial sandboxed build stopped in the locale test file without a detailed
assertion report. The isolated rerun and full packaging run outside that sandbox
both passed without changing or suppressing a test.

Browser acceptance completed at **2026-11-14 11:01:45 UTC**. It exercised all
28 task panels and their reference routes, clipboard, manual checks, plugin
filtering, search and empty state, search preservation and browser-history restoration, the real example iframe,
contextual assistant, English task deep links, the native theme toggle and mobile
back navigation. It recorded zero page errors and zero failed local requests.
Screenshots were inspected at desktop, tablet and mobile sizes; horizontal
overflow was checked. No interaction was represented as a live model call.

## Deployment preparation

The new ZIP SHA-256 is
`12227c4b00786e98d9b833390ac16842f5fe035ce7abaac92b46fdd935bb1912`.
The 82,497,916-byte uncompressed package was uploaded as a new immutable version
to the existing private asset bucket. The CloudFormation update change set is
prepared and has not been executed.

Its direct changes replace the immutable Web Function revision and update the
endpoint's revision weights. CloudFront and both DNS records appear as dynamic
attribute-reference updates; none requires replacement. Authentication, quotas,
permissions and the model configuration are unchanged.

## Remaining gates

Independent code/content review has not run: automatic approval review rejected launching a Codex review process
because transmitting unpublished source to that service required explicit
authorization. A narrowly scoped user approval request is pending. No alternate
model service or process was used to bypass that decision.

The existing site continues serving the initial release. The new revision must
pass the required review before execution of the prepared change set, cache
invalidation and production verification.
