---
remarp: true
block: 01-aiops-foundations
---

@type: cover

# AIOps: 지능형 클라우드 운영
Block 1 — AIOps 기초와 관측성 전략 (30 min)

Junseok Oh
Sr. Solutions Architect
AWS

:::notes
{timing: 2min}
환영 인사와 함께 세션을 시작합니다. 오늘 다룰 AIOps의 핵심 가치를 간략히 소개하세요.
"클라우드 운영의 복잡성이 증가하면서, 수동 대응으로는 한계가 있습니다. 오늘은 AWS AIOps 서비스를 활용해 지능형 운영을 구현하는 방법을 알아보겠습니다."
청중에게 현재 운영 환경에 대해 간단히 질문하며 참여를 유도하세요.
:::

---
@type: steps
@steps-shape: circle

## 오늘 다룰 내용

- **수동 운영의 한계** — 왜 AIOps가 필요한가?
- **AIOps 개념과 AWS 서비스** — ML + 자동화 + 관측성의 결합
- **관측성 3대 축** — Metrics, Logs, Traces의 통합 전략

:::notes
{timing: 2min}
세 가지 핵심 주제를 순서대로 소개합니다.
첫 번째로 현재 수동 운영의 문제점을 짚고, 두 번째로 AIOps가 이를 어떻게 해결하는지 살펴봅니다.
마지막으로 AIOps의 기반이 되는 관측성(Observability) 전략을 다룹니다.
"각 주제는 약 10분씩 진행되며, 중간에 아키텍처 다이어그램 데모가 포함됩니다."
:::

---
@type: content

## 수동 운영의 한계

> "장애가 발생하면 알람 폭풍 속에서 원인을 찾느라 몇 시간을 소비합니다..."

- **탐지 지연**: 평균 MTTD(Mean Time To Detect) 30분 이상 {.click}
- **복구 시간**: 평균 MTTR(Mean Time To Recover) 4시간+ {.click}
- **알람 피로**: 하루 수백 개의 알람, 90%는 false positive {.click}
- **사일로 문제**: 팀 간 정보 단절로 근본 원인 파악 지연 {.click}
- **확장성 한계**: 서비스 증가 → 운영 복잡도 기하급수적 증가 {.click}

:::notes
{timing: 3min}
{cue: pain-point}
수동 운영의 고통을 청중이 공감할 수 있도록 설명합니다. 각 항목을 클릭하며 순차 공개하세요.
MTTD 30분: "장애 발생 후 30분이 지나서야 인지하는 경우가 많습니다. 그 30분 동안 사용자는 이미 불편을 겪고 있죠."
MTTR 4시간: "원인 파악, 담당자 호출, 수정, 배포까지 평균 4시간. 비즈니스 영향이 큽니다."
알람 피로: "너무 많은 알람은 오히려 중요한 알람을 놓치게 만듭니다."
청중에게 질문: "여러분도 비슷한 경험이 있으신가요?"
:::

---
@type: content
@layout: two-column

## AIOps란?

::: left
### 정의와 핵심 원칙

**AIOps** = AI + IT Operations

- **Machine Learning**: 패턴 학습 및 이상 탐지
- **자동화(Automation)**: 반복 작업의 자동 처리
- **관측성(Observability)**: 메트릭/로그/트레이스 통합

> Gartner 정의: "빅데이터, ML, 자동화를 결합하여 IT 운영을 향상시키는 접근법"
:::

::: right
### 전통적 운영 vs AIOps

| 구분 | 전통적 운영 | AIOps |
|------|------------|-------|
| 탐지 | 임계값 기반 | ML 이상 탐지 |
| 분석 | 수동 로그 검색 | 자동 상관 분석 |
| 대응 | 수동 조치 | 자동 복구 |
| 확장 | 인력 비례 | 자동 스케일 |
| MTTD | 30분+ | 수 분 |
| MTTR | 4시간+ | 30분 이하 |
:::

:::notes
{timing: 3min}
AIOps의 정의와 전통적 운영과의 차이를 설명합니다.
왼쪽: "AIOps는 단순히 AI를 붙인 것이 아니라, ML, 자동화, 관측성이라는 세 가지 축이 결합된 접근법입니다."
오른쪽: "표를 보시면 각 영역에서 어떻게 개선되는지 한눈에 볼 수 있습니다. 특히 MTTD와 MTTR의 단축이 핵심입니다."
Gartner 정의를 인용하며 업계 표준 용어임을 강조하세요.
:::

---
@type: canvas
@canvas-id: aiops-cycle

## AIOps 사이클

:::canvas
box collect "수집 (Collect)" at 150,80 size 140,50 color #FF9900 step 1
icon cw "CloudWatch" at 220,160 size 40 step 1

box analyze "분석 (Analyze)" at 380,80 size 140,50 color #3B48CC step 2
icon dg "DevOps-Guru" at 450,160 size 40 step 2

