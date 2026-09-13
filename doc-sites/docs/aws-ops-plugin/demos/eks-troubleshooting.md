---
sidebar_position: 1
title: "EKS troubleshooting example"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="eks-트러블슈팅-워크플로우" />
<span id="시나리오" />
<span id="워크플로우" />
<span id="step-1-문제-보고" />
<span id="step-2-5분-트리아지" />
<span id="step-3-근본원인-조사" />
<span id="step-4-진단-결과" />
<span id="step-5-해결책-제시" />
<span id="verification" />
<span id="prevention" />
<span id="핵심-포인트" />


# EKS troubleshooting example

A node becomes NotReady and workloads stop scheduling. This example demonstrates evidence collection and verification; it is not an instruction to change an arbitrary live cluster.

## Triage {#triage}

Confirm context, affected nodes/pods, timestamps, and recent changes. Read node conditions and events, then inspect kubelet, CNI, resource pressure, and scheduler messages for the affected component.

```bash
kubectl get nodes -o wide
kubectl get pods -A -o wide
kubectl get events -A --sort-by=.lastTimestamp
```

## Diagnose and resolve {#diagnose-and-resolve}

Compare the observed evidence with the EKS agent's node/pod decision tree. A network condition, disk pressure, failed image pull, or capacity shortage needs a different fix. Apply only the remedy supported by evidence and within the user's authorization.

## Verify and report {#verify-and-report}

Check node readiness, pod scheduling, workload health, and recurrence of the original event. Report cause, action, measured result, and prevention. Escalate correlated networking, identity, or storage symptoms to the relevant specialist.

[EKS agent](/docs/aws-ops-plugin/agents/eks-agent) · [Troubleshooting workflow](/docs/aws-ops-plugin/skills/ops-troubleshoot)
