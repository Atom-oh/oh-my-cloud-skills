---
remarp: true
block: foundations
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
{timing: 1min}
안녕하세요, AWS Solutions Architect 오준석입니다. 오늘은 AnyCompany 여러분과 함께 AIOps, 즉 AI를 활용한 클라우드 운영 자동화에 대해 깊이 있게 다뤄보겠습니다. 90분 동안 3개 블록으로 나눠서 진행하며, 첫 번째 블록에서는 AIOps의 기반이 되는 관측성 스택을 살펴보겠습니다.
{cue: transition}
먼저 오늘 세션의 전체 아젠다를 확인해 볼까요?
:::

---
<!-- Slide 2: Agenda -->
@type: agenda
@timing: 90min

## 오늘의 아젠다

1. AIOps Foundations & AWS Observability (30분)
2. ML-Powered Operations & Anomaly Detection (30분)
- Break (5분)
3. Implementation Strategies & Best Practices (25분)

> 300 레벨 — 개념보다 실전 중심 | 실시간 Q&A 환영 | 각 블록 후 브레이크

:::notes
{timing: 2min}
오늘 세션은 크게 세 블록으로 구성됩니다. 첫 번째 블록에서는 AIOps의 핵심 기반인 관측성 스택을 다루고, 두 번째 블록에서는 ML 기반 서비스들을 깊이 살펴봅니다. 마지막 블록에서는 AnyCompany 환경에 맞는 실제 구현 전략을 논의하겠습니다.
300레벨 세션인 만큼 기본 개념 설명은 최소화하고, 실제 구성과 운영 경험 중심으로 진행합니다. 궁금한 점은 언제든 질문해 주세요.
{cue: transition}
그럼 AIOps가 정확히 무엇인지부터 정리해 보겠습니다.
:::

---
<!-- Slide 3: What is AIOps -->
@transition: fade

## AIOps란 무엇인가?

::: left
### 정의
**AI for IT Operations** — ML과 빅데이터 분석을 활용하여 IT 운영을 자동화하고 향상시키는 접근법

### 핵심 요소
- **Observe** — 전체 스택 가시성 확보 {.click}
- **Detect** — 이상 징후 자동 탐지 {.click}
- **Diagnose** — 근본 원인 분석 (RCA) {.click}
- **Respond** — 자동화된 대응 및 복구 {.click}
:::

::: right
### Gartner 정의 (2024)
> "AIOps platforms combine big data and ML to automate IT operations processes, including event correlation, anomaly detection, and causality determination."

### 왜 지금 AIOps인가?
- 마이크로서비스 → 복잡성 기하급수적 증가
- 분당 수백만 이벤트 → 사람이 처리 불가
- MTTR 단축 압박 → 수동 분석의 한계
- Gen AI 발전 → 자연어 기반 운영 가능
:::

:::notes
{timing: 3min}
AIOps는 단순한 모니터링 자동화가 아닙니다. Gartner가 정의한 것처럼, 빅데이터와 ML을 결합해서 IT 운영 전체 프로세스를 자동화하는 플랫폼 접근법입니다.

핵심은 네 가지 단계입니다. 먼저 Observe — 전체 인프라와 애플리케이션의 가시성을 확보합니다. 그다음 Detect — ML로 이상 징후를 자동 탐지하고, Diagnose — 근본 원인을 분석하며, Respond — 자동화된 대응까지 수행합니다.

왜 지금 AIOps가 중요한지 생각해 보시면, AnyCompany에서도 마이크로서비스 전환 이후 서비스 간 의존성이 기하급수적으로 늘어났을 겁니다. 분당 수백만 개 이벤트를 사람이 일일이 보는 건 물리적으로 불가능합니다.
{cue: question}
여러분 팀에서 현재 장애 대응 시 MTTR이 어느 정도 되시나요? 보통 30분에서 수 시간이라고 말씀하시는 분이 많은데, AIOps는 이걸 분 단위로 줄이는 것이 목표입니다.
{cue: transition}
AIOps의 기반에는 관측성이 있습니다. 모니터링과 어떻게 다른지 짚어 보겠습니다.
:::

