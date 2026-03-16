---
remarp: true
block: implementation
---

@type: cover
@background: ../common/pptx-theme/images/Picture_13.png
@badge: ../common/pptx-theme/images/Picture_8.png

# AIOps on AWS
구현 전략과 Best Practices

@speaker: Junseok Oh
@title: Sr. Solutions Architect, AWS
@company: AnyCompany Technical Session

:::notes
{timing: 1min}
마지막 블록을 시작하겠습니다. 이번 블록에서는 앞서 다룬 아키텍처를 실제로 어떻게 단계적으로 구현하는지, 그리고 성공적인 AIOps 도입을 위한 Best Practices를 다루겠습니다.

{cue: transition} 먼저 AIOps 구현 로드맵부터 보겠습니다.
:::

---

@type: timeline

## AIOps 구현 로드맵 — Overview

### Phase 1: Foundation (M1-2)
Observability Pipeline 구축
ADOT + CloudWatch 통합 수집, SLI/SLO 정의

### Phase 2: Detection (M3-4)
ML 기반 이상 탐지 활성화
DevOps Guru, Anomaly Detection, Alert 최적화

### Phase 3: Automation (M5-6)
자동 복구 파이프라인 구현
EventBridge → SSM Runbook, Human-in-the-Loop → Full Auto

### Phase 4: Optimization (M7+)
지능형 운영 고도화
Bedrock Agent PoC, 피드백 루프, 비용 최적화

:::notes
{timing: 2min}
AIOps 구현은 빅뱅이 아닌 단계적 접근이 핵심입니다. 이 타임라인은 4단계 로드맵의 전체 흐름을 보여줍니다. ↑↓ 키로 각 Phase를 하나씩 살펴보겠습니다.

Phase 1에서 데이터 수집 파이프라인을 제대로 구축하는 것이 가장 중요합니다. Phase 2에서 ML 기반 이상 탐지를, Phase 3에서 자동 복구를, Phase 4에서 Bedrock Agent를 활용한 지능형 운영을 구현합니다.

{cue: transition} 이제 각 Phase의 세부 구성요소를 다이어그램으로 살펴보겠습니다.
:::

---

@type: canvas
@canvas-id: implementation-roadmap

## AIOps 구현 로드맵 — Detail

:::canvas
box phase1 "Phase 1: Foundation (M1-2)" at 20,60 size 180,70 color #41B3FF step 1
box phase2 "Phase 2: Detection (M3-4)" at 240,60 size 180,70 color #AD5CFF step 2
box phase3 "Phase 3: Automation (M5-6)" at 460,60 size 180,70 color #00E500 step 3
box phase4 "Phase 4: Optimization (M7+)" at 680,60 size 180,70 color #FF9900 step 4

arrow phase1 -> phase2 "" step 2
arrow phase2 -> phase3 "" step 3
arrow phase3 -> phase4 "" step 4

box p1a "Observability Pipeline" at 20,170 size 180,35 color #41B3FF step 1
box p1b "ADOT + CW 통합 수집" at 20,215 size 180,35 color #41B3FF step 1
box p1c "SLI/SLO 정의" at 20,260 size 180,35 color #41B3FF step 1

box p2a "DevOps Guru 활성화" at 240,170 size 180,35 color #AD5CFF step 2
box p2b "Anomaly Detection 적용" at 240,215 size 180,35 color #AD5CFF step 2
box p2c "Alert 최적화" at 240,260 size 180,35 color #AD5CFF step 2

box p3a "EventBridge Rule 설정" at 460,170 size 180,35 color #00E500 step 3
box p3b "SSM Runbook 자동 복구" at 460,215 size 180,35 color #00E500 step 3
box p3c "Human -> Full Auto" at 460,260 size 180,35 color #00E500 step 3

box p4a "Bedrock Agent PoC" at 680,170 size 180,35 color #FF9900 step 4
box p4b "피드백 루프 / 모델 개선" at 680,215 size 180,35 color #FF9900 step 4
box p4c "비용 최적화 & 확장" at 680,260 size 180,35 color #FF9900 step 4
:::

:::notes
{timing: 3min}
AIOps 구현은 빅뱅이 아닌 단계적 접근이 핵심입니다. 4단계 로드맵을 제안합니다.

