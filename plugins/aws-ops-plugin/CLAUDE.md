# AWS Ops Plugin — Claude Code Configuration

A unified plugin for AWS/EKS infrastructure operations and troubleshooting: cluster management, networking diagnostics, IAM/RBAC, observability, storage, database, and cost optimization.

Uses AWS MCP servers for real-time documentation and resource analysis.

---

## MCP Integration

This plugin bundles 2 MCP servers. The remaining 3 (`awsknowledge`, `awspricing`, `awsiac`) are provided by the `deploy-on-aws` plugin and available when both plugins are loaded.

| MCP Server | Source | Purpose | Used By |
|------------|--------|---------|---------|
| `awsdocs` | **this plugin** | AWS official documentation search/read | All agents |
| `awsapi` | **this plugin** | AWS API direct calls (describe, list, etc.) | eks, network, iam, storage, database, observability, analytics, wellarchitected |
| `awsknowledge` | deploy-on-aws | AWS architecture knowledge, recommendations, regional info | All agents |
| `awspricing` | deploy-on-aws | Cost analysis, pricing queries | cost-agent |
| `awsiac` | deploy-on-aws | CloudFormation/CDK validation, troubleshooting | eks-agent, ops-coordinator |

---

## Workflow Patterns

### Incident Response Workflow
```
User incident report → ops-coordinator-agent (triage)
                        ├── Network symptoms → network-agent
                        ├── Cluster symptoms → eks-agent
                        ├── Auth symptoms → iam-agent
                        ├── Storage symptoms → storage-agent
                        ├── Observability → observability-agent
                        └── Analytics → analytics-agent

ops-coordinator-agent ← Aggregate results → Root cause → Resolve → Verify
```

### Single-Domain Troubleshooting
```
User query → Matched agent → Diagnose → Resolve → Verify
```

### superpowers Handoff (systematic-debugging ↔ aws-ops)

When a debugging session runs under **`superpowers:systematic-debugging`** and the failing
system is AWS/EKS, hand the *reproduce → diagnose* step to this plugin, then return the root
cause to the debugging loop. The method stays with superpowers; we supply domain commands.

| Symptom | Route to |
|---------------------|------------------------|
| Node NotReady, pod crash/OOM, upgrade failure | `eks-agent` |
| DNS failure, ALB/NLB, IP exhaustion, VPC CNI | `network-agent` |
| AccessDenied, IRSA/Pod Identity, aws-auth, RBAC | `iam-agent` |
| PVC pending, volume mount failure, CSI | `storage-agent` |
| DB connection failure, throttling, ElastiCache | `database-agent` |
| Symptom unclear / spans multiple domains | `ops-troubleshoot` (5-minute triage first) |

> Triggers (KO/EN): `디버깅`, `systematic-debugging`, `버그`, `장애 디버깅`, "debug an AWS/EKS issue".
> For non-infra bugs, use `superpowers:systematic-debugging` directly — this handoff is only for cloud infrastructure symptoms.

### Well-Architected Review Workflow
```
User WAF request → wellarchitected-agent (scope)
                    ├── Full review → All 6 pillars assessed
                    │   ├── Cost Optimization → CE API + idle scan
                    │   ├── Security → exposure + encryption + IAM
                    │   ├── Reliability → HA + SPOF + backup
                    │   ├── Performance → right-sizing + tuning
                    │   ├── OpEx → monitoring + automation
                    │   └── Sustainability → Graviton + efficiency
                    └── Specific pillar → Targeted deep dive

wellarchitected-agent → Score (XX/100) → Findings → AS-IS/TO-BE Roadmap
                        └── Pillar < 60 → Delegate to specialist agent
```

---

## Team Workflow Patterns (parallel orchestration)

**The default is sequential** (`query → matched agent → diagnose → resolve → verify`). Single-domain issues do not use a team. Team-based parallelism only when a trigger is met:

| Trigger | Team |
|--------|----|
| P1/P2 incident, 2+ domains | `ops-incident-response` (coordinator + specialist agents in parallel) |
| Full health check | `ops-health-check` (eks+network+iam+storage+observability+analytics) |
| security audit | `ops-security-audit` (iam+network+storage) |
| well-architected review | `ops-waf-review` (wellarchitected+cost+iam+network) |

Also used when the user explicitly requests "in parallel/simultaneously".

> **Details** (incident orchestration execution order, rules for preserving the sequential path): **`references/team-workflows.md`** — consult this when actually spawning a team.

---

## Agents

| Agent | Purpose |
|-------|---------|
| `eks-agent` | EKS cluster management, node groups, upgrades, add-ons, 5-minute triage |
| `network-agent` | VPC CNI, ALB/NLB, DNS, Security Groups, IP exhaustion |
| `iam-agent` | IRSA, Pod Identity, RBAC, aws-auth, policy validation |
| `observability-agent` | CloudWatch, AMP, AMG, ADOT, Prometheus/Grafana, X-Ray |
| `storage-agent` | EBS/EFS/FSx CSI, PVC binding, mount errors |
| `database-agent` | RDS/Aurora connectivity, DynamoDB throttling, ElastiCache |
| `cost-agent` | awspricing MCP cost analysis, savings strategies |
| `analytics-agent` | OpenSearch, ClickHouse, Athena, QuickSight, Kinesis |
| `ops-coordinator-agent` | Multi-domain incident coordination, severity assessment, team orchestration |
| `wellarchitected-agent` | AWS Well-Architected 6-pillar review: 100-point scoring, findings, roadmap |

## Skills

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `ops-troubleshoot` | "troubleshoot", "debug", "systematic-debugging", "장애" (incident), "디버깅" (debugging), "문제 해결" (problem solving) | 5-minute triage → investigate → resolve → postmortem (AWS/EKS arm of `superpowers:systematic-debugging`) |
| `ops-health-check` | "health check", "상태 점검" (status check), "헬스체크" (health check) | Full infrastructure health assessment (includes analytics) |
| `ops-network-diagnosis` | "network issue", "네트워크 오류" (network error), "연결 문제" (connection problem) | VPC CNI, LB, DNS deep diagnosis |
| `ops-observability` | "monitoring", "모니터링" (monitoring), "로그 분석" (log analysis), "알람" (alarm), "opentelemetry", "clickhouse", "grafana", "devops agent", "데브옵스 에이전트" (devops agent) | CloudWatch/PromQL/logs + OSS stack (OTel, Loki, Tempo, ClickHouse, VictoriaMetrics) + AWS DevOps Agent incident escalation |
| `ops-security-audit` | "security audit", "보안 점검" (security check), "compliance", "security agent", "penetration testing", "pentest" | IAM/network/CIS posture + AWS Security Agent (design/code review, on-demand pentest) |
| `ops-wellarchitected-review` | "well-architected", "WAF review", "인프라 진단" (infrastructure diagnosis), "아키텍처 리뷰" (architecture review) | 6-pillar assessment, 100-point scoring, AS-IS/TO-BE roadmap |
