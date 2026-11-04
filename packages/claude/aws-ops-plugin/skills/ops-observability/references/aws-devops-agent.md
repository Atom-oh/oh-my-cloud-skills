# AWS DevOps Agent Integration

**AWS DevOps Agent** is a managed frontier agent (GA 2026-03-31, built on Amazon Bedrock
AgentCore) that investigates incidents across AWS, multicloud and on-prem. This file keeps
only what the official plugin does not: when to escalate from this plugin, and the
CloudWatch alarm wiring.

> Investigate, chat, multi-space and backlog-task procedures (`aws devops-agent
> create-backlog-task`, Agent Space selection) are owned by the official
> `aws-agents-for-devsecops` skills: `investigating-incidents-with-aws-devops-agent`
> (+ its `REFERENCE.md`), `chatting-with-aws-devops-agent`,
> `coordinating-multi-space-devops-agent`, `setup-devops-agent`. Use those, not a copy here.

> **Human-approval boundary**: the agent produces a mitigation plan but does **not** change
> the environment on its own; execution needs human approval. Vendor metrics (e.g. lower
> MTTR) are AWS-reported claims, not guarantees.

> Distinct from native **CloudWatch investigations** (`cloudwatch-setup.md` → agentic AIOps),
> which are first-line RCA inside CloudWatch.

## When to escalate

| Situation | Action |
|-----------|--------|
| Single known cause | Fix locally with this plugin's specialist agents |
| Multi-resource / multi-service / unclear RCA after CloudWatch investigations | Start a DevOps Agent investigation (official skill above) |
| Mitigation plan produced | Review; hand the Kiro-compatible spec to a coding agent or IaC. Pair with `co-agent` review before Apply |

## Wiring CloudWatch to DevOps Agent (autonomous entry)

Chain: **CloudWatch Alarm -> EventBridge -> Lambda -> DevOps Agent webhook** (HMAC-SHA256 signed).

```bash
# 1. Create the webhook in the DevOps Agent console / Agent Space. Save the URL and
#    secret key (the secret cannot be retrieved later).
# 2. Lambda forwards the payload. Required schema:
#    { eventType: 'incident', incidentId, action: created|updated|closed|resolved,
#      priority: CRITICAL|HIGH|MEDIUM|LOW|MINIMAL, title, ... }
# 3. Verify end to end by forcing the alarm into ALARM:
aws cloudwatch set-alarm-state --alarm-name "$CLUSTER_NAME-high-cpu" \
  --state-value ALARM --state-reason "wiring test -> DevOps Agent"
```

Other verified trigger sources: PagerDuty, Dynatrace, ServiceNow and generic webhooks.
Confirm CLI parameter names with `aws devops-agent help` (new API surface).

## Common issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Alarm fires but no investigation | Webhook signature mismatch | Re-check the HMAC secret in the Lambda env; resend a test payload |
| Investigation lacks context | Topology incomplete / no starting point | Attach account integrations to the Agent Space; pass a starting point |
| Mitigation not actionable | Scope too broad | Narrow the starting point to the suspect alarm/resource |
