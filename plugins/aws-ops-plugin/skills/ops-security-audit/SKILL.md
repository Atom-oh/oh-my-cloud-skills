---
name: ops-security-audit
description: "AWS/EKS security audit: IAM, network security, compliance checks"
triggers:
  - "security audit"
  - "보안 점검"
  - "compliance"
  - "security review"
  - "보안 감사"
model: sonnet
allowed-tools:
  - Bash
  - Read
  - Grep
---

# Ops Security Audit Skill

Comprehensive security audit for AWS/EKS environments covering IAM, network, and compliance.

## Audit Domains

### 1. IAM & Authentication
- IRSA/Pod Identity configuration audit
- RBAC role and binding review
- aws-auth ConfigMap analysis
- Least privilege assessment

### 2. Network Security
- Security group rule review
- Network policy coverage
- VPC endpoint configuration
- Public endpoint exposure

### 3. Compliance
- CIS Kubernetes Benchmark checks
- AWS security best practices
- Pod security standards
- Secret management

## Quick Audit Commands

```bash
# Privileged containers
kubectl get pods -A -o json | jq '[.items[] | select(.spec.containers[].securityContext.privileged==true) | {name:.metadata.name,ns:.metadata.namespace}]'

# Pods running as root
kubectl get pods -A -o json | jq '[.items[] | select(.spec.securityContext.runAsUser==0 or .spec.containers[].securityContext.runAsUser==0) | {name:.metadata.name,ns:.metadata.namespace}]'

# Network policy coverage
kubectl get networkpolicies -A
kubectl get namespaces -o json | jq '.items[].metadata.name' | while read ns; do echo "$ns: $(kubectl get networkpolicies -n $(echo $ns | tr -d '"') 2>/dev/null | wc -l) policies"; done

# Public services
kubectl get svc -A -o json | jq '[.items[] | select(.spec.type=="LoadBalancer") | {name:.metadata.name,ns:.metadata.namespace,type:.spec.type}]'
```

## Output Format

```
# Security Audit Report

## Summary
- Audit Date: [timestamp]
- Cluster: [name]
- Overall Risk: LOW / MEDIUM / HIGH / CRITICAL

## Findings

| # | Severity | Domain | Finding | Recommendation |
|---|----------|--------|---------|----------------|
| 1 | CRITICAL | IAM | [Finding] | [Fix] |
| 2 | HIGH | Network | [Finding] | [Fix] |

## Compliance Checklist
- [ ] No privileged containers in workloads
- [ ] All pods run as non-root
- [ ] Network policies in all namespaces
- [ ] IRSA/Pod Identity for all AWS access
- [ ] Secrets encrypted with KMS
- [ ] Control plane audit logging enabled
- [ ] VPC endpoints for AWS services
- [ ] Cluster endpoint private access
```

## References

- `references/iam-audit.md` — IAM, IRSA, Pod Identity, RBAC audit
- `references/network-security.md` — Security groups, network policies, VPC endpoints
- `references/compliance-checklist.md` — CIS benchmark, best practices checklist
