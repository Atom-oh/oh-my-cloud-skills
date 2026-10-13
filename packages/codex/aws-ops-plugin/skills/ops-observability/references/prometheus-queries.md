# Prometheus Queries

PromQL alert rules for EKS operational monitoring.

---

## Alert Severity Levels

| Severity | Response Time | Examples | Notification |
|----------|--------------|----------|-------------|
| **critical** | < 5 min | Node down, API unreachable | PagerDuty + Slack |
| **warning** | < 30 min | High CPU, memory pressure | Slack |
| **info** | Next business day | Scaling events | Email/Log |

---

## Node Alerts

```yaml
# Node Not Ready
- alert: NodeNotReady
  expr: kube_node_status_condition{condition="Ready",status="true"} == 0
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Node {{ $labels.node }} is NotReady"

# Node Memory Pressure
- alert: NodeHighMemoryUsage
  expr: (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) > 0.9
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Node {{ $labels.instance }} memory usage above 90%"

# Node Disk Pressure
- alert: NodeHighDiskUsage
  expr: (1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) > 0.85
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Node {{ $labels.instance }} disk usage above 85%"

# Node CPU High
- alert: NodeHighCPU
  expr: (1 - avg by(instance)(rate(node_cpu_seconds_total{mode="idle"}[5m]))) > 0.9
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Node {{ $labels.instance }} CPU above 90%"
```

## Pod Alerts

```yaml
# Pod CrashLoopBackOff
- alert: PodCrashLooping
  expr: rate(kube_pod_container_status_restarts_total[15m]) * 60 * 15 > 3
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Pod {{ $labels.namespace }}/{{ $labels.pod }} restarting frequently"

# Pod OOMKilled
- alert: PodOOMKilled
  expr: kube_pod_container_status_last_terminated_reason{reason="OOMKilled"} == 1
  for: 0m
  labels:
    severity: warning
  annotations:
    summary: "Pod {{ $labels.namespace }}/{{ $labels.pod }} was OOMKilled"

# Pod Pending Too Long
- alert: PodPendingTooLong
  expr: kube_pod_status_phase{phase="Pending"} == 1
  for: 15m
  labels:
    severity: warning
  annotations:
    summary: "Pod {{ $labels.namespace }}/{{ $labels.pod }} pending for 15+ minutes"

# Container CPU Throttling
- alert: ContainerCPUThrottling
  expr: rate(container_cpu_cfs_throttled_periods_total[5m]) / rate(container_cpu_cfs_periods_total[5m]) > 0.5
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Container {{ $labels.container }} in {{ $labels.pod }} is being throttled > 50%"
```

## Deployment Alerts

```yaml
# Deployment Replica Mismatch
- alert: DeploymentReplicaMismatch
  expr: kube_deployment_spec_replicas != kube_deployment_status_ready_replicas
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Deployment {{ $labels.namespace }}/{{ $labels.deployment }} has replica mismatch"

# StatefulSet Not Ready
- alert: StatefulSetNotReady
  expr: kube_statefulset_status_replicas_ready != kube_statefulset_status_replicas
  for: 15m
  labels:
    severity: warning
  annotations:
    summary: "StatefulSet {{ $labels.namespace }}/{{ $labels.statefulset }} not fully ready"

# DaemonSet Not Scheduled
- alert: DaemonSetNotScheduled
  expr: kube_daemonset_status_desired_number_scheduled - kube_daemonset_status_current_number_scheduled > 0
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "DaemonSet {{ $labels.namespace }}/{{ $labels.daemonset }} not fully scheduled"
```

## VPC CNI Alerts

```yaml
# High IP Utilization
- alert: HighIPUtilization
  expr: awscni_assigned_ip_addresses / awscni_total_ip_addresses > 0.9
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "VPC CNI IP utilization above 90% on {{ $labels.instance }}"

# ENI Allocation Failures
- alert: ENIAllocationFailure
  expr: increase(awscni_aws_api_error_count[5m]) > 0
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "VPC CNI API errors detected on {{ $labels.instance }}"
```

## Karpenter Alerts

```yaml
# Karpenter Provisioning Failures
- alert: KarpenterProvisioningFailed
  expr: increase(karpenter_provisioner_scheduling_duration_seconds_count{result="error"}[5m]) > 0
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Karpenter provisioning failures detected"

# Karpenter Node Not Ready
- alert: KarpenterNodeNotReady
  expr: karpenter_nodes_allocatable{} == 0
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Karpenter node {{ $labels.node }} has no allocatable resources"
```
