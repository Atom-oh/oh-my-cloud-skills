---
sidebar_position: 3
title: "IAM agent"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="핵심-기능" />
<span id="진단-명령어" />
<span id="irsa" />
<span id="pod-identity" />
<span id="rbac" />
<span id="aws-auth-configmap" />
<span id="의사결정-트리" />
<span id="일반적인-오류와-해결책" />
<span id="mcp-서버-연동" />
<span id="사용-예시" />
<span id="irsa-accessdenied-문제-해결" />
<span id="rbac-forbidden-진단" />
<span id="출력-형식" />
<span id="least-privilege-review" />


# IAM agent

IRSA, EKS Pod Identity, IAM trust and permissions, Kubernetes RBAC, EKS access entries, and legacy aws-auth mappings.

## Diagnostic approach

Identify the caller and failed action. Check the service account and its identity association, trust conditions, policy scope, endpoint access, and RBAC binding. Distinguish IAM denial from Kubernetes Forbidden before changing permissions.

## Initial read-only checks

Run only in the intended account, region, and Kubernetes context. Service-specific follow-ups come from the observed result.

```bash
aws sts get-caller-identity
kubectl get serviceaccounts -A
kubectl get clusterrolebindings
kubectl get configmap aws-auth -n kube-system -o yaml
```

## Evidence and handoff

Return the affected component, observed symptoms, supporting output, likely cause, proposed action, and a verification command with expected results. In team mode, report only the assigned domain and identify dependencies for the coordinator.

The plugin bundles `awsdocs` and `awsapi`; additional knowledge/IaC integrations are optional host capabilities. Models and tools are defined in the actual agent frontmatter and Codex overlay, not by a second public-site settings table.

[Agent commands and decision tree](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/agents/iam-agent.md)