---
<!-- Slide 4: Observability vs Monitoring -->

## Observability vs Monitoring

### Traditional Monitoring
- **Known-unknowns** — 미리 정의한 임계값 기반 알람
- 대시보드 중심, 사후 분석
- "CPU > 80% 이면 알람" → 증상만 탐지

### Modern Observability
- **Unknown-unknowns** — 예상치 못한 문제를 발견하는 능력
- 세 가지 신호(Three Pillars): Metrics, Logs, Traces
- "왜 이 API가 느려졌는지" 역추적 가능

### AIOps가 추가하는 가치
- ML 기반 **이상 탐지** — 시즌별/시간대별 패턴 학습 후 편차 감지
- **이벤트 상관 분석** — 수천 개 알람을 소수의 인시던트로 그룹핑
- **예측** — 리소스 고갈, 장애 전조 사전 경고

:::notes
{timing: 3min}
300레벨이시니 Observability의 기본 개념은 아실 겁니다. 핵심 차이만 짚겠습니다.

전통적 모니터링은 "CPU가 80% 넘으면 알람"처럼 Known-unknown을 다룹니다. 반면 관측성은 "이 API가 왜 갑자기 느려졌는지"를 시스템 외부에서 내부 상태를 추론할 수 있는 능력입니다.

AIOps는 여기에 세 가지를 더합니다. 첫째, ML 기반 이상 탐지 — CloudWatch가 2주간 메트릭 패턴을 학습하고 월요일 오전 트래픽 패턴과 일요일 패턴을 다르게 인식합니다. 둘째, 이벤트 상관 분석 — "ELB 5xx 증가, Lambda Duration 급증, DynamoDB Throttle" 세 알람이 실은 하나의 DynamoDB 용량 부족 때문이라는 걸 자동 파악합니다. 셋째, 예측 — 디스크가 3일 후에 부족해질 것을 사전에 알려줍니다.
{cue: pause}
{cue: transition}
이 세 가지 기능을 AWS에서 어떤 서비스로 구현하는지 봐 보겠습니다.
:::

---
<!-- Slide 5: AWS Observability Stack -->
@type: canvas

## AWS Observability Stack — 전체 구성도

:::canvas
@width: 960
@height: 420

# Data Sources (left column)
box "EC2/EKS\nWorkloads" 40,30 130,50 fill:#1a2744 border:#41B3FF step:0
box "Lambda\nFunctions" 40,100 130,50 fill:#1a2744 border:#41B3FF step:0
box "API Gateway\n& ALB" 40,170 130,50 fill:#1a2744 border:#41B3FF step:0
box "RDS/DynamoDB\nData Stores" 40,240 130,50 fill:#1a2744 border:#41B3FF step:0

# Collection Layer
box "CloudWatch\nAgent" 240,30 130,50 fill:#232f3e border:#FF9900 step:1
box "ADOT\nCollector" 240,100 130,50 fill:#232f3e border:#FF9900 step:1
box "X-Ray\nDaemon" 240,170 130,50 fill:#232f3e border:#FF9900 step:1
box "VPC Flow\nLogs" 240,240 130,50 fill:#232f3e border:#FF9900 step:1

# Arrows: Sources -> Collection
arrow 170,55 240,55 #41B3FF step:1
arrow 170,125 240,125 #41B3FF step:1
arrow 170,195 240,195 #41B3FF step:1
arrow 170,265 240,265 #41B3FF step:1

# Storage & Processing
box "CloudWatch\nMetrics & Logs" 440,30 140,50 fill:#232f3e border:#00E500 step:2
box "Amazon\nManaged\nPrometheus" 440,100 140,55 fill:#232f3e border:#00E500 step:2
box "AWS X-Ray\nTraces" 440,175 140,50 fill:#232f3e border:#00E500 step:2
box "S3 Data Lake\n(Archive)" 440,245 140,50 fill:#232f3e border:#00E500 step:2

