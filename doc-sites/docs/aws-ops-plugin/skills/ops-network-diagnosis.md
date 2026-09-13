---
sidebar_position: 3
title: "Network diagnosis"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="ops-network-diagnosis" />
<span id="description" />
<span id="trigger-keywords" />
<span id="diagnosis-workflow" />
<span id="step-1-layer-identification" />
<span id="step-2-layer-specific-diagnosis" />
<span id="step-3-resolution-verification" />
<span id="quick-connectivity-tests" />
<span id="vpc-cni-deep-guide" />
<span id="architecture-overview" />
<span id="ip-allocation-modes" />
<span id="instance-type-limits" />
<span id="key-environment-variables" />
<span id="vpc-cni-diagnostic-commands" />
<span id="ip-exhaustion-solutions" />
<span id="subnet-cidr-planning-best-practice" />
<span id="vpc-cni-error-solutions" />
<span id="load-balancer-troubleshooting" />
<span id="prerequisites-checklist" />
<span id="key-annotations-reference" />
<span id="alb-ingress" />
<span id="nlb-service" />
<span id="alb-not-created---debugging" />
<span id="targets-unhealthy---debugging" />
<span id="502-bad-gateway-resolution" />
<span id="subnet-tagging" />
<span id="cost-optimization---alb-sharing" />
<span id="dns-deep-diagnosis" />
<span id="coredns-architecture-in-eks" />
<span id="dns-diagnostic-commands" />
<span id="dns-resolution-timeout-solutions" />
<span id="coredns-scaling" />
<span id="coredns-configmap-customization" />
<span id="external-dns-not-resolving-from-pods" />
<span id="route-53-integration---external-dns" />
<span id="dns-error-solutions" />
<span id="layer-specific-diagnosis-guide" />
<span id="l3---iprouting" />
<span id="l4---security-groups" />
<span id="l7---load-balancer" />
<span id="usage-examples" />
<span id="ip-exhaustion-issue" />
<span id="alb-502-error" />
<span id="reference-files" />


# Network diagnosis

Trace AWS/EKS connectivity failures, unhealthy targets, DNS errors, and IP exhaustion.

## Workflow

Define source, destination, protocol, port, and expected path. Check endpoints and service selection; inspect CNI allocation, route tables, SG/NACL rules, network policies, load-balancer health, DNS, and private endpoints.

## Coverage

VPC CNI/IPAMD; ENI/subnet capacity; ALB/NLB target groups; CoreDNS and upstream resolution; pod-to-service and cross-VPC access; security group and route constraints.

## Reporting and boundaries

Use observed path evidence before remediation. Security-group changes follow the repository IaC policy; broad public ingress is not a diagnostic shortcut.

The source skill contains the command playbooks, decision trees, examples, reference files, and host/team integration. Consult it for the exact operation being performed.

[Canonical workflow and playbooks](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/skills/ops-network-diagnosis/SKILL.md)
