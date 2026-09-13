---
sidebar_position: 4
title: "관측성 에이전트"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="핵심-기능" />
<span id="진단-명령어" />
<span id="container-insights-상태" />
<span id="주요-logs-insights-쿼리" />
<span id="알람-관리" />
<span id="amazon-managed-prometheus-amp" />
<span id="amazon-managed-grafana-amg" />
<span id="adot-collector" />
<span id="self-managed-prometheusgrafana" />
<span id="주요-메트릭-참조" />
<span id="의사결정-트리" />
<span id="mcp-서버-연동" />
<span id="사용-예시" />
<span id="container-insights-설정" />
<span id="로그-분석-쿼리" />
<span id="출력-형식" />
<span id="dashboard-recommendations" />


# 관측성 에이전트

CloudWatch/Container Insights, Logs Insights, 알람, AMP, AMG, ADOT, 자체 관리형 Prometheus/Grafana를 다룹니다.

## 진단 방법 {#diagnostic-approach}

애플리케이션·수집기에서 자격 증명과 네트워크 송신 경로를 거쳐 목적지에 도달하는 텔레메트리를 추적합니다. 스크레이프 대상, exporter 오류, 레이블, 보존 기간, 알림 임계값, 대시보드 쿼리를 점검합니다. 새 스택을 제안하기 전에 데이터 누락 원인을 진단합니다.

## 초기 읽기 전용 점검 {#initial-read-only-checks}

대상 계정, 리전, Kubernetes 컨텍스트에서만 실행합니다. 관찰한 결과에 따라 서비스별 후속 점검을 진행합니다.

```bash
kubectl get pods -n amazon-cloudwatch -o wide
kubectl get pods -A -l app.kubernetes.io/name=opentelemetry-collector
aws cloudwatch describe-alarms --state-value ALARM
```

## 근거와 인계 {#evidence-and-handoff}

영향받는 구성 요소, 관찰한 증상, 근거 출력, 추정 원인, 제안 조치, 검증 명령과 예상 결과를 제시합니다. 팀 모드에서는 배정된 영역만 보고하고 조정자가 확인할 의존 관계를 명시합니다.

이 플러그인에는 `awsdocs`와 `awsapi`가 포함됩니다. 추가 지식/IaC 연동은 호스트에서 선택적으로 제공하는 기능입니다. 모델과 도구는 공개 사이트의 별도 설정 표가 아니라 실제 에이전트 frontmatter와 Codex 오버레이에 정의됩니다.

[에이전트 명령어와 의사결정 트리](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/agents/observability-agent.md)