# Arrows: Collection -> Storage
arrow 370,55 440,55 #FF9900 step:2
arrow 370,125 440,125 #FF9900 step:2
arrow 370,195 440,195 #FF9900 step:2
arrow 370,265 440,265 #FF9900 step:2

# AI/ML Layer
box "DevOps Guru\nInsights" 650,30 140,50 fill:#161D26 border:#AD5CFF step:3
box "CloudWatch\nAnomaly Detection" 650,100 140,50 fill:#161D26 border:#AD5CFF step:3
box "Amazon\nBedrock (GenAI)" 650,175 140,50 fill:#161D26 border:#AD5CFF step:3
box "Lookout for\nMetrics" 650,245 140,50 fill:#161D26 border:#AD5CFF step:3

# Arrows: Storage -> AI/ML
arrow 580,55 650,55 #00E500 step:3
arrow 580,125 650,125 #00E500 step:3
arrow 580,195 650,195 #00E500 step:3
arrow 580,265 650,265 #00E500 step:3

# Action Layer
box "EventBridge\nAutomation" 850,80 100,55 fill:#161D26 border:#FF5C85 step:4
box "SNS/PagerDuty\nNotification" 850,165 100,55 fill:#161D26 border:#FF5C85 step:4
box "Systems Manager\nRemediation" 850,250 100,55 fill:#161D26 border:#FF5C85 step:4

# Arrows: AI/ML -> Action
arrow 790,55 850,107 #AD5CFF step:4
arrow 790,125 850,107 #AD5CFF step:4
arrow 790,200 850,192 #AD5CFF step:4
arrow 790,270 850,277 #AD5CFF step:4

# Layer Labels
text "Data Sources" 75,310 size:13 color:#41B3FF step:0
text "Collection" 275,310 size:13 color:#FF9900 step:1
text "Storage" 480,310 size:13 color:#00E500 step:2
text "AI/ML" 690,310 size:13 color:#AD5CFF step:3
text "Action" 870,310 size:13 color:#FF5C85 step:4

# Flow direction indicator
text "Observe → Detect → Diagnose → Respond" 380,380 size:15 color:#ffffff step:4
:::

:::notes
{timing: 4min}
이 다이어그램은 AWS에서 AIOps를 구현할 때의 전체 데이터 흐름입니다. 화살표 아래로 하나씩 따라가 보겠습니다.

왼쪽 Data Sources에서 시작합니다. EC2, EKS 워크로드, Lambda, API Gateway, 데이터베이스까지 — AnyCompany의 전체 스택이 여기에 해당합니다.

두 번째 레이어는 Collection입니다. CloudWatch Agent가 시스템 메트릭과 커스텀 메트릭을 수집하고, ADOT(AWS Distro for OpenTelemetry)가 분산 트레이싱 데이터를 수집합니다. 특히 EKS 환경이라면 ADOT이 Prometheus 메트릭까지 한 번에 수집할 수 있어서 효율적입니다.

세 번째는 Storage입니다. CloudWatch Metrics & Logs가 핫 데이터를, AMP(Amazon Managed Prometheus)가 커스텀 메트릭을, X-Ray가 트레이스를, S3가 장기 아카이브를 담당합니다.

네 번째 AI/ML 레이어가 AIOps의 핵심입니다. DevOps Guru가 운영 이상을 탐지하고, CloudWatch Anomaly Detection이 메트릭 이상을 잡고, Bedrock이 Gen AI 기반 분석을 수행합니다.

마지막으로 Action 레이어에서 EventBridge가 자동화 워크플로를 트리거하고, Systems Manager가 자동 복구를 실행합니다.
{cue: question}
AnyCompany에서 현재 이 레이어 중 어디까지 구성되어 있으신가요?
{cue: transition}
이제 각 레이어의 핵심 서비스를 하나씩 살펴보겠습니다.
:::

