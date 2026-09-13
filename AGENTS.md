<!-- generated-by: co-agent · source: CLAUDE.md · claude-md-sha: 39a22b7957cb · generated-at: 2026-09-13 · DO NOT EDIT — edit CLAUDE.md then run /co-agent sync-context -->
> Shared context derived from CLAUDE.md; facts describe the trusted base.

# Review contract

This is a Claude Code/Codex plugin marketplace: Markdown procedures and Python,
Bash and Node helpers. `docs/` is internal; `doc-sites/` is public. Derived inventory
separates source skills, commands, agents, generated entries and review cells.

## Authority

- Maintain English prose without duplicate translations. Literal aliases, syntax,
  fixtures and localized payloads are data. Deliverable language follows the user.
- Use current root/scoped policy and non-superseded decisions. Historical ADRs,
  plans and prior test results are evidence, not current requirements or waivers.
- Verify base/head code before alleging a missing helper or contradiction: absence
  from a diff is not absence from base. Unverified assumptions are not findings.
  Code demonstrates behavior; it does not excuse policy violations.

## Distinct workflows

- Required CI needs complete configured peer/input coverage, a completed chair and
  no active Critical/Major. Missing/failed/truncated evidence is ERROR. Inspect
  latest-HEAD Issues and inline comments; both AI and Codex checks must pass.
- Privileged review runs trusted-base code on PR data. Isolated head CI validates
  the head generator/output/context. Branch-protection settings are external facts.
- Local co-agent excludes its current host. Review/decide/ADR may report solo work;
  consensus/harness need ready peers. Opt-in hooks retain their own quorum/failure
  rules and do not replace CI.
- Codex entries are procedures, not native roles or permission grants. Hooks need
  trust; project-init templates additionally need consumer installation and project
  trust. Kiro guards the applied diff, not its process. Atlas Codex repair differs
  from optional Claude-backed unattended repair.

## Checks and calibration

- Run TAP, both manifest validators, all-plugin freshness and skill evaluation.
  Runtime probes require local Codex. Edit maintained source and regenerate overlays;
  no skipped packages. Project-init source is mirrored; its overlay is local.
- Versions agree across manifests/registries; release tags need not change per PR.
  Follow `docs/reference/review-routing.md`: content >=85, diagram XML/layout >=80,
  Remarp validation before build.
- Use bare tool names, correct installed paths, quoted arguments and stdin for
  untrusted text. Reject unsafe XML. Themes use `.theme-dark`/`.theme-light`.
- Shared/generated code is not exempt from real defects. Check the changed exposure
  and maintained source. Fixture/credential names are not leaked values by themselves.
  Provider catalogs differ. Historical-path notes alone are not Major defects.
- Compare suspected environment failures on base/head; never waive required checks.
  Panel agreement is not proof. Never expose credential values.

## Banned patterns

AWS/IaC project mandates:
- No `0.0.0.0/0` inbound. Security groups via CDK/Terraform, never ad-hoc CLI ingress.
- Public ALBs use CloudFront's prefix list; no direct Route53-to-ALB/EC2 bypass.
- No IAM `Principal:"*"`, with or without Condition. Wildcard Resource needs Condition.
- No Lambda URL `AuthType: NONE`. No secrets in environment variables; use Secrets Manager/SSM.
- DynamoDB PII needs KMS+TTL. S3 Block Public Access stays on. Never delete CloudTrail logs.
