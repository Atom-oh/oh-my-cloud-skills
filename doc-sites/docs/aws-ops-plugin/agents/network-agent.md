---
sidebar_position: 2
title: "Network agent"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="핵심-기능" />
<span id="진단-명령어" />
<span id="vpc-cni" />
<span id="로드-밸런서" />
<span id="dns" />
<span id="security-groups" />
<span id="의사결정-트리" />
<span id="일반적인-오류와-해결책" />
<span id="mcp-서버-연동" />
<span id="사용-예시" />
<span id="ip-고갈-문제-해결" />
<span id="alb-타겟-unhealthy-진단" />
<span id="출력-형식" />


# Network agent

VPC CNI, ENI/IP capacity, pod connectivity, load balancers, DNS, routes, network policies, security groups, and VPC endpoints.

## Diagnostic approach {#diagnostic-approach}

Trace the actual source-to-destination path. For IP exhaustion compare subnet capacity, CNI settings, and node allocation; for unhealthy targets inspect target status, readiness, ports, and allowed traffic; for DNS inspect CoreDNS and resolver reachability.

## Initial read-only checks {#initial-read-only-checks}

Run only in the intended account, region, and Kubernetes context. Service-specific follow-ups come from the observed result.

```bash
kubectl get pods -n kube-system -o wide
kubectl get services,endpointslices -A
kubectl get networkpolicies -A
kubectl logs -n kube-system deployment/coredns --tail=100
```

## Evidence and handoff {#evidence-and-handoff}

Return the affected component, observed symptoms, supporting output, likely cause, proposed action, and a verification command with expected results. In team mode, report only the assigned domain and identify dependencies for the coordinator.

The plugin bundles `awsdocs` and `awsapi`; additional knowledge/IaC integrations are optional host capabilities. Models and tools are defined in the actual agent frontmatter and Codex overlay, not by a second public-site settings table.

[Agent commands and decision tree](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/agents/network-agent.md)
