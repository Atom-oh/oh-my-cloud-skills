# Compliance Checklist

CIS Kubernetes Benchmark and AWS security best practices for EKS.

---

## CIS Kubernetes Benchmark (EKS-relevant)

### Control Plane (AWS Managed)
AWS manages these for EKS — verify they're enabled:

| # | Check | Verification |
|---|-------|-------------|
| 1.1 | API server audit logging | `aws eks describe-cluster --query 'cluster.logging'` |
| 1.2 | RBAC enabled | Always enabled on EKS |
| 1.3 | Admission controllers | PodSecurity, ResourceQuota active |

### Worker Nodes

| # | Check | Command | Expected |
|---|-------|---------|----------|
| 4.1 | kubelet authentication | Check kubelet config | anonymous-auth=false |
| 4.2 | kubelet authorization | Check kubelet config | mode=Webhook |
| 4.3 | Protect kubelet certificates | `kubectl get nodes -o json \| jq '.items[].status.daemonEndpoints'` | Port 10250 only |

### Workload Security

| # | Check | Command | Expected |
|---|-------|---------|----------|
| 5.1 | No privileged containers | `kubectl get pods -A -o json \| jq '[.items[] \| select(.spec.containers[].securityContext.privileged==true)]'` | Empty (except system) |
| 5.2 | No root containers | Check securityContext | runAsNonRoot=true |
| 5.3 | No hostNetwork | Check pod spec | hostNetwork=false |
| 5.4 | No hostPID | Check pod spec | hostPID=false |
| 5.5 | No hostIPC | Check pod spec | hostIPC=false |
| 5.6 | Read-only root FS | Check securityContext | readOnlyRootFilesystem=true |
| 5.7 | Drop ALL capabilities | Check securityContext | capabilities.drop=["ALL"] |

### Network Security

| # | Check | Command | Expected |
|---|-------|---------|----------|
| 6.1 | Network policies | `kubectl get networkpolicies -A` | All namespaces covered |
| 6.2 | Private endpoint | Check cluster config | privateAccess=true |
| 6.3 | Restricted public access | Check publicAccessCidrs | Not 0.0.0.0/0 |

---

## AWS EKS Security Best Practices

### Identity & Access

- [ ] Use IRSA or Pod Identity (never node IAM role for workloads)
- [ ] Scope IRSA trust policies to specific namespace:serviceaccount
- [ ] Minimize cluster-admin ClusterRoleBindings
- [ ] Enable EKS access entries (migrate from aws-auth)
- [ ] Rotate IAM credentials regularly
- [ ] Enable MFA for human users

### Network

- [ ] Enable VPC endpoints for AWS services
- [ ] Use private cluster endpoint (or restrict public CIDRs)
- [ ] Deploy network policies in all namespaces
- [ ] Use Security Groups for Pods where needed
- [ ] Enable VPC Flow Logs for audit

### Data Protection

- [ ] Enable EKS secrets encryption with KMS
- [ ] Use encrypted EBS volumes (gp3 with KMS)
- [ ] Use IRSA for Secrets Manager/Parameter Store access
- [ ] Never store secrets in ConfigMaps
- [ ] Use external-secrets-operator for secret rotation

### Monitoring & Audit

- [ ] Enable control plane logging (api + audit + authenticator)
- [ ] Enable Container Insights
- [ ] Set up CloudTrail for AWS API auditing
- [ ] Create alarms for security events
- [ ] Enable GuardDuty EKS protection

### Runtime Security

- [ ] Use Bottlerocket or AL2023 (minimal OS)
- [ ] Enable Pod Security Standards (Restricted)
- [ ] Deploy admission webhooks (OPA/Kyverno)
- [ ] Scan container images (ECR scanning, Trivy)
- [ ] Use read-only root filesystems

---

## Quick Compliance Check Script

```bash
#!/bin/bash
echo "=== EKS Security Quick Check ==="
CLUSTER=$1

echo "--- Endpoint Access ---"
aws eks describe-cluster --name $CLUSTER --query 'cluster.resourcesVpcConfig.{public:endpointPublicAccess,private:endpointPrivateAccess,cidrs:publicAccessCidrs}'

echo "--- Logging ---"
aws eks describe-cluster --name $CLUSTER --query 'cluster.logging.clusterLogging[?enabled==`true`].types[]'

echo "--- Encryption ---"
aws eks describe-cluster --name $CLUSTER --query 'cluster.encryptionConfig'

echo "--- Privileged Containers ---"
kubectl get pods -A -o json | jq '[.items[] | select(.spec.containers[].securityContext.privileged==true) | {name:.metadata.name,ns:.metadata.namespace}] | length'

echo "--- Root Containers ---"
kubectl get pods -A -o json | jq '[.items[] | select(.spec.securityContext.runAsUser==0) | {name:.metadata.name,ns:.metadata.namespace}] | length'

echo "--- Network Policies ---"
kubectl get networkpolicies -A --no-headers | wc -l

echo "--- cluster-admin Bindings ---"
kubectl get clusterrolebindings -o json | jq '[.items[] | select(.roleRef.name=="cluster-admin") | .metadata.name]'
```