---
<!-- Slide 6: CloudWatch Deep Dive -->

## CloudWatch — AIOps의 데이터 허브

::: left
### Metrics
- **고해상도 메트릭** — 1초 간격 수집 가능
- **Embedded Metric Format (EMF)** — 구조화된 로그에서 메트릭 자동 추출
- **Metric Math** — 실시간 연산 (에러율 = Errors / Invocations × 100)
- **Contributor Insights** — Top-N 기여자 실시간 분석

### Logs Insights
```
fields @timestamp, @message
| filter @message like /ERROR/
| stats count(*) as errorCount by bin(5m)
| sort errorCount desc
```
:::

::: right
### Anomaly Detection
- 2주간 메트릭 패턴 학습 (시간대, 요일, 계절)
- **Band 모델** — 정상 범위를 밴드로 표현
- 밴드 이탈 시 알람 → 정적 임계값 없이 동적 탐지
- `ANOMALY_DETECTION_BAND(metric, stddev)` 함수

### Cross-Account Observability
- **Monitoring Account** 하나에서 모든 계정 관측
- Organization 전체 로그/메트릭/트레이스 통합
- AnyCompany 멀티 계정 환경에 필수
:::

:::notes
{timing: 3min}
CloudWatch를 단순한 모니터링 도구로 생각하시면 곤란합니다. AIOps 관점에서 CloudWatch는 데이터 허브 역할을 합니다.

Embedded Metric Format은 특히 강력합니다. 로그를 구조화된 JSON으로 보내면 CloudWatch가 자동으로 메트릭을 추출합니다. 커스텀 메트릭을 위해 별도 API 콜이 필요 없으니 비용도 절감됩니다.

Anomaly Detection은 AIOps의 핵심 기능입니다. 정적 임계값 대신 2주간의 패턴을 학습해서 "이 시간대에 이 정도면 비정상"이라고 판단합니다. 예를 들어 월요일 오전 9시의 트래픽과 일요일 새벽 3시의 트래픽은 당연히 다르잖아요. ML 모델이 이런 계절성을 자동 학습합니다.

Cross-Account Observability는 AnyCompany처럼 멀티 계정을 운영하시는 환경에서 필수입니다. 하나의 모니터링 계정에서 전체 Organization의 데이터를 볼 수 있습니다.
{cue: transition}
CloudWatch 단독으로는 부족합니다. OpenTelemetry 기반 수집 체계를 보겠습니다.
:::

---
<!-- Slide 7: ADOT & OpenTelemetry -->

## ADOT — 통합 텔레메트리 수집

::: left
### AWS Distro for OpenTelemetry
- **벤더 중립** — CNCF 표준 기반
- **하나의 에이전트**로 Metrics + Traces + Logs 수집
- EKS DaemonSet 또는 Sidecar 배포
- Kubernetes 메타데이터 자동 태깅 (pod, namespace, node)

### 수집 파이프라인
```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
  prometheus:
    config:
      scrape_configs:
        - job_name: 'k8s-pods'
          kubernetes_sd_configs:
            - role: pod
```
:::

::: right
### Exporters 구성
```yaml
exporters:
  awsxray:
    region: ap-northeast-2
  awsemf:
    namespace: AnyCompany/App
    region: ap-northeast-2
  prometheusremotewrite:
    endpoint: https://aps-workspaces...
    auth:
      authenticator: sigv4auth

service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [awsxray]
    metrics:
      receivers: [otlp, prometheus]
      exporters: [awsemf, prometheusremotewrite]
```

### 핵심 이점
- X-Ray + CloudWatch + AMP에 동시 전송
- 애플리케이션 코드 변경 최소화
:::

:::notes
{timing: 3min}
ADOT는 AWS가 배포하는 OpenTelemetry 디스트리뷰션입니다. 가장 큰 장점은 하나의 에이전트로 메트릭, 트레이스, 로그를 모두 수집하고 여러 백엔드로 동시에 보낼 수 있다는 점입니다.

