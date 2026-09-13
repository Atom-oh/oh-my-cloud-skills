---
sidebar_position: 1
title: "EKS 에이전트"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="핵심-기능" />
<span id="진단-명령어" />
<span id="클러스터-상태" />
<span id="노드-트러블슈팅" />
<span id="파드-트러블슈팅" />
<span id="애드온-관리" />
<span id="의사결정-트리" />
<span id="일반적인-오류와-해결책" />
<span id="mcp-서버-연동" />
<span id="사용-예시" />
<span id="노드-notready-트러블슈팅" />
<span id="파드-crashloop-분석" />
<span id="출력-형식" />
<span id="prevention" />


# EKS 에이전트

클러스터와 노드 상태, 추가 기능 수명 주기, 업그레이드, 파드 스케줄링, CrashLoopBackOff, ImagePullBackOff, 축출, 리소스 부족을 다룹니다.

## 진단 방법 {#diagnostic-approach}

노드 장애에서는 상태 조건, kubelet, 네트워크, 디스크를 점검합니다. Pending 파드는 스케줄러 이벤트, 선택기, taint, 용량, 볼륨을 확인합니다. 반복 비정상 종료에서는 이전 로그, 리소스 한도, 설정을 확인합니다. 업그레이드 전에 대상 버전, 추가 기능, 지원 중단 예정 API를 점검합니다.

## 초기 읽기 전용 점검 {#initial-read-only-checks}

대상 계정, 리전, Kubernetes 컨텍스트에서만 실행합니다. 관찰한 결과에 따라 서비스별 후속 점검을 진행합니다.

```bash
kubectl cluster-info
kubectl get nodes -o wide
kubectl get pods -A -o wide
kubectl get events -A --sort-by=.lastTimestamp
```

## 근거와 인계 {#evidence-and-handoff}

영향받는 구성 요소, 관찰한 증상, 근거 출력, 추정 원인, 제안 조치, 검증 명령과 예상 결과를 제시합니다. 팀 모드에서는 배정된 영역만 보고하고 조정자가 확인할 의존 관계를 명시합니다.

이 플러그인에는 `awsdocs`와 `awsapi`가 포함됩니다. 추가 지식/IaC 연동은 호스트에서 선택적으로 제공하는 기능입니다. 모델과 도구는 공개 사이트의 별도 설정 표가 아니라 실제 에이전트 frontmatter와 Codex 오버레이에 정의됩니다.

[에이전트 명령어와 의사결정 트리](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/agents/eks-agent.md)
