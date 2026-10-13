# Well-Architected Infrastructure Health Scoring Framework

## 100-Point Weighted Scoring

| Pillar | Weight | Sub-Category | Weight | Key Metric |
|--------|--------|-------------|--------|------------|
| Operational Excellence | 15% | Monitoring Coverage | 8% | CloudWatch alarms per service category |
| | | Automation Maturity | 7% | IaC coverage, ASG adoption, automated patching |
| Security | 20% | Public Exposure | 7% | Public resources count (S3, SG, RDS, ELB) |
| | | Encryption Coverage | 7% | % resources encrypted (EBS, RDS, S3, ElastiCache) |
| | | IAM Hygiene | 6% | MFA coverage, key age, least privilege |
| Reliability | 20% | Network Resilience | 7% | Multi-AZ coverage, NAT GW redundancy, SPOF count |
| | | Data Tier Reliability | 7% | Multi-AZ DB, backup retention, engine currency |
| | | Compute Reliability | 6% | ASG coverage, scaling policy, instance generation |
| Performance Efficiency | 15% | Compute Right-sizing | 8% | Over/under-provisioned instance ratio |
| | | Database Tuning | 7% | DB utilization, IOPS efficiency, cache hit ratio |
| Cost Optimization | 20% | Cost Efficiency | 8% | MoM trend, discount coverage (RI/SP) |
| | | Storage Optimization | 6% | S3 class optimization, gp2→gp3 ratio |
| | | Idle Resource Hygiene | 6% | Waste $ (unattached EBS, stopped EC2, unused EIP) |
| Sustainability | 10% | Graviton Adoption | 5% | arm64 / total instance ratio |
| | | Efficient Resource Usage | 5% | Right-sized ratio, serverless adoption |

## Sub-Category Scoring Criteria

### Public Exposure (7%)
| Score | Criteria |
|-------|----------|
| 100% | No unintended public exposure |
| 75% | Only intentional public ELBs with WAF |
| 50% | Some SG issues (0.0.0.0/0 on non-critical ports) |
| 25% | Public DB/cache instances |
| 0% | Public S3 buckets + open SG on sensitive ports (22,3389,3306,5432,6379) |

### Encryption Coverage (7%)
| Score | Criteria |
|-------|----------|
| 100% | All resources encrypted with CMK |
| 75% | All encrypted (mix CMK + AWS-managed keys) |
| 50% | >80% encrypted |
| 25% | >50% encrypted |
| 0% | <50% encrypted |

### Network Resilience (7%)
| Score | Criteria |
|-------|----------|
| 100% | Multi-AZ all VPCs, NAT GW per AZ, no SPOF |
| 75% | Multi-AZ with minor gaps |
| 50% | Some single-AZ resources |
| 25% | Production workloads in single AZ |
| 0% | Critical services single AZ + single NAT GW |

### Cost Efficiency (8%)
| Score | Criteria |
|-------|----------|
| 100% | MoM stable, >70% discount coverage, no waste |
| 75% | MoM <5% growth, >50% discount coverage |
| 50% | MoM <15% growth, >30% discount coverage |
| 25% | MoM >15% growth OR <30% discount coverage |
| 0% | MoM >20% growth AND <10% discount coverage |

### Graviton Adoption (5%)
| Score | Criteria |
|-------|----------|
| 100% | >80% Graviton instances |
| 75% | >50% Graviton |
| 50% | >25% Graviton |
| 25% | >10% Graviton |
| 0% | <10% Graviton or no Graviton |

## Score Interpretation

| Range | Rating | Action |
|-------|--------|--------|
| 90-100 | Excellent | Maintain current practices |
| 70-89 | Good | Targeted optimizations |
| 50-69 | Fair | Plan improvements this quarter |
| < 50 | Needs Attention | Immediate remediation required |

## Pillar-Level Delegation

| Pillar Score | Status | Action |
|---|---|---|
| >= 80 | Good | Report only |
| 60-79 | Fair | Recommend improvements |
| < 60 | Needs Attention | Delegate deep dive to specialist agent |

Delegation targets:
- Cost < 60 → `cost-agent`
- Security < 60 → `iam-agent` + `ops-security-audit`
- Reliability/Network < 60 → `network-agent` + `ops-network-diagnosis`
- Performance < 60 → `eks-agent` (compute) + `database-agent` (data tier)

## Priority Matrix

| | Low Effort | High Effort |
|---|---|---|
| **High Impact** | Do First (P1) | Plan & Schedule (P2) |
| **Low Impact** | Quick Wins (P3) | Deprioritize |

## AS-IS → TO-BE Template

| Field | Description |
|-------|-------------|
| AS-IS | Current state with quantified metrics |
| TO-BE | Target state with expected improvement |
| Action | Specific remediation steps |
| Effort | Low (<1 day) / Medium (1-5 days) / High (>5 days) |
| Priority | P1 (this week) / P2 (this month) / P3 (this quarter) |
| Pillar | Which WAF pillar this addresses |
| Est. Impact | $ savings or risk reduction % |
