---
sidebar_position: 1
title: "EKS agent"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="핵심-기능" />
<span id="진단-명령어" />
<span id="클러스터-상태" />
<span id="노드-트러블슈팅" />
<span id="파드-트러블슈팅" />
<span id="애드온-관리" />
<span id="의사결정-트리" />
<span id="일반적인-오류와-해결책" />
<span id="mcp-서버-연동" />
<span id="사용-예시" />
<span id="노드-notready-트러블슈팅" />
<span id="파드-crashloop-분석" />
<span id="출력-형식" />
<span id="prevention" />


# EKS agent

Cluster and node health, add-on lifecycle, upgrades, pod scheduling, CrashLoopBackOff, ImagePullBackOff, eviction, and resource pressure.

## Diagnostic approach {#diagnostic-approach}

For node failures inspect conditions, kubelet, network, and disk. For Pending pods inspect scheduler events, selectors, taints, capacity, and volumes. For crash loops inspect previous logs, limits, and configuration. Before upgrades check the target version, add-ons, and deprecated APIs.

## Initial read-only checks {#initial-read-only-checks}

Run only in the intended account, region, and Kubernetes context. Service-specific follow-ups come from the observed result.

```bash
kubectl cluster-info
kubectl get nodes -o wide
kubectl get pods -A -o wide
kubectl get events -A --sort-by=.lastTimestamp
```

## Evidence and handoff {#evidence-and-handoff}

Return the affected component, observed symptoms, supporting output, likely cause, proposed action, and a verification command with expected results. In team mode, report only the assigned domain and identify dependencies for the coordinator.

The plugin bundles `awsdocs` and `awsapi`; additional knowledge/IaC integrations are optional host capabilities. Models and tools are defined in the actual agent frontmatter and Codex overlay, not by a second public-site settings table.

[Agent commands and decision tree](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/agents/eks-agent.md)
