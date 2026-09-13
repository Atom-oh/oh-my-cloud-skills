---
sidebar_position: 1
title: "Troubleshoot AWS and EKS"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="ops-troubleshoot" />
<span id="description" />
<span id="trigger-keywords" />
<span id="workflow-overview" />
<span id="phase-1-triage-5-minutes" />
<span id="phase-2-investigation" />
<span id="phase-3-resolution" />
<span id="phase-4-postmortem" />
<span id="severity-classification" />
<span id="decision-trees-extended" />
<span id="pod-not-starting-decision-tree" />
<span id="node-not-ready-decision-tree" />
<span id="network-connectivity-decision-tree" />
<span id="storage-issue-decision-tree" />
<span id="error-to-solution-mapping-table" />
<span id="cluster-errors" />
<span id="node-errors" />
<span id="pod-errors" />
<span id="network-errors" />
<span id="storage-errors" />
<span id="iamauth-errors" />
<span id="real-world-scenarios" />
<span id="scenario-1-crashloopbackoff" />
<span id="scenario-2-imagepullbackoff" />
<span id="scenario-3-oomkilled-investigation" />
<span id="usage-example" />
<span id="reference-files" />


# Troubleshoot AWS and EKS

Use for a concrete incident, error, or broken cloud behavior.

## Workflow {#workflow}

Triage scope, impact, severity, and recent changes; collect evidence; form and test a hypothesis; apply authorized mitigation; reproduce the original operation; document cause, recovery, and prevention.

## Coverage {#coverage}

Pod scheduling/crash/image/OOM failures; node conditions and kubelet; API/add-on errors; CNI/DNS/load-balancer paths; PVC/CSI topology; IAM and RBAC denials.

## Reporting and boundaries {#reporting-and-boundaries}

P1/P2 incidents or symptoms spanning multiple domains can use the coordinator. Preserve timestamps and correlation evidence; do not infer one root cause merely because symptoms occurred together.

The source skill contains the command playbooks, decision trees, examples, reference files, and host/team integration. Consult it for the exact operation being performed.

[Canonical workflow and playbooks](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/skills/ops-troubleshoot/SKILL.md)
