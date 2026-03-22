---
remarp: true
block: implementation
---

<!-- Slide 1: Session Cover -->
@type: cover
@background: linear-gradient(135deg, #161D26 0%, #0d1117 50%, #1a2332 100%)

# AIOps on AWS
Intelligent Cloud Operations for AnyCompany

@speaker: Junseok Oh
@speaker-title: Sr. Solutions Architect
@company: AWS

:::notes
{timing: 0.5min}
마지막 블록입니다. 지금까지 배운 서비스들을 AnyCompany 환경에 어떻게 적용할지 구체적인 전략을 논의하겠습니다.
{cue: transition}
:::

---
<!-- Slide 2: Block 3 Title -->
@type: title
@transition: fade

# Implementation Strategies
Block 3 — AnyCompany를 위한 AIOps 구현 (25분)

:::notes
{timing: 0.5min}
세 번째 블록입니다. 이론을 넘어 실제 구현으로 들어갑니다. AnyCompany 환경을 가정한 아키텍처, 단계별 로드맵, 비용 최적화를 다룹니다.
:::

---
<!-- Slide 3: AnyCompany Reference Architecture -->
@type: canvas

## AnyCompany AIOps 레퍼런스 아키텍처

:::canvas
@width: 960
@height: 420

# Top: Application Layer
box "EKS Cluster\n(Production)" 30,20 140,55 fill:#1a2744 border:#41B3FF step:0
box "Lambda\nMicroservices" 200,20 140,55 fill:#1a2744 border:#41B3FF step:0
box "Aurora\nPostgreSQL" 370,20 140,55 fill:#1a2744 border:#41B3FF step:0
box "DynamoDB\nTables" 540,20 140,55 fill:#1a2744 border:#41B3FF step:0
box "S3 + CloudFront\nStatic Assets" 710,20 140,55 fill:#1a2744 border:#41B3FF step:0

# Collection Layer
box "ADOT\nCollector" 80,120 120,45 fill:#232f3e border:#FF9900 step:1
box "CloudWatch\nAgent" 260,120 120,45 fill:#232f3e border:#FF9900 step:1
box "VPC Flow\nLogs" 440,120 120,45 fill:#232f3e border:#FF9900 step:1
box "CloudTrail" 620,120 120,45 fill:#232f3e border:#FF9900 step:1

# Arrows: App -> Collection
arrow 100,75 130,120 #41B3FF step:1
arrow 270,75 310,120 #41B3FF step:1
arrow 440,75 490,120 #41B3FF step:1
arrow 610,75 670,120 #41B3FF step:1

# Central Data Hub
box "CloudWatch\n(Monitoring Account)" 250,200 200,55 fill:#232f3e border:#00E500 step:2
box "AMP\n(Custom Metrics)" 500,200 160,55 fill:#232f3e border:#00E500 step:2

arrow 140,165 310,200 #FF9900 step:2
arrow 320,165 350,200 #FF9900 step:2
arrow 500,165 400,200 #FF9900 step:2
arrow 680,165 550,200 #FF9900 step:2

# AI/ML Layer
box "DevOps\nGuru" 80,300 110,50 fill:#161D26 border:#AD5CFF step:3
box "CW Anomaly\nDetection" 220,300 120,50 fill:#161D26 border:#AD5CFF step:3
box "Bedrock\nAgent" 370,300 110,50 fill:#161D26 border:#AD5CFF step:3
box "Lookout\nfor Metrics" 510,300 120,50 fill:#161D26 border:#AD5CFF step:3

arrow 320,255 135,300 #00E500 step:3
arrow 350,255 280,300 #00E500 step:3
arrow 380,255 425,300 #00E500 step:3
arrow 560,255 570,300 #00E500 step:3

# Action Layer
box "EventBridge\nRules" 700,270 120,45 fill:#161D26 border:#FF5C85 step:4
box "SSM\nAutomation" 700,330 120,45 fill:#161D26 border:#FF5C85 step:4

arrow 630,325 700,290 #AD5CFF step:4
arrow 630,325 700,352 #AD5CFF step:4

# Notification
box "Slack\nPagerDuty" 860,290 90,50 fill:#161D26 border:#FBD332 step:4
arrow 820,292 860,310 #FF5C85 step:4
arrow 820,352 860,320 #FF5C85 step:4

# AMG Dashboard
box "AMG\nDashboard" 860,200 90,50 fill:#161D26 border:#00E500 step:2
arrow 660,227 860,225 #00E500 step:2

# Labels
text "Application Layer" 400,85 size:12 color:#41B3FF step:0
text "Collection" 400,175 size:12 color:#FF9900 step:1
text "Data Hub" 400,265 size:12 color:#00E500 step:2
text "AI/ML Analysis" 300,365 size:12 color:#AD5CFF step:3
text "Automation" 770,385 size:12 color:#FF5C85 step:4
:::

:::notes
{timing: 4min}
이것이 AnyCompany를 위한 AIOps 레퍼런스 아키텍처입니다.

Step 0 — Application Layer입니다. EKS 클러스터, Lambda 마이크로서비스, Aurora PostgreSQL, DynamoDB, S3+CloudFront까지 — 전형적인 현대 웹 서비스 스택입니다.

Step 1 — Collection Layer에서 ADOT Collector가 EKS 트레이스와 메트릭을, CloudWatch Agent가 시스템 메트릭과 로그를, VPC Flow Logs가 네트워크 데이터를, CloudTrail이 API 감사 로그를 수집합니다.

Step 2 — Central Data Hub는 Monitoring Account의 CloudWatch로 모든 계정의 데이터가 통합됩니다. AMP는 Prometheus 커스텀 메트릭을 저장하고, AMG 대시보드로 시각화합니다.

Step 3 — AI/ML Layer에서 DevOps Guru, CloudWatch AD, Bedrock Agent, Lookout이 각각의 분석을 수행합니다.

Step 4 — EventBridge가 탐지된 이상을 받아서 SSM Automation으로 자동 복구하고, Slack과 PagerDuty로 알림을 보냅니다.

이 전체 아키텍처를 한 번에 구축하는 것은 비현실적입니다. 다음 슬라이드에서 단계별 로드맵을 보겠습니다.
{cue: transition}
:::

---
<!-- Slide 4: Implementation Roadmap -->
@type: canvas

## 단계별 도입 로드맵

:::canvas
@width: 960
@height: 400

# Phase 1 (Month 1-2)
box "Phase 1\nFoundation\n(Month 1-2)" 30,30 180,80 fill:#1a2744 border:#41B3FF step:0
text "CloudWatch Agent 전체 배포" 120,130 size:11 color:#ffffff step:0
text "ADOT DaemonSet (EKS)" 120,150 size:11 color:#ffffff step:0
text "Cross-Account Observability" 120,170 size:11 color:#ffffff step:0
text "SLI/SLO 정의 워크숍" 120,190 size:11 color:#ffffff step:0

# Phase 2 (Month 3-4)
arrow 210,70 260,70 #41B3FF step:1
box "Phase 2\nDetection\n(Month 3-4)" 260,30 180,80 fill:#232f3e border:#FF9900 step:1
text "CloudWatch Anomaly Detection" 350,130 size:11 color:#ffffff step:1
text "DevOps Guru 활성화" 350,150 size:11 color:#ffffff step:1
text "Composite Alarm 3계층" 350,170 size:11 color:#ffffff step:1
text "AMP + AMG 구축" 350,190 size:11 color:#ffffff step:1

# Phase 3 (Month 5-6)
arrow 440,70 490,70 #FF9900 step:2
box "Phase 3\nAutomation\n(Month 5-6)" 490,30 180,80 fill:#232f3e border:#00E500 step:2
text "EventBridge 자동화 규칙" 580,130 size:11 color:#ffffff step:2
text "SSM Runbook 자동 복구" 580,150 size:11 color:#ffffff step:2
text "Incident 자동 분류/라우팅" 580,170 size:11 color:#ffffff step:2
text "CodeGuru + Lookout 연동" 580,190 size:11 color:#ffffff step:2

# Phase 4 (Month 7+)
arrow 670,70 720,70 #00E500 step:3
box "Phase 4\nIntelligence\n(Month 7+)" 720,30 180,80 fill:#161D26 border:#AD5CFF step:3
text "Bedrock Agent AIOps 챗봇" 810,130 size:11 color:#ffffff step:3
text "자동 RCA 파이프라인" 810,150 size:11 color:#ffffff step:3
text "Predictive Scaling 연동" 810,170 size:11 color:#ffffff step:3
text "Chaos Engineering 통합" 810,190 size:11 color:#ffffff step:3

# Maturity bar
text "Level 1: Reactive" 100,250 size:12 color:#41B3FF step:0
text "Level 2: Proactive" 330,250 size:12 color:#FF9900 step:1
text "Level 3: Automated" 560,250 size:12 color:#00E500 step:2
text "Level 4: Intelligent" 790,250 size:12 color:#AD5CFF step:3

# KPIs
box "MTTR\n4h → 2h" 70,280 100,40 fill:#1a2744 border:#41B3FF step:0
box "MTTR\n2h → 30m" 300,280 100,40 fill:#232f3e border:#FF9900 step:1
box "MTTR\n30m → 5m" 530,280 100,40 fill:#232f3e border:#00E500 step:2
box "MTTR\n5m → auto" 760,280 100,40 fill:#161D26 border:#AD5CFF step:3

text "MTTR 개선 추이" 430,350 size:13 color:#FBD332 step:0
:::

:::notes
{timing: 4min}
이 로드맵은 AnyCompany가 6-9개월에 걸쳐 AIOps를 도입하는 현실적 계획입니다.

Phase 1 Foundation은 2개월입니다. 가장 중요한 건 데이터 수집 체계를 완성하는 것입니다. CloudWatch Agent를 모든 워크로드에 배포하고, EKS에 ADOT DaemonSet을 올리고, Cross-Account Observability를 설정합니다. 이 단계에서 SLI/SLO를 반드시 정의하세요. 단순히 가시성만 확보해도 MTTR이 4시간에서 2시간으로 줄어듭니다.

Phase 2 Detection은 3-4개월 차입니다. CloudWatch AD와 DevOps Guru를 활성화하고, Composite Alarm 3계층을 설정합니다. MTTR이 30분으로 줄어듭니다.

Phase 3 Automation은 5-6개월 차입니다. EventBridge와 SSM Runbook으로 자동 복구를 구현합니다. MTTR 5분 목표.

Phase 4 Intelligence는 7개월 이후입니다. Bedrock Agent로 AIOps 챗봇을 만들고 자동 RCA 파이프라인을 구축합니다.
{cue: question}
AnyCompany의 현재 MTTR은 어느 정도인가요? 현 위치에 따라 시작점이 달라집니다.
{cue: transition}
비용에 대해 이야기해 봅시다.
:::

---
<!-- Slide 5: Cost Optimization -->
@type: tabs

## AIOps 비용 최적화 전략

::: tab "비용 구조"
### 서비스별 월간 비용 (100 리소스 기준)
| 서비스 | 항목 | 월 비용 |
|--------|------|---------|
| CloudWatch Metrics | 커스텀 메트릭 200개 | ~$60 |
| CloudWatch Logs | 50GB 수집, 30일 보존 | ~$75 |
| CloudWatch AD | 메트릭 50개 | 무료 (CW 포함) |
| DevOps Guru | 100 리소스 | ~$200 |
| AMP | 50M samples/month | ~$150 |
| AMG | 1 workspace, 5 editors | ~$45 |
| X-Ray | 10M traces | ~$50 |
| Lookout | 50 메트릭 | ~$300 |
| **합계** | | **~$880/month** |

> Production만 적용 시 기준. Dev/Staging은 ~$380/month로 축소 가능
:::

::: tab "비용 절감 팁"
### 즉시 적용 가능
- **로그 보존 정책**: hot 30일 → warm 90일 → S3 아카이브 {.click}
- **메트릭 필터링**: 불필요한 high-cardinality 메트릭 drop {.click}
- **AMP relabeling**: label 조합 100만 이하로 관리 {.click}
- **X-Ray 샘플링**: reservoir 1/s + fixed_rate 5% {.click}

### 아키텍처 레벨
- **Monitoring Account** 통합으로 중복 수집 제거 {.click}
- **ADOT Processor**: batch + filter로 불필요 데이터 제거 {.click}
- **Tiered Alerting**: L1은 CloudWatch만, L2부터 DevOps Guru {.click}

### ROI 측정 공식
```
AIOps ROI = (MTTR_before - MTTR_after) × incidents/month
            × cost_per_minute_downtime
            - AIOps_monthly_cost
```
:::

::: tab "비용 vs 가치"
### AnyCompany 시나리오

**Before AIOps**
- 월 평균 장애: 8건
- 평균 MTTR: 2시간
- 분당 비즈니스 영향: $500
- **월 손실: 8 × 120분 × $500 = $480,000**

**After AIOps (Phase 3)**
- 월 평균 장애: 5건 (3건 사전 예방)
- 평균 MTTR: 15분
- **월 손실: 5 × 15분 × $500 = $37,500**

### 결과
| 항목 | 금액 |
|------|------|
| 월 손실 감소 | $442,500 |
| AIOps 월 비용 | $880 |
| **월 순이익** | **$441,620** |
| **ROI** | **50,000%+** |

> 장애 비용이 있는 환경이라면 AIOps는 거의 항상 positive ROI
:::

:::notes
{timing: 4min}
비용 이야기를 해야죠. 첫 번째 탭에서 100개 리소스 기준 월 880달러입니다.

두 번째 탭의 비용 절감 팁이 중요합니다. 가장 큰 비용 요인은 보통 CloudWatch Logs입니다. 30일 이상 된 로그는 warm storage로, 90일 이상은 S3로 자동 이전하세요. AMP에서는 relabeling으로 불필요한 label 조합을 제거하면 비용이 크게 절감됩니다.

세 번째 탭이 핵심입니다. AnyCompany 시나리오에서 장애 비용을 계산해 보면, Before AIOps에서 월 48만 달러 손실이 After AIOps에서 3.75만 달러로 줄어듭니다. AIOps 비용 880달러와 비교하면 ROI가 5만 퍼센트입니다.
{cue: transition}
운영 성숙도 모델을 보겠습니다.
:::

---
<!-- Slide 6: Maturity Model -->

## AIOps 운영 성숙도 모델

### Level 1 — Reactive (수동 대응)
- 장애 발생 후 수동 확인, 개인 경험에 의존
- 알람 = 정적 임계값, 대시보드 수동 확인
- MTTR: 2-4시간 {.click}

### Level 2 — Proactive (사전 탐지)
- ML 기반 이상 탐지, 관측성 3 Pillars 구축
- DevOps Guru + CloudWatch AD 활성화
- MTTR: 15-30분 {.click}

### Level 3 — Automated (자동 대응)
- EventBridge + SSM 자동 복구, Composite Alarm
- Runbook 기반 셀프 힐링
- MTTR: 1-5분 {.click}

### Level 4 — Intelligent (지능형 운영)
- Gen AI 기반 자연어 분석, Predictive scaling
- 자동 RCA → 자동 수정 → 자동 검증
- MTTR: 자동 복구 (사람 개입 최소) {.click}

:::notes
{timing: 3min}
운영 성숙도를 4단계로 정의합니다.

Level 1 Reactive는 대부분의 조직이 시작하는 곳입니다. Level 2 Proactive는 Phase 2를 완료한 상태입니다. Level 3 Automated는 Phase 3를 완료한 상태입니다. Level 4 Intelligent는 최종 목표입니다.

AnyCompany는 현재 어디 계신가요? 대부분 Level 1에서 Level 2로 넘어가는 단계일 텐데, 6-9개월이면 Level 3까지 도달할 수 있습니다.
{cue: transition}
실전 도전 과제들을 이야기합시다.
:::

---
<!-- Slide 7: Common Challenges -->
@type: compare

## AIOps 도입 시 흔한 도전과 해결책

### Challenge
- **데이터 사일로** — 팀마다 다른 모니터링 도구 사용
- **알람 피로** — 수백 개 알람이 울려도 무시
- **스킬 갭** — ML/데이터 분석 역량 부족
- **신뢰 부족** — "ML 판단을 믿을 수 있나?"
- **비용 우려** — 관측성 비용이 인프라 비용의 10%+

### Solution
- **Monitoring Account** 통합 + ADOT 표준화 → 사일로 해소
- **Composite Alarm 3계층** + DevOps Guru 상관 분석 → 노이즈 80% 감소
- **Amazon Q** — ML 전문성 없이 자연어로 분석 → 스킬 갭 해소
- **점진적 자동화** — 알림부터 시작, 신뢰 구축 후 자동 대응
- **Tiered 수집** — 핵심 SLI만 ML 적용 → 비용 최적화

:::notes
{timing: 3min}
AIOps 도입 시 가장 흔히 겪는 5가지 도전을 정리했습니다.

데이터 사일로가 가장 큰 장벽입니다. 해결책은 Monitoring Account로 통합하고, ADOT를 표준 수집기로 채택하는 것입니다.

스킬 갭은 GenAI가 해결합니다. Amazon Q in CloudWatch를 쓰면 PromQL을 몰라도 자연어로 분석할 수 있습니다.

가장 중요한 건 신뢰입니다. 처음부터 자동 대응을 켜지 마세요. 3-6개월간 알림만 보내면서 팀이 ML 판단을 체감한 후에 단계적으로 자동화를 확대하세요.
{cue: transition}
Quick Win을 정리하겠습니다.
:::

---
<!-- Slide 8: Quick Wins -->

## AnyCompany — 내일부터 시작할 수 있는 Quick Wins

::: left
### Week 1 — 즉시 적용
1. **Amazon Q in CloudWatch** 활성화 (무료) {.click}
   - 팀 전원에게 접근 권한 부여
   - "가장 에러가 많은 Lambda는?" 테스트
2. **CloudWatch Anomaly Detection** 핵심 SLI 5개 적용 {.click}
   - API latency P99, Error rate, Lambda Duration
   - Stddev = 2로 시작
3. **Composite Alarm** 1개 시범 구성 {.click}
   - 가장 중요한 서비스의 L3 알람
:::

::: right
### Week 2-4 — 기반 구축
4. **SLI/SLO 워크숍** 개최 {.click}
   - 서비스 소유자와 함께 핵심 SLI 정의
   - 99.9% availability = 월 43분 다운타임
5. **DevOps Guru** Production 스택 활성화 {.click}
   - HIGH severity만 SNS → Slack 알림
6. **ADOT 파일럿** EKS 1개 클러스터 적용 {.click}
   - DaemonSet 배포 + AMP 연동

### 성공 기준
- 2주 내: "ML이 잡아낸 이상" 최초 사례 1건
- 4주 내: MTTR 30% 감소 (측정 시작)
:::

:::notes
{timing: 3min}
이론은 충분합니다. 내일부터 할 수 있는 것들을 정리했습니다.

Week 1에 바로 할 수 있는 세 가지가 있습니다. 첫째, Amazon Q in CloudWatch 활성화는 설정이 필요 없고 무료입니다. 둘째, CloudWatch Anomaly Detection은 가장 중요한 SLI 5개에만 적용합니다. 셋째, Composite Alarm을 가장 중요한 서비스 하나에 시범 적용합니다.

성공 기준을 명확히 합니다. 2주 내에 ML이 실제로 이상을 잡아낸 사례 1건을 만들어야 팀의 buy-in을 얻을 수 있습니다.
{cue: transition}
마지막으로 전체 세션을 정리합니다.
:::

---
<!-- Slide 9: Session Summary -->
@transition: fade

## 전체 세션 요약

::: left
### Block 1 — Foundations
- AIOps = Observe + Detect + Diagnose + Respond
- ADOT 통합 수집 → CloudWatch + AMP + X-Ray
- Cross-Account Observability로 통합 모니터링

### Block 2 — ML Operations
- DevOps Guru — 이벤트 상관 분석, 사전 예측
- CloudWatch AD — RCF 기반 동적 이상 탐지
- Gen AI (Q, Bedrock) — 자연어 운영 인터페이스
- Composite Alarm — 3계층 알람 전략
:::

::: right
### Block 3 — Implementation
- 4-Phase 로드맵: Foundation → Detection → Automation → Intelligence
- MTTR: 4시간 → 30분 → 5분 → 자동 복구
- ROI: AIOps 비용 대비 50,000%+ 절감 가능

### 핵심 메시지
> **"AIOps는 목적지가 아니라 여정입니다."**
> 작게 시작하고(Quick Wins), 신뢰를 구축하고(점진적 자동화), 지속적으로 발전시키세요.

### Next Steps
1. SLI/SLO 워크숍 스케줄링
2. Amazon Q + CloudWatch AD 시범 적용
3. DevOps Guru PoC 범위 합의
:::

:::notes
{timing: 3min}
90분간의 세션을 마무리하겠습니다.

가장 기억하셨으면 하는 메시지는 "AIOps는 여정"이라는 것입니다.

한꺼번에 모든 걸 도입하려고 하면 실패합니다. Quick Win으로 시작하세요. Amazon Q를 켜고, Anomaly Detection을 5개 메트릭에 적용하고, DevOps Guru를 Production에 활성화하세요. 2주 안에 첫 번째 성공 사례가 나올 겁니다.

다음 단계로 SLI/SLO 워크숍을 먼저 잡으시는 것을 추천합니다. 감사합니다!
{cue: question}
질문 있으신 분 계신가요?
:::

---
<!-- Slide 10: Q&A -->
@transition: fade

## Q&A

궁금한 점을 자유롭게 질문해 주세요.

::: left
### 추가 리소스
- AWS Well-Architected — Operational Excellence Pillar
- Amazon DevOps Guru Documentation
- AWS Observability Best Practices Guide
- AWS AIOps Workshop (workshops.aws)
:::

::: right
### Contact
**Junseok Oh**
Sr. Solutions Architect, AWS

세션 후에도 언제든 연락 주세요.
:::

:::notes
{timing: 5min}
Q&A 시간입니다. 오늘 다룬 내용 중 궁금한 점이나, AnyCompany 환경에 적용하면서 예상되는 이슈에 대해 편하게 질문해 주세요.
:::

---
<!-- Slide 11: Thank You -->
@type: thankyou

## Thank You!

AIOps on AWS — Intelligent Cloud Operations

:::notes
{timing: 0.5min}
감사합니다. 오늘 세션이 AnyCompany의 AIOps 여정에 도움이 되었길 바랍니다.
:::