box automate "자동화 (Automate)" at 610,80 size 140,50 color #1B660F step 3
icon lm "Lambda" at 680,160 size 40 step 3

arrow collect -> analyze "ML 분석" step 4
arrow analyze -> automate "이벤트 트리거" step 4
arrow automate -> collect "피드백 루프" curved step 4
:::

:::notes
{timing: 4min}
{cue: demo}
AIOps의 핵심 사이클을 단계별로 설명합니다. 화살표 키로 step 애니메이션을 진행하세요.
Step 1 - 수집: "CloudWatch가 메트릭, 로그, 트레이스를 수집합니다. 모든 AIOps의 시작점입니다."
Step 2 - 분석: "DevOps Guru가 ML로 이상 징후를 탐지하고 근본 원인을 분석합니다."
Step 3 - 자동화: "Lambda와 EventBridge가 자동 대응을 실행합니다."
Step 4 - 화살표: "이 사이클이 계속 순환하며 시스템을 학습하고 개선합니다. 피드백 루프가 핵심입니다."
:::

---
@type: canvas
@canvas-id: aws-aiops-map

## AWS AIOps 서비스 맵

:::canvas
box layer1 "Data Collection Layer" at 50,40 size 700,80 color #232F3E step 1
icon cw2 "CloudWatch" at 150,70 size 36 step 1
icon xray "X-Ray" at 350,70 size 36 step 1
icon ct "CloudTrail" at 550,70 size 36 step 1

box layer2 "Intelligent Analysis Layer" at 50,150 size 700,80 color #3B48CC step 2
icon dg2 "DevOps-Guru" at 250,180 size 36 step 2
icon lfm "Lookout-for-Metrics" at 450,180 size 36 step 2

box layer3 "Automation Layer" at 50,260 size 700,80 color #1B660F step 3
icon eb "EventBridge" at 150,290 size 36 step 3
icon lm2 "Lambda" at 350,290 size 36 step 3
icon ssm "Systems-Manager" at 550,290 size 36 step 3

arrow layer1 -> layer2 "분석 데이터" step 4
arrow layer2 -> layer3 "인사이트/이벤트" step 4
:::

:::notes
{timing: 4min}
{cue: architecture}
AWS AIOps 서비스 스택을 3계층으로 설명합니다. step별로 각 계층을 공개하세요.
Step 1 - 수집 계층: "CloudWatch(메트릭/로그), X-Ray(트레이스), CloudTrail(API 감사 로그). 이 세 서비스가 관측성의 기반입니다."
Step 2 - 분석 계층: "DevOps Guru는 운영 이상 탐지, Lookout for Metrics는 비즈니스 메트릭 이상 탐지에 특화되어 있습니다."
Step 3 - 자동화 계층: "EventBridge가 이벤트를 라우팅하고, Lambda가 자동 대응을 실행합니다. Systems Manager로 인프라 자동화까지 연결됩니다."
Step 4: "계층 간 데이터 흐름을 보여주며 전체 파이프라인을 설명하세요."
:::

---
@type: canvas
@canvas-id: aiops-pipeline-prompt

## AIOps 파이프라인 (Prompt Demo)

:::prompt
AWS AIOps 3계층 아키텍처를 그려주세요:
1층 - 데이터 수집: CloudWatch, X-Ray, CloudTrail
2층 - 지능형 분석: DevOps Guru, Lookout for Metrics
3층 - 자동화: EventBridge, Lambda, Systems Manager
각 층 사이에 화살표, 층별 다른 색상 라벨, Step 애니메이션 적용.
:::

:::notes
{timing: 3min}
{cue: prompt-demo}
이 슬라이드는 Remarp의 새로운 Prompt 기능을 데모합니다.
":::prompt 블록 안에 자연어로 원하는 다이어그램을 설명하면, 에이전트가 Canvas 코드를 자동 생성합니다."
"앞서 본 서비스 맵과 동일한 구조를 프롬프트로 요청한 예시입니다."
"실제 프로젝트에서는 '반영해주세요'라고 말하면 에이전트가 이 프롬프트를 읽고 Canvas DSL 또는 JS로 변환합니다."
"복잡한 코드 없이도 아키텍처 다이어그램을 빠르게 만들 수 있는 것이 장점입니다."
:::

---
@type: content
@layout: two-column

## CloudWatch 에코시스템

::: left
### 핵심 서비스

- **CloudWatch Metrics** {.click}
  - 70+ AWS 서비스 자동 수집
  - 커스텀 메트릭 지원

- **CloudWatch Logs** {.click}
  - 로그 수집/저장/분석
  - Logs Insights 쿼리 엔진

- **CloudWatch Alarms** {.click}
  - 임계값 + 이상 탐지 알람
  - 복합 알람(Composite Alarms)
:::

::: right
### 확장 기능

- **Container Insights** {.click}
  - EKS/ECS 컨테이너 관측성
  - 자동 대시보드 생성