Phase 1은 Foundation입니다. 1~2개월 동안 관측성 파이프라인을 구축합니다. ADOT Collector를 배포하고, CloudWatch에 메트릭/로그/트레이스를 통합 수집합니다. 이 단계에서 SLI와 SLO를 정의하는 것이 중요합니다. "우리 서비스의 정상이란 무엇인가?"를 데이터로 정의해야 이상을 탐지할 수 있습니다.

Phase 2는 Detection입니다. 3~4개월차에 DevOps Guru를 활성화하고, 핵심 메트릭에 Anomaly Detection을 적용합니다. 이 단계의 핵심 작업은 Alert 최적화입니다. 기존 정적 알림을 ML 기반으로 전환하면서 false positive를 줄여나갑니다.

Phase 3는 Automation입니다. 5~6개월차에 EventBridge와 SSM으로 자동 복구를 구현합니다. 반드시 Human Approval 단계부터 시작하세요. 자동 분석 → 사람 승인 → 자동 실행을 거쳐 신뢰가 쌓이면 완전 자동화로 전환합니다.

Phase 4는 Optimization입니다. 7개월차 이후에 Bedrock Agent PoC를 시작하고, 피드백 루프로 모델을 개선합니다.

{cue: question} 이 로드맵에서 가장 시간이 오래 걸리는 단계가 어딘지 아시나요? Phase 1입니다. 데이터 수집 파이프라인을 제대로 구축하는 것이 가장 중요하고 가장 시간이 걸립니다.

{cue: transition} Phase 1의 구체적인 구현을 살펴보겠습니다.
:::

---

## Phase 1: 관측성 파이프라인 구축

@type: tabs

::: tab "EKS 환경"
### EKS 관측성 구성
```yaml
# ADOT Collector DaemonSet
apiVersion: opentelemetry.io/v1alpha1
kind: OpenTelemetryCollector
metadata:
  name: adot-collector
spec:
  mode: daemonset
  config: |
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
      prometheus:
        config:
          scrape_configs:
            - job_name: 'kubernetes-pods'
              kubernetes_sd_configs:
                - role: pod
    processors:
      batch:
        timeout: 10s
      resourcedetection:
        detectors: [eks]
    exporters:
      awsxray: {}
      awsemf:
        namespace: ContainerInsights
        log_group_name: '/aws/eks/cluster/performance'
      awscloudwatchlogs:
        log_group_name: '/aws/eks/cluster/application'
    service:
      pipelines:
        traces:
          receivers: [otlp]
          processors: [batch, resourcedetection]
          exporters: [awsxray]
        metrics:
          receivers: [otlp, prometheus]
          processors: [batch]
          exporters: [awsemf]
```
:::

::: tab "Lambda 환경"
### Lambda 관측성 구성
```yaml
# SAM Template
Resources:
  MyFunction:
    Type: AWS::Serverless::Function
    Properties:
      Runtime: python3.12
      Layers:
        # ADOT Lambda Layer
        - !Sub arn:aws:lambda:${AWS::Region}:
            901920570463:layer:
            aws-otel-python-amd64-ver-1-25-0:1
      Environment:
        Variables:
          AWS_LAMBDA_EXEC_WRAPPER:
            /opt/otel-instrument
          OTEL_SERVICE_NAME: my-service
          OTEL_PROPAGATORS: xray
      Tracing: Active
      # Powertools for structured logging
      # pip install aws-lambda-powertools
```

```python
from aws_lambda_powertools import Logger, Tracer, Metrics

logger = Logger()
tracer = Tracer()
metrics = Metrics(namespace="MyApp")

@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics
def handler(event, context):
    metrics.add_metric(
        name="OrderProcessed", unit="Count", value=1
    )
    logger.info("Processing order",
        extra={"order_id": event["id"]})
```
:::

::: tab "SLI/SLO 정의"
### SLI/SLO 프레임워크
```yaml
# Application Signals SLO 설정
SLOs:
  - name: api-availability
    description: "API 가용성 SLO"
    sli:
      metric: 5xx_error_rate
      source: Application Signals
    goal:
      target: 99.9%          # 월 43분 허용
      warning: 99.95%
    window: rolling_28_days

  - name: api-latency
    description: "API 응답시간 SLO"
    sli:
      metric: p99_latency
      source: CloudWatch
    goal:
      target: 500ms
      warning: 300ms
    window: rolling_28_days

  - name: order-processing
    description: "주문 처리 SLO"
    sli:
      metric: processing_time
      source: Custom Metric
    goal:
      target: 95%_under_3sec
      warning: 95%_under_2sec
    window: rolling_7_days
```

