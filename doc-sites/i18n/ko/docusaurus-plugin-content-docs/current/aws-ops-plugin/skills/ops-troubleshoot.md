---
sidebar_position: 1
title: "AWS 및 EKS 문제 해결"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
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


# AWS 및 EKS 문제 해결

구체적인 인시던트, 오류 또는 클라우드의 비정상 동작을 해결할 때 사용합니다.

## 워크플로 {#workflow}

범위, 영향, 심각도, 최근 변경을 초기 분류합니다. 근거를 수집하고 가설을 세워 검증한 뒤 승인된 완화 조치를 적용합니다. 원래 작업을 다시 실행하고 원인, 복구, 예방책을 기록합니다.

## 대상 범위 {#coverage}

파드 스케줄링·비정상 종료·이미지·OOM 실패, 노드 상태 조건과 kubelet, API·추가 기능 오류, CNI·DNS·로드 밸런서 경로, PVC/CSI 토폴로지, IAM·RBAC 거부를 다룹니다.

## 보고 및 경계 {#reporting-and-boundaries}

P1/P2 인시던트 또는 여러 영역에 걸친 증상에는 조정자를 활용할 수 있습니다. 시각 정보와 연관성 근거를 보존합니다. 증상이 동시에 발생했다는 이유만으로 근본 원인이 하나라고 추정하지 않습니다.

소스 스킬에는 명령별 실행 절차, 의사결정 트리, 예제, 참조 파일, 호스트·팀 연동이 포함되어 있습니다. 수행할 작업의 정확한 절차는 소스 스킬에서 확인합니다.

[기준 워크플로 및 실행 절차](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/skills/ops-troubleshoot/SKILL.md)
