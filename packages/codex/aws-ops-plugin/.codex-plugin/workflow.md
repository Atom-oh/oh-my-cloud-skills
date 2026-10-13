# Operations workflow in Codex

Use the symptom-specific procedure: `eks-agent`, `network-agent`, `iam-agent`,
`storage-agent`, `database-agent`, `observability-agent`, `analytics-agent` or
`cost-agent`. Use `ops-coordinator-agent` when symptoms cross domains. These names
are installed skills containing the shared specialist procedure, not native
Codex agent types.

Preserve each runbook's evidence and remediation boundaries. A diagnosis is not
authorization to change cloud resources. For infrastructure review, use both the
Well-Architected procedure and `ops-security-audit` when their scopes apply.
MCP availability and credentials must be checked from the active session.

For a cross-domain incident, the host owns triage, the dependency/status list and
the final evidence synthesis. Delegate independent read-only domain checks with
available host tools or perform them inline. Apply the runtime's team-orchestration
mapping to shared team references; `team_name` and Claude lifecycle calls do not
provision a native Codex team. Keep remediation authorization separate from diagnosis.

This plugin bundles `awsdocs` and `awsapi`. Knowledge, pricing and IaC tools are
additional capabilities discovered in the active session; no companion package is
assumed installed. Use the source's documented CLI alternative when available and
report required missing capability or credentials as a gap.
