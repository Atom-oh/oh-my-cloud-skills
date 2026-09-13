---
sidebar_position: 1
title: "EKS 문제 해결 예제"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
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


# EKS 문제 해결 예제

노드가 NotReady 상태가 되어 워크로드 스케줄링이 멈춘 상황입니다. 이 예제는 근거 수집과 검증 과정을 보여 주며, 임의의 실제 클러스터를 변경하라는 지침이 아닙니다.

## 초기 분류 {#triage}

컨텍스트, 영향받는 노드·파드, 시각, 최근 변경을 확인합니다. 노드 상태 조건과 이벤트를 읽은 뒤 해당 구성 요소의 kubelet, CNI, 리소스 부족, 스케줄러 메시지를 점검합니다.

```bash
kubectl get nodes -o wide
kubectl get pods -A -o wide
kubectl get events -A --sort-by=.lastTimestamp
```

## 진단 및 해결 {#diagnose-and-resolve}

관찰한 근거를 EKS 에이전트의 노드·파드 의사결정 트리와 비교합니다. 네트워크 상태, 디스크 부족, 이미지 가져오기 실패, 용량 부족은 각각 다른 조치가 필요합니다. 근거가 뒷받침하고 사용자가 승인한 범위에 있는 조치만 적용합니다.

## 검증 및 보고 {#verify-and-report}

노드 준비 상태, 파드 스케줄링, 워크로드 상태, 원래 이벤트의 재발 여부를 확인합니다. 원인, 조치, 측정 결과, 예방책을 보고합니다. 연관된 네트워크, 자격 증명, 스토리지 증상은 해당 전문가에게 넘깁니다.

[EKS 에이전트](/docs/aws-ops-plugin/agents/eks-agent) · [문제 해결 워크플로](/docs/aws-ops-plugin/skills/ops-troubleshoot)
