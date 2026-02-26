---
name: ops-network-diagnosis
description: "Deep network diagnosis for AWS/EKS: VPC CNI, load balancers, DNS"
triggers:
  - "network issue"
  - "네트워크 오류"
  - "연결 문제"
  - "connectivity"
  - "DNS failure"
---

# Ops Network Diagnosis Skill

Deep network diagnostics for VPC CNI, load balancers, and DNS in EKS environments.

## Diagnosis Workflow

### Step 1: Identify the Layer
- **L3 (IP)**: IP exhaustion, subnet, routing, VPC peering
- **L4 (Transport)**: Security groups, NACLs, port connectivity
- **L7 (Application)**: Load balancer, Ingress, target health
- **DNS**: CoreDNS, Route 53, external-dns

### Step 2: Layer-Specific Diagnostics
Route to appropriate reference for detailed commands and decision trees.

### Step 3: Verify Resolution
Test connectivity end-to-end after applying fixes.

## Quick Connectivity Tests

```bash
# Pod-to-pod
kubectl exec -it <pod1> -- curl -s <pod2-ip>:<port>

# Pod-to-service
kubectl exec -it <pod> -- curl -s <service>.<namespace>.svc.cluster.local:<port>

# DNS resolution
kubectl exec -it <pod> -- nslookup <service>.<namespace>.svc.cluster.local

# External connectivity
kubectl exec -it <pod> -- curl -s -o /dev/null -w "%{http_code}" https://aws.amazon.com
```

## References

- `references/vpc-cni-troubleshooting.md` — IP management, ENI, prefix delegation
- `references/load-balancer-troubleshooting.md` — ALB/NLB setup, target health
- `references/dns-troubleshooting.md` — CoreDNS, Route 53, resolution issues
