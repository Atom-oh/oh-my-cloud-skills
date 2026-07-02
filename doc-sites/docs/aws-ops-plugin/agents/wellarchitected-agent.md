---
sidebar_position: 10
title: "Well-Architected Agent"
---

# Well-Architected Framework Review Agent

AWS Well-Architected Framework 6개 필러를 기반으로 인프라를 종합 평가하고, 100점 스코어링과 AS-IS/TO-BE 변환 로드맵을 생성하는 에이전트입니다.

## 트리거 키워드

- "well-architected", "WAF review", "WAF 점검"
- "인프라 진단", "아키텍처 리뷰", "심층 진단", "인프라 점수"

## 6-Pillar 평가

| 필러 | 평가 항목 |
|------|----------|
| **Cost Optimization** | 서비스별 비용 분석, MoM 트렌드, 유휴 리소스, RI/SP 커버리지, 스토리지 클래스, Graviton 절감 |
| **Security** | 퍼블릭 노출 스캔, 암호화 커버리지, IAM 위생 (MFA, 키 수명, 최소 권한), CIS 컴플라이언스 |
| **Reliability** | SPOF 감지, Multi-AZ 커버리지, NAT GW 이중화, DB HA, ASG 커버리지, 엔진 버전 현행화 |
| **Performance** | 컴퓨팅 라이트사이징, EKS 네임스페이스 효율, Lambda 메모리 최적화, DB 튜닝, 인스턴스 세대 |
| **Operational Excellence** | 모니터링 커버리지, 로그 보존, CloudTrail 검증, IaC 감지, 자동화 성숙도 |
| **Sustainability** | Graviton 채택율, gp2→gp3 마이그레이션, 서버리스 채택, 리소스 효율 |

## 스코어링

각 필러는 가중 평균으로 100점 만점 스코어를 산출합니다:

| 점수 | 등급 | 설명 |
|------|------|------|
| 80-100 | A | 우수 — 모범 사례 적용 |
| 60-79 | B | 양호 — 일부 개선 필요 |
| 40-59 | C | 주의 — 중요 개선 필요 |
| 0-39 | D | 위험 — 즉시 조치 필요 |

### 전문 에이전트 위임

60점 미만인 필러는 전문 에이전트에 심층 분석을 위임합니다:

| 필러 | 위임 에이전트 |
|------|-------------|
| Cost | cost-agent |
| Security | iam-agent |
| Reliability | eks-agent, network-agent |
| Performance | eks-agent, database-agent |
| Operational Excellence | observability-agent |

## 사용 예시

### 전체 리뷰

```
"인프라 Well-Architected 리뷰 실행해줘"
```

### 특정 필러 집중

```
"Security 필러만 심층 진단해줘"
```

## 출력 형식

```markdown
# Well-Architected Review Report

## Overall Score: 72/100 (Grade: B)

| Pillar | Score | Grade | Key Finding |
|--------|-------|-------|-------------|
| Cost | 65 | B | 유휴 EC2 3대 감지 |
| Security | 82 | A | MFA 전체 적용됨 |
| Reliability | 58 | C | NAT GW 단일 AZ |
| Performance | 78 | B | gp2 볼륨 5개 |
| OpEx | 75 | B | CloudTrail 미설정 |
| Sustainability | 70 | B | Graviton 30% |

## AS-IS → TO-BE Roadmap

### P1 (즉시)
- NAT Gateway Multi-AZ 이중화
- CloudTrail 활성화

### P2 (1주 이내)
- 유휴 EC2 인스턴스 종료
- gp2 → gp3 마이그레이션

### P3 (1개월 이내)
- Graviton 인스턴스 마이그레이션
- Savings Plan 구매 검토
```

## MCP 연동

| 서버 | 용도 |
|------|------|
| `awsdocs` | AWS 공식 문서 검색 |
| `awsapi` | AWS API 직접 호출 (CE, EC2, RDS, EKS 등) |
