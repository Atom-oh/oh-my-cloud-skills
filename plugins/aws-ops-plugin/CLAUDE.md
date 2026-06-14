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

| 증상 신호 (symptom) | 라우팅 대상 (route to) |
|---------------------|------------------------|
| 노드 NotReady, pod crash/OOM, 업그레이드 실패 | `eks-agent` |
| DNS 실패, ALB/NLB, IP 고갈, VPC CNI | `network-agent` |
| AccessDenied, IRSA/Pod Identity, aws-auth, RBAC | `iam-agent` |
| PVC pending, 볼륨 mount 실패, CSI | `storage-agent` |
| DB 연결 실패, throttling, ElastiCache | `database-agent` |
| 증상이 불명확/다중 도메인 | `ops-troubleshoot` (5분 triage 먼저) |

> 트리거 (KO/EN): `디버깅`, `systematic-debugging`, `버그`, `장애 디버깅`, "debug an AWS/EKS issue".
> Non-infra 버그는 `superpowers:systematic-debugging`을 직접 사용 — 이 핸드오프는 클라우드 인프라 증상에만.

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

## Team Workflow Patterns (병렬 오케스트레이션)

**기본값은 순차** (`쿼리 → 매칭 에이전트 → 진단 → 해결 → 검증`). 단일 도메인 이슈는 팀 미사용. 팀 기반 병렬은 트리거 충족 시에만:

| 트리거 | 팀 |
|--------|----|
| P1/P2 인시던트, 2+ 도메인 | `ops-incident-response` (coordinator + 전문 에이전트 병렬) |
| 전체 health check | `ops-health-check` (eks+network+iam+storage+observability+analytics) |
| security audit | `ops-security-audit` (iam+network+storage) |
| well-architected review | `ops-waf-review` (wellarchitected+cost+iam+network) |

사용자가 "병렬/동시에" 명시 시에도 사용.

> **상세**(인시던트 오케스트레이션 실행 순서, 순차 보존 규칙): **`references/team-workflows.md`** — 팀을 실제로 스폰할 때 참조.

---

## Agents

| Agent | Purpose |
|-------|---------|
| `eks-agent` | EKS cluster management, node groups, upgrades, add-ons, 5-min triage |
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
| `ops-troubleshoot` | "troubleshoot", "debug", "장애", "문제 해결" | 5-min triage → investigate → resolve → postmortem |
| `ops-health-check` | "health check", "상태 점검", "헬스체크" | Full infrastructure health assessment (includes analytics) |
| `ops-network-diagnosis` | "network issue", "네트워크 오류", "연결 문제" | VPC CNI, LB, DNS deep diagnosis |
| `ops-observability` | "monitoring", "모니터링", "로그 분석", "알람", "opentelemetry", "clickhouse", "grafana", "devops agent", "데브옵스 에이전트" | CloudWatch/PromQL/logs + OSS stack (OTel, Loki, Tempo, ClickHouse, VictoriaMetrics) + AWS DevOps Agent incident escalation |
| `ops-security-audit` | "security audit", "보안 점검", "compliance", "security agent", "penetration testing", "pentest" | IAM/network/CIS posture + AWS Security Agent (design/code review, on-demand pentest) |
| `ops-wellarchitected-review` | "well-architected", "WAF review", "인프라 진단", "아키텍처 리뷰" | 6-pillar assessment, 100-point scoring, AS-IS/TO-BE roadmap |
