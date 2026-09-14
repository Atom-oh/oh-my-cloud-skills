---
sidebar_position: 5
title: 보안 감사 데모
---

# 보안 감사 데모

이 문서는 설명을 위한 예제입니다. 명령 출력, 식별자, 임계값, 발견 사항은 샘플 데이터이며 실제 평가 결과나 플러그인 기본값이 아닙니다. 실행 규칙은 현재 스킬을 따르고, 제안된 수정을 적용하기 전에 실제 환경을 확인합니다.

IAM, 네트워크, 규정 준수 감사 결과와 발견 사항 보고서를 다루는 보안 감사 예제입니다.

## 시나리오 {#scenario}

보안 검토 전에 EKS 클러스터를 종합 감사하여 취약점과 규정 준수의 공백을 파악합니다.

## 감사 워크플로 {#audit-workflow}

```mermaid
flowchart TD
    START[Security Audit Request] --> IAM[1. IAM & Authentication Audit]
    IAM --> NET[2. Network Security Audit]
    NET --> COMP[3. Compliance Audit]
    COMP --> REPORT[Generate Findings Report]
    REPORT --> REMEDIATION[Remediation Plan]
```

## 1단계: 보안 감사 시작 {#step-1-initiate-security-audit}

사용자 요청:

```
Please run a comprehensive security audit on the cluster.
```

**ops-security-audit** 스킬이 활성화되어 체계적인 보안 점검을 시작합니다.

---

## 1단계: IAM 및 인증 감사 {#phase-1-iam--authentication-audit}

### 1.1 IRSA 설정 점검 {#11-irsa-configuration-check}

```bash
# List all IRSA-annotated service accounts
kubectl get sa -A -o json | jq '.items[] | select(.metadata.annotations["eks.amazonaws.com/role-arn"] != null) | {namespace:.metadata.namespace, name:.metadata.name, role:.metadata.annotations["eks.amazonaws.com/role-arn"]}'
```

출력:
```json
{"namespace":"kube-system","name":"aws-load-balancer-controller","role":"arn:aws:iam::123456789012:role/eks-lb-controller-role"}
{"namespace":"kube-system","name":"ebs-csi-controller-sa","role":"arn:aws:iam::123456789012:role/eks-ebs-csi-role"}
{"namespace":"backend","name":"api-service-account","role":"arn:aws:iam::123456789012:role/api-backend-role"}
{"namespace":"analytics","name":"data-processor","role":"arn:aws:iam::123456789012:role/analytics-full-access"}
```

### 1.2 신뢰 정책 검증 {#12-verify-trust-policies}

```bash
# Check trust policy for suspicious role
aws iam get-role --role-name analytics-full-access --query 'Role.AssumeRolePolicyDocument'
```

출력:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::123456789012:oidc-provider/oidc.eks.us-west-2.amazonaws.com/id/ABC123"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringLike": {
                    "oidc.eks.us-west-2.amazonaws.com/id/ABC123:sub": "system:serviceaccount:*:*"
                }
            }
        }
    ]
}
```

**발견 사항 (CRITICAL)**: 신뢰 정책이 와일드카드 `*:*`를 사용하므로 모든 서비스 계정이 이 역할을 수임할 수 있습니다.

### 1.3 IAM 권한 점검 {#13-check-iam-permissions}

```bash
# Check for overly permissive policies
aws iam list-attached-role-policies --role-name analytics-full-access
```

출력:
```json
{
    "AttachedPolicies": [
        {"PolicyName": "AmazonS3FullAccess", "PolicyArn": "arn:aws:iam::aws:policy/AmazonS3FullAccess"},
        {"PolicyName": "AmazonDynamoDBFullAccess", "PolicyArn": "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"}
    ]
}
```

**발견 사항 (HIGH)**: 역할에 FullAccess 정책이 연결되어 최소 권한 원칙을 위반합니다.

### 1.4 RBAC 감사 {#14-rbac-audit}

```bash
# Find cluster-admin bindings
kubectl get clusterrolebindings -o json | jq '.items[] | select(.roleRef.name=="cluster-admin") | {name:.metadata.name, subjects:.subjects}'
```

출력:
```json
{
  "name": "cluster-admin-binding",
  "subjects": [
    {"kind": "User", "name": "admin@company.com"},
    {"kind": "User", "name": "developer@company.com"},
    {"kind": "Group", "name": "system:masters"}
  ]
}
{
  "name": "emergency-access",
  "subjects": [
    {"kind": "ServiceAccount", "name": "default", "namespace": "kube-system"}
  ]
}
```

**발견 사항 (HIGH)**: 개발자 사용자에게 cluster-admin 바인딩이 있고 기본 서비스 계정도 cluster-admin 권한을 가집니다.

### 1.5 aws-auth ConfigMap 점검 {#15-aws-auth-configmap-check}

```bash
kubectl get configmap aws-auth -n kube-system -o yaml
```

출력:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: aws-auth
  namespace: kube-system
data:
  mapRoles: |
    - rolearn: arn:aws:iam::123456789012:role/eks-node-role
      username: system:node:{{EC2PrivateDNSName}}
      groups:
        - system:bootstrappers
        - system:nodes
    - rolearn: arn:aws:iam::123456789012:role/admin-role
      username: admin
      groups:
        - system:masters
    - rolearn: arn:aws:iam::123456789012:role/developer-role
      username: developer
      groups:
        - system:masters
```

