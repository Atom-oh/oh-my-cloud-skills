---
sidebar_position: 7
title: "Cost agent"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="핵심-기능" />
<span id="분석-명령어" />
<span id="비용-개요" />
<span id="eks-리소스-사용량" />
<span id="절감-기회" />
<span id="최적화-전략" />
<span id="의사결정-트리" />
<span id="mcp-서버-연동" />
<span id="사용-예시" />
<span id="월간-비용-분석" />
<span id="eks-비용-최적화" />
<span id="출력-형식" />


# Cost agent

Service-level spending, EKS allocation, idle resources, utilization, storage lifecycle, and commitment/right-sizing opportunities.

## Diagnostic approach

Start with a stated account/time range and cost basis. Compare usage and capacity, distinguish recurring savings from one-time changes, and quantify assumptions. A recommendation must consider performance, availability, and existing commitments.

## Initial read-only checks

Run only in the intended account, region, and Kubernetes context. Service-specific follow-ups come from the observed result.

```bash
kubectl top nodes
kubectl top pods -A
kubectl get deployments -A
```

## Evidence and handoff

Return the affected component, observed symptoms, supporting output, likely cause, proposed action, and a verification command with expected results. In team mode, report only the assigned domain and identify dependencies for the coordinator.

The plugin bundles `awsdocs` and `awsapi`; additional knowledge/IaC integrations are optional host capabilities. Models and tools are defined in the actual agent frontmatter and Codex overlay, not by a second public-site settings table.

[Agent commands and decision tree](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/agents/cost-agent.md)
