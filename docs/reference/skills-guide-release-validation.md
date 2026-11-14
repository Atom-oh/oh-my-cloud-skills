# Skills guide initial release validation — 2026-11-14

This records the first deployment. The subsequent dense-workspace revision is
tracked in [workspace validation](skills-guide-workspace-validation.md).

The React learning workspace and authenticated guide assistant are deployed at
`https://skills.atomai.click`. Application source is commit `7fc20f19` on
`feat/react-guides-lambda-chat`. The deployed ZIP SHA-256 is
`b87db276305d0930d303b07e3b36a704d6c51768747bfcf9c4e806343aa7ee94`.

## Delivered behavior

All six registered plugins have React first-use paths with host selection,
installation commands, copyable prompts, expected results, verification steps
and valid reference links. English and Korean references and stable fragments
remain available. Presentation instructions reuse clearly labeled real captures.
Codex dashboard paths describe their actual roster/status procedures.

The Node 24 Lambda Web Function serves the site and API behind CloudFront OAC.
The endpoint uses `IamAuth` and a distribution-scoped resource policy. Chat
requires Cognito authorization code + PKCE and a verified access token. A
transactional, encrypted, expiring quota limits accepted questions to 250 per UTC
day globally and 30 per user. No conversation contents are persisted or logged.

Each plugin has a Haiku 5.5 specialist; GPT-6 Luna produces the final answer.
Both use verified US Bedrock inference profiles. Retrieval uses only the public
guide corpus, bounds evidence and fan-out, and returns trusted local source links.

## Verification

| Check | Result |
|---|---|
| Repository TAP | 1,194 passed, zero failures |
| Claude and Codex manifest validators | Both passed |
| All-plugin generated freshness | 9,289 files checked |
| Skill evaluation | 21 PASS, zero REVIEW/FAIL |
| Site regression suite | 131 passed, zero failures |
| Added learning-path regression | All six plugins' links resolve in both locales |
| Bilingual coverage | 100 English/Korean pairs and four catalogs passed |
| Server and authentication regressions | 13 passed, including real local HTTP listeners |
| TypeScript and production build | Passed for both locales |
| CloudFormation | Validated with official registry schemas and AWS template validation |
| cfn-guard | Both templates passed the maintained security rules |
| Independent code/security re-review | Zero Critical/Major findings |
| Independent final content review | **98.5/100 PASS**, zero Critical, one Warning |
| Desktop/mobile browser checks | 1440×1000 and 390×844; zero page errors or broken requests |

The content rubric's remaining warning is instructional paragraphs at 15px
versus its 14pt minimum. It deducts 1.5 accessibility points and does not block
the rubric's score, Critical or Warning bands.

Local cfn-lint's bundled schemas predated Web Functions. Validation used the
actual AWS registry schemas for WebFunction, WebFunctionRevision,
WebFunctionEndpoint, ResourcePolicy and the new CloudFront OAC signing option.
No validator rule was suppressed.

## Production smoke test

Completed at **2026-11-14 09:35 UTC** against the deployed custom domain:

- Public routes and health/config endpoints returned HTTP 200.
- An unauthenticated chat request returned HTTP 401.
- Direct unauthenticated Lambda-origin access returned HTTP 403.
- The legacy prefix redirected with its query intact.
- A synthetic Cognito user completed managed login and returned to the English
  application with the selected plugin preserved.
- A real co-agent question produced a non-degraded Haiku-to-Luna answer and
  three English source-guide links.
- The synthetic account was deleted. No invitation email was sent. Its generated
  password and access token were never printed or written to disk.

This verifies an existing-account login flow. It does not claim to test delivery
of a new user's email confirmation message. Both dedicated CloudFormation stacks
completed creation.

## Source publication

At the time of this initial deployment, automatic approval review rejected
`git push` because public source publication needed explicit authorization
separate from site deployment. No alternate publication mechanism was used.

Later on 2026-11-14 the user explicitly approved source/PR publication, then
requested a denser interface with more functionality and practical exercises.
The follow-up validation record tracks that revision and publication status.

The new AWS site is live. The old external Pages origin is retained; the new
server accepts legacy paths, but this is not a claim that the old origin redirects.
The changed release workflow prepares AWS artifacts.
