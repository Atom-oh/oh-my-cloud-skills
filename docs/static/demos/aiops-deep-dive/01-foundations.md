---
remarp: true
block: foundations
---

@type: cover
@background: ../common/pptx-theme/images/Picture_13.png
@badge: ../common/pptx-theme/images/Picture_8.png

# AIOps on AWS
AI 기반 클라우드 운영 자동화 Deep Dive

@speaker: Junseok Oh
@title: Sr. Solutions Architect, AWS
@company: AnyCompany Technical Session

:::notes
{timing: 1min}
안녕하세요, AWS Solutions Architect 오준석입니다. 오늘은 AIOps — 즉, AI와 머신러닝을 활용한 클라우드 운영 자동화에 대해 깊이 있게 다뤄보겠습니다.

이 세션은 90분간 3개 블록으로 진행됩니다. 첫 번째 블록에서는 AIOps의 기반과 왜 지금 필요한지, 두 번째에서는 AWS 서비스 기반의 핵심 아키텍처, 마지막으로 실제 구현 전략과 Best Practices를 살펴보겠습니다.

{cue: question} 혹시 현재 운영 환경에서 ML 기반 모니터링이나 자동화된 이상 탐지를 사용하고 계신 분 계신가요? 오늘 세션이 끝나면 여러분의 운영 환경에 바로 적용할 수 있는 구체적인 아키텍처와 패턴을 가져가실 수 있습니다.

{cue: transition} 먼저 AIOps가 정확히 무엇이고, 왜 지금 이 시점에 주목해야 하는지부터 시작하겠습니다.
:::

---

## Agenda

- **Block 1** — AIOps 기반과 왜 지금인가 (25 min) {.click}
- **Block 2** — AIOps 핵심 아키텍처와 AWS 서비스 (30 min) {.click}
- *5분 휴식* {.click}
- **Block 3** — 구현 전략과 Best Practices (30 min) {.click}

:::notes
{timing: 1min}
오늘 세션의 전체 구성입니다. 총 90분이며, 각 블록 사이에 질문 시간을 드리겠습니다.

첫 번째 블록에서는 AIOps의 정의와 현재 운영 환경의 문제점, 그리고 왜 지금 AIOps가 필요한지를 다룹니다. 두 번째 블록에서는 AWS 서비스를 중심으로 한 AIOps 아키텍처를 깊이 있게 살펴보고, 마지막 블록에서는 실제 구현 로드맵과 성공 사례를 공유합니다.

300레벨 세션답게 기초 설명은 최소화하고, 아키텍처 패턴과 구현 세부사항에 집중하겠습니다.

{cue: transition} 그럼 AIOps가 무엇인지부터 명확히 정의해보겠습니다.
:::

---

## AIOps란 무엇인가?

:::click
> **AIOps** = Artificial Intelligence for IT Operations
> Gartner가 2017년 정의한 용어로, ML/AI를 IT 운영에 적용하여
> **이상 탐지, 이벤트 상관관계 분석, 자동 복구**를 수행하는 방법론
:::

:::click
::: left
### 전통적 운영
- 임계값 기반 알림 (정적 threshold)
- 수동 로그 분석
- 경험 기반 트러블슈팅
- 사후 대응 (reactive)
:::

::: right
### AIOps 운영
- ML 기반 이상 탐지 (동적 baseline)
- 자동화된 로그 패턴 분석
- 데이터 기반 근본 원인 분석
- 예측 및 예방 (proactive)
:::
:::

:::notes
{timing: 3min}
AIOps는 Gartner가 2017년에 처음 정의한 개념입니다. 핵심은 단순합니다 — 머신러닝과 AI를 IT 운영에 적용하는 것입니다.

왼쪽의 전통적 운영을 보시면, CPU 80% 넘으면 알림, 에러 로그 직접 grep으로 검색, 시니어 엔지니어의 경험에 의존하는 트러블슈팅 — 이런 패턴이 대부분입니다. 문제가 발생한 후에야 대응하는 reactive 방식이죠.

오른쪽의 AIOps 운영에서는 ML이 정상 패턴을 학습하고, 그 baseline에서 벗어나면 알림을 보냅니다. 로그 패턴을 자동으로 클러스터링하고, 여러 이벤트 간의 상관관계를 분석해서 근본 원인을 찾아냅니다. 가장 중요한 차이는 proactive — 문제가 발생하기 전에 예측하고 예방한다는 점입니다.

{cue: question} 실무에서 흔히 겪는 상황을 생각해보세요. 새벽 3시에 CPU 알림이 왔는데, 실제로는 배치 잡 때문에 매일 그 시간에 올라가는 정상적인 패턴이었던 적 있으시죠? AIOps는 이런 false positive를 줄여줍니다.