**Error Budget = 1 - SLO Target**
- 99.9% SLO → 0.1% Error Budget → 월 43분
- Error Budget 소진 시 → 새 배포 중단, 안정화 집중
:::

:::notes
{timing: 4min}
Phase 1의 구체적인 구현을 환경별로 보겠습니다.

EKS 환경에서는 ADOT Collector를 DaemonSet으로 배포합니다. 하나의 Collector가 OTLP로 트레이스를 받고, Prometheus scraping으로 메트릭을 수집하고, 로그도 수집합니다. exporter를 보면 X-Ray, EMF(메트릭), CloudWatch Logs로 모든 데이터를 보냅니다. 이것 하나로 3가지 시그널을 모두 커버합니다.

Lambda 환경에서는 ADOT Lambda Layer를 추가하면 됩니다. 코드 변경은 최소화되고, Lambda Powertools를 함께 사용하면 구조화된 로깅, 자동 트레이싱, 커스텀 메트릭을 깔끔하게 구현할 수 있습니다.

세 번째 탭의 SLI/SLO 정의가 가장 중요합니다. SLI(Service Level Indicator)는 "무엇을 측정하는가"이고, SLO(Service Level Objective)는 "어디까지 허용하는가"입니다. 예를 들어 API 가용성 SLO 99.9%면 월 43분까지 다운타임을 허용한다는 의미입니다. Error Budget 개념을 도입하면 "이번 달 에러 예산을 50% 이상 소진했으니 새 배포를 중단하고 안정화에 집중하자"는 데이터 기반 의사결정이 가능해집니다.

{cue: transition} 다음은 노이즈 감소 전략입니다.
:::

---

## Alert 노이즈 감소 전략

::: left
### Before AIOps
```
[Alert Storm - 30분간 147개 알림]
03:00 CPU > 80% on web-01     ← noise
03:00 CPU > 80% on web-02     ← noise
03:01 Memory > 90% on web-01  ← noise
03:01 5xx > 1% on ALB         ← symptom
03:02 p99 > 2s on API         ← symptom
03:02 Connection pool full     ← ROOT CAUSE
03:03 DynamoDB throttling     ← symptom
...+140 more alerts
```
:::

::: right
### After AIOps
```
[Single Insight - 1개 알림]
03:02 DevOps Guru Insight:
  Severity: HIGH
  Root Cause: DynamoDB
    write capacity exceeded
  Related Events (7):
    - ALB 5xx increase
    - API latency spike
    - Connection pool exhaustion
    - CPU spikes (cascading)
  Recommendation:
    - Increase WCU or enable
      auto-scaling
    - Review burst traffic pattern
  Auto-Action:
    DynamoDB AutoScale triggered
```
:::

:::notes
{timing: 3min}
이 비교가 AIOps의 가치를 가장 직관적으로 보여줍니다.

왼쪽은 전형적인 Alert Storm입니다. 새벽 3시에 30분 동안 147개 알림이 쏟아집니다. CPU 알림, 메모리 알림, 5xx 알림, 레이턴시 알림 — 다 연관된 건데 각각 따로 옵니다. 엔지니어는 잠에서 깨서 이 147개를 하나하나 보면서 "진짜 원인이 뭐지?" 추적해야 합니다.

오른쪽은 AIOps 적용 후입니다. DevOps Guru가 147개 알림을 1개 Insight로 묶었습니다. 근본 원인은 DynamoDB write capacity 초과입니다. ALB 5xx, API 레이턴시, 커넥션 풀 고갈, CPU 스파이크 — 이 모든 것이 DynamoDB throttling에서 연쇄적으로 발생한 증상이라고 정리해줍니다. 그리고 이미 DynamoDB Auto Scaling이 자동으로 트리거되었습니다.

Alert 건수로 보면 147개에서 1개로 — 99% 이상 노이즈가 감소합니다. MTTR은 어떨까요? 수동으로 원인 추적하면 30분~1시간, AIOps로는 2분입니다.

{cue: transition} 이제 이벤트 상관분석의 기술적 구현을 더 깊이 보겠습니다.
:::

---

## 이벤트 상관분석 패턴

:::click
### 1. 시간 기반 상관 (Temporal Correlation)
- 같은 시간대에 발생한 이벤트 그룹핑
- **Window**: 5분 이내 발생한 이벤트를 하나의 그룹으로
- DevOps Guru가 자동으로 수행
:::

