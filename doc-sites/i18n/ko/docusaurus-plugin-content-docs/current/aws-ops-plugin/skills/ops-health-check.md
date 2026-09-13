---
sidebar_position: 2
title: "인프라 상태 점검"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
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


# 인프라 상태 점검

진단할 특정 장애가 없는 상태에서 AWS/EKS 전반을 평가할 때 사용합니다.

## 워크플로 {#workflow}

계정, 리전, 클러스터, 네임스페이스, 범위를 확인하고 각 계층을 점검합니다. 근거와 함께 OK/WARN/CRIT를 기록하고 후속 조치의 우선순위를 정하며, 승인된 시정 조치를 검증합니다.

## 대상 범위 {#coverage}

클러스터 API·컨트롤 플레인, 노드·용량, 워크로드 준비 상태·재시작, 네트워크·DNS·로드 밸런서, 스토리지·PVC, 자격 증명·보안, 관측성과 리소스 사용률을 다룹니다.

## 보고 및 경계 {#reporting-and-boundaries}

시점별 점검 결과로 미래의 가용성을 입증할 수는 없습니다. 관찰하지 않은 영역을 정상으로 표시하지 말고, 건너뛴 점검, 부족한 권한, 평가 시각을 보고합니다.

소스 스킬에는 명령별 실행 절차, 의사결정 트리, 예제, 참조 파일, 호스트·팀 연동이 포함되어 있습니다. 수행할 작업의 정확한 절차는 소스 스킬에서 확인합니다.

[기준 워크플로 및 실행 절차](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/skills/ops-health-check/SKILL.md)
