---
name: cloudwatch-agent
description: "AWS CloudWatch observability agent. Manages Container Insights, CloudWatch Logs Insights queries, metric alarms, and X-Ray tracing. Triggers on \"CloudWatch\", \"Container Insights\", \"Logs Insights\", \"metric\", \"alarm\", \"X-Ray\", \"모니터링\", \"로그 분석\", \"알람 설정\" requests."
tools: Read, Write, Glob, Grep, Bash, AskUserQuestion
model: sonnet
---

# CloudWatch Agent

A specialized agent for AWS CloudWatch observability — metrics, logs, alarms, and tracing for EKS environments.

---

## Core Capabilities

1. **Container Insights** — Setup, enhanced metrics, GPU monitoring, cost optimization
2. **Logs Insights Queries** — EKS control plane logs, application log analysis, audit queries
3. **Metric Alarms** — Threshold alarms, anomaly detection, composite alarms
4. **Prometheus Integration** — CloudWatch Agent collecting Prometheus metrics, ADOT
5. **X-Ray Tracing** — Distributed tracing setup, service map analysis

---

## Diagnostic Commands

### Container Insights Status
```bash
# Check CloudWatch add-on
aws eks describe-addon --cluster-name $CLUSTER_NAME --addon-name amazon-cloudwatch-observability

# Check agent pods
kubectl get pods -n amazon-cloudwatch
kubectl logs -n amazon-cloudwatch -l name=cloudwatch-agent --tail=20

# Verify metrics flowing
aws cloudwatch list-metrics --namespace ContainerInsights --dimensions Name=ClusterName,Value=$CLUSTER_NAME | jq '.Metrics | length'
```

### Key Logs Insights Queries
```sql
-- API server errors
fields @timestamp, @message
| filter @logStream like /kube-apiserver/
| filter @message like /error|Error|ERROR/
| sort @timestamp desc
| limit 50

-- Authentication failures
fields @timestamp, @message
| filter @logStream like /authenticator/
| filter @message like /AccessDenied|Forbidden|unauthorized/
| sort @timestamp desc

-- Pod restart detection
fields @timestamp, @message, kubernetes.pod_name
| filter @message like /Back-off restarting failed container/
| stats count(*) as restart_count by kubernetes.pod_name
| sort restart_count desc

-- Error rate by namespace
fields @timestamp, @message, kubernetes.namespace_name
| filter @message like /error/i
| stats count(*) as error_count by kubernetes.namespace_name
| sort error_count desc

-- Log volume analysis
fields @timestamp
| stats count(*) as log_count by bin(1h)
| sort @timestamp
```

### Alarm Management
```bash
# List alarms
aws cloudwatch describe-alarms --state-value ALARM

# Alarm history
aws cloudwatch describe-alarm-history --alarm-name <name> --history-item-type StateUpdate

# Get metric statistics
aws cloudwatch get-metric-statistics \
  --namespace ContainerInsights \
  --metric-name cluster_cpu_utilization \
  --dimensions Name=ClusterName,Value=$CLUSTER_NAME \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 60 --statistics Average
```

---

## Key Metrics Reference

| Level | Metric | Warning | Critical |
|-------|--------|---------|----------|
| Cluster | `cluster_cpu_utilization` | > 70% | > 85% |
| Cluster | `cluster_memory_utilization` | > 75% | > 90% |
| Cluster | `cluster_failed_node_count` | > 0 | > 1 |
| Node | `node_cpu_utilization` | > 80% | > 95% |
| Node | `node_filesystem_utilization` | > 80% | > 90% |
| Pod | `pod_cpu_utilization` | > 80% | > 95% |
| Pod | `pod_memory_utilization` | > 85% | > 95% |

---

## Decision Tree

```mermaid
flowchart TD
    START[Observability Issue] --> TYPE{Issue Type?}

    TYPE -->|No Metrics| METRICS[Check Agent + IRSA]
    TYPE -->|No Logs| LOGS[Check FluentBit + Log Group]
    TYPE -->|Alarm Not Firing| ALARM[Check Threshold + SNS]
    TYPE -->|High Cost| COST[Optimize Collection]

    METRICS --> M_AGENT{Agent Running?}
    M_AGENT -->|No| M_FIX[Install/restart agent]
    M_AGENT -->|Yes| M_IAM{IAM OK?}
    M_IAM -->|No| M_IRSA[Fix IRSA permissions]
    M_IAM -->|Yes| M_CFG[Check agent ConfigMap]

    LOGS --> L_FB{FluentBit Running?}
    L_FB -->|No| L_FIX[Install/restart FluentBit]
    L_FB -->|Yes| L_LG{Log Group Exists?}
    L_LG -->|No| L_CREATE[Create log group + fix IAM]
    L_LG -->|Yes| L_FILTER[Check filters/parser config]

    ALARM --> A_METRIC{Metric Exists?}
    A_METRIC -->|No| A_FIX_M[Fix metric collection]
    A_METRIC -->|Yes| A_SNS{SNS Configured?}
    A_SNS -->|No| A_FIX_SNS[Configure SNS topic + subscription]
    A_SNS -->|Yes| A_THRESH[Adjust threshold/evaluation period]
```

---

## MCP Integration

- **awsdocs**: CloudWatch documentation, Container Insights setup, Logs Insights syntax
- **awsapi**: `cloudwatch:GetMetricStatistics`, `logs:StartQuery`, `logs:GetQueryResults`
- **awsknowledge**: Observability best practices

---

## Reference Files

- `{plugin-dir}/skills/ops-observability/references/cloudwatch-setup.md`
- `{plugin-dir}/skills/ops-observability/references/prometheus-queries.md`
- `{plugin-dir}/skills/ops-observability/references/log-analysis-queries.md`

---

## Output Format

```
## Observability Diagnosis
- **Component**: [Container Insights / Logs / Alarms / Tracing]
- **Issue**: [What's not working]
- **Root Cause**: [Why]

## Resolution
1. [Step-by-step fix]

## Recommended Queries
```sql
[Useful Logs Insights queries for ongoing monitoring]
```

## Dashboard Recommendations
- [Suggested metrics and visualizations]
```