{cue: transition} 그런데 왜 하필 지금 AIOps가 중요해졌을까요?
:::

---

@type: content

## 왜 지금 AIOps인가?

::: left
### 운영 복잡성 폭발

- 마이크로서비스 아키텍처 → 서비스 수 10x 증가 {.click}
- 컨테이너/서버리스 → 수명 짧은 리소스 급증 {.click}
- 멀티 리전, 하이브리드 클라우드 {.click}
- 하루 수백 번 배포 (CI/CD) {.click}
:::

::: right
### 데이터 볼륨 폭발

- 평균 기업: **하루 100TB+** 운영 데이터 {.click}
- 메트릭, 로그, 트레이스, 이벤트 {.click}
- 사람이 처리할 수 있는 한계 초과 {.click}
- **MTTR 감소 압박**: 99.99% SLA = 연 52분 다운타임 {.click}
:::

:::notes
{timing: 3min}
AIOps가 지금 이 시점에 필수가 된 이유는 두 가지입니다.

첫째, 운영 복잡성이 폭발적으로 증가했습니다. 모놀리스에서 마이크로서비스로 전환하면서 관리해야 할 서비스 수가 10배 이상 늘었습니다. 컨테이너와 서버리스는 수명이 몇 분에 불과한 리소스를 수천 개 만들어냅니다. 거기에 멀티 리전, 하이브리드 클라우드까지 더하면 사람이 전체 그림을 파악하는 것 자체가 불가능해집니다.

둘째, 데이터 볼륨입니다. 평균적인 기업 환경에서 하루에 100테라바이트 이상의 운영 데이터가 생성됩니다. 메트릭, 로그, 트레이스, 이벤트 — 이걸 사람이 다 보는 건 물리적으로 불가능합니다.

특히 99.99% SLA를 약속했다면 연간 허용 다운타임이 52분밖에 안 됩니다. 장애 감지부터 복구까지의 MTTR을 분 단위로 줄여야 하는데, 이건 자동화 없이는 달성할 수 없습니다.

{cue: transition} 이런 배경을 이해하셨다면, 현재 많은 조직이 겪고 있는 운영 과제를 구체적으로 살펴보겠습니다.
:::


:::css
<body>
  fontSize: 29px
</body>
:::
---

## 현재 운영 팀의 과제

> "알림이 하루 1,000개 이상 오는데, 진짜 중요한 건 5개도 안 됩니다.
> 나머지는 noise입니다." {.click}

:::click
- **Alert Fatigue**: 과도한 알림 → 진짜 문제 놓침 {.click}
- **Siloed Data**: 메트릭/로그/트레이스가 각각 다른 도구 {.click}
- **Manual Correlation**: "이 에러가 저 배포 때문인가?" — 수동 추적 {.click}
- **Tribal Knowledge**: 핵심 지식이 특정 엔지니어 머릿속에만 존재 {.click}
- **Reactive Posture**: 항상 불끄기 모드, 예방 불가 {.click}
:::

:::notes
{timing: 3min}
이 인용문은 실제로 많은 운영 팀에서 공통적으로 하는 이야기입니다. 하루 천 개 이상의 알림 중 실제 조치가 필요한 건 5개 미만입니다. 이것이 Alert Fatigue의 현실입니다.

Siloed Data도 큰 문제입니다. CloudWatch에서 메트릭을 보고, Elasticsearch에서 로그를 검색하고, X-Ray에서 트레이스를 추적하는데, 이 세 가지를 연결해서 보는 게 쉽지 않습니다. 그래서 "이 에러가 30분 전 배포 때문인가?"를 확인하려면 수동으로 여러 도구를 왔다갔다해야 합니다.

가장 위험한 건 Tribal Knowledge입니다. "이 서비스가 이상하면 시니어 엔지니어 김 과장님한테 물어봐" — 이런 상황이 흔하죠? 그 사람이 휴가가거나 퇴사하면 어떻게 될까요?

{cue: pause} 이 다섯 가지 과제 중 여러분 조직에서 가장 심각한 것은 어떤 건가요?

{cue: transition} AIOps는 이 모든 과제를 ML과 자동화로 해결하려는 접근입니다. 이제 AIOps의 핵심 기능을 살펴보겠습니다.
:::

---

@type: canvas
@canvas-id: aiops-pillars

## AIOps 4대 핵심 기능

:::canvas
box collect "Data Collection & Aggregation" at 50,60 size 170,70 color #41B3FF step 1
box detect "Anomaly Detection" at 270,60 size 170,70 color #AD5CFF step 2
box correlate "Event Correlation & Root Cause" at 490,60 size 170,70 color #00E500 step 3
box automate "Automated Remediation" at 710,60 size 170,70 color #FF9900 step 4