:::click
### 2. 토폴로지 기반 상관 (Topology Correlation)
- 서비스 의존성 그래프 기반 원인 추적
- **X-Ray Service Map** → 호출 경로 상의 이상 식별
- Application Signals → 서비스 간 SLI 상관관계
:::

:::click
### 3. 변경 기반 상관 (Change Correlation)
- CloudTrail + Config 변경 이력과 이상 시점 매칭
- "이 이상이 시작된 시점에 어떤 변경이 있었나?"
- **CodePipeline 배포** ↔ **성능 저하** 자동 연결
:::

:::click
### 4. 패턴 기반 상관 (Pattern Correlation)
- 과거 장애와 유사한 패턴 매칭
- Bedrock Knowledge Base에 과거 장애 보고서 저장
- "이전에 비슷한 패턴에서 어떻게 해결했는가?"
:::

:::notes
{timing: 3min}
이벤트 상관분석에는 네 가지 패턴이 있습니다.

첫째, 시간 기반 상관입니다. 5분 이내에 발생한 이벤트들을 하나의 그룹으로 묶습니다. 가장 기본적이면서도 효과적인 방법입니다. DevOps Guru가 자동으로 수행합니다.

둘째, 토폴로지 기반 상관입니다. X-Ray Service Map이 서비스 간 호출 관계를 파악하고 있기 때문에, "A 서비스가 B를 호출하는데, B에서 에러가 나면 A도 영향받는다"는 것을 자동으로 추적합니다. 이것이 가능하려면 Phase 1의 관측성 파이프라인이 잘 구축되어 있어야 합니다.

셋째, 변경 기반 상관입니다. 이것이 실무에서 가장 유용합니다. 장애의 70%는 변경에 의해 발생합니다. CloudTrail과 Config의 변경 이력을 이상 탐지 시점과 자동으로 매칭하면 "10분 전 이 IAM 정책이 변경되었습니다"라는 단서를 즉시 얻을 수 있습니다.

넷째, 패턴 기반 상관입니다. 이것은 Bedrock Knowledge Base를 활용하는 고급 패턴으로, 과거 장애 보고서와 현재 상황의 유사도를 비교합니다.

{cue: transition} 이제 실제 구현에서 흔히 겪는 함정과 Best Practices를 살펴보겠습니다.
:::

---

## AIOps 구현 Best Practices

@type: checklist

- **Start Small, Scale Fast** — 가장 빈번한 장애 유형 3가지부터 자동화 {.click}
- **Data Quality First** — 커스텀 메트릭 네이밍 컨벤션 통일, 구조화된 로깅 필수 {.click}
- **SLO-Driven** — SLO 위반 기준으로 Alert, 임의 임계값 금지 {.click}
- **Gradual Automation** — 분석→승인→실행→풀오토 단계적 전환 {.click}
- **Feedback Loop** — 모든 Insight에 유용/무용 피드백, ML 모델 개선 {.click}
- **Runbook-as-Code** — SSM 문서를 CloudFormation/CDK로 관리, 버전 관리 필수 {.click}
- **Blast Radius Control** — 자동 복구의 범위 제한 (한 번에 1 AZ, 10% 인스턴스) {.click}
- **Cost Awareness** — Anomaly Detection 메트릭 선별, 로그 보존 기간 계층화 {.click}

:::notes
{timing: 3min}
8가지 Best Practices를 체크리스트로 정리했습니다.

Start Small이 가장 중요합니다. 모든 것을 한번에 자동화하려 하지 마세요. 여러분 환경에서 가장 자주 발생하는 장애 유형 3가지를 뽑으세요. 그것부터 자동화합니다.

Data Quality는 간과하기 쉽지만 치명적입니다. 메트릭 이름이 팀마다 다르면 — 어디는 api_latency, 어디는 ApiLatency, 어디는 api-response-time — 상관분석이 불가능합니다. 네이밍 컨벤션을 통일하고 구조화된 JSON 로깅을 필수로 하세요.

Blast Radius Control도 강조하고 싶습니다. 자동 복구가 잘못 판단하면 오히려 장애를 확대할 수 있습니다. 한 번에 전체 클러스터를 재시작하는 것이 아니라, 1개 AZ의 10% 인스턴스만 먼저 처리하고 결과를 확인하는 식으로 범위를 제한하세요.

