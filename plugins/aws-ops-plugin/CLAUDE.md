# AWS Ops Plugin — Claude Code Configuration

A unified plugin for AWS/EKS infrastructure operations and troubleshooting: cluster management, networking diagnostics, IAM/RBAC, observability, storage, database, and cost optimization.

Uses AWS MCP servers for real-time documentation and resource analysis.

---

## Auto-Invocation Rules

When the following keywords are detected, automatically invoke the corresponding agent.

### EKS Cluster Operations

| Keywords | Agent | Description |
|----------|-------|-------------|
| "EKS troubleshoot", "cluster issue", "node NotReady", "pod crash", "EKS upgrade", "add-on", "노드 문제", "클러스터 장애", "EKS 업그레이드" | `eks-agent` | EKS cluster operations and troubleshooting |

### Network Diagnostics

| Keywords | Agent | Description |
|----------|-------|-------------|
| "VPC CNI", "IP exhaustion", "load balancer", "ALB", "NLB", "DNS resolution", "security group", "네트워크 오류", "IP 부족", "로드밸런서", "연결 문제" | `network-agent` | VPC, CNI, Load Balancer, DNS diagnostics |

### IAM & Security

| Keywords | Agent | Description |
|----------|-------|-------------|
| "IRSA", "Pod Identity", "RBAC", "aws-auth", "IAM role", "permission denied", "AccessDenied", "권한 오류", "인증 실패", "보안 설정" | `iam-agent` | IAM, IRSA, Pod Identity, RBAC troubleshooting |

### Observability

| Keywords | Agent | Description |
|----------|-------|-------------|
| "CloudWatch", "Container Insights", "Logs Insights", "metric", "alarm", "X-Ray", "모니터링", "로그 분석", "알람 설정", "메트릭" | `cloudwatch-agent` | Metrics, logs, alarms, tracing |

### Storage

| Keywords | Agent | Description |
|----------|-------|-------------|
| "EBS CSI", "EFS CSI", "FSx", "PVC", "PersistentVolume", "mount error", "volume attach", "스토리지 오류", "볼륨 마운트", "PVC 바인딩" | `storage-agent` | EBS, EFS, FSx CSI driver troubleshooting |

### Database

| Keywords | Agent | Description |
|----------|-------|-------------|
| "RDS", "Aurora", "DynamoDB", "ElastiCache", "database connection", "throttling", "DB 연결", "데이터베이스 오류", "스로틀링" | `database-agent` | RDS, Aurora, DynamoDB, ElastiCache operations |

### Cost

| Keywords | Agent | Description |
|----------|-------|-------------|
| "cost analysis", "cost optimization", "billing", "savings plan", "reserved instance", "비용 분석", "비용 절감", "요금" | `cost-agent` | Cost analysis and optimization |

### Incident Coordination

| Keywords | Agent | Description |
|----------|-------|-------------|
| "incident", "outage", "서비스 장애", "긴급 대응", "복합 장애", "장애 조율" | `ops-coordinator-agent` | Multi-domain incident coordination |

---

## MCP Integration

| MCP Server | Purpose | Used By |
|------------|---------|---------|
| `awsknowledge` | AWS architecture knowledge, recommendations, regional info | All agents |
| `awsdocs` | AWS official documentation search/read | All agents |
| `awsapi` | AWS API direct calls (describe, list, etc.) | eks, network, iam, storage, database, cloudwatch |
| `awspricing` | Cost analysis, pricing queries | cost-agent |
| `awsiac` | CloudFormation/CDK validation, troubleshooting | eks-agent, ops-coordinator |

---

## Workflow Patterns

### Incident Response Workflow
```
User incident report → ops-coordinator-agent (triage)
                        ├── Network symptoms → network-agent
                        ├── Cluster symptoms → eks-agent
                        ├── Auth symptoms → iam-agent
                        ├── Storage symptoms → storage-agent
                        └── Observability → cloudwatch-agent

ops-coordinator-agent ← Aggregate results → Root cause → Resolve → Verify
```

### Single-Domain Troubleshooting
```
User query → Matched agent → Diagnose → Resolve → Verify
```

---

## Agents

| Agent | Model | Purpose |
|-------|-------|---------|
| `eks-agent` | sonnet | EKS cluster management, node groups, upgrades, add-ons, 5-min triage |
| `network-agent` | sonnet | VPC CNI, ALB/NLB, DNS, Security Groups, IP exhaustion |
| `iam-agent` | sonnet | IRSA, Pod Identity, RBAC, aws-auth, policy validation |
| `cloudwatch-agent` | sonnet | Container Insights, Logs Insights queries, alarms, X-Ray |
| `storage-agent` | sonnet | EBS/EFS/FSx CSI, PVC binding, mount errors |
| `database-agent` | sonnet | RDS/Aurora connectivity, DynamoDB throttling, ElastiCache |
| `cost-agent` | sonnet | awspricing MCP cost analysis, savings strategies |
| `ops-coordinator-agent` | opus | Multi-domain incident coordination, severity assessment, team orchestration |

## Skills

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `ops-troubleshoot` | "troubleshoot", "debug", "장애", "문제 해결" | 5-min triage → investigate → resolve → postmortem |
| `ops-health-check` | "health check", "상태 점검", "헬스체크" | Full infrastructure health assessment |
| `ops-network-diagnosis` | "network issue", "네트워크 오류", "연결 문제" | VPC CNI, LB, DNS deep diagnosis |
| `ops-observability` | "monitoring", "모니터링", "로그 분석", "알람" | CloudWatch setup, PromQL, log analysis |
| `ops-security-audit` | "security audit", "보안 점검", "compliance" | IAM audit, network security, compliance |
