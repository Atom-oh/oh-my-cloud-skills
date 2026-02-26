# Log Analysis Queries

CloudWatch Logs Insights query templates for EKS operations.

---

## Control Plane Queries

### API Server Errors
```sql
fields @timestamp, @message
| filter @logStream like /kube-apiserver/
| filter @message like /error|Error|ERROR/
| sort @timestamp desc
| limit 50
```

### Audit Log — User Activity
```sql
fields @timestamp, @message
| filter @logStream like /kube-apiserver-audit/
| parse @message '"user":{"username":"*"' as username
| filter username != "system:serviceaccount:*"
| stats count(*) as actions by username
| sort actions desc
```

### Audit Log — Resource Changes
```sql
fields @timestamp, @message
| filter @logStream like /kube-apiserver-audit/
| filter @message like /"verb":"create"/ or @message like /"verb":"delete"/ or @message like /"verb":"update"/
| filter @message like /"resource":"pods"/ or @message like /"resource":"deployments"/ or @message like /"resource":"services"/
| sort @timestamp desc
| limit 100
```

### Authentication Failures
```sql
fields @timestamp, @message
| filter @logStream like /authenticator/
| filter @message like /AccessDenied|Forbidden|unauthorized|error/
| sort @timestamp desc
| limit 50
```

### Scheduler Issues
```sql
fields @timestamp, @message
| filter @logStream like /kube-scheduler/
| filter @message like /error|failed|unable/i
| sort @timestamp desc
| limit 30
```

---

## Application Log Queries

### Error Rate by Namespace
```sql
fields @timestamp, @message, kubernetes.namespace_name
| filter @message like /error/i
| stats count(*) as error_count by kubernetes.namespace_name
| sort error_count desc
```

### Pod Restart Detection
```sql
fields @timestamp, @message, kubernetes.pod_name
| filter @message like /Back-off restarting failed container/
| stats count(*) as restart_count by kubernetes.pod_name
| sort restart_count desc
```

### OOMKilled Events
```sql
fields @timestamp, @message, kubernetes.pod_name, kubernetes.namespace_name
| filter @message like /OOMKilled|oom-kill|Out of memory/
| sort @timestamp desc
| limit 30
```

### Log Volume by Time
```sql
fields @timestamp
| stats count(*) as log_count by bin(1h)
| sort @timestamp
```

### Top Error Messages
```sql
fields @timestamp, @message
| filter @message like /error/i
| stats count(*) as count by @message
| sort count desc
| limit 10
```

### Response Time Analysis (JSON Logs)
```sql
fields @timestamp, @message
| filter kubernetes.container_name = "api"
| parse @message '{"response_time":*,' as response_time
| filter response_time > 1000
| stats avg(response_time) as avg_rt, max(response_time) as max_rt, percentile(response_time, 95) as p95_rt by bin(5m)
```

---

## Infrastructure Queries

### VPC CNI Errors
```sql
-- Log group: /aws/containerinsights/$CLUSTER_NAME/dataplane
fields @timestamp, @message
| filter kubernetes.container_name = "aws-node"
| filter @message like /error|failed|insufficient/i
| sort @timestamp desc
| limit 30
```

### kubelet Issues
```sql
-- Log group: /aws/containerinsights/$CLUSTER_NAME/dataplane
fields @timestamp, @message
| filter @message like /kubelet/
| filter @message like /error|failed|unable/i
| sort @timestamp desc
| limit 30
```

### Node System Issues
```sql
-- Log group: /aws/containerinsights/$CLUSTER_NAME/host
fields @timestamp, @message
| filter @message like /oom-kill|kernel|panic|error/i
| sort @timestamp desc
| limit 30
```

---

## Cost Analysis Queries

### Log Volume by Container
```sql
fields @timestamp, kubernetes.container_name, kubernetes.namespace_name
| stats count(*) as log_lines by kubernetes.container_name, kubernetes.namespace_name
| sort log_lines desc
| limit 20
```

### Identify Noisy Containers
```sql
fields @timestamp, kubernetes.container_name, kubernetes.namespace_name
| stats count(*) as log_count by kubernetes.container_name, kubernetes.namespace_name
| filter log_count > 10000
| sort log_count desc
```

---

## Multi-Cluster Query

```sql
-- Query across multiple log groups
SOURCE '/aws/containerinsights/cluster-a/application'
     | '/aws/containerinsights/cluster-b/application'
| fields @timestamp, @message, @logStream
| filter @message like /error/i
| sort @timestamp desc
| limit 100
```
