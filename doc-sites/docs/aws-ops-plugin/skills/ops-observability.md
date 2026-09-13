---
sidebar_position: 4
title: "Observability workflow"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="ops-observability" />
<span id="description" />
<span id="trigger-keywords" />
<span id="step-1-current-state-assessment" />
<span id="step-2-setupfix" />
<span id="step-3-query-and-alarm-creation" />
<span id="quick-reference" />
<span id="enable-container-insights" />
<span id="open-source-observability-stack" />
<span id="version-coupling-clickhouse-backed-stacks" />
<span id="aws-devops-agent-incident-escalation" />
<span id="promql-alarm-rules-extended" />
<span id="alert-severity-levels" />
<span id="node-alerts" />
<span id="pod-alerts" />
<span id="deployment-alerts" />
<span id="vpc-cni-alerts" />
<span id="pvc-and-network-alerts" />
<span id="dashboard-configuration-guide" />
<span id="container-insights-collected-metrics" />
<span id="cluster-level" />
<span id="node-level" />
<span id="podcontainer-level" />
<span id="container-insights-setup" />
<span id="method-1-eks-add-on-recommended" />
<span id="eks-control-plane-logging" />
<span id="log-group-structure" />
<span id="essential-cloudwatch-alarms" />
<span id="cost-optimization-strategies" />
<span id="log-analysis-queries-extended" />
<span id="control-plane-queries" />
<span id="api-server-errors" />
<span id="audit-log---user-activity" />
<span id="audit-log---resource-changes" />
<span id="authentication-failures" />
<span id="scheduler-issues" />
<span id="application-log-queries" />
<span id="error-rate-by-namespace" />
<span id="pod-restart-detection" />
<span id="oomkilled-events" />
<span id="log-volume-by-time" />
<span id="top-error-messages" />
<span id="response-time-analysis-json-logs" />
<span id="infrastructure-queries" />
<span id="vpc-cni-errors" />
<span id="kubelet-issues" />
<span id="node-system-issues" />
<span id="cost-analysis-queries" />
<span id="log-volume-by-container" />
<span id="identify-noisy-containers" />
<span id="usage-examples" />
<span id="container-insights-setup-1" />
<span id="log-analysis" />
<span id="reference-files" />


# Observability workflow

Set up or analyze monitoring, logs, metrics, traces, alarms, and incident signals.

## Workflow

Map producers, collectors, transports, storage, queries, dashboards, and alerts. Inspect the failing hop, permissions, configuration, and retention. Validate that a representative event reaches the destination and triggers the intended query or alert.

## Coverage

CloudWatch and Logs Insights; X-Ray/ADOT/OTel; Prometheus/AMP; Grafana/AMG; self-managed Loki, Tempo, ClickHouse, and VictoriaMetrics; relevant DevOps Agent escalation.

## Reporting and boundaries

Examples and thresholds must fit the workload. Distinguish telemetry setup from diagnosing an application bug; record evidence and gaps rather than treating a dashboard screenshot as end-to-end validation.

The source skill contains the command playbooks, decision trees, examples, reference files, and host/team integration. Consult it for the exact operation being performed.

[Canonical workflow and playbooks](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/skills/ops-observability/SKILL.md)