**발견 사항 (HIGH)**: 개발자 역할이 system:masters 그룹에 매핑되어 있습니다.

---

## 2단계: 네트워크 보안 감사 {#phase-2-network-security-audit}

### 2.1 보안 그룹 분석 {#21-security-group-analysis}

```bash
# Get cluster security group
CLUSTER_SG=$(aws eks describe-cluster --name prod-cluster --query 'cluster.resourcesVpcConfig.clusterSecurityGroupId' --output text)

# Check inbound rules
aws ec2 describe-security-group-rules --filter Name=group-id,Values=$CLUSTER_SG --query 'SecurityGroupRules[?!IsEgress].{FromPort:FromPort,ToPort:ToPort,Source:CidrIpv4}'
```

출력:
```json
[
    {"FromPort": 443, "ToPort": 443, "Source": "0.0.0.0/0"},
    {"FromPort": 22, "ToPort": 22, "Source": "0.0.0.0/0"}
]
```

**발견 사항 (CRITICAL)**: SSH(포트 22)가 0.0.0.0/0에 개방되어 있습니다.

### 2.2 네트워크 정책 적용 범위 {#22-network-policy-coverage}

```bash
# Check namespaces without network policies
for ns in $(kubectl get ns -o jsonpath='{.items[*].metadata.name}'); do
  policies=$(kubectl get networkpolicies -n $ns 2>/dev/null | tail -n +2 | wc -l)
  pods=$(kubectl get pods -n $ns 2>/dev/null | tail -n +2 | wc -l)
  if [ "$policies" -eq "0" ] && [ "$pods" -gt "0" ]; then
    echo "WARNING: $ns has $pods pods but no network policies"
  fi
done
```

출력:
```
WARNING: backend has 6 pods but no network policies
WARNING: analytics has 4 pods but no network policies
WARNING: monitoring has 8 pods but no network policies
WARNING: default has 2 pods but no network policies
```

**발견 사항 (MEDIUM)**: 워크로드가 있는 네임스페이스 4개에 네트워크 정책이 없습니다.

### 2.3 클러스터 엔드포인트 접근 {#23-cluster-endpoint-access}

```bash
aws eks describe-cluster --name prod-cluster --query 'cluster.resourcesVpcConfig.{publicAccess:endpointPublicAccess,privateAccess:endpointPrivateAccess,publicCIDRs:publicAccessCidrs}'
```

출력:
```json
{
    "publicAccess": true,
    "privateAccess": true,
    "publicCIDRs": ["0.0.0.0/0"]
}
```

**발견 사항 (HIGH)**: 클러스터 API 엔드포인트에 어디서나 공개적으로 접근할 수 있습니다.

### 2.4 VPC 엔드포인트 점검 {#24-vpc-endpoints-check}

```bash
# Check existing VPC endpoints
VPC_ID=$(aws eks describe-cluster --name prod-cluster --query 'cluster.resourcesVpcConfig.vpcId' --output text)
aws ec2 describe-vpc-endpoints --filters Name=vpc-id,Values=$VPC_ID --query 'VpcEndpoints[].ServiceName'
```

출력:
```json
[
    "com.amazonaws.us-west-2.s3",
    "com.amazonaws.us-west-2.ecr.api"
]
```

**발견 사항 (MEDIUM)**: 권장 VPC 엔드포인트(ecr.dkr, sts, logs, ec2)가 없습니다.

---

## 3단계: 규정 준수 감사 {#phase-3-compliance-audit}

### 3.1 특권 컨테이너 {#31-privileged-containers}

