# React guides and Lambda Web Function assistant

## Intent and recovered context

The user resumed Inferplane session `01a182f2-3078-7072-8115-35102c69da14`.
That session shipped the expanded bilingual Remarp guides in PR #304, then
requested React-led learning screens at `skills.atomai.click`, hosted on Lambda
Web Functions, with one Haiku specialist per plugin and a Luna final answer.
No implementation of this follow-up existed at the start of this session.

## Product

Retain Docusaurus's React runtime, bilingual reference documents, screenshots,
stable fragments and locale switcher. Replace the document-list home with a
learning workspace: choose a plugin, choose a host, follow installation,
try a concrete first task, inspect the expected result and open deeper references.
Use interactive steps, copyable prompts and real presentation screenshots.
All six registered plugins receive a complete starting path. The assistant is
available throughout the site and carries the selected plugin into a question.

Guides remain publicly readable. The chat endpoint checks application identity,
caps input/context/output, retrieves only public maintained guide content, invokes
relevant Haiku specialists, then asks Luna to synthesize their evidence. Responses
include local source links. Unsupported questions and provider failures must not
produce invented answers. Do not store or log chat contents or credentials.

## Architecture and author choices

- Keep React 19 / Docusaurus 3.9.2. React owns the learning interface; existing
  Markdown remains the searchable reference library.
- Serve the static bilingual build and Node HTTP API from a real Lambda Web
  Function (`nodejs24.x`, `AWS_LAMBDA_HTTP_ENDPOINT`), not a Function URL adapter.
- Canonical origin is `https://skills.atomai.click`, base path `/`; preserve
  `/oh-my-cloud-skills/` paths and `/ko/` aliases in the HTTP server.
- Interpret the user's “OAI” as CloudFront origin protection, using Web Functions
  OAC (`always-amz-auth`, regional `sigv4`) and an `IamAuth` endpoint. This choice
  was presented for clarification.
- Use Bedrock Converse with configurable Haiku and Luna inference-profile IDs;
  model availability must be verified in the target account. The prior session's
  provider name is not evidence that the chatbot must use Inferplane.
- Public-site content is the only retrieval corpus. English and Korean UI use
  static translation IDs and the existing coverage checker.
- Infrastructure uses reviewed CloudFormation, restricted IAM resources,
  endpoint throttles, private encrypted deployment artifacts and a scoped
  CloudFront resource policy. Deployment is separate from the local build.

## Acceptance

All six first-use paths, both locales, copy/step controls, accessible mobile
layout, chat error/authentication states and source links work. Tests exercise
retrieval boundaries, input validation, model orchestration, request isolation,
auth failure, traversal rejection and old-link redirects. Build and required
repository validators pass. A content-review-agent score of at least 85 is
mandatory before deployment. Production claims require actual HTTP and model
smoke checks; mocked provider tests do not prove account model access.