Cost Awareness도 현실적으로 중요합니다. 모든 메트릭에 Anomaly Detection을 적용하면 비용이 급증합니다. 비즈니스 임팩트가 큰 핵심 메트릭만 선별하세요.

{cue: transition} 흔한 실패 패턴도 알아두면 도움이 됩니다.
:::

---

## AIOps 안티패턴

::: left
### 흔한 실패 패턴

- **Tool-First Approach** {.click}
  "DevOps Guru 켜면 끝 아닌가요?"
  → 데이터 품질 없이 도구만 도입

- **Big Bang Deployment** {.click}
  전체 인프라 한번에 AIOps 적용
  → 알림 폭주, 팀 피로, 포기

- **No Feedback Loop** {.click}
  Insight 무시하거나 피드백 안 줌
  → ML 모델 개선 안 됨

- **Over-Automation** {.click}
  모든 것을 자동 복구하려 함
  → 잘못된 자동 복구가 장애 확대
:::

::: right
### 올바른 접근

- **Outcome-First Approach** {.click}
  "MTTR 30분→5분 달성"이 목표
  → 목표 역산으로 필요 기능 식별

- **Incremental Rollout** {.click}
  1개 팀, 1개 서비스부터 시작
  → 성공 사례 만들고 확산

- **Active Feedback** {.click}
  모든 Insight에 Thumbs up/down
  → 2개월 후 정확도 체감 향상

- **Tiered Automation** {.click}
  L1 자동, L2 승인 필요, L3 수동
  → 리스크 수준별 자동화 차등
:::

:::notes
{timing: 3min}
안티패턴을 알아야 피할 수 있습니다.

가장 흔한 실패는 Tool-First Approach입니다. "DevOps Guru 활성화하면 자동으로 다 해주는 거 아닌가요?" — 아닙니다. 데이터 품질이 좋지 않으면 ML도 쓸모없는 결과를 냅니다. 도구보다 데이터가 먼저입니다.

Big Bang Deployment도 흔합니다. 전체 인프라에 한번에 적용하면 Insight가 폭주합니다. 처음 보는 팀은 "이게 다 뭐야?" 하면서 무시하기 시작하고, 결국 Alert Fatigue로 돌아갑니다.

올바른 접근은 오른쪽입니다. Outcome-First — "MTTR을 30분에서 5분으로 줄이겠다"는 명확한 목표를 세우고, 그 목표 달성에 필요한 기능만 구현합니다.

Incremental Rollout — 가장 의지 있는 1개 팀의 1개 서비스에서 시작합니다. 성공 사례를 만들면 나머지 팀이 자발적으로 따라옵니다.

Tiered Automation이 현실적입니다. 스케일 아웃처럼 리스크가 낮은 건 완전 자동화, 데이터베이스 failover처럼 리스크가 높은 건 승인 필요, 코드 롤백은 수동 — 이렇게 계층을 나눕니다.

{cue: transition} 마지막으로 비용 측면을 살펴보겠습니다.
:::

---

## AIOps 비용 최적화

@type: compare

### 주요 서비스 비용 (ap-northeast-2)

::: compare "DevOps Guru"
### DevOps Guru
| 항목 | 비용 |
|------|------|
| AWS 리소스 분석 | $0.0028/리소스/시간 |
| 월 100 리소스 | ~$201/월 |
| API 호출 분석 | $0.000005/API 호출 |
| 월 1억 API 호출 | ~$500/월 |

**ROI 계산**: 장애 1건 MTTR 30분 단축
→ 엔지니어 시간 절약 + 비즈니스 손실 방지
:::

::: compare "CloudWatch AI"
### CloudWatch AI/ML
| 항목 | 비용 |
|------|------|
| Anomaly Detection | $3/메트릭/월 |
| 50개 핵심 메트릭 | $150/월 |
| Application Signals | $12/서비스/월 |
| 10개 서비스 | $120/월 |
| Log Anomaly | Logs 비용에 포함 |

**최적화**: 핵심 메트릭만 선별
→ 비즈니스 KPI + SLI 메트릭 위주
:::

::: compare "자동화 인프라"
### Automation 비용
| 항목 | 비용 |
|------|------|
| EventBridge | $1/백만 이벤트 |
| SSM Automation | 무료 (API 호출만) |
| SNS 알림 | $0.50/백만 발행 |
| Lambda (glue) | $0.20/백만 요청 |

**합계**: $5~20/월 수준
→ 거의 무시 가능한 비용
:::