```bash
kubectl get pods -A -o json | jq '[.items[] | select(.spec.containers[].securityContext.privileged==true) | {name:.metadata.name, ns:.metadata.namespace}]'
```

출력:
```json
[
  {"name":"aws-node-abc","ns":"kube-system"},
  {"name":"aws-node-def","ns":"kube-system"},
  {"name":"debug-pod","ns":"default"},
  {"name":"data-processor-xyz","ns":"analytics"}
]
```

**발견 사항 (HIGH)**: 시스템용이 아닌 네임스페이스(default, analytics)에 특권 컨테이너 2개가 있습니다.

### 3.2 root 컨테이너 {#32-root-containers}

```bash
kubectl get pods -A -o json | jq '[.items[] | select(.spec.securityContext.runAsUser==0 or .spec.containers[].securityContext.runAsUser==0) | {name:.metadata.name, ns:.metadata.namespace}]'
```

출력:
```json
[
  {"name":"api-server-abc","ns":"backend"},
  {"name":"worker-def","ns":"backend"},
  {"name":"data-processor-xyz","ns":"analytics"},
  {"name":"web-app-ghi","ns":"frontend"}
]
```

**발견 사항 (MEDIUM)**: 파드 4개가 root 사용자로 실행됩니다.

### 3.3 Pod Security Standards {#33-pod-security-standards}

```bash
# Check namespace labels for Pod Security Standards
kubectl get ns -o json | jq '.items[] | select(.metadata.labels["pod-security.kubernetes.io/enforce"] != null) | {name:.metadata.name, enforce:.metadata.labels["pod-security.kubernetes.io/enforce"]}'
```

출력:
```json
```

**발견 사항 (MEDIUM)**: Pod Security Standards가 적용된 네임스페이스가 없습니다.

### 3.4 컨트롤 플레인 로깅 {#34-control-plane-logging}

```bash
aws eks describe-cluster --name prod-cluster --query 'cluster.logging.clusterLogging[?enabled==`true`].types[]'
```

출력:
```json
["api"]
```

**발견 사항 (MEDIUM)**: API 로깅만 활성화되어 있으며 audit 및 authenticator 로그가 없습니다.

### 3.5 Secret 암호화 {#35-secrets-encryption}

```bash
aws eks describe-cluster --name prod-cluster --query 'cluster.encryptionConfig'
```

출력:
```json
null
```

**발견 사항 (MEDIUM)**: EKS Secret 암호화가 활성화되어 있지 않습니다(Secret이 etcd에 암호화되지 않은 상태로 저장됩니다).

---

## 보안 감사 보고서 {#security-audit-report}