arrow collect -> detect "" step 2
arrow detect -> correlate "" step 3
arrow correlate -> automate "" step 4

box metrics "Metrics" at 10,190 size 80,40 color #41B3FF step 1
box logs "Logs" at 95,190 size 80,40 color #41B3FF step 1
box traces "Traces" at 180,190 size 80,40 color #41B3FF step 1

arrow metrics -> collect "" step 1
arrow logs -> collect "" step 1
arrow traces -> collect "" step 1

box ml "ML Models / Baseline Learning" at 280,190 size 160,45 color #AD5CFF step 2
arrow ml -> detect "" step 2

box topology "Service Topology / Dependency Map" at 490,190 size 170,45 color #00E500 step 3
arrow topology -> correlate "" step 3

box runbook "Runbook Automation" at 710,190 size 170,45 color #FF9900 step 4
arrow runbook -> automate "" step 4
:::

:::notes
{timing: 3min}
AIOps의 네 가지 핵심 기능을 단계별로 살펴보겠습니다. 화살표 키로 각 단계를 하나씩 확인하실 수 있습니다.

첫 번째, Data Collection & Aggregation — 메트릭, 로그, 트레이스를 한곳에 수집하고 정규화합니다. 데이터가 사일로에 있으면 AI가 패턴을 찾을 수 없습니다.

두 번째, Anomaly Detection — ML 모델이 정상 패턴의 baseline을 학습하고, 이 baseline에서 벗어나는 이상 징후를 탐지합니다. 정적 임계값이 아닌 동적 baseline이 핵심입니다.

세 번째, Event Correlation & Root Cause — 수천 개의 이벤트 중 관련된 것들을 묶고, 서비스 토폴로지 기반으로 근본 원인을 추적합니다. "로드밸런서 5xx 증가"와 "백엔드 메모리 부족"이 같은 사건임을 자동으로 연결합니다.

네 번째, Automated Remediation — 확인된 문제에 대해 사전 정의된 Runbook을 자동 실행합니다. 사람 개입 없이 스케일 아웃, 재시작, 롤백 등을 수행합니다.

{cue: transition} 이 네 기능이 조직에서 어느 수준까지 적용되어 있는지 판단하는 성숙도 모델을 보겠습니다.
:::

---

## AIOps 성숙도 모델

| Level | 단계 | 특징 | AWS 서비스 예시 |
|-------|------|------|----------------|
| **L1** | Reactive Monitoring | 정적 임계값, 수동 대응 | CloudWatch Alarms |
| **L2** | Proactive Detection | ML 이상 탐지, 자동 알림 | CloudWatch Anomaly Detection |
| **L3** | Intelligent Analysis | 이벤트 상관분석, 근본원인 추적 | DevOps Guru, AI Operations |
| **L4** | Automated Response | 자동 복구, 예측 스케일링 | SSM Automation + EventBridge |
| **L5** | Autonomous Ops | 자율 운영, 지속 최적화 | Amazon Q + Bedrock Agents |

{.click}

:::click
> **현실**: 대부분 조직은 L1~L2 — 오늘 세션 목표는 **L3~L4 달성** 로드맵 제공
:::

:::notes
{timing: 3min}
AIOps 성숙도를 5단계로 나눠봤습니다.

Level 1은 대부분의 조직이 현재 있는 단계입니다. CPU 80%면 알림, 디스크 90%면 알림 — 이런 정적 임계값 기반 모니터링입니다.

Level 2는 CloudWatch Anomaly Detection처럼 ML이 정상 패턴을 학습해서 동적으로 이상을 탐지하는 단계입니다. 이미 AWS에서 바로 사용할 수 있습니다.

Level 3가 오늘 핵심적으로 다룰 내용입니다. DevOps Guru가 여러 서비스의 이벤트를 상관 분석해서 "이 문제의 근본 원인은 X입니다"라고 알려주는 단계입니다.

Level 4는 SSM Automation과 EventBridge를 결합해서 "이 문제가 감지되면 자동으로 이 Runbook을 실행해라"까지 구현하는 단계입니다.

Level 5는 Amazon Q Developer와 Bedrock Agent를 활용한 자율 운영인데, 이건 아직 발전 중인 영역입니다.

{cue: pause} 여러분 조직은 현재 어느 레벨에 있다고 생각하시나요?

오늘 세션의 목표는 Level 3~4를 구현하는 구체적인 아키텍처와 로드맵을 제공하는 것입니다.

{cue: transition} 마지막으로 AWS AIOps 에코시스템을 한눈에 정리하고 이 블록을 마무리하겠습니다.
:::

---

