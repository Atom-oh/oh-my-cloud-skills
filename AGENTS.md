<!-- generated-by: co-agent · source: CLAUDE.md · claude-md-sha: bda703d304b3 · generated-at: 2026-09-13 · DO NOT EDIT — edit CLAUDE.md then run /co-agent sync-context -->
> Shared reviewer context derived from CLAUDE.md. Use the same facts in every peer
> review and chair synthesis; facts below describe the trusted base checkout.

# Repository review contract

A Claude Code and Codex plugin marketplace: Markdown skills, command workflows,
agent procedures, Python/Bash/Node helpers. `docs/` is internal; `doc-sites/` is the
public site. Derive inventory counts from manifests and Codex inventories: source
skills, commands, agents and generated entries are different populations.

## Authority and language

- Maintained instructions/docs and CI review prose are English. No bilingual-copy
  requirement. Literal invocation aliases, syntax, fixtures and localized example
  payloads remain data; user-requested deliverables may use another language.
- Current root/scoped contracts and accepted, non-superseded decisions guide work.
  ADR histories, specs/plans and earlier acceptance results are dated evidence.
  Do not apply an old proposal or past failure count as a current requirement.
- Verify factual claims against the correct base/head code and configuration. An
  absent diff hunk does not prove a helper/file is missing. Code evidence does not
  excuse a current policy violation. Unverified assumptions are not findings.

## Distinct workflows

- CI: configured peers each review the complete diff; the chair verifies findings.
  Active Critical/Major blocks. Required missing/failed/truncated evidence is ERROR.
  Inspect current-HEAD body and inline comments, not just the badge. Both AI Code
  Review and Codex package validation must pass before authorized merge.
- CI review uses trusted-base code and PR data; isolated PR CI runs the head's
  generator. A legitimate generator change includes its regenerated outputs.
  GitHub branch-protection registration is external configuration, not a fact
  established merely by adding a workflow or stating a merge procedure.
- Local co-agent: the current Claude/Codex host chairs and excludes itself from
  peers. Review/decide/ADR may report solo execution; consensus/harness need ready
  peers. Opt-in local PR/push hooks have their own quorum/failure contracts.
- Codex entries adapt procedures; Claude agent metadata does not create native
  Codex roles or grants. Plugin hooks need trust. Project-init's three project
  hook templates need separate consumer installation, project trust and hook trust.
- Kiro's scope guard limits the applied diff, not every action of its CLI process.
  Atlas on-demand Codex repair and optional Claude-backed unattended repair differ.

## Checks and source ownership

- Full TAP suite, both manifest validators, all-plugin generated freshness and skill
  evaluation must pass. Actual runtime/hook probes additionally require local Codex.
- Source files and generated `.codex-plugin` outputs must agree; edit maintained
  sources and regenerate. Do not skip a package or hand-fix an overlay alone.
- Project-init upstream sources remain mirrored; its Codex overlay is repository
  owned. Shared version fields agree; tags belong to releases, not every PR.
- Read `docs/reference/review-routing.md` for scope-specific artifact/security
  gates. Content score >=85; diagram XML then layout >=80; Remarp validates before
  build. Reuse aws-light-fcd's sibling icon library; that reference is intentional.

## Safety and review calibration

- Bare agent tool names only; scoped Bash text is not an enforced restriction.
  Use plain `${CLAUDE_PLUGIN_ROOT}` in Claude Markdown; Codex resolves installed paths.
- Quote shell arguments and keep untrusted text on stdin. Use defused XML or reject
  DOCTYPE/ENTITY on fallback. Theme classes are `.theme-dark`/`.theme-light`.
- No committed secrets. Fixture tokens and credential variable names are not leaks
  by themselves. Never expose real values. Provider model catalogs are independent.
- Generated/shared/pre-existing code is not categorically exempt. Report a verified
  defect at its maintained source; assess the changed exposure and concrete impact.
  Advisory wording or a historical-local-path note alone is not a Major.
- A past environment failure needs a same-environment base/head comparison; it is
  not a waiver for missing required checks. Panel agreement is not evidence by itself.

## Banned patterns

These project rules apply to AWS/IaC changes:
- No `0.0.0.0/0` inbound. Manage security groups through CDK/Terraform, never ad-hoc CLI ingress.
- Public ALBs use the CloudFront prefix list; no direct Route53-to-ALB/EC2 bypass.
- No IAM `Principal:"*"`, with or without a Condition. Wildcard `Resource` requires a restrictive Condition.
- No Lambda function URL `AuthType: NONE`.
- No secrets in environment variables; use Secrets Manager or SSM Parameter Store.
- PII in DynamoDB needs KMS and TTL. Keep S3 Block Public Access enabled. Never delete CloudTrail logs.
