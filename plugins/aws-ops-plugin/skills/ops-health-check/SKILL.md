---
name: ops-health-check
description: "Comprehensive AWS/EKS infrastructure health assessment"
triggers:
  - "health check"
  - "상태 점검"
  - "헬스체크"
  - "cluster health"
  - "인프라 점검"
---

# Ops Health Check Skill

Comprehensive infrastructure health assessment covering cluster, nodes, workloads, networking, storage, and security.

## Health Check Domains

### 1. Cluster Health
```bash
kubectl cluster-info
aws eks describe-cluster --name $CLUSTER_NAME --query 'cluster.{status:status,version:version,platformVersion:platformVersion}'
kubectl get componentstatuses 2>/dev/null
```

### 2. Node Health
```bash
kubectl get nodes -o wide
kubectl top nodes
kubectl get nodes -o json | jq '.items[] | {name:.metadata.name, ready:[.status.conditions[] | select(.type=="Ready") | .status][0], cpu:.status.allocatable.cpu, memory:.status.allocatable.memory}'
```

### 3. Workload Health
```bash
kubectl get pods -A --field-selector=status.phase!=Running,status.phase!=Succeeded | head -20
kubectl get deployments -A -o json | jq '.items[] | select(.status.unavailableReplicas > 0) | {name:.metadata.name, ns:.metadata.namespace, unavailable:.status.unavailableReplicas}'
kubectl get daemonsets -A -o json | jq '.items[] | select(.status.desiredNumberScheduled != .status.numberReady) | {name:.metadata.name, ns:.metadata.namespace, desired:.status.desiredNumberScheduled, ready:.status.numberReady}'
```

### 4. Network Health
```bash
kubectl get pods -n kube-system -l k8s-app=kube-dns -o wide
kubectl get pods -n kube-system -l k8s-app=aws-node -o wide
kubectl get svc -A --field-selector spec.type=LoadBalancer
```

### 5. Storage Health
```bash
kubectl get pvc -A --field-selector status.phase!=Bound
kubectl get pv --field-selector status.phase!=Bound,status.phase!=Released
kubectl get csidrivers
```

### 6. Security Health
```bash
kubectl get pods -A -o json | jq '[.items[] | select(.spec.containers[].securityContext.privileged==true) | {name:.metadata.name, ns:.metadata.namespace}]'
kubectl get networkpolicies -A
kubectl get podsecuritypolicies 2>/dev/null
```

## Output Format

```
# Infrastructure Health Report

## Summary
- Overall: HEALTHY / WARNING / CRITICAL
- Checked: [timestamp]
- Cluster: [name] (v[version])

## Results

| Domain | Status | Details |
|--------|--------|---------|
| Cluster | ✅/⚠️/❌ | [Summary] |
| Nodes (N/N ready) | ✅/⚠️/❌ | [Summary] |
| Workloads | ✅/⚠️/❌ | [N unhealthy pods] |
| Network | ✅/⚠️/❌ | [Summary] |
| Storage | ✅/⚠️/❌ | [N unbound PVCs] |
| Security | ✅/⚠️/❌ | [Summary] |

## Recommendations
1. [Action item]
2. [Action item]
```

## References

- `references/health-check-procedures.md` — Detailed procedures per domain
- `references/metrics-thresholds.md` — Warning/critical thresholds