@type: canvas
@canvas-id: aws-aiops-ecosystem

## AWS AIOps 에코시스템

:::canvas
box cw "Amazon CloudWatch" at 50,15 size 150,45 color #41B3FF step 1
box xray "AWS X-Ray" at 230,15 size 150,45 color #41B3FF step 1
box ct "AWS CloudTrail" at 410,15 size 150,45 color #41B3FF step 1
box config "AWS Config" at 590,15 size 150,45 color #41B3FF step 1

box label1 "Collect & Observe" at 310,68 size 180,22 color #41B3FF step 1

box devguru "Amazon DevOps Guru" at 150,100 size 170,45 color #AD5CFF step 2
box cw_ai "CW Anomaly Detection" at 420,100 size 170,45 color #AD5CFF step 2

box label2 "Analyze & Detect" at 310,153 size 180,22 color #AD5CFF step 2

box codeguru "Amazon CodeGuru" at 50,185 size 150,45 color #00E500 step 3
box q_dev "Amazon Q Developer" at 230,185 size 150,45 color #00E500 step 3
box bedrock "Amazon Bedrock" at 410,185 size 150,45 color #00E500 step 3
box health "AWS Health" at 590,185 size 150,45 color #00E500 step 3

box label3 "Intelligence & Action" at 310,238 size 180,22 color #00E500 step 3

box eb "Amazon EventBridge" at 150,270 size 170,45 color #FF9900 step 4
box ssm "AWS Systems Manager" at 420,270 size 170,45 color #FF9900 step 4

box label4 "Automate & Remediate" at 310,323 size 180,22 color #FF9900 step 4

arrow cw -> devguru "" step 2
arrow xray -> devguru "" step 2
arrow ct -> cw_ai "" step 2
arrow devguru -> eb "" step 4
arrow cw_ai -> eb "" step 4
arrow eb -> ssm "" step 4
:::

:::notes
{timing: 3min}
AWS AIOps 에코시스템을 4개 레이어로 정리했습니다.

최상위 Collect & Observe 레이어에는 CloudWatch, X-Ray, CloudTrail, AWS Config가 있습니다. 이 서비스들이 메트릭, 트레이스, API 호출 기록, 리소스 변경 사항을 수집합니다.

두 번째 Analyze & Detect 레이어에서 DevOps Guru와 CloudWatch Anomaly Detection이 ML 기반 분석을 수행합니다. DevOps Guru는 특히 여러 서비스의 데이터를 통합 분석해서 인사이트를 제공합니다.

세 번째 Intelligence & Action 레이어에는 CodeGuru가 코드 레벨 성능 분석을, Amazon Q Developer가 자연어 기반 운영 지원을, Bedrock가 커스텀 AI 에이전트 구축을 지원합니다.

마지막 Automate & Remediate 레이어에서 EventBridge가 이벤트를 라우팅하고, Systems Manager가 자동 복구 작업을 실행합니다.

다음 블록에서 이 서비스들의 구체적인 아키텍처와 연동 방법을 깊이 있게 다루겠습니다.

{cue: transition} 이것으로 첫 번째 블록을 마무리하겠습니다. 핵심 내용을 정리해보겠습니다.
:::

---

## Block 1 — Key Takeaways

:::click
**AIOps = ML/AI + IT Operations**
정적 임계값에서 동적 baseline 기반 운영으로의 전환
:::

:::click
**4대 핵심 기능**: 수집 → 탐지 → 상관분석 → 자동복구
각 단계가 연결되어야 진정한 AIOps
:::

:::click
**성숙도 L3~L4가 현실적 목표**
AWS 서비스만으로 구현 가능 — 다음 블록에서 구체적으로!
:::

:::click
> 5분 휴식 후 Block 2에서 AWS 서비스 기반 아키텍처를 상세히 다룹니다
:::

:::notes
{timing: 2min}
첫 번째 블록의 핵심을 세 가지로 정리하겠습니다.

첫째, AIOps는 ML과 AI를 IT 운영에 적용하는 것입니다. 가장 중요한 변화는 정적 임계값에서 동적 baseline으로의 전환입니다.

둘째, AIOps의 네 기능 — 수집, 탐지, 상관분석, 자동복구 — 이 네 단계가 파이프라인으로 연결되어야 합니다. 어느 한 단계만 구현하면 효과가 제한적입니다.

셋째, 대부분 조직이 L1~L2에 있는데, L3~L4까지는 AWS 네이티브 서비스만으로 달성 가능합니다. 다음 블록에서 구체적인 아키텍처를 보여드리겠습니다.

{cue: pause} 5분 휴식하겠습니다. 질문 있으신 분은 이 시간에 편하게 물어봐 주세요.
:::
