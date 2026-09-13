---
sidebar_position: 5
title: "Storage agent"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="핵심-기능" />
<span id="진단-명령어" />
<span id="pvcpv-상태" />
<span id="ebs-트러블슈팅" />
<span id="efs-트러블슈팅" />
<span id="의사결정-트리" />
<span id="일반적인-오류와-해결책" />
<span id="mcp-서버-연동" />
<span id="사용-예시" />
<span id="pvc-pending-문제-해결" />
<span id="efs-마운트-실패-진단" />
<span id="출력-형식" />


# Storage agent

EBS/EFS, CSI drivers, persistent volumes/claims, StorageClasses, access modes, topology, attachment failures, throughput, and lifecycle.

## Diagnostic approach {#diagnostic-approach}

For Pending PVCs compare class/provisioner, capacity, binding mode, and node AZ. For mount errors inspect CSI controller/node logs, IAM, endpoints, and filesystem permissions. Confirm snapshots and recovery implications before destructive changes.

## Initial read-only checks {#initial-read-only-checks}

Run only in the intended account, region, and Kubernetes context. Service-specific follow-ups come from the observed result.

```bash
kubectl get storageclasses
kubectl get pv
kubectl get pvc -A
kubectl get volumeattachments
```

## Evidence and handoff {#evidence-and-handoff}

Return the affected component, observed symptoms, supporting output, likely cause, proposed action, and a verification command with expected results. In team mode, report only the assigned domain and identify dependencies for the coordinator.

The plugin bundles `awsdocs` and `awsapi`; additional knowledge/IaC integrations are optional host capabilities. Models and tools are defined in the actual agent frontmatter and Codex overlay, not by a second public-site settings table.

[Agent commands and decision tree](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/agents/storage-agent.md)