:::notes
{timing: 3min}
AIOps 구현 비용을 현실적으로 살펴보겠습니다.

DevOps Guru는 모니터링하는 리소스 수에 따라 과금됩니다. 100개 리소스면 월 약 200달러입니다. API 호출 분석도 별도로 과금되는데, 월 1억 호출이면 약 500달러입니다. 합하면 월 700달러 수준인데, 장애 1건의 비즈니스 손실을 생각하면 충분히 합리적입니다.

CloudWatch AI/ML은 Anomaly Detection이 메트릭당 월 3달러입니다. 모든 메트릭이 아니라 핵심 50개만 적용하면 150달러입니다. Application Signals는 서비스당 월 12달러로, 10개 서비스면 120달러입니다.

가장 좋은 소식은 자동화 인프라 비용입니다. EventBridge, SSM, SNS 비용은 합쳐도 월 5~20달러 수준으로 거의 무시할 수 있습니다. Level 4 자동 복구를 구현하는 데 추가 비용이 거의 들지 않는다는 것입니다.

총 비용은 환경 규모에 따라 월 500~1,500달러 수준입니다. 이것은 장애 1건의 MTTR을 30분 단축하는 것만으로도 ROI가 나옵니다.

{cue: transition} 마지막으로 이 세션의 전체 내용을 정리하겠습니다.
:::

---

## Session Summary — AIOps on AWS

:::click
### Foundation (L1→L2)
관측성 파이프라인이 모든 것의 시작
- ADOT + CloudWatch + X-Ray 통합 수집
- SLI/SLO 정의 → 데이터 기반 운영
:::

:::click
### Intelligence (L2→L3)
ML 기반 이상 탐지와 근본 원인 분석
- CloudWatch Anomaly Detection → 동적 baseline
- DevOps Guru → 이벤트 상관분석 + Insight
- Amazon Q → 자연어 운영 지원
:::

:::click
### Automation (L3→L4)
알려진 문제의 자동 복구
- EventBridge → SSM Automation 파이프라인
- 점진적 자동화: 분석 → 승인 → 실행 → 풀오토
- Blast Radius 제한 필수
:::

:::click
### Next Steps for AnyCompany
1. 핵심 서비스 3개의 SLI/SLO 정의 (2주)
2. ADOT 배포 + DevOps Guru 활성화 (2주)
3. 첫 번째 자동 복구 Runbook 작성 (2주)
:::

:::notes
{timing: 3min}
90분간의 세션을 세 단계로 정리합니다.

Foundation — 관측성 파이프라인이 모든 것의 시작입니다. ADOT로 메트릭, 로그, 트레이스를 통합 수집하고, SLI/SLO를 정의하세요. 이것 없이 AIOps는 시작할 수 없습니다.

Intelligence — CloudWatch Anomaly Detection과 DevOps Guru로 ML 기반 이상 탐지와 근본 원인 분석을 구현합니다. 정적 임계값에서 동적 baseline으로의 전환이 핵심입니다.

Automation — EventBridge와 SSM으로 자동 복구를 구현합니다. "알려진 문제는 자동화, 모르는 문제는 사람에게" 원칙을 지키세요.

AnyCompany의 다음 단계를 구체적으로 제안합니다. 먼저 핵심 서비스 3개의 SLI/SLO를 정의하는 데 2주, ADOT 배포와 DevOps Guru 활성화에 2주, 첫 번째 자동 복구 Runbook 작성에 2주 — 총 6주면 AIOps Level 3에 진입할 수 있습니다.

{cue: question} 질문 있으신 분 계신가요? 또는 여러분 환경에 특화된 아키텍처 상담이 필요하시면 세션 후에 개별적으로 이야기 나누겠습니다.
:::

---

## Thank You

:::click
> AIOps는 도구가 아니라 **여정**입니다.
> 작게 시작하고, 데이터로 판단하고, 점진적으로 자동화하세요.
:::

**Junseok Oh**
Sr. Solutions Architect, AWS

:::notes
{timing: 1min}
오늘 세션에 참석해 주셔서 감사합니다. AIOps는 하루아침에 완성되는 것이 아니라 여정입니다. 오늘 공유드린 로드맵과 Best Practices가 여러분의 AIOps 여정에 도움이 되길 바랍니다.

추가 질문이나 아키텍처 상담이 필요하시면 언제든 연락 주세요. 감사합니다.
:::
