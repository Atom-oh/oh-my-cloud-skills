---
sidebar_position: 4
title: "Observability agent"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="핵심-기능" />
<span id="진단-명령어" />
<span id="container-insights-상태" />
<span id="주요-logs-insights-쿼리" />
<span id="알람-관리" />
<span id="amazon-managed-prometheus-amp" />
<span id="amazon-managed-grafana-amg" />
<span id="adot-collector" />
<span id="self-managed-prometheusgrafana" />
<span id="주요-메트릭-참조" />
<span id="의사결정-트리" />
<span id="mcp-서버-연동" />
<span id="사용-예시" />
<span id="container-insights-설정" />
<span id="로그-분석-쿼리" />
<span id="출력-형식" />
<span id="dashboard-recommendations" />


# Observability agent

CloudWatch/Container Insights, Logs Insights, alarms, AMP, AMG, ADOT, and self-managed Prometheus/Grafana.

## Diagnostic approach

Trace telemetry from application/collector through credentials and network egress to the destination. Inspect scrape targets, exporter errors, labels, retention, alert thresholds, and dashboard queries. Diagnose missing data before proposing a new stack.

## Initial read-only checks

Run only in the intended account, region, and Kubernetes context. Service-specific follow-ups come from the observed result.

```bash
kubectl get pods -n amazon-cloudwatch -o wide
kubectl get pods -A -l app.kubernetes.io/name=opentelemetry-collector
aws cloudwatch describe-alarms --state-value ALARM
```

## Evidence and handoff

Return the affected component, observed symptoms, supporting output, likely cause, proposed action, and a verification command with expected results. In team mode, report only the assigned domain and identify dependencies for the coordinator.

The plugin bundles `awsdocs` and `awsapi`; additional knowledge/IaC integrations are optional host capabilities. Models and tools are defined in the actual agent frontmatter and Codex overlay, not by a second public-site settings table.

[Agent commands and decision tree](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/agents/observability-agent.md)
