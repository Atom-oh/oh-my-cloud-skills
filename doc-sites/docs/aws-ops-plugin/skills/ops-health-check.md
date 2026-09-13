---
sidebar_position: 2
title: "Infrastructure health check"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="ops-health-check" />
<span id="description" />
<span id="trigger-keywords" />
<span id="health-check-domains" />
<span id="1-cluster-health" />
<span id="2-node-health" />
<span id="3-workload-health" />
<span id="4-network-health" />
<span id="5-storage-health" />
<span id="6-security-health" />
<span id="threshold-tables" />
<span id="cluster-level-thresholds" />
<span id="node-level-thresholds" />
<span id="pod-level-thresholds" />
<span id="network-level-thresholds" />
<span id="storage-level-thresholds" />
<span id="security-level-thresholds" />
<span id="domain-specific-detailed-procedures" />
<span id="1-cluster-health-check-procedures" />
<span id="eks-control-plane" />
<span id="2-node-health-check-procedures" />
<span id="3-workload-health-check-procedures" />
<span id="4-network-health-check-procedures" />
<span id="5-storage-health-check-procedures" />
<span id="6-security-health-check-procedures" />
<span id="usage-example" />
<span id="output-format" />
<span id="team-mode" />
<span id="reference-files" />


# Infrastructure health check

Use for an overall AWS/EKS assessment without a specific failure to diagnose.

## Workflow {#workflow}

Identify account, region, cluster, namespaces, and scope; inspect each layer; record OK/WARN/CRIT with evidence; prioritize follow-up; verify any authorized remediation.

## Coverage {#coverage}

Cluster API/control plane; nodes/capacity; workload readiness/restarts; network/DNS/load balancers; storage/PVCs; identity/security; observability and resource utilization.

## Reporting and boundaries {#reporting-and-boundaries}

A snapshot cannot prove future availability. Report skipped checks, permission gaps, and the time of assessment instead of marking unobserved areas healthy.

The source skill contains the command playbooks, decision trees, examples, reference files, and host/team integration. Consult it for the exact operation being performed.

[Canonical workflow and playbooks](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/skills/ops-health-check/SKILL.md)
