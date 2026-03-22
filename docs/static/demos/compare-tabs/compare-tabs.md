---
remarp: true
block: compare-tabs
---

@type: cover
@background: linear-gradient(135deg, #161D26 0%, #0d1117 50%, #1a2332 100%)

# Compare & Tabs Demo
인터랙티브 비교/탭 슬라이드 데모

@speaker: Remarp Demo
@speaker-title: Interactive Presentation Framework

---
@type: compare

## Traditional Ops vs AIOps

### Traditional Ops

- **수동 모니터링** -- 대시보드를 지속적으로 감시
- **정적 임계값** -- 고정된 threshold 기반 알림
- **사후 대응** -- 문제 발생 후 대응 시작
- **사일로화된 도구** -- 분리된 모니터링 시스템
- **수동 상관관계 분석** -- 담당자 경험에 의존

### AIOps

- **ML 기반 이상 탐지** -- 자동화된 패턴 인식
- **동적 기준선** -- 학습 기반 적응형 threshold
- **예방적 운영** -- 문제 예측 및 선제 대응
- **통합 Observability** -- 메트릭/로그/트레이스 통합
- **자동 근본 원인 분석** -- AI가 상관관계 파악

---
@type: tabs

## CloudWatch 핵심 개념

### Metrics

**Custom Metrics 발행**
- Namespace 구조: `MyApp/ServiceName`
- 해상도: Standard (60초) / High-Resolution (1초)
- Dimension 설계가 비용과 쿼리 성능에 직결

**주요 지표**
- CPUUtilization, NetworkIn/Out, DiskReadOps
- Custom: RequestLatency, ErrorCount, ActiveConnections

### Logs

**Log 구조**
- **Log Groups** -- 애플리케이션/서비스 단위 그룹
- **Log Streams** -- 인스턴스/컨테이너 단위 스트림
- **Insights** -- SQL 유사 쿼리로 로그 분석

**보존 정책**
- 1일 ~ 영구 보관 설정 가능
- S3 내보내기로 장기 보관 비용 절감

### Alarms

**알람 유형**
- **Static Threshold** -- 고정 임계값 기반
- **Anomaly Detection** -- ML 기반 동적 기준선
- **Composite Alarms** -- 여러 알람 조합

**알람 상태**
- OK / ALARM / INSUFFICIENT_DATA
- 평가 기간(Period)과 평가 횟수(Evaluation Periods) 설정
