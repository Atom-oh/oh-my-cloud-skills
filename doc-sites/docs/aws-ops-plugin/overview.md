---
sidebar_position: 1
title: "AWS operations plugin"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="aws-ops-plugin-개요" />
<span id="구성-요소" />
<span id="에이전트-목록" />
<span id="스킬-목록" />
<span id="인시던트-대응-워크플로우" />
<span id="단일-도메인-트러블슈팅-플로우" />
<span id="팀-워크플로우-트리거" />
<span id="자동-호출-키워드" />


# AWS operations plugin

Diagnose AWS and EKS incidents across compute, networking, identity, observability, storage, databases, analytics, and cost.

## Specialists {#specialists}

- [EKS agent](/docs/aws-ops-plugin/agents/eks-agent): Cluster and node health, add-on lifecycle, upgrades, pod scheduling, CrashLoopBackOff, ImagePullBackOff, eviction, and resource pressure.
- [Network agent](/docs/aws-ops-plugin/agents/network-agent): VPC CNI, ENI/IP capacity, pod connectivity, load balancers, DNS, routes, network policies, security groups, and VPC endpoints.
- [IAM agent](/docs/aws-ops-plugin/agents/iam-agent): IRSA, EKS Pod Identity, IAM trust and permissions, Kubernetes RBAC, EKS access entries, and legacy aws-auth mappings.
- [Observability agent](/docs/aws-ops-plugin/agents/observability-agent): CloudWatch/Container Insights, Logs Insights, alarms, AMP, AMG, ADOT, and self-managed Prometheus/Grafana.
- [Storage agent](/docs/aws-ops-plugin/agents/storage-agent): EBS/EFS, CSI drivers, persistent volumes/claims, StorageClasses, access modes, topology, attachment failures, throughput, and lifecycle.
- [Database agent](/docs/aws-ops-plugin/agents/database-agent): RDS/Aurora connectivity and performance, DynamoDB throttling/capacity, and ElastiCache connectivity, memory, and latency.
- [Analytics agent](/docs/aws-ops-plugin/agents/analytics-agent): OpenSearch and OpenSearch Serverless, ClickHouse, Athena, QuickSight, and Kinesis ingestion/query pipelines.
- [Cost agent](/docs/aws-ops-plugin/agents/cost-agent): Service-level spending, EKS allocation, idle resources, utilization, storage lifecycle, and commitment/right-sizing opportunities.
- [Ops coordinator agent](/docs/aws-ops-plugin/agents/ops-coordinator-agent): Incident severity, five-minute triage, domain routing, cross-domain evidence, mitigation, verification, and postmortems.
- [Well-Architected agent](/docs/aws-ops-plugin/agents/wellarchitected-agent): Review operational excellence, security, reliability, performance efficiency, cost optimization, and sustainability.

## Workflows {#workflows}

Use ops-troubleshoot for a concrete failure, ops-health-check for a general assessment, ops-network-diagnosis for connectivity, ops-observability for telemetry, ops-security-audit for security evidence, and ops-wellarchitected-review for a scored six-pillar review.

Start with scope and read-only evidence. Diagnose before changing resources, apply only authorized remediation, and verify against the original symptom. Single-domain work goes to a specialist; severe or multi-domain incidents can use the coordinator and parallel specialists where supported by the host.

The Claude manifest declares ten agents and six skills. Codex uses generated skill overlays and host-specific tools. The bundled MCP configuration is limited to the servers actually declared in the package.
