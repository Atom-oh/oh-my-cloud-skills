# Troubleshooting Framework

Systematic approach to AWS/EKS troubleshooting.

---

## Approach

1. **Identify** — What is the symptom? When did it start? What changed?
2. **Collect** — Gather logs, events, metrics, resource status
3. **Analyze** — Correlate findings, identify root cause
4. **Resolve** — Apply fix, verify
5. **Document** — Record for future reference

---

## Essential Diagnostic Commands

### Cluster Level
```bash
kubectl cluster-info
kubectl get nodes -o wide
kubectl get componentstatuses
kubectl get events -A --sort-by='.lastTimestamp' | tail -50
kubectl get pods -A --field-selector=status.phase!=Running
```

### Node Level
```bash
kubectl describe node <node> | grep -A 20 "Conditions:"
kubectl get nodes -o json | jq '.items[] | {name:.metadata.name, conditions:[.status.conditions[] | select(.status!="False") | .type]}'
journalctl -u kubelet -n 100 --no-pager
```

### Pod Level
```bash
kubectl describe pod <pod> -n <namespace>
kubectl logs <pod> -n <namespace> --previous
kubectl get events -n <namespace> --field-selector involvedObject.name=<pod>
```

### AWS Level
```bash
aws eks describe-cluster --name $CLUSTER_NAME
aws ec2 describe-instance-status --filters Name=instance-state-name,Values=running
aws cloudwatch get-metric-statistics --namespace ContainerInsights --metric-name cluster_failed_node_count --dimensions Name=ClusterName,Value=$CLUSTER_NAME --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) --period 300 --statistics Maximum
```

---

## Log Collection

### EKS Control Plane Logs
```bash
# Enable logging
aws eks update-cluster-config --name $CLUSTER_NAME --logging '{"clusterLogging":[{"types":["api","audit","authenticator","controllerManager","scheduler"],"enabled":true}]}'

# Query via Logs Insights
aws logs start-query --log-group-name /aws/eks/$CLUSTER_NAME/cluster --start-time $(date -d '1 hour ago' +%s) --end-time $(date +%s) --query-string 'fields @timestamp, @message | filter @message like /error/i | sort @timestamp desc | limit 50'
```

### Node Logs
```bash
# Via SSM Session Manager
aws ssm start-session --target <instance-id>
# Then: journalctl -u kubelet -n 200
```

### Pod Logs
```bash
kubectl logs <pod> -n <ns> --tail=100
kubectl logs <pod> -n <ns> -c <container> --previous
kubectl logs -l app=<label> -n <ns> --tail=50
```

---

## Diagnostic Information Collection Script

```bash
#!/bin/bash
# Quick diagnostic info collection
CLUSTER_NAME=${1:-$(kubectl config current-context | cut -d/ -f2)}
echo "=== Cluster: $CLUSTER_NAME ==="
echo "--- Nodes ---"
kubectl get nodes -o wide
echo "--- Failed Pods ---"
kubectl get pods -A --field-selector=status.phase!=Running,status.phase!=Succeeded
echo "--- Recent Events ---"
kubectl get events -A --sort-by='.lastTimestamp' | tail -30
echo "--- System Pods ---"
kubectl get pods -n kube-system
echo "--- Resource Usage ---"
kubectl top nodes 2>/dev/null || echo "Metrics server not available"
echo "--- EKS Status ---"
aws eks describe-cluster --name $CLUSTER_NAME --query 'cluster.{status:status,version:version}' 2>/dev/null
```
