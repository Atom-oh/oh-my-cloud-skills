---
name: ops-security-audit
description: "AWS/EKS security audit: IAM, network security, compliance checks, plus AWS Security Agent (design/code review, on-demand penetration testing). The mandatory security leg of superpowers:requesting-code-review for IaC/AWS changes — enforces the repo's global AWS security mandates (no 0.0.0.0/0 ingress; no IAM Principal:\"*\" or Resource:\"*\" without Condition; no Lambda AuthType:NONE; no secrets in env; S3 Block Public Access on; no ALB bypassing CloudFront) — and a shift-left security pre-check during superpowers:writing-plans. Use when the user asks for a security audit, security review, code security review, compliance check, penetration testing/pentest, or mentions the AWS Security Agent — '보안 점검', '보안 감사', '취약점 점검', '시큐리티 에이전트'."
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

### 4. Application Security — AWS Security Agent
For application-layer security (beyond cluster/IAM posture), delegate to **AWS
Security Agent** (frontier agent): design review, full-repo/PR code security
review, and on-demand penetration testing validated with proof-based exploit
paths + fix PRs. This skill covers cloud/cluster posture; Security Agent covers
the app. See `references/aws-security-agent.md`.

> Scope split: **AWS Security Agent** = app design/code/pentest · **this skill** =
> EKS/IAM/network/CIS posture · **`co-agent` plugin** = per-diff adversarial review.

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
- `references/aws-security-agent.md` — AWS Security Agent: design/code review, on-demand penetration testing, org requirements, CI/CD API
