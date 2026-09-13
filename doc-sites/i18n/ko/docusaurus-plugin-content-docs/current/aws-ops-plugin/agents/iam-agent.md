---
sidebar_position: 3
title: "IAM 에이전트"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="핵심-기능" />
<span id="진단-명령어" />
<span id="irsa" />
<span id="pod-identity" />
<span id="rbac" />
<span id="aws-auth-configmap" />
<span id="의사결정-트리" />
<span id="일반적인-오류와-해결책" />
<span id="mcp-서버-연동" />
<span id="사용-예시" />
<span id="irsa-accessdenied-문제-해결" />
<span id="rbac-forbidden-진단" />
<span id="출력-형식" />
<span id="least-privilege-review" />


# IAM 에이전트

IRSA, EKS Pod Identity, IAM 신뢰와 권한, Kubernetes RBAC, EKS 액세스 항목, 기존 aws-auth 매핑을 다룹니다.

## 진단 방법 {#diagnostic-approach}

호출자와 실패한 작업을 식별합니다. 서비스 계정과 자격 증명 연결, 신뢰 조건, 정책 범위, 엔드포인트 접근, RBAC 바인딩을 확인합니다. 권한을 변경하기 전에 IAM 거부와 Kubernetes Forbidden을 구분합니다.

## 초기 읽기 전용 점검 {#initial-read-only-checks}

대상 계정, 리전, Kubernetes 컨텍스트에서만 실행합니다. 관찰한 결과에 따라 서비스별 후속 점검을 진행합니다.

```bash
aws sts get-caller-identity
kubectl get serviceaccounts -A
kubectl get clusterrolebindings
kubectl get configmap aws-auth -n kube-system -o yaml
```

## 근거와 인계 {#evidence-and-handoff}

영향받는 구성 요소, 관찰한 증상, 근거 출력, 추정 원인, 제안 조치, 검증 명령과 예상 결과를 제시합니다. 팀 모드에서는 배정된 영역만 보고하고 조정자가 확인할 의존 관계를 명시합니다.

이 플러그인에는 `awsdocs`와 `awsapi`가 포함됩니다. 추가 지식/IaC 연동은 호스트에서 선택적으로 제공하는 기능입니다. 모델과 도구는 공개 사이트의 별도 설정 표가 아니라 실제 에이전트 frontmatter와 Codex 오버레이에 정의됩니다.

[에이전트 명령어와 의사결정 트리](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/agents/iam-agent.md)
