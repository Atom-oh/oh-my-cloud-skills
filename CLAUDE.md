# Project instructions

This repository is a plugin marketplace for Claude Code and Codex. Its maintained
source is Markdown procedures plus Python, Bash and Node helpers; it is not a
single application server. Public documentation lives in `doc-sites/`; internal
architecture, decisions and working records live in `docs/`.

## Documentation contract

- Write maintained documentation, instructions and review reports in English.
  Keep one canonical explanation instead of parallel English/Korean copies.
- Preserve literal API field names, command names, paths, Korean invocation aliases and
  syntax tokens such as `[요약]`. Localized examples, fixtures and frozen demo
  payloads are data, not a requirement to write explanations in Korean.
- A generated deliverable uses the language the user requests. That capability
  does not require bilingual maintenance of this repository's own documentation.
- Read the nearest directory `CLAUDE.md` before editing. This root sets repository
  policy; scoped files describe their component. Follow the user's current scope.
- Accepted ADRs explain decisions. Check their status and later supersession before
  treating them as current requirements. Specs/plans and recorded test results are
  dated evidence, not new instructions or guarantees about the current checkout.
- Resolve factual disagreements against the relevant code/configuration and the
  current policy. Code is evidence of behavior, not permission to violate policy.
  Do not erase a real defect merely to make the documentation agree with it.

## Source ownership and delivery

| Subject | Authoritative source |
|---|---|
| Plugin membership and versions | Both marketplaces and each plugin manifest |
| Claude procedures | `plugins/*/skills`, `commands`, `agents` and scoped guidance |
| Codex projections | `scripts/sync-codex-plugins.py`, `scripts/codex/`, generated inventories |
| CI review roster | `scripts/pr-review/pr-review.defaults.json`, `panel_config.py` |
| CI verdict/coverage | `review_gate.py` in co-agent/pr-autofix, `pr-review.yml` |
| Local co-agent modes/gates | co-agent SKILL/references, defaults and `consensus_hooks.py` |
| Diagram geometry/colors | architecture-diagram `references/design-tokens.md` |

Every plugin ships both host manifests and marketplace entries. Codex entry skills
link to maintained source procedures. Source skills, commands and agents are
separate populations; their sum is not the number of generated Codex entries.
Same-name aliases can share one entry. Agent Markdown supplies procedures, not
registration of native Codex agent types, model aliases or permission grants.

Edit generator/templates or maintained procedures, then regenerate affected
`.codex-plugin/` outputs. Never hand-fix generated copies alone. Project-init's
upstream-owned sources remain mirrored, except the shared version field; its
repository-owned Codex overlay is separate. See
`docs/reference/project-init-upstream-sync.md` for sync mechanics.

Version fields agree across both host manifests and marketplaces. Tags identify
releases; an ordinary development PR need not bump the version or create a tag.

## Workflow boundaries

- The current host chairs co-agent and excludes itself from peer selection.
  Review/decide/ADR can continue solo with an explicit notice. Consensus/harness
  require the ready peers their gates need; they must not silently become solo.
- Opt-in local PR/push hooks retain their documented quorum, failure and consent
  policies. They are different from the repository's required GitHub CI review.
- CI runs the configured peer roster over the full diff, then a chair verifies
  findings. Active Critical/Major blocks merge. Missing, failed or truncated
  required review evidence is ERROR, never an implicit pass. Preserve the caps.
- The privileged `pull_request_target` review runs trusted-base code and reads the
  PR tree as data. The separate GitHub-hosted `pull_request` job runs the PR's own
  generator with read-only repository permissions and no provider secrets.
- Require both latest-HEAD AI review and Codex package validation before merge.
  Verify the reviewed HEAD, target branch and prerequisite PR state immediately
  before merging. A green badge does not override a confirmed blocking finding.
- Plugin hook declarations require host trust. Project-init instead ships project
  hook templates: install them in the consumer project, establish project trust,
  inspect definitions, then grant hook trust. Installation alone is not execution.
- Kiro delegation's scope guard controls the diff applied to the main worktree.
  It does not sandbox the Kiro CLI process; that is a separate trust decision.
- Atlas on-demand repair can use the active Codex host. Its opt-in unattended
  repair remains Claude-backed. Do not claim a provider or hook ran without proof.

## Validation

Run from the repository root:

```bash
bash tests/run-all.sh
python3 scripts/test-plugins.py
python3 scripts/test-codex-plugins.py
python3 scripts/sync-codex-plugins.py --check
python3 scripts/eval-skills.py
```