EKS에서는 DaemonSet으로 배포하면 각 노드의 모든 Pod에서 텔레메트리를 수집합니다. 왼쪽의 Receivers 설정을 보시면, OTLP 프로토콜로 트레이스를 받고, Prometheus 프로토콜로 메트릭도 스크래핑합니다.

오른쪽 Exporters에서는 X-Ray, CloudWatch EMF, AMP 세 곳으로 동시에 데이터를 보냅니다. 이렇게 하면 트레이스는 X-Ray에서, 메트릭은 CloudWatch와 AMP 양쪽에서, 로그는 CloudWatch Logs에서 분석할 수 있습니다.

AnyCompany에서 이미 Prometheus를 쓰고 계시다면 ADOT의 Prometheus receiver로 기존 설정을 그대로 재활용할 수 있습니다.
{cue: transition}
수집 체계를 갖췄으니, 이 데이터를 어떻게 시각화하고 분석하는지 보겠습니다.
:::

---
<!-- Slide 8: Amazon Managed Grafana -->
@type: tabs

## AMP & AMG — 시각화와 분석

::: tab "Amazon Managed Prometheus"
### AMP 핵심 기능
- **완전 관리형** — PromQL 호환, 스케일링/패치 자동
- **150일 보존** — 장기 트렌드 분석 가능
- **Cross-region replication** — DR 지원
- **IAM 인증** — Prometheus 네이티브 인증 대비 보안 강화

### 비용 고려
| 항목 | 가격 |
|------|------|
| 샘플 수집 | $0.003/1K samples |
| 쿼리 처리 | $0.10/10억 samples |
| 스토리지 | $0.03/GB/month |

> **팁**: cardinality 관리가 비용의 핵심. label 조합이 100만 개 넘으면 비용 급증
:::

::: tab "Amazon Managed Grafana"
### AMG로 AIOps 대시보드 구축
- **다중 데이터소스**: CloudWatch, AMP, X-Ray, Athena
- **Alerting**: Grafana Alerting → SNS → PagerDuty/Slack
- **ML Plugin**: Prophet 기반 메트릭 예측 시각화

### 권장 대시보드 구성
1. **Overview** — 서비스 헬스맵, 핵심 SLI/SLO
2. **Deep Dive** — 서비스별 상세 메트릭 (p99, error rate)
3. **AIOps** — Anomaly Detection 밴드, DevOps Guru 인사이트
4. **Cost** — 리소스 사용량 vs 비용 트렌드
:::

::: tab "PromQL AIOps 패턴"
### 이상 탐지 PromQL 예시
```promql
# SLO burn rate (1시간 윈도우)
(
  sum(rate(http_requests_total{code=~"5.."}[1h]))
  / sum(rate(http_requests_total[1h]))
) / 0.001 > 1

# P99 latency 이동 편차
histogram_quantile(0.99,
  sum(rate(http_request_duration_seconds_bucket[5m]))
  by (le, service)
) > 2 * histogram_quantile(0.99,
  sum(rate(http_request_duration_seconds_bucket[1h]))
  by (le, service)
)

# CPU throttling 비율
sum(rate(container_cpu_cfs_throttled_periods_total[5m]))
by (pod) /
sum(rate(container_cpu_cfs_periods_total[5m]))
by (pod) > 0.25
```
:::

:::notes
{timing: 4min}
AMP와 AMG는 Prometheus/Grafana 오픈소스 생태계를 완전 관리형으로 제공합니다.

AMP는 PromQL 100% 호환이고, 150일까지 데이터를 보존합니다. 비용 측면에서 주의할 점은 cardinality입니다. label 조합이 많아지면 비용이 급증하니, 불필요한 high-cardinality label은 drop하는 relabeling 설정이 필수입니다.

