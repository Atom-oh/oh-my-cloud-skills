# React Guides and Lambda Chat Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans for inline implementation.

**Goal:** Deliver React-led bilingual plugin guides and a grounded Haiku/Luna
assistant at skills.atomai.click on Lambda Web Functions.

**Architecture:** Docusaurus renders React learning screens and reference pages.
A Node HTTP server serves the build and a protected chat API. CloudFront OAC
fronts a regional IAM-authenticated Web Function.

**Tech Stack:** React 19, TypeScript, Node 24, Bedrock Converse, CloudFormation.

**Spec:** `docs/superpowers/specs/2026-11-14-react-guides-lambda-chat.md`

## Global constraints

- Preserve all six plugins and bilingual page/fragment parity.
- No secrets in browser bundles, environment variables, logs or committed files.
- Real Web Functions use `IamAuth`, OAC `always-amz-auth`, and source-ARN policy.
- Required repository checks and content review >=85 precede deployment.
- Work in `feat/react-guides-lambda-chat`; preserve other worktrees.

## Review focus

- Cold navigation and locale changes retain valid source links.
- Provider failure cannot be shown as a successful or fabricated answer.
- Input and history cannot expand the retrieval scope or select arbitrary models.
- Concurrent users cannot share conversation data; chat requires valid identity.
- Encoded traversal and legacy URLs cannot expose server files or loop redirects.

## Tasks and evidence

- [x] Build React guide data, host-specific steps, responsive workspace and
  contextual chat panel in `doc-sites/src/components/GuideWorkspace/` and
  `doc-sites/src/theme/Root/`. Verify locale coverage, types and browser behavior.
- [x] Add public-guide corpus builder and bounded Haiku/Luna orchestration under
  `doc-sites/server/`. First run failing Node tests for validation, retrieval,
  partial specialist failure and final-model failure; implement and rerun.
- [x] Add Node HTTP serving, chat authentication and route/config contracts.
  First run failing tests for auth, malformed requests, safe file serving and
  redirects; implement and rerun with real HTTP requests.
- [x] Add CloudFormation and repeatable packaging/deployment instructions under
  `doc-sites/infra/`; replace Pages deployment workflow with AWS handoff.
  Validate resource schemas, restricted IAM, throttles and origin policy.
- [ ] Run repository TAP, manifest validators, freshness, skill evaluation,
  bilingual build, content review and desktop/mobile browser checks.
- [ ] Deploy within user-authorized scope after the concrete artifact passes
  review; verify DNS, TLS, origin rejection, static routes and real chat.

## Baseline

2026-11-14: Clean main at `8e995cfe`; TypeScript and all 100 locale pairs passed.
The recovered session contains the user's product direction but no later code or
model-provider decision. Network credentials work outside the local sandbox.

## Progress — 2026-11-14

- Existing repository TAP: 1,194 passed, zero failures. Both manifests, all-plugin
  freshness (9,289 files) and 21 skill evaluations passed.
- Current server/auth regressions: 13 passed. A durable learning-path test checks
  all registered plugins and both locale destinations.
- Official CloudFormation registry schemas validate both templates; cfn-guard
  passes the authored security rules. No banned AWS pattern found in review.
- The first independent review identified redirect, locale-login and transaction
  contention defects. All were reproduced and corrected; focused re-review
  reports zero Critical/Major code or security findings.
- Content review passed at 90/100, then source re-review passed at 86.5/90
  (fresh visual testing excluded). Remaining source warnings were corrected.
  Final package/browser verification and deployment smoke checks are pending.
- The reviewed private source-bucket stack is created. Site deployment is pending.
