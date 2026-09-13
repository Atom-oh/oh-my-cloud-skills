---
sidebar_position: 2
title: "네트워크 에이전트"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="핵심-기능" />
<span id="진단-명령어" />
<span id="vpc-cni" />
<span id="로드-밸런서" />
<span id="dns" />
<span id="security-groups" />
<span id="의사결정-트리" />
<span id="일반적인-오류와-해결책" />
<span id="mcp-서버-연동" />
<span id="사용-예시" />
<span id="ip-고갈-문제-해결" />
<span id="alb-타겟-unhealthy-진단" />
<span id="출력-형식" />


# 네트워크 에이전트

VPC CNI, ENI/IP 용량, 파드 연결, 로드 밸런서, DNS, 경로, 네트워크 정책, 보안 그룹, VPC 엔드포인트를 다룹니다.

## 진단 방법 {#diagnostic-approach}

실제 출발지에서 목적지까지의 경로를 추적합니다. IP 고갈에서는 서브넷 용량, CNI 설정, 노드 할당을 비교합니다. 비정상 대상은 상태, 준비 상태, 포트, 허용된 트래픽을 확인하고, DNS는 CoreDNS와 리졸버 도달 가능성을 점검합니다.

## 초기 읽기 전용 점검 {#initial-read-only-checks}

대상 계정, 리전, Kubernetes 컨텍스트에서만 실행합니다. 관찰한 결과에 따라 서비스별 후속 점검을 진행합니다.

```bash
kubectl get pods -n kube-system -o wide
kubectl get services,endpointslices -A
kubectl get networkpolicies -A
kubectl logs -n kube-system deployment/coredns --tail=100
```

## 근거와 인계 {#evidence-and-handoff}

영향받는 구성 요소, 관찰한 증상, 근거 출력, 추정 원인, 제안 조치, 검증 명령과 예상 결과를 제시합니다. 팀 모드에서는 배정된 영역만 보고하고 조정자가 확인할 의존 관계를 명시합니다.

이 플러그인에는 `awsdocs`와 `awsapi`가 포함됩니다. 추가 지식/IaC 연동은 호스트에서 선택적으로 제공하는 기능입니다. 모델과 도구는 공개 사이트의 별도 설정 표가 아니라 실제 에이전트 frontmatter와 Codex 오버레이에 정의됩니다.

[에이전트 명령어와 의사결정 트리](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/agents/network-agent.md)
