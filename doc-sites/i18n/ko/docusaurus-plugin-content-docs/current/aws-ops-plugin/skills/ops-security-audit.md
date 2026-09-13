---
sidebar_position: 5
title: "보안 감사"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
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


# 보안 감사

AWS/EKS 보안 통제와 근거를 평가합니다. 요청되고 설정된 경우 선택적 AWS Security Agent 워크플로도 포함합니다.

## 워크플로 {#workflow}

범위와 필수 통제를 정의하고 자격 증명과 접근, 파드 보안, 네트워크, 암호화, 비밀 정보, 감사 로깅, 런타임 보안 상태를 점검합니다. 발견 사항을 검증하고 확인된 위험의 우선순위를 정한 뒤 구체적인 수정과 검증 방법을 제안합니다.

## 대상 범위 {#coverage}

IRSA/Pod Identity 신뢰, RBAC와 액세스 항목, Pod Security Standards, SG·네트워크 정책·엔드포인트, KMS와 스토리지 보호, 비밀 정보 처리, 컨트롤 플레인·감사 로깅을 다룹니다.

## 보고 및 경계 {#reporting-and-boundaries}

[저장소의 AWS 보안 필수 규칙](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/CLAUDE.md#banned-patterns)과 소스 스킬의 [공통 AWS 보안 필수 규칙](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/skills/ops-security-audit/SKILL.md#global-aws-security-mandates)을 빠짐없이 적용합니다. 침투 테스트에는 적절하고 명시적인 범위와 승인이 필요합니다.

소스 스킬에는 명령별 실행 절차, 의사결정 트리, 예제, 참조 파일, 호스트·팀 연동이 포함되어 있습니다. 수행할 작업의 정확한 절차는 소스 스킬에서 확인합니다.

[기준 워크플로 및 실행 절차](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/skills/ops-security-audit/SKILL.md)