- **Application Insights** {.click}
  - .NET/Java/Node.js 앱 모니터링
  - 이상 탐지 내장

- **Contributor Insights** {.click}
  - 상위 기여자 실시간 분석
  - VPC Flow Logs 트래픽 분석
:::

:::notes
{timing: 3min}
CloudWatch의 핵심 서비스와 확장 기능을 나눠서 설명합니다. 각 항목을 클릭하며 순차 공개하세요.
왼쪽 - 핵심: "Metrics, Logs, Alarms는 CloudWatch의 기본 삼형제입니다. 대부분의 AWS 서비스가 자동으로 메트릭을 보냅니다."
오른쪽 - 확장: "Container Insights는 EKS 사용자에게 필수입니다. Application Insights는 애플리케이션 레벨 관측성을 제공합니다."
"Contributor Insights는 덜 알려져 있지만, 트래픽 분석에 매우 유용합니다."
:::

---
@type: compare

## 관측성 3대 축

::: tab Metrics
### Metrics (지표)

**정의**: 시간에 따른 수치 데이터

**특징**:
- 집계 가능 (평균, 합계, 백분위)
- 저장 비용 효율적
- 대시보드/알람에 최적화

**AWS 서비스**:
- CloudWatch Metrics
- Amazon Managed Prometheus (AMP)

**사용 사례**:
- CPU/메모리 사용률
- 요청 처리량 (RPS)
- 에러율, 지연 시간 (p99)
:::

::: tab Logs
### Logs (로그)

**정의**: 이벤트의 텍스트 기록

**특징**:
- 상세한 컨텍스트 제공
- 구조화/비구조화 모두 지원
- 검색/필터링으로 디버깅

**AWS 서비스**:
- CloudWatch Logs
- OpenSearch Service

**사용 사례**:
- 에러 스택 트레이스
- 감사 로그 (CloudTrail)
- 애플리케이션 디버깅
:::

::: tab Traces
### Traces (트레이스)

**정의**: 분산 시스템의 요청 경로 추적

**특징**:
- 서비스 간 흐름 시각화
- 지연 구간 식별
- 근본 원인 분석에 필수

**AWS 서비스**:
- AWS X-Ray
- AWS Distro for OpenTelemetry (ADOT)

**사용 사례**:
- 마이크로서비스 병목 분석
- 콜드 스타트 지연 추적
- 서비스 의존성 맵
:::

:::notes
{timing: 4min}
{cue: tabs}
관측성의 세 기둥을 탭으로 전환하며 설명합니다. 각 탭을 클릭해 보여주세요.
Metrics 탭: "메트릭은 '무엇이 일어나고 있는가'를 알려줍니다. 시스템의 건강 상태를 한눈에 파악할 수 있죠."
Logs 탭: "로그는 '왜 일어났는가'를 알려줍니다. 디버깅의 핵심 자료입니다."
Traces 탭: "트레이스는 '어디서 일어났는가'를 알려줍니다. 분산 시스템에서 필수적입니다."
"이 세 가지를 결합해야 완전한 관측성을 확보할 수 있습니다. AIOps는 이 데이터를 ML로 분석합니다."
:::

---
@type: content

## Key Takeaways

### Block 1에서 배운 핵심 내용

- **수동 운영의 한계**: MTTD 30분+, MTTR 4시간+의 비효율. 알람 피로와 사일로 문제로 확장 불가

- **AIOps = ML + 자동화 + 관측성**: 단순 모니터링이 아닌, 지능형 탐지 → 자동 분석 → 자동 대응의 사이클

- **관측성 3대 축**: Metrics(무엇이), Logs(왜), Traces(어디서) — 세 가지를 통합해야 AIOps의 기반 완성

---

### 다음 블록 예고

**Block 2: 지능형 분석과 인사이트** — DevOps Guru 심층 분석, 이상 탐지 ML 모델, 실전 데모

<div style="display:flex; gap:16px; margin-top:24px; justify-content:center;">
  <a href="index.html" class="btn btn-sm" style="text-decoration:none;">← 목차로 돌아가기</a>
  <a href="02-intelligent-analysis.html" class="btn btn-primary btn-sm" style="text-decoration:none;">다음: Block 2 →</a>
</div>

:::notes
{timing: 2min}
Block 1의 핵심 내용을 요약합니다. 세 가지 takeaway를 강조하세요.
"첫째, 수동 운영은 더 이상 클라우드 규모를 감당할 수 없습니다."
"둘째, AIOps는 세 가지 요소의 결합입니다. 하나라도 빠지면 효과가 반감됩니다."
"셋째, 관측성이 AIOps의 기반입니다. 데이터 없이는 ML도 자동화도 불가능합니다."
"다음 블록에서는 DevOps Guru를 중심으로 지능형 분석을 깊이 있게 다루겠습니다."
질문을 받거나 잠시 휴식을 가질 수 있습니다.
:::
