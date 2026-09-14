---
sidebar_position: 5
title: "Security audit"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="ops-security-audit" />
<span id="description" />
<span id="trigger-keywords" />
<span id="audit-domains" />
<span id="1-iam--authentication" />
<span id="2-network-security" />
<span id="3-compliance" />
<span id="4-application-security--aws-security-agent" />
<span id="scope-split" />
<span id="quick-audit-commands" />
<span id="cis-benchmark-checklist-detail" />
<span id="control-plane-aws-managed" />
<span id="worker-nodes" />
<span id="workload-security" />
<span id="network-security" />
<span id="iam-audit-detail" />
<span id="irsa-verification" />
<span id="check-all-service-account-annotations" />
<span id="verify-trust-policies" />
<span id="check-irsa-permissions" />
<span id="pod-identity-checks" />
<span id="rbac-analysis-commands" />
<span id="overly-permissive-roles" />
<span id="aws-auth-configmap-audit" />
<span id="access-entry-audit-eks-api" />
<span id="iam-security-best-practices-checklist" />
<span id="pod-security-standards-guide" />
<span id="comparison-table" />
<span id="enforcement-commands" />
<span id="recommended-pod-security-context" />
<span id="network-security-audit" />
<span id="security-group-audit" />
<span id="eks-cluster-security-groups" />
<span id="node-security-groups" />
<span id="security-group-red-flags" />
<span id="network-policy-audit" />
<span id="coverage-assessment" />
<span id="default-deny-policy-template" />
<span id="vpc-endpoint-audit" />
<span id="cluster-endpoint-access" />
<span id="aws-eks-security-best-practices" />
<span id="identity--access" />
<span id="network" />
<span id="data-protection" />
<span id="monitoring--audit" />
<span id="runtime-security" />
<span id="quick-compliance-check-script" />
<span id="team-mode" />
<span id="usage-examples" />
<span id="full-security-audit" />
<span id="specific-domain-audit" />
<span id="output-format" />
<span id="reference-files" />


# Security audit

Assess AWS/EKS security controls and evidence, including optional AWS Security Agent workflows when requested and configured.

## Workflow {#workflow}

Define scope and required controls; inspect identity and access, pod security, networking, encryption, secrets, audit logging, and runtime posture; validate findings; rank confirmed risk; propose specific fixes and verification.

## Coverage {#coverage}

IRSA/Pod Identity trust; RBAC and access entries; Pod Security Standards; SGs/network policies/endpoints; KMS and storage protection; secrets handling; control-plane/audit logging.

## Reporting and boundaries {#reporting-and-boundaries}

Apply the [repository's AWS security mandates](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/CLAUDE.md#banned-patterns) and the source skill's [Global AWS Security Mandates](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/skills/ops-security-audit/SKILL.md#global-aws-security-mandates) in full. Penetration testing requires the appropriate explicit scope and authorization.

The source skill contains the command playbooks, decision trees, examples, reference files, and host/team integration. Consult it for the exact operation being performed.

[Canonical workflow and playbooks](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/skills/ops-security-audit/SKILL.md)
