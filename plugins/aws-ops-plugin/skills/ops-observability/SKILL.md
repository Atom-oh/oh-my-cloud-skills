---
name: ops-observability
description: "AWS/EKS observability setup and analysis: CloudWatch, Prometheus, log analysis"
triggers:
  - "monitoring"
  - "모니터링"
  - "로그 분석"
  - "알람"
  - "observability"
  - "logs insights"
model: sonnet
allowed-tools:
  - Bash
  - Read
  - Grep
---

# Ops Observability Skill

Observability setup, configuration, and analysis for AWS/EKS environments.

## Workflow

### Step 1: Assess Current State
```bash
# What's collecting metrics?
kubectl get pods -n amazon-cloudwatch
kubectl get pods -n monitoring
kubectl get pods -n prometheus

# What log groups exist?
aws logs describe-log-groups --log-group-name-prefix /aws/containerinsights/$CLUSTER_NAME --query 'logGroups[].{name:logGroupName,retention:retentionInDays,size:storedBytes}'

# What alarms exist?
aws cloudwatch describe-alarms --state-value ALARM --query 'MetricAlarms[].{name:AlarmName,state:StateValue,metric:MetricName}'
```

### Step 2: Setup / Fix
Route to appropriate reference for setup procedures.

### Step 3: Create Queries and Alarms
Use reference files for query templates and threshold guidelines.

## Quick Reference

### Enable Container Insights
```bash
aws eks create-addon --cluster-name $CLUSTER_NAME --addon-name amazon-cloudwatch-observability --addon-version v1.5.0-eksbuild.1
```

### Essential Logs Insights Query
```sql
fields @timestamp, @message
| filter @message like /error/i
| sort @timestamp desc
| limit 50
```

### Essential Alarm
```bash
aws cloudwatch put-metric-alarm --alarm-name "$CLUSTER_NAME-high-cpu" --namespace ContainerInsights --metric-name cluster_cpu_utilization --dimensions Name=ClusterName,Value=$CLUSTER_NAME --statistic Average --period 300 --evaluation-periods 2 --threshold 80 --comparison-operator GreaterThanThreshold --alarm-actions <sns-topic-arn>
```

## References

- `references/cloudwatch-setup.md` — Container Insights, log groups, dashboards
- `references/prometheus-queries.md` — PromQL alert rules for EKS
- `references/log-analysis-queries.md` — CloudWatch Logs Insights query templates