AMG에서는 여러 데이터소스를 하나의 대시보드에 통합할 수 있습니다. CloudWatch 메트릭과 AMP의 커스텀 메트릭, X-Ray 트레이스를 하나의 화면에서 상관 분석할 수 있는 게 큰 강점입니다.

세 번째 탭의 PromQL 패턴은 AIOps에서 자주 사용하는 쿼리입니다. SLO burn rate 알림은 구글 SRE 책에서 제안하는 방식으로, 에러 예산 소진 속도를 모니터링합니다. P99 이동 편차는 현재 5분 레이턴시가 1시간 평균의 2배를 넘으면 알리는 방식입니다.
{cue: question}
AnyCompany에서 현재 SLO/SLI를 정량적으로 관리하고 계신가요? AIOps 도입의 출발점이 SLO 정의입니다.
{cue: transition}
이제 데이터 수집부터 시각화까지의 파이프라인 전체 흐름을 애니메이션으로 정리해 보겠습니다.
:::

---
<!-- Slide 9: Data Pipeline Flow -->
@type: canvas

## AIOps 데이터 파이프라인 — 실시간 흐름

:::canvas
@width: 960
@height: 380

# Application Layer
box "App Pod\n(OTel SDK)" 30,20 120,50 fill:#1a2744 border:#41B3FF step:0
box "Sidecar\nProxy" 30,90 120,50 fill:#1a2744 border:#41B3FF step:0
box "System\nMetrics" 30,160 120,50 fill:#1a2744 border:#41B3FF step:0

# ADOT Collector
box "ADOT Collector\n(DaemonSet)" 230,70 140,70 fill:#232f3e border:#FF9900 step:1
text "Receive → Process → Export" 300,160 size:11 color:#FF9900 step:1

# Arrows to ADOT
arrow 150,45 230,90 #41B3FF step:1
arrow 150,115 230,105 #41B3FF step:1
arrow 150,185 230,120 #41B3FF step:1

# Destinations - Fan out
box "CloudWatch\nLogs" 450,10 120,45 fill:#232f3e border:#00E500 step:2
box "CloudWatch\nMetrics" 450,70 120,45 fill:#232f3e border:#00E500 step:2
box "X-Ray\nTraces" 450,130 120,45 fill:#232f3e border:#00E500 step:2
box "AMP\nMetrics" 450,190 120,45 fill:#232f3e border:#00E500 step:2
box "S3\nArchive" 450,250 120,45 fill:#232f3e border:#00E500 step:2

# Fan-out arrows
arrow 370,90 450,32 #FF9900 step:2
arrow 370,100 450,92 #FF9900 step:2
arrow 370,110 450,152 #FF9900 step:2
arrow 370,120 450,212 #FF9900 step:2
arrow 370,130 450,272 #FF9900 step:2

# Analysis Layer
box "Anomaly\nDetection" 650,30 120,50 fill:#161D26 border:#AD5CFF step:3
box "Logs\nInsights" 650,100 120,50 fill:#161D26 border:#AD5CFF step:3
box "DevOps\nGuru" 650,170 120,50 fill:#161D26 border:#AD5CFF step:3

# Arrows to Analysis
arrow 570,32 650,45 #00E500 step:3
arrow 570,92 650,55 #00E500 step:3
arrow 570,92 650,125 #00E500 step:3
arrow 570,152 650,195 #00E500 step:3

# Automation
box "EventBridge\n→ Lambda\n→ Remediation" 840,80 110,70 fill:#161D26 border:#FF5C85 step:4

arrow 770,55 840,100 #AD5CFF step:4
arrow 770,125 840,115 #AD5CFF step:4
arrow 770,195 840,130 #AD5CFF step:4

# Labels
text "수집 (< 1s)" 290,340 size:12 color:#FF9900 step:1
text "저장 & 인덱싱" 480,340 size:12 color:#00E500 step:2
text "ML 분석 (< 5min)" 680,340 size:12 color:#AD5CFF step:3
text "자동 대응" 865,340 size:12 color:#FF5C85 step:4
:::

