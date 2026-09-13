---
sidebar_position: 7
title: "비용 에이전트"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="핵심-기능" />
<span id="분석-명령어" />
<span id="비용-개요" />
<span id="eks-리소스-사용량" />
<span id="절감-기회" />
<span id="최적화-전략" />
<span id="의사결정-트리" />
<span id="mcp-서버-연동" />
<span id="사용-예시" />
<span id="월간-비용-분석" />
<span id="eks-비용-최적화" />
<span id="출력-형식" />


# 비용 에이전트

서비스별 지출, EKS 비용 배분, 유휴 리소스, 사용률, 스토리지 수명 주기, 약정 및 적정 규모 조정 기회를 다룹니다.

## 진단 방법 {#diagnostic-approach}

계정, 기간, 비용 산정 기준을 먼저 명시합니다. 사용량과 용량을 비교하고 지속적인 절감과 일회성 변화를 구분하며 가정을 수치화합니다. 권고안은 성능, 가용성, 기존 약정을 반드시 고려해야 합니다.

## 초기 읽기 전용 점검 {#initial-read-only-checks}

선택한 청구 기간과 계정에 대해 소스 절차의 [Cost Explorer 쿼리](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/agents/cost-agent.md#analysis-commands)를 사용합니다. EKS 워크로드에서는 대상 Kubernetes 클러스터에서 다음 읽기 전용 점검으로 사용률을 파악합니다:

```bash
kubectl top nodes
kubectl top pods -A
kubectl get deployments -A
```

## 근거와 인계 {#evidence-and-handoff}

청구 범위, 측정한 지출과 사용률, 권고안의 가정, 예상 절감액, 성능·복구 측면의 절충을 제시합니다. 계정별 근거와 요금 추정치를 구분합니다.

이 플러그인에는 `awsdocs`와 `awsapi`가 포함됩니다. 선택적 `awspricing` 연동은 외부 `deploy-on-aws` 플러그인을 설정한 경우 제공되며, 비용 절차는 이를 Cost Explorer 근거와 함께 사용합니다. 모델과 도구는 공개 사이트의 별도 설정 표가 아니라 실제 에이전트 frontmatter와 Codex 오버레이에 정의됩니다.

[에이전트 명령어와 의사결정 트리](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/agents/cost-agent.md)
