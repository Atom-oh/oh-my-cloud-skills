# CloudWatch Setup

Container Insights, log groups, and dashboards for EKS.

---

## Container Insights Setup

### Method 1: EKS Add-on (Recommended)
```bash
# Create IRSA for CloudWatch Agent
eksctl create iamserviceaccount \
  --name cloudwatch-agent \
  --namespace amazon-cloudwatch \
  --cluster $CLUSTER_NAME \
  --attach-policy-arn arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy \
  --approve

# Install add-on
aws eks create-addon \
  --cluster-name $CLUSTER_NAME \
  --addon-name amazon-cloudwatch-observability \
  --service-account-role-arn <role-arn>

# Verify
aws eks describe-addon --cluster-name $CLUSTER_NAME --addon-name amazon-cloudwatch-observability
kubectl get pods -n amazon-cloudwatch
```

### Method 2: Manual Installation
```bash
kubectl create namespace amazon-cloudwatch
kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/quickstart/cwagent-fluent-bit-quickstart.yaml
```

## Collected Metrics

### Cluster Level
- `cluster_node_count` — Node count
- `cluster_failed_node_count` — Failed node count
- `cluster_cpu_utilization` — CPU utilization
- `cluster_memory_utilization` — Memory utilization

### Node Level
- `node_cpu_utilization` — Node CPU utilization
- `node_memory_utilization` — Node memory utilization
- `node_network_total_bytes` — Total network bytes
- `node_filesystem_utilization` — Filesystem utilization

### Pod/Container Level
- `pod_cpu_utilization` — Pod CPU utilization
- `pod_memory_utilization` — Pod memory utilization
- `pod_network_rx_bytes` — Received bytes
- `pod_network_tx_bytes` — Transmitted bytes

## EKS Control Plane Logging

```bash
# Enable all log types
aws eks update-cluster-config \
  --name $CLUSTER_NAME \
  --logging '{"clusterLogging":[{"types":["api","audit","authenticator","controllerManager","scheduler"],"enabled":true}]}'

# Recommended: Enable at minimum
# - api: API server logs
# - audit: Audit logs (security)
# - authenticator: IAM authentication logs
```

### Log Group Structure
```
/aws/eks/$CLUSTER_NAME/cluster
├── kube-apiserver-*           # API server
├── kube-apiserver-audit-*     # Audit logs
├── authenticator-*            # IAM auth
├── kube-controller-manager-*  # Controller manager
└── kube-scheduler-*           # Scheduler
```

### Container Log Groups
```
/aws/containerinsights/$CLUSTER_NAME/application   # App stdout/stderr
/aws/containerinsights/$CLUSTER_NAME/host           # Node system logs
/aws/containerinsights/$CLUSTER_NAME/dataplane      # kubelet, kube-proxy
/aws/containerinsights/$CLUSTER_NAME/performance    # Performance metrics
```

## Log Retention Best Practices

```bash
# Production: 30 days for app logs, 90 days for audit
aws logs put-retention-policy --log-group-name /aws/containerinsights/$CLUSTER_NAME/application --retention-in-days 30
aws logs put-retention-policy --log-group-name /aws/eks/$CLUSTER_NAME/cluster --retention-in-days 90

# Development: 7 days
aws logs put-retention-policy --log-group-name /aws/containerinsights/dev-cluster/application --retention-in-days 7

# Use Infrequent Access for cost savings (50%)
aws logs create-log-group --log-group-name /aws/containerinsights/$CLUSTER_NAME/audit --log-group-class INFREQUENT_ACCESS
```

## Essential Alarms

```bash
# High CPU
aws cloudwatch put-metric-alarm \
  --alarm-name "$CLUSTER_NAME-high-cpu" \
  --namespace ContainerInsights \
  --metric-name cluster_cpu_utilization \
  --dimensions Name=ClusterName,Value=$CLUSTER_NAME \
  --statistic Average --period 300 --evaluation-periods 2 \
  --threshold 80 --comparison-operator GreaterThanThreshold \
  --alarm-actions $SNS_TOPIC_ARN

# High Memory
aws cloudwatch put-metric-alarm \
  --alarm-name "$CLUSTER_NAME-high-memory" \
  --namespace ContainerInsights \
  --metric-name cluster_memory_utilization \
  --dimensions Name=ClusterName,Value=$CLUSTER_NAME \
  --statistic Average --period 300 --evaluation-periods 2 \
  --threshold 85 --comparison-operator GreaterThanThreshold \
  --alarm-actions $SNS_TOPIC_ARN

# Node Failures
aws cloudwatch put-metric-alarm \
  --alarm-name "$CLUSTER_NAME-node-failure" \
  --namespace ContainerInsights \
  --metric-name cluster_failed_node_count \
  --dimensions Name=ClusterName,Value=$CLUSTER_NAME \
  --statistic Maximum --period 60 --evaluation-periods 2 \
  --threshold 0 --comparison-operator GreaterThanThreshold \
  --alarm-actions $SNS_TOPIC_ARN
```