:::notes
{timing: 3min}
이 Canvas는 실제 데이터가 흐르는 경로를 step별로 보여줍니다.

Step 0에서 애플리케이션 Pod는 OTel SDK로 트레이스를, Sidecar Proxy가 서비스 메시 메트릭을, 시스템 레벨에서 CPU/Memory 메트릭을 생성합니다.

Step 1에서 ADOT Collector가 이 세 종류 데이터를 모두 수집합니다. DaemonSet으로 각 노드에 하나씩 배포되어 있으니 네트워크 홉이 최소화됩니다. 수집 지연은 1초 미만입니다.

Step 2에서 팬아웃됩니다. 로그는 CloudWatch Logs로, 메트릭은 CloudWatch와 AMP 양쪽으로, 트레이스는 X-Ray로, 장기 보관은 S3로 갑니다. 이 팬아웃이 ADOT의 핵심 가치입니다.

Step 3에서 ML 분석이 시작됩니다. CloudWatch Anomaly Detection이 메트릭 이상을, Logs Insights가 에러 패턴을, DevOps Guru가 운영 이상을 각각 탐지합니다. 분석 지연은 보통 5분 이내입니다.

Step 4에서 탐지된 이상이 EventBridge를 통해 Lambda를 트리거하고, Lambda가 자동 복구 작업을 실행합니다.
{cue: transition}
Block 1의 핵심 내용을 정리해 보겠습니다.
:::

---
<!-- Slide 10: Block 1 Key Takeaways -->
@transition: fade

## Block 1 — Key Takeaways

::: left
### 핵심 포인트
- **AIOps = Observe + Detect + Diagnose + Respond** 4단계 자동화 {.click}
- **Three Pillars** — Metrics, Logs, Traces 통합 수집이 전제 조건 {.click}
- **ADOT** — 벤더 중립 통합 수집기, EKS 환경의 표준 {.click}
- **CloudWatch Anomaly Detection** — 정적 임계값의 대안, ML 기반 밴드 모델 {.click}
- **AMP + AMG** — 오픈소스 호환 관리형 분석/시각화 스택 {.click}
:::

::: right
### AnyCompany 체크포인트
- [ ] CloudWatch Agent 전체 워크로드 배포 여부
- [ ] ADOT 또는 기존 Prometheus 수집 파이프라인 존재
- [ ] Cross-Account Observability 설정 유무
- [ ] SLI/SLO 정량적 정의 및 대시보드 운영
- [ ] 로그 보존 정책 및 아카이빙 전략

### 다음 블록 예고
Block 2에서는 이 데이터를 활용하는 **ML 서비스들** — DevOps Guru, CodeGuru, Lookout for Metrics, 그리고 **Gen AI 기반 운영**을 다룹니다.
:::

:::notes
{timing: 2min}
Block 1을 정리하겠습니다.

AIOps는 네 단계입니다 — 관측, 탐지, 진단, 대응. 오늘 이 첫 번째 블록에서는 관측 단계, 즉 데이터를 어떻게 수집하고 저장하는지를 다뤘습니다.

AnyCompany에서 바로 확인해 보실 수 있는 체크리스트를 오른쪽에 정리했습니다. 특히 SLI/SLO 정의가 없으시다면, AIOps 도입 전에 이걸 먼저 정의하시는 것을 강력히 추천합니다. 이상 탐지는 "정상이 뭔지" 정의되어야 의미가 있으니까요.

5분 브레이크 후 Block 2에서 ML 서비스들을 본격적으로 살펴보겠습니다.
{cue: transition}
5분 쉬었다 오겠습니다!
:::

---
<!-- Slide 11: Thank You Block 1 -->
@type: thankyou

## Block 1 완료

AIOps Foundations & AWS Observability

:::notes
{timing: 0.5min}
Block 1이 끝났습니다. 5분 브레이크 후 Block 2를 시작하겠습니다.
:::
