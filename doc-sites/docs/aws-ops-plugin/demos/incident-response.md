---
sidebar_position: 2
title: "Incident response example"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="인시던트-대응-예시" />
<span id="시나리오" />
<span id="인시던트-타임라인" />
<span id="step-1-인시던트-보고" />
<span id="step-2-5분-트리아지" />
<span id="트리아지-결과" />
<span id="step-3-팀-생성-및-병렬-조사" />
<span id="eks-agent-조사-결과" />
<span id="network-agent-조사-결과" />
<span id="database-agent-조사-결과" />
<span id="step-4-결과-집계-및-근본원인-분석" />
<span id="step-5-수정-및-검증" />
<span id="검증" />
<span id="결과" />
<span id="incident-postmortem" />
<span id="summary" />
<span id="timeline" />
<span id="root-cause" />
<span id="resolution" />
<span id="prevention" />


# Incident response example

A service outage spans unhealthy load-balancer targets and failing application pods. The coordinator gathers a shared timeline and assigns independent network and workload investigations.

## Five-minute triage

Record affected users/services, start time, severity, recent deployments, and the selected account/cluster. Collect node/pod status, events, target health, and relevant telemetry. Preserve the difference between observations and hypotheses.

## Parallel investigation

The network specialist traces target selection, ports, readiness, routes, and allowed traffic. The EKS specialist checks restarts, previous logs, configuration, scheduling, and resources. Add identity, storage, database, or observability specialists only when the evidence calls for them and host tools support the workflow.

## Correlation and mitigation

Identify which finding explains the other, or treat uncorrelated failures separately. Choose the smallest authorized mitigation, document its recovery implications, and verify the original user-visible path. Recheck workload health and alarms instead of declaring recovery from one green pod.

## Postmortem

Record impact, timeline, confirmed cause, actions, verification, and prevention with owners. Keep secrets, raw credentials, and unnecessary personal data out of the report.

[Coordinator](/docs/aws-ops-plugin/agents/ops-coordinator-agent) · [Troubleshooting workflow](/docs/aws-ops-plugin/skills/ops-troubleshoot)
