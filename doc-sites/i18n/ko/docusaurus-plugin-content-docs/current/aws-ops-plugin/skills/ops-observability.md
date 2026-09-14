---
sidebar_position: 4
title: "관측성 워크플로"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="ops-observability" />
<span id="description" />
<span id="trigger-keywords" />
<span id="step-1-current-state-assessment" />
<span id="step-2-setupfix" />
<span id="step-3-query-and-alarm-creation" />
<span id="quick-reference" />
<span id="enable-container-insights" />
<span id="open-source-observability-stack" />
<span id="version-coupling-clickhouse-backed-stacks" />
<span id="aws-devops-agent-incident-escalation" />
<span id="promql-alarm-rules-extended" />
<span id="alert-severity-levels" />
<span id="node-alerts" />
<span id="pod-alerts" />
<span id="deployment-alerts" />
<span id="vpc-cni-alerts" />
<span id="pvc-and-network-alerts" />
<span id="dashboard-configuration-guide" />
<span id="container-insights-collected-metrics" />
<span id="cluster-level" />
<span id="node-level" />
<span id="podcontainer-level" />
<span id="container-insights-setup" />
<span id="method-1-eks-add-on-recommended" />
<span id="eks-control-plane-logging" />
<span id="log-group-structure" />
<span id="essential-cloudwatch-alarms" />
<span id="cost-optimization-strategies" />
<span id="log-analysis-queries-extended" />
<span id="control-plane-queries" />
<span id="api-server-errors" />
<span id="audit-log---user-activity" />
<span id="audit-log---resource-changes" />
<span id="authentication-failures" />
<span id="scheduler-issues" />
<span id="application-log-queries" />
<span id="error-rate-by-namespace" />
<span id="pod-restart-detection" />
<span id="oomkilled-events" />
<span id="log-volume-by-time" />
<span id="top-error-messages" />
<span id="response-time-analysis-json-logs" />
<span id="infrastructure-queries" />
<span id="vpc-cni-errors" />
<span id="kubelet-issues" />
<span id="node-system-issues" />
<span id="cost-analysis-queries" />
<span id="log-volume-by-container" />
<span id="identify-noisy-containers" />
<span id="usage-examples" />
<span id="container-insights-setup-1" />
<span id="log-analysis" />
<span id="reference-files" />


# 관측성 워크플로

모니터링, 로그, 메트릭, 트레이스, 알람, 인시던트 신호를 설정하거나 분석합니다.

## 워크플로 {#workflow}

생성자, 수집기, 전송 경로, 저장소, 쿼리, 대시보드, 알림의 관계를 파악합니다. 실패한 구간, 권한, 설정, 보존 기간을 점검합니다. 대표 이벤트가 목적지에 도달하고 의도한 쿼리나 알림으로 이어지는지 검증합니다.

## 대상 범위 {#coverage}

CloudWatch와 Logs Insights, X-Ray/ADOT/OTel, Prometheus/AMP, Grafana/AMG, 자체 관리형 Loki·Tempo·ClickHouse·VictoriaMetrics, 관련 DevOps Agent 에스컬레이션을 다룹니다.

## 보고 및 경계 {#reporting-and-boundaries}

예제와 임계값은 워크로드에 맞아야 합니다. 텔레메트리 설정과 애플리케이션 버그 진단을 구분합니다. 대시보드 스크린샷을 종단 간 검증으로 간주하지 말고 근거와 공백을 기록합니다.

소스 스킬에는 명령별 실행 절차, 의사결정 트리, 예제, 참조 파일, 호스트·팀 연동이 포함되어 있습니다. 수행할 작업의 정확한 절차는 소스 스킬에서 확인합니다.

[기준 워크플로 및 실행 절차](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/skills/ops-observability/SKILL.md)
