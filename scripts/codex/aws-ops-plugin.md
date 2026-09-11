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
