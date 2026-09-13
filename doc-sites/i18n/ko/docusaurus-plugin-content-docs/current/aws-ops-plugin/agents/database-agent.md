---
sidebar_position: 6
title: "데이터베이스 에이전트"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="핵심-기능" />
<span id="진단-명령어" />
<span id="rdsaurora-연결" />
<span id="dynamodb" />
<span id="elasticache" />
<span id="의사결정-트리" />
<span id="일반적인-오류와-해결책" />
<span id="mcp-서버-연동" />
<span id="사용-예시" />
<span id="rds-연결-문제-해결" />
<span id="dynamodb-스로틀링-진단" />
<span id="출력-형식" />
<span id="performance-recommendations" />


# 데이터베이스 에이전트

RDS/Aurora의 연결과 성능, DynamoDB의 요청 제한과 용량, ElastiCache의 연결·메모리·지연 시간을 다룹니다.

## 진단 방법 {#diagnostic-approach}

쿼리 성능보다 먼저 엔드포인트, 네트워크, 인증을 확인합니다. 연결 한도, 장애 조치 이벤트, 핫 파티션, 용량 모드, 캐시 축출, 애플리케이션 재시도 동작의 연관성을 분석합니다. 제안한 변경은 워크로드와 복구 요구 사항에 맞춰 검증합니다.

## 초기 읽기 전용 점검 {#initial-read-only-checks}

대상 계정과 리전에서만 다음 AWS CLI 점검을 실행합니다. 관찰한 결과에 따라 서비스별 후속 점검을 선택합니다.

```bash
aws rds describe-db-instances
aws dynamodb list-tables
aws elasticache describe-cache-clusters
```

## 근거와 인계 {#evidence-and-handoff}

영향받는 구성 요소, 관찰한 증상, 근거 출력, 추정 원인, 제안 조치, 검증 명령과 예상 결과를 제시합니다. 팀 모드에서는 배정된 영역만 보고하고 조정자가 확인할 의존 관계를 명시합니다.

이 플러그인에는 `awsdocs`와 `awsapi`가 포함됩니다. 추가 지식/IaC 연동은 호스트에서 선택적으로 제공하는 기능입니다. 모델과 도구는 공개 사이트의 별도 설정 표가 아니라 실제 에이전트 frontmatter와 Codex 오버레이에 정의됩니다.

[에이전트 명령어와 의사결정 트리](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/agents/database-agent.md)