```markdown
# Security Audit Report

## Summary
- **Audit Date**: 2026-03-22 15:00:00 UTC
- **Cluster**: prod-cluster (us-west-2)
- **EKS Version**: 1.29
- **Overall Risk**: CRITICAL

## Executive Summary
The audit identified 15 security findings across IAM, Network, and Compliance domains.
2 Critical, 5 High, 6 Medium, 2 Low severity issues require remediation.

## Findings by Severity

### CRITICAL (2)

| # | Domain | Finding | Risk | Remediation |
|---|--------|---------|------|-------------|
| 1 | IAM | IRSA trust policy with wildcard (`*:*`) | Any pod can assume analytics-full-access role | Scope trust policy to specific namespace:serviceaccount |
| 2 | Network | SSH (22) open to 0.0.0.0/0 | Direct SSH access from internet | Remove rule, use SSM Session Manager |

### HIGH (5)

| # | Domain | Finding | Risk | Remediation |
|---|--------|---------|------|-------------|
| 3 | IAM | S3/DynamoDB FullAccess policies | Excessive permissions | Create scoped IAM policies |
| 4 | IAM | Developer has cluster-admin | Excessive cluster access | Create limited developer role |
| 5 | IAM | Default SA has cluster-admin | Privilege escalation risk | Remove emergency-access binding |
| 6 | IAM | Developer role in system:masters | Full cluster admin via aws-auth | Map to limited group |
| 7 | Network | API endpoint open to 0.0.0.0/0 | API accessible from internet | Restrict publicAccessCidrs |
| 8 | Compliance | Privileged containers in workloads | Container escape risk | Remove privileged flag |

### MEDIUM (6)

| # | Domain | Finding | Risk | Remediation |
|---|--------|---------|------|-------------|
| 9 | Network | 4 namespaces without NetworkPolicy | Unrestricted pod communication | Deploy default-deny policies |
| 10 | Network | Missing VPC endpoints | Traffic via internet | Add ecr.dkr, sts, logs endpoints |
| 11 | Compliance | 4 pods running as root | Container privilege abuse | Set runAsNonRoot: true |
| 12 | Compliance | No Pod Security Standards | No policy enforcement | Enable PSS restricted mode |
| 13 | Compliance | Incomplete control plane logging | Limited audit trail | Enable audit + authenticator logs |
| 14 | Compliance | Secrets not encrypted | Data at rest exposure | Enable KMS encryption |

### LOW (2)

| # | Domain | Finding | Risk | Remediation |
|---|--------|---------|------|-------------|
| 15 | Compliance | Debug pod in default namespace | Potential backdoor | Remove debug pod |
| 16 | Network | Unused security groups | Management overhead | Clean up stale SGs |

## Compliance Checklist

| Requirement | Status | Notes |
|-------------|--------|-------|
| No privileged containers in workloads | FAIL | 2 found in default, analytics |
| All pods run as non-root | FAIL | 4 pods running as root |
| Network policies in all namespaces | FAIL | 4 namespaces missing |
| IRSA/Pod Identity for AWS access | PARTIAL | IRSA used but misconfigured |
| Secrets encrypted with KMS | FAIL | Not enabled |
| Control plane audit logging | PARTIAL | Only api logs enabled |
| VPC endpoints for AWS services | PARTIAL | 2 of 6 recommended |
| Cluster endpoint private access | PASS | Private access enabled |
| Restricted public access CIDRs | FAIL | Open to 0.0.0.0/0 |

## Remediation Priority

### Immediate (24 hours)
1. Fix IRSA trust policy wildcard (Critical #1)
2. Remove SSH 0.0.0.0/0 rule (Critical #2)
3. Restrict API endpoint CIDRs (High #7)
4. Remove privileged flag from workload containers (High #8)

### This Week
5. Create scoped IAM policies (High #3)
6. Fix developer RBAC permissions (High #4, #6)
7. Remove default SA cluster-admin binding (High #5)
8. Deploy default-deny NetworkPolicies (Medium #9)

### This Month
9. Add missing VPC endpoints (Medium #10)
10. Implement Pod Security Standards (Medium #12)
11. Enable full control plane logging (Medium #13)
12. Enable secrets encryption (Medium #14)

### Ongoing
13. Enforce runAsNonRoot for all workloads (Medium #11)
14. Clean up debug resources (Low #15)
15. Security group hygiene (Low #16)
```

---

## 시정 조치 명령어 {#remediation-commands}

### Critical #1: IRSA 신뢰 정책 수정 {#critical-1-fix-irsa-trust-policy}

```bash
# Create scoped trust policy
cat > trust-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::123456789012:oidc-provider/oidc.eks.us-west-2.amazonaws.com/id/ABC123"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringEquals": {
                    "oidc.eks.us-west-2.amazonaws.com/id/ABC123:sub": "system:serviceaccount:analytics:data-processor"
                }
            }
        }
    ]
}
EOF

aws iam update-assume-role-policy --role-name analytics-full-access --policy-document file://trust-policy.json
```

### Critical #2: SSH 규칙 제거 {#critical-2-remove-ssh-rule}

```bash
# Remove SSH 0.0.0.0/0 rule
aws ec2 revoke-security-group-ingress --group-id $CLUSTER_SG --protocol tcp --port 22 --cidr 0.0.0.0/0
```

### High #7: API 엔드포인트 제한 {#high-7-restrict-api-endpoint}

```bash
# Restrict to corporate IPs only
aws eks update-cluster-config --name prod-cluster \
  --resources-vpc-config publicAccessCidrs="10.0.0.0/8","192.168.1.0/24"
```

---

## 핵심 사항 {#key-points}

:::danger Critical 발견 사항
IRSA 와일드카드 신뢰 정책과 인터넷에 개방된 SSH는 클러스터 침해로 이어질 수 있는 심각한 취약점입니다. 즉시 시정합니다.
:::

:::warning 최소 권한
여러 발견 사항이 과도한 권한(FullAccess 정책, system:masters 매핑)과 관련되어 있습니다. IAM과 RBAC 전반에 최소 권한을 적용합니다.
:::

:::tip 심층 방어
네트워크 분리를 위한 NetworkPolicies, 워크로드 보안 강화를 위한 Pod Security Standards, 데이터 보호를 위한 암호화 등 여러 보안 계층을 활성화합니다.
:::
