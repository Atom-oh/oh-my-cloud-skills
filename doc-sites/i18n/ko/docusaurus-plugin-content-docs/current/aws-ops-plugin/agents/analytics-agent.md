---
sidebar_position: 9
title: "분석 에이전트"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="핵심-기능" />
<span id="진단-명령어" />
<span id="amazon-opensearch-service" />
<span id="opensearch-serverless" />
<span id="clickhouse" />
<span id="amazon-athena" />
<span id="amazon-quicksight" />
<span id="amazon-kinesis" />
<span id="주요-메트릭-참조" />
<span id="의사결정-트리" />
<span id="mcp-서버-연동" />
<span id="사용-예시" />
<span id="opensearch-클러스터-트러블슈팅" />
<span id="athena-쿼리-최적화" />
<span id="출력-형식" />


# 분석 에이전트

OpenSearch 및 OpenSearch Serverless, ClickHouse, Athena, QuickSight, Kinesis의 수집·쿼리 파이프라인을 다룹니다.

## 진단 방법 {#diagnostic-approach}

수집 지연과 쿼리 지연을 구분합니다. 클러스터·샤드 상태, 스토리지와 메모리 부하, 컬렉션 접근, 쿼리 계획, 스캔한 데이터, 파티셔닝, 대시보드 갱신, 스트림 용량, iterator age를 점검합니다. 측정된 병목에 근거해 튜닝을 제안합니다.

## 초기 읽기 전용 점검 {#initial-read-only-checks}

대상 계정과 리전에서만 다음 AWS CLI 점검을 실행합니다. 관찰한 결과에 따라 서비스별 후속 점검을 선택합니다.

```bash
aws opensearch list-domain-names
aws opensearchserverless list-collections
aws athena list-work-groups
aws kinesis list-streams
```

## 근거와 인계 {#evidence-and-handoff}

영향받는 구성 요소, 관찰한 증상, 근거 출력, 추정 원인, 제안 조치, 검증 명령과 예상 결과를 제시합니다. 팀 모드에서는 배정된 영역만 보고하고 조정자가 확인할 의존 관계를 명시합니다.

이 플러그인에는 `awsdocs`와 `awsapi`가 포함됩니다. 추가 지식/IaC 연동은 호스트에서 선택적으로 제공하는 기능입니다. 모델과 도구는 공개 사이트의 별도 설정 표가 아니라 실제 에이전트 frontmatter와 Codex 오버레이에 정의됩니다.

[에이전트 명령어와 의사결정 트리](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/agents/analytics-agent.md)
