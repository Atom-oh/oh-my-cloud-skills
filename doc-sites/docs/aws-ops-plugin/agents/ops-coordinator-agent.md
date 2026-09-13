---
sidebar_position: 8
title: "Ops coordinator agent"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="핵심-기능" />
<span id="심각도-매트릭스" />
<span id="5분-트리아지-체크리스트" />
<span id="의사결정-트리" />
<span id="팀-조율-패턴" />
<span id="sequential-mode-기본" />
<span id="parallel-team-mode-p1p2-또는-멀티-도메인" />
<span id="집계-의사결정" />
<span id="mcp-서버-연동" />
<span id="사용-예시" />
<span id="복합-인시던트-대응" />
<span id="전체-상태-점검" />
<span id="출력-형식" />


# Ops coordinator agent

Incident severity, five-minute triage, domain routing, cross-domain evidence, mitigation, verification, and postmortems.

## Diagnostic approach

Use a direct specialist for a single-domain symptom. P1/P2 or multi-domain incidents can use parallel specialists when host tools support them. Correlate evidence without forcing independent failures into one root cause. Report impact, chronology, fixes, checks, and prevention.

## Initial read-only checks

Run only in the intended account, region, and Kubernetes context. Service-specific follow-ups come from the observed result.

```bash
kubectl get nodes
kubectl get pods -A -o wide
kubectl get events -A --sort-by=.lastTimestamp
```

## Evidence and handoff

Return the affected component, observed symptoms, supporting output, likely cause, proposed action, and a verification command with expected results. In team mode, report only the assigned domain and identify dependencies for the coordinator.

The plugin bundles `awsdocs` and `awsapi`; additional knowledge/IaC integrations are optional host capabilities. Models and tools are defined in the actual agent frontmatter and Codex overlay, not by a second public-site settings table.

[Agent commands and decision tree](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/agents/ops-coordinator-agent.md)
