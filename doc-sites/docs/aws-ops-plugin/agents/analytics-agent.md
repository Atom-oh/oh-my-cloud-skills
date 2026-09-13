---
sidebar_position: 9
title: "Analytics agent"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="핵심-기능" />
<span id="진단-명령어" />
<span id="amazon-opensearch-service" />
<span id="opensearch-serverless" />
<span id="clickhouse" />
<span id="amazon-athena" />
<span id="amazon-quicksight" />
<span id="amazon-kinesis" />
<span id="주요-메트릭-참조" />
<span id="의사결정-트리" />
<span id="mcp-서버-연동" />
<span id="사용-예시" />
<span id="opensearch-클러스터-트러블슈팅" />
<span id="athena-쿼리-최적화" />
<span id="출력-형식" />


# Analytics agent

OpenSearch and OpenSearch Serverless, ClickHouse, Athena, QuickSight, and Kinesis ingestion/query pipelines.

## Diagnostic approach

Separate ingest lag from query latency. Inspect cluster/shard health, storage and memory pressure, collection access, query plans, scanned data, partitioning, dashboard refreshes, stream capacity, and iterator age. Tie suggested tuning to measured bottlenecks.

## Initial read-only checks

Run only in the intended account, region, and Kubernetes context. Service-specific follow-ups come from the observed result.

```bash
aws opensearch list-domain-names
aws opensearchserverless list-collections
aws athena list-work-groups
aws kinesis list-streams
```

## Evidence and handoff

Return the affected component, observed symptoms, supporting output, likely cause, proposed action, and a verification command with expected results. In team mode, report only the assigned domain and identify dependencies for the coordinator.

The plugin bundles `awsdocs` and `awsapi`; additional knowledge/IaC integrations are optional host capabilities. Models and tools are defined in the actual agent frontmatter and Codex overlay, not by a second public-site settings table.

[Agent commands and decision tree](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/agents/analytics-agent.md)
