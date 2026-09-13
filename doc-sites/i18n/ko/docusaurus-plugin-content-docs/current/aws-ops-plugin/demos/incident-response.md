---
sidebar_position: 2
title: "인시던트 대응 예제"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="인시던트-대응-예시" />
<span id="시나리오" />
<span id="인시던트-타임라인" />
<span id="step-1-인시던트-보고" />
<span id="step-2-5분-트리아지" />
<span id="트리아지-결과" />
<span id="step-3-팀-생성-및-병렬-조사" />
<span id="eks-agent-조사-결과" />
<span id="network-agent-조사-결과" />
<span id="database-agent-조사-결과" />
<span id="step-4-결과-집계-및-근본원인-분석" />
<span id="step-5-수정-및-검증" />
<span id="검증" />
<span id="결과" />
<span id="incident-postmortem" />
<span id="summary" />
<span id="timeline" />
<span id="root-cause" />
<span id="resolution" />
<span id="prevention" />


# 인시던트 대응 예제

서비스 중단이 비정상 로드 밸런서 대상과 실패한 애플리케이션 파드에 걸쳐 발생한 상황입니다. 조정자는 공통 타임라인을 수집하고 네트워크와 워크로드 조사를 각각 배정합니다.

## 5분 초기 분류 {#five-minute-triage}

영향받는 사용자·서비스, 시작 시각, 심각도, 최근 배포, 선택한 계정·클러스터를 기록합니다. 노드·파드 상태, 이벤트, 대상 상태, 관련 텔레메트리를 수집합니다. 관찰 결과와 가설을 명확히 구분합니다.

## 병렬 조사 {#parallel-investigation}

네트워크 전문가는 대상 선택, 포트, 준비 상태, 경로, 허용 트래픽을 추적합니다. EKS 전문가는 재시작, 이전 로그, 설정, 스케줄링, 리소스를 확인합니다. 근거상 필요하고 호스트 도구가 워크플로를 지원할 때만 자격 증명, 스토리지, 데이터베이스, 관측성 전문가를 추가합니다.

## 연관성 분석 및 완화 {#correlation-and-mitigation}

어떤 발견 사항이 다른 문제를 설명하는지 파악하고, 연관이 없는 장애는 별도로 처리합니다. 승인된 범위에서 가장 작은 완화 조치를 선택하고 복구에 미치는 영향을 기록한 뒤 원래 사용자 경로를 검증합니다. 파드 하나가 정상이라는 이유로 복구를 선언하지 않고 워크로드 상태와 알람을 다시 확인합니다.

## 사후 분석 {#postmortem}

영향, 타임라인, 확인된 원인, 조치, 검증, 예방책과 담당자를 기록합니다. 비밀 값, 원문 자격 증명, 불필요한 개인 정보는 보고서에 포함하지 않습니다.

[조정 에이전트](/docs/aws-ops-plugin/agents/ops-coordinator-agent) · [문제 해결 워크플로](/docs/aws-ops-plugin/skills/ops-troubleshoot)
