# Metrics Thresholds

Warning and critical thresholds for infrastructure health assessment.

---

## Cluster Level

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| `cluster_cpu_utilization` | > 70% | > 85% | Scale out nodes |
| `cluster_memory_utilization` | > 75% | > 90% | Scale out nodes |
| `cluster_failed_node_count` | > 0 | >= 2 | Investigate node issues |
| EKS version age | > 6 months | > 12 months | Plan upgrade |
| Add-on version lag | > 1 minor | > 2 minor | Update add-ons |

## Node Level

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| `node_cpu_utilization` | > 80% | > 95% | Scale or optimize |
| `node_memory_utilization` | > 80% | > 95% | Scale or optimize |
| `node_filesystem_utilization` | > 80% | > 90% | Expand disk, clean images |
| Node age | > 30 days | > 90 days | Rotate nodes |
| kubelet restarts | > 2/day | > 5/day | Investigate kubelet |

## Pod Level

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| `pod_cpu_utilization` | > 80% of limit | > 95% of limit | Increase limit or optimize |
| `pod_memory_utilization` | > 85% of limit | > 95% of limit | Increase limit or optimize |
| Restart count | > 3/hour | > 10/hour | Investigate crashes |
| Container age (restartless) | < 1 hour | < 10 min | CrashLoop investigation |

## Network Level

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Subnet IP availability | < 30% | < 10% | Add CIDR, prefix delegation |
| CoreDNS CPU | > 70% | > 90% | Scale CoreDNS |
| DNS latency p99 | > 100ms | > 500ms | Optimize CoreDNS, ndots |
| LB target unhealthy | > 0 | > 50% | Investigate targets |

## Storage Level

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| PVC utilization | > 80% | > 90% | Expand volume |
| Unbound PVCs | > 0 | > 3 | Fix binding |
| EBS burst balance | < 30% | < 10% | Upgrade to gp3 or io2 |
| EFS burst credits | < 30% | < 10% | Switch to provisioned throughput |

## Security Level

| Check | Warning | Critical | Action |
|-------|---------|----------|--------|
| Privileged containers | > 0 (non-system) | Any in workloads | Remove privileged flag |
| Containers as root | > 0 (non-system) | Any in workloads | Set runAsNonRoot |
| No network policies | Some namespaces | All namespaces | Create network policies |
| Secrets not rotated | > 90 days | > 180 days | Rotate secrets |