## Cost Optimization

| Strategy | Savings | Effort |
|----------|---------|--------|
| Set log retention (vs. forever) | 50-80% | Low |
| Use Infrequent Access log class | 50% | Low |
| Filter health check logs | 10-30% | Low |
| Reduce metric collection interval (60s vs 30s) | 30% | Low |
| Disable Enhanced Container Insights when not needed | 20-40% | Low |
| Consolidate dashboards (3 free) | 100% per dashboard | Low |

## Troubleshooting

### Metrics Not Showing
```bash
# Check agent logs
kubectl logs -n amazon-cloudwatch -l name=cloudwatch-agent --tail=30

# Check IAM permissions
kubectl exec -n amazon-cloudwatch ds/cloudwatch-agent -- aws sts get-caller-identity

# Verify metrics
aws cloudwatch list-metrics --namespace ContainerInsights --dimensions Name=ClusterName,Value=$CLUSTER_NAME | jq '.Metrics | length'
```

### Alarms Not Firing
```bash
aws cloudwatch describe-alarms --alarm-names <name>
aws cloudwatch describe-alarm-history --alarm-name <name> --history-item-type StateUpdate
```

---

## Native CloudWatch agentic AIOps (2025–2026)

CloudWatch now ships built-in agentic RCA. Reach for these **before** standing up a
standalone investigation — they live inside the console you already use and tie
remediation back to your existing SSM runbooks. (Verified 2026-06 against AWS
official sources; AWS markets the bundle under **"AIOps"**.)

| Feature | Status | What it does | How to invoke |
|---------|--------|--------------|---------------|
| **CloudWatch investigations** | **GA 2025-06-24** (was *Amazon Q Developer operational investigations* preview) | AI agent finds anomalies, surfaces related signals, generates root-cause hypotheses, suggests remediation (incl. **SSM Automation runbooks**) | `Investigate` action on any metric widget · as a **CloudWatch alarm action** · from 80+ AWS consoles · Amazon Q chat · Slack / MS Teams |
| **Five Whys incident reports** | Launched **2025-11-30**, 12 regions, **no additional cost** | Guided, chat-based "5 Whys" RCA powered by **Amazon Q**, blending human input + AI analysis; recommends preventive measures | Create an investigation → **Incident report** → *Guide Me* under Five Why's. Needs Amazon Q perms (`AIOpsConsoleAdminPolicy`) |
| **Generative AI observability** | **GA 2025-10-13**, 9 regions, std CloudWatch pricing | Monitors your **AI agents/workloads** — incl. agents operated with **Bedrock AgentCore** — via a dedicated `AgentCore` console section (latency, tokens, errors); supports Strands, LangChain, LangGraph | CloudWatch console → **AgentCore** section; emit OTel/GenAI telemetry from the agent |

```bash
# Wire an alarm to auto-launch an investigation (alarm action = investigation group ARN)
aws cloudwatch put-metric-alarm --alarm-name "$CLUSTER_NAME-high-cpu" \
  --alarm-actions "arn:aws:aiops:<region>:<acct>:investigation-group/<id>" \
  --metric-name ... # (plus the usual metric/threshold flags)
```

> **Positioning vs AWS DevOps Agent**: CloudWatch *investigations* are the native,
> first-line agentic RCA **inside CloudWatch** (anomaly → hypotheses → SSM runbook).
> **AWS DevOps Agent** (`references/aws-devops-agent.md`) is the standalone,
> always-on autonomous SRE teammate for **multi-resource / cross-signal** incidents
> that span beyond CloudWatch. Escalate to DevOps Agent when an investigation's
> scope crosses services, repos, or clouds.
>
> Vendor-reported metrics (MTTR reduction, RCA accuracy) are AWS/preview-customer
> self-reported — cite as claims, not guarantees. Re-check region availability at use
> time; this surface is iterating fast.

Sources: AWS What's New (CloudWatch investigations GA 2025-06, Five Whys 2025-11,
GenAI observability GA 2025-10), CloudWatch User Guide (`Investigations.html`,
`incident-report-5whys.html`, `GenAI-observability.html`).
