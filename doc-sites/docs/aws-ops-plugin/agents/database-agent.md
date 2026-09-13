---
sidebar_position: 6
title: "Database agent"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="핵심-기능" />
<span id="진단-명령어" />
<span id="rdsaurora-연결" />
<span id="dynamodb" />
<span id="elasticache" />
<span id="의사결정-트리" />
<span id="일반적인-오류와-해결책" />
<span id="mcp-서버-연동" />
<span id="사용-예시" />
<span id="rds-연결-문제-해결" />
<span id="dynamodb-스로틀링-진단" />
<span id="출력-형식" />
<span id="performance-recommendations" />


# Database agent

RDS/Aurora connectivity and performance, DynamoDB throttling/capacity, and ElastiCache connectivity, memory, and latency.

## Diagnostic approach {#diagnostic-approach}

Check endpoint/network/authentication before query performance. Correlate connection limits, failover events, hot partitions, capacity modes, cache evictions, and application retry behavior. Validate any proposed change against workload and recovery needs.

## Initial read-only checks {#initial-read-only-checks}

Run these AWS CLI checks only in the intended account and region. Choose service-specific follow-ups from the observed result.

```bash
aws rds describe-db-instances
aws dynamodb list-tables
aws elasticache describe-cache-clusters
```

## Evidence and handoff {#evidence-and-handoff}

Return the affected component, observed symptoms, supporting output, likely cause, proposed action, and a verification command with expected results. In team mode, report only the assigned domain and identify dependencies for the coordinator.

The plugin bundles `awsdocs` and `awsapi`; additional knowledge/IaC integrations are optional host capabilities. Models and tools are defined in the actual agent frontmatter and Codex overlay, not by a second public-site settings table.

[Agent commands and decision tree](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/agents/database-agent.md)
