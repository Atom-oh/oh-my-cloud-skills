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
| "CloudWatch", "Prometheus", "Grafana", "ADOT", "OpenTelemetry", "Container Insights", "Logs Insights", "metric", "alarm", "X-Ray", "모니터링", "로그 분석", "알람 설정", "메트릭", "프로메테우스", "그라파나" | `observability-agent` | Metrics, logs, alarms, tracing, AMP, AMG, ADOT |

### Analytics

| Keywords | Agent | Description |
|----------|-------|-------------|
| "OpenSearch", "Elasticsearch", "ClickHouse", "Athena", "QuickSight", "Kinesis", "데이터 분석", "로그 분석 파이프라인", "검색 엔진", "대시보드" | `analytics-agent` | OpenSearch, Athena, Kinesis, QuickSight, ClickHouse |

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
| `awsapi` | AWS API direct calls (describe, list, etc.) | eks, network, iam, storage, database, observability, analytics |
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
                        ├── Observability → observability-agent
                        └── Analytics → analytics-agent

ops-coordinator-agent ← Aggregate results → Root cause → Resolve → Verify
```

### Single-Domain Troubleshooting
```
User query → Matched agent → Diagnose → Resolve → Verify
```

---

## Team Workflow Patterns

기본값은 순차 워크플로우입니다. 팀 기반 병렬 실행은 아래 트리거 조건 충족 시에만 사용합니다.

### 팀 생성 트리거

| 트리거 조건 | 팀 이름 | 구성 |
|-------------|---------|------|
| P1/P2 인시던트, 2+ 도메인 증상 | `ops-incident-response` | ops-coordinator + 전문 에이전트 병렬 |
| "health check" 전체 점검 요청 | `ops-health-check` | eks + network + iam + storage + observability + analytics 병렬 |
| "security audit" 보안 감사 요청 | `ops-security-audit` | iam + network + storage 병렬 감사 |

### 인시던트 대응 오케스트레이션

```
1. TeamCreate("incident-{timestamp}")
2. ops-coordinator 5분 트리아지 (메인 세션)
3. 증상별 TaskCreate (network, eks, iam 등)
4. 전문 에이전트 병렬 스폰 (team_name 파라미터)
5. 결과 수집 (TaskList 모니터링)
6. ops-coordinator 근본원인 분석 + 타임스탬프 상관분석
7. 수정 실행 → 검증
8. TeamDelete + 포스트모템
```

### 순차 워크플로우 보존 규칙

- **단일 도메인 이슈는 팀을 사용하지 않습니다** (오버헤드 방지)
- 기본값: `사용자 쿼리 → 매칭 에이전트 → 진단 → 해결 → 검증`
- 팀은 위 트리거 테이블의 조건을 충족하는 경우에만 사용
- 사용자가 "병렬", "동시에", "in parallel"을 명시적으로 요청한 경우에도 사용 가능

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

## Skills

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `ops-troubleshoot` | "troubleshoot", "debug", "장애", "문제 해결" | 5-min triage → investigate → resolve → postmortem |
| `ops-health-check` | "health check", "상태 점검", "헬스체크" | Full infrastructure health assessment (includes analytics) |
| `ops-network-diagnosis` | "network issue", "네트워크 오류", "연결 문제" | VPC CNI, LB, DNS deep diagnosis |
| `ops-observability` | "monitoring", "모니터링", "로그 분석", "알람" | CloudWatch setup, PromQL, log analysis |
| `ops-security-audit` | "security audit", "보안 점검", "compliance" | IAM audit, network security, compliance |