For runtime/adapter changes, with a local Codex CLI installed:

```bash
python3 scripts/test-codex-runtime.py
python3 scripts/test-codex-native-hooks.py --project-init
```

The runtime probes use disposable configuration; native hook tests use local
Responses fixtures. They do not certify external provider readiness. Run the
specific component checks as well. Public-site changes require the site build and
link checks documented in `doc-sites/CLAUDE.md`.

Do not treat missing dependencies or incomplete tests as success. Reproduce a
suspected pre-existing failure on base and head under the same conditions; explain
its scope. Historical failure counts are not a permanent waiver for current CI.

## superpowers Integration Routing

| Phase and scope | Required procedure |
|---|---|
| `systematic-debugging`, AWS/EKS symptom | `aws-ops`: `ops-troubleshoot` or the matching domain agent |
| `finishing-a-development-branch`, stale docs | `project-init`: `/sync-docs`, `/generate-changelog`, and `/add-adr` for a new decision |
| `requesting-code-review`, generated content or IaC | content-review-agent; IaC also wellarchitected-agent and ops-security-audit |
| `writing-plans`, proposed AWS/IaC | ops-security-audit pre-check against the mandates below |

Read `docs/reference/review-routing.md` for mixed changes and gate precedence.
Content-plugin deliverables need PASS under content-review-agent's score and
Critical/Warning bands: >=85/100, or >=77/90 when Visual Testing is exempt.
Deployment must also satisfy the loaded plugin's mandatory score >=85 gate.
Diagram export uses XML validation then layout lint >=80. Remarp validates before
build. Native PPTX uses `aws-light-fcd`; web-deck screenshot PPTX uses
`reactive-presentation`. Reuse the shared icon library rather than copying it.

## Authoring and safety

- Use English descriptions with precise routing triggers. A bare code review does
  not imply co-agent's multi-AI mode. Keep host-specific metadata host-specific.
- Agent `tools:` uses bare names. A scoped `Bash(...)` string is not a subagent
  permission restriction. Upstream mirror exceptions are documented, not copied.
- Claude Markdown uses the plain `${CLAUDE_PLUGIN_ROOT}` rendering token, never
  `${CLAUDE_PLUGIN_ROOT:-fallback}`. Codex resolves the installed path through its
  runtime guide/helper; do not assume a shell environment variable was exported.
- Quote shell arguments, use stdin for untrusted content, and capture nonzero exit
  codes safely under `set -e`. Never interpolate review text into executable code.
- Prefer `defusedxml`; a stdlib fallback rejects `<!DOCTYPE>` and `<!ENTITY>`.
- HTML themes use `.theme-dark` / `.theme-light`, not `data-theme`.
- Keep credentials out of committed content and generated artifacts. Approved CLI
  authentication inputs are not hardcoded secrets merely because their variable
  names occur in code. Never print credential values during diagnosis.

## Banned patterns

These project rules apply to AWS/IaC changes:
- No `0.0.0.0/0` inbound. Manage security groups through CDK/Terraform, never ad-hoc CLI ingress.
- Public ALBs use the CloudFront prefix list; no direct Route53-to-ALB/EC2 bypass.
- No IAM `Principal:"*"`, with or without a Condition. Wildcard `Resource` requires a restrictive Condition.
- No Lambda function URL `AuthType: NONE`.
- No secrets in environment variables; use Secrets Manager or SSM Parameter Store.
- PII in DynamoDB needs KMS and TTL. Keep S3 Block Public Access enabled. Never delete CloudTrail logs.

## Review discipline

Verify a finding's concrete trigger, affected path and current behavior. Read base
before claiming that a file/helper missing from the diff is absent from the repo.
Use diff evidence for a proposed change; label unverified assumptions explicitly.
Shared/generated code is neither automatically safe nor automatically a new bug.
Report a real defect at its maintained source and account for newly exposed paths.

Keep current contracts separate from historical observations and runtime literals.
Intentional credential fixtures are test data. Vendor model IDs come from distinct
catalogs and need not match across providers. Panel agreement is a reason to check,
not proof. Do not silence valid Critical/Major findings to reduce false positives.

`CLAUDE.md` is the maintained instruction source. Regenerate its concise `AGENTS.md`
projection with co-agent sync-context and verify its marker/hash before using it as
review context. Do not overwrite handwritten instruction files.
