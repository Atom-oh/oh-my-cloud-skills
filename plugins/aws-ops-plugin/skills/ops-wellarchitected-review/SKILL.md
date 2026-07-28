---
name: ops-wellarchitected-review
description: "AWS Well-Architected Framework 6-pillar infrastructure review with 100-point scoring, severity-rated findings, and AS-IS to TO-BE transformation roadmap. Use when the user asks for a well-architected review, WAF review, pillar review, or an architecture/infrastructure assessment with a score — '인프라 진단', '아키텍처 리뷰', '심층 진단', 'WAF 점검', '인프라 점수'."
allowed-tools:
  - Bash
  - Read
  - Grep
---

# Well-Architected Framework Review Workflow

Systematic 6-pillar infrastructure assessment producing quantified scores, prioritized findings, and a transformation roadmap.

## Phase 1: Scope & Context

1. **Determine review scope**:
   - Full 6-pillar review (default, ~15-20 min)
   - Specific pillar deep dive (user specifies: Cost, Security, Reliability, Performance, OpEx, Sustainability)
2. **Identify target environment**:
   - AWS account and region
   - EKS cluster name (if applicable)
   - Key service categories in use
3. **Baseline inventory**:

```bash
# Account and region
aws sts get-caller-identity
aws configure get region

# Service summary
aws ec2 describe-instances --query 'Reservations[].Instances[?State.Name==`running`] | length(@)'
aws rds describe-db-instances --query 'DBInstances | length(@)'
aws eks list-clusters --query 'clusters[]' --output text
aws s3api list-buckets --query 'Buckets | length(@)'
aws lambda list-functions --query 'Functions | length(@)'
```

## Phase 2: Data Collection

Gather data by pillar. Run commands from reference files:

| Pillar | Key Data Sources | Reference |
|--------|-----------------|-----------|
| Cost Optimization | CE API (cost/usage, RI/SP coverage), idle resource scan | `references/pillar-cost-optimization.md` |
| Security | SG audit, encryption check, IAM credential report, public exposure | `references/pillar-security-reliability.md` Part A |
| Reliability | VPC/AZ distribution, NAT GW count, Multi-AZ DB, ASG coverage, backup retention | `references/pillar-security-reliability.md` Part B |
| Performance | Instance utilization, kubectl top, Lambda memory, DB metrics | `references/pillar-performance-opex-sustainability.md` Part A |
| OpEx | CloudWatch alarms, log retention, CloudTrail, IaC detection | `references/pillar-performance-opex-sustainability.md` Part B |
| Sustainability | Graviton ratio, gp2/gp3 ratio, Lambda architecture, serverless count | `references/pillar-performance-opex-sustainability.md` Part C |

**Missing data handling**: If a service is not detected (no EKS clusters, no MSK, etc.), skip that sub-assessment and note: `"[Service] not detected — skipping related assessment."` Do not fabricate data.

## Phase 3: Pillar Assessment

For each pillar, apply scoring criteria from `references/waf-scoring-framework.md`:

1. Calculate sub-category scores (0-100 scale per sub-category)
2. Apply weights to get pillar score
3. Rate findings by severity:

| Severity | Criteria | Examples |
|----------|----------|---------|
| Critical | Immediate exploitation/failure risk | Public S3, unencrypted prod DB, single-AZ prod |
| Warning | Elevated risk, planned remediation | Old access keys, no Multi-AZ dev DB, gp2 volumes |
| Info | Best practice recommendation | Graviton candidates, lifecycle policy missing |

## Phase 4: Scoring Synthesis

1. **Calculate Infrastructure Health Score** (weighted sum of pillar scores):

```
Score = Σ (pillar_score × pillar_weight)
```

2. **Generate pillar summary table**:

| Pillar | Score | Weight | Weighted | Status |
|--------|-------|--------|----------|--------|
| Operational Excellence | XX | 15% | X.X | Good/Fair/Needs Attention |
| Security | XX | 20% | X.X | ... |
| Reliability | XX | 20% | X.X | ... |
| Performance Efficiency | XX | 15% | X.X | ... |
| Cost Optimization | XX | 20% | X.X | ... |
| Sustainability | XX | 10% | X.X | ... |
| **Total** | | **100%** | **XX/100** | **[Rating]** |

3. **Top 5 findings** — rank by impact (severity × blast radius)
4. **Estimated savings** — aggregate from Cost and Performance findings

## Phase 5: Roadmap Generation

Generate AS-IS → TO-BE recommendations using the Priority Matrix from `references/waf-scoring-framework.md`:

### Quick Wins (This Week)
| # | Finding | AS-IS | TO-BE | Est. Impact | Effort |
|---|---------|-------|-------|-------------|--------|

### Short-term (1-3 Months)
| # | Finding | AS-IS | TO-BE | Est. Impact | Effort |
|---|---------|-------|-------|-------------|--------|

### Medium-term (3-6 Months)
| # | Finding | AS-IS | TO-BE | Est. Impact | Effort |
|---|---------|-------|-------|-------------|--------|

Include dependency notes (e.g., "Requires VPC endpoint before NAT GW removal").

## Phase 6: Report Delivery

Output the structured WAF report. Match user's language (Korean or English).

```
============================================================
  AWS Well-Architected Review Report
============================================================
  Date:    YYYY-MM-DD
  Account: XXXXXXXXXXXX
  Region:  ap-northeast-2
  Scope:   Full 6-Pillar Review
============================================================
  Infrastructure Health Score: XX / 100  [Rating]
============================================================

  [Pillar Scores Table]
  [Top 5 Findings]
  [Estimated Savings: Monthly $X, Annual $Y]
  [Quick Wins / Short-term / Medium-term Roadmap]
  [Immediate Action Items]
============================================================
```

## Cross-Agent Delegation

When a pillar scores below 60, recommend delegation to specialist:

| Pillar < 60 | Delegate To | Action |
|---|---|---|
| Cost Optimization | `cost-agent` | Deep FinOps analysis |
| Security | `iam-agent` + `ops-security-audit` | Full security audit |
| Reliability (Network) | `network-agent` + `ops-network-diagnosis` | Network deep dive |
| Performance (Compute) | `eks-agent` | EKS/compute optimization |
| Performance (Data) | `database-agent` | Database right-sizing |

## References

- `references/waf-scoring-framework.md` — Scoring methodology, weights, criteria, priority matrix
- `references/pillar-cost-optimization.md` — Cost assessment commands, pricing benchmarks, idle detection
- `references/pillar-security-reliability.md` — Security scoring, public exposure, encryption, reliability checks
- `references/pillar-performance-opex-sustainability.md` — Right-sizing, monitoring, Graviton, sustainability metrics
