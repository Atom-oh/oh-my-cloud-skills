---
remarp: true
block: ml-operations
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
브레이크 후 돌아오신 것 환영합니다. Block 2에서는 AWS의 ML 기반 운영 서비스들을 본격적으로 다루겠습니다.
{cue: transition}
DevOps Guru부터 시작합니다.
:::

---
<!-- Slide 2: Block 2 Title -->
@type: title
@transition: fade

# ML-Powered Operations
Block 2 — Anomaly Detection & Intelligent Diagnostics (30분)

:::notes
{timing: 0.5min}
두 번째 블록입니다. DevOps Guru, CloudWatch Anomaly Detection, CodeGuru, 그리고 GenAI까지 — AWS가 제공하는 ML 운영 서비스를 하나씩 깊이 들어가 보겠습니다.
:::

---
<!-- Slide 3: DevOps Guru Overview -->

## Amazon DevOps Guru — ML 기반 운영 인사이트

::: left
### 작동 원리
- AWS 리소스의 **운영 메트릭**을 ML로 분석
- 서비스별 사전 학습 모델 (Lambda, RDS, ECS, DynamoDB 등)
- 비정상 패턴 감지 시 **Insight** 생성
- 관련 이벤트를 자동 **그룹핑** (노이즈 감소)

### Insight 유형
| 유형 | 설명 |
|------|------|
| **Reactive** | 이미 발생한 문제에 대한 분석 |
| **Proactive** | 곧 발생할 문제 사전 경고 |

### 지원 리소스
Lambda, API Gateway, DynamoDB, RDS, ECS, EKS, SQS, SNS, Step Functions, CloudFormation stacks
:::

::: right
### Insight 구성 요소
1. **Anomalous Metrics** — 어떤 메트릭이 비정상인지 {.click}
2. **Related Events** — CloudTrail 이벤트 상관 분석 {.click}
3. **Recommendations** — 구체적 조치 방안 {.click}

### 실제 사례
> Lambda Duration이 평소 200ms → 2s로 증가
> → DevOps Guru가 동시에 발생한 DynamoDB ProvisionedThroughputExceeded 이벤트와 상관 분석
> → "DynamoDB 테이블 용량 부족이 Lambda 지연의 원인" 진단
> → "Auto Scaling 활성화 또는 On-Demand 전환" 권고

### 비용
- $0.0028 / AWS 리소스 / 시간
- 100개 리소스 기준 ~$200/월
:::

:::notes
{timing: 4min}
DevOps Guru는 AWS가 20년간 축적한 운영 경험을 ML 모델로 만든 서비스입니다. 가장 큰 차별점은 단순 이상 탐지가 아니라 이벤트 상관 분석과 권고까지 제공한다는 점입니다.

실제 사례를 보시면, Lambda Duration이 10배 증가했을 때 단순 모니터링은 "Lambda가 느리다"만 알려줍니다. DevOps Guru는 같은 시간대에 발생한 DynamoDB Throttle 이벤트를 CloudTrail에서 찾아서, "DynamoDB 용량 부족이 근본 원인이고, Auto Scaling을 켜라"는 구체적 권고를 줍니다.

이게 AIOps의 핵심 가치입니다 — 증상이 아니라 원인을 자동으로 찾아주는 것.

비용 관점에서 리소스당 시간당 $0.0028인데, 100개 리소스 기준 월 $200 정도입니다. 한 번의 장애로 손실되는 비용과 비교하면 매우 합리적입니다.
{cue: question}
AnyCompany에서 현재 장애 한 건당 예상 비용이 어느 정도 되시나요? MTTR × 분당 매출 손실로 계산해 보시면 DevOps Guru의 ROI가 나옵니다.
{cue: transition}
DevOps Guru 설정 방법을 봐 보겠습니다.
:::

---
<!-- Slide 4: DevOps Guru Setup -->
@type: tabs

## DevOps Guru — 설정과 운영

::: tab "활성화 방법"
### CloudFormation Stack 기반 활성화
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  DevOpsGuruConfig:
    Type: AWS::DevOpsGuru::ResourceCollection
    Properties:
      ResourceCollectionFilter:
        CloudFormation:
          StackNames:
            - "AnyCompany-Production-*"

  DevOpsGuruNotification:
    Type: AWS::DevOpsGuru::NotificationChannel
    Properties:
      Config:
        Sns:
          TopicArn: !Ref OpsAlertTopic
        Filters:
          Severities:
            - HIGH
            - MEDIUM
          MessageTypes:
            - NEW_INSIGHT
            - SEVERITY_UPGRADED
```

### 권장 설정
- Production 스택만 활성화 (비용 최적화)
- HIGH + MEDIUM severity만 알림 (노이즈 최소화)
- SNS → Lambda → Slack/PagerDuty 연동
:::

::: tab "EKS 통합"
### DevOps Guru for EKS
```bash
# EKS 클러스터에 DevOps Guru 활성화
aws devops-guru update-resource-collection \
  --action ADD \
  --resource-collection '{
    "Tags": [{
      "AppBoundaryKey": "devops-guru-eks",
      "TagValues": ["anycompany-prod"]
    }]
  }'
```

### 탐지 가능한 EKS 이슈
- Pod CPU/Memory 이상 사용 패턴
- Container restart loop 감지
- Node 리소스 고갈 예측
- API Server latency 이상

### 제한 사항
- Container Insights 활성화 필수
- EKS 1.23+ 지원
- Fargate Pod은 일부 메트릭 제한
:::

::: tab "Insight 자동화"
### EventBridge 연동
```json
{
  "source": ["aws.devops-guru"],
  "detail-type": ["DevOps Guru New Insight Open"],
  "detail": {
    "insightSeverity": ["HIGH"]
  }
}
```

### Lambda 자동 대응 예시
```python
def handler(event, context):
    insight = event['detail']
    severity = insight['insightSeverity']
    anomalies = insight.get('anomalies', [])

    for anomaly in anomalies:
        source = anomaly['sourceDetails']
        if 'DynamoDB' in str(source):
            # DynamoDB Auto Scaling 활성화
            enable_auto_scaling(source)
        elif 'Lambda' in str(source):
            # Lambda concurrency 조정
            adjust_concurrency(source)

    # Slack 알림 발송
    send_slack_notification(insight)
```
:::

:::notes
{timing: 4min}
DevOps Guru 설정은 생각보다 간단합니다.

첫 번째 탭 — CloudFormation 스택 이름 패턴으로 모니터링 범위를 지정합니다. AnyCompany에서 "AnyCompany-Production"으로 시작하는 스택만 지정하면 프로덕션 환경만 모니터링됩니다. 알림은 HIGH와 MEDIUM만 보내는 것을 권장합니다. LOW까지 보내면 노이즈가 많습니다.

두 번째 탭 — EKS 통합입니다. 태그 기반으로 클러스터를 지정하고, Container Insights가 활성화되어 있어야 합니다. Pod 레벨의 CPU/Memory 이상, container restart loop, node 리소스 고갈까지 탐지합니다.

세 번째 탭이 실전에서 가장 중요합니다. DevOps Guru Insight가 생성되면 EventBridge가 이벤트를 받고, Lambda가 자동 대응을 실행합니다. 예시 코드처럼 DynamoDB 관련 이상이면 Auto Scaling을 활성화하고, Lambda 관련이면 concurrency를 조정하는 식입니다.

물론 모든 자동 대응을 바로 프로덕션에 적용하는 것은 위험합니다. 초기에는 알림만 보내다가, 신뢰가 쌓이면 단계적으로 자동 대응을 활성화하세요.
{cue: transition}
다음은 CloudWatch의 ML 기능을 더 깊이 봅니다.
:::

---
<!-- Slide 5: CloudWatch Anomaly Detection Deep Dive -->
@type: canvas

## CloudWatch Anomaly Detection — ML 모델 동작 원리

:::canvas
@width: 960
@height: 400

# ML Model Training Phase
box "Historical\nMetrics\n(2 weeks)" 30,40 130,70 fill:#1a2744 border:#41B3FF step:0
arrow 160,75 220,75 #41B3FF step:1
box "ML Model\nTraining" 220,45 130,60 fill:#232f3e border:#FF9900 step:1
text "Random Cut Forest\n+ Seasonal Decomposition" 285,125 size:10 color:#FF9900 step:1

# Pattern Recognition
arrow 350,75 420,30 #FF9900 step:2
arrow 350,75 420,75 #FF9900 step:2
arrow 350,75 420,120 #FF9900 step:2

box "Daily\nPattern" 420,10 110,40 fill:#232f3e border:#AD5CFF step:2
box "Weekly\nPattern" 420,60 110,40 fill:#232f3e border:#AD5CFF step:2
box "Seasonal\nPattern" 420,110 110,40 fill:#232f3e border:#AD5CFF step:2

# Band Generation
arrow 530,75 600,75 #AD5CFF step:3
box "Anomaly\nDetection\nBand" 600,35 130,80 fill:#161D26 border:#00E500 step:3
text "Upper Bound ─── Expected ─── Lower Bound" 665,135 size:10 color:#00E500 step:3

# Real-time Evaluation
arrow 730,75 800,40 #00E500 step:4
arrow 730,75 800,105 #00E500 step:4

box "NORMAL\n밴드 내" 800,15 120,50 fill:#1a3a1a border:#00E500 step:4
box "ANOMALY\n밴드 이탈" 800,80 120,50 fill:#3a1a1a border:#FF5C85 step:4

# Alert Flow
arrow 920,105 935,170 #FF5C85 step:5
box "CloudWatch\nAlarm\n→ SNS\n→ EventBridge" 850,170 130,70 fill:#161D26 border:#FF5C85 step:5

# Configuration
text "ANOMALY_DETECTION_BAND(m1, 2)" 200,250 size:13 color:#FBD332 step:3
text "stddev = 2 → 밴드 폭 조절" 200,275 size:11 color:#b0b0b0 step:3

# Timeline
text "2주 학습" 100,340 size:12 color:#41B3FF step:0
text "모델 생성" 280,340 size:12 color:#FF9900 step:1
text "패턴 분해" 460,340 size:12 color:#AD5CFF step:2
text "밴드 생성" 650,340 size:12 color:#00E500 step:3
text "실시간 판정" 850,340 size:12 color:#FF5C85 step:4
:::

:::notes
{timing: 4min}
CloudWatch Anomaly Detection의 내부 동작을 단계별로 풀어보겠습니다.

Step 0 — 먼저 최소 2주간의 과거 메트릭 데이터가 필요합니다. 이게 ML 모델의 학습 데이터입니다.

Step 1 — AWS는 Random Cut Forest 알고리즘과 Seasonal Decomposition을 결합한 모델을 사용합니다. RCF는 Amazon이 개발한 비지도 학습 알고리즘으로, 정상 데이터의 분포를 학습합니다.

Step 2 — 모델이 일간 패턴(출근 시간 트래픽 증가), 주간 패턴(주말 감소), 계절 패턴(블랙프라이데이, 연말 피크)을 분리하여 인식합니다.

Step 3 — 이 패턴들을 기반으로 Anomaly Detection Band를 생성합니다. ANOMALY_DETECTION_BAND 함수의 두 번째 파라미터가 표준편차 배수인데, 2로 설정하면 95% 신뢰구간이 됩니다. 이 밴드를 좁히면 민감도가 올라가고, 넓히면 내려갑니다.

Step 4 — 실시간 데이터 포인트가 밴드 안에 있으면 NORMAL, 밴드를 벗어나면 ANOMALY로 판정합니다.

{cue: question}
한 가지 주의점 — stddev를 너무 낮게 설정하면(예: 1) false positive가 많아져서 알람 피로가 옵니다. 보통 2~3으로 시작해서 조정하시길 권합니다.
{cue: transition}
이제 코드 레벨의 성능 분석 도구를 봅니다.
:::

---
<!-- Slide 6: CodeGuru & Lookout -->

## Amazon CodeGuru & Lookout for Metrics

::: left
### CodeGuru Profiler
- **프로덕션 환경** 프로파일링 (overhead < 1%)
- CPU, Latency hotspot 자동 탐지
- ML 기반 **비용 절감 권고** (비효율 코드 식별)
- Java, Python 지원

### 프로파일링 결과 예시
```
Top CPU Consumers:
1. com.anycompany.OrderService.processPayment()
   → 37% CPU, 12ms avg latency
   → Recommendation: Connection pool 재사용
      예상 절감: $340/month (EC2 비용)

2. com.anycompany.InventoryService.checkStock()
   → 22% CPU, 8ms avg latency
   → Recommendation: DynamoDB BatchGetItem 사용
      예상 절감: $120/month (DynamoDB 비용)
```
:::

::: right
### Amazon Lookout for Metrics
- 비즈니스 메트릭 이상 탐지 특화
- **Revenue**, **Order count**, **User engagement** 모니터링
- RDS, S3, CloudWatch, Redshift 데이터소스 연동
- **근본 원인 기여도** 자동 분석

### Lookout vs CloudWatch AD
| 기준 | Lookout | CW AD |
|------|---------|-------|
| 대상 | 비즈니스 메트릭 | 인프라 메트릭 |
| 차원 분석 | 다차원 기여도 | 단일 메트릭 |
| 데이터소스 | RDS, S3, Redshift | CloudWatch only |
| 알림 지연 | 5~15분 | 1~5분 |
| 비용 | 메트릭당 과금 | 무료 (CloudWatch 포함) |

### 사용 시나리오
> "주문량이 평소 대비 30% 감소"
> → Lookout이 **region=ap-northeast-2 + category=electronics**에서 주로 감소했다고 차원 분석
:::

:::notes
{timing: 3min}
CodeGuru와 Lookout은 각각 코드 레벨과 비즈니스 메트릭 레벨에서 AIOps를 보완합니다.

CodeGuru Profiler는 프로덕션에서 실행되는 코드의 CPU 사용 패턴을 분석합니다. 오버헤드가 1% 미만이라 프로덕션에 바로 붙여도 됩니다. 왼쪽 예시를 보시면 OrderService의 processPayment 메서드가 CPU 37%를 차지하면서 connection pool을 매번 새로 만들고 있다는 것을 발견하고, 재사용하면 월 $340 절감된다고 권고합니다.

Lookout for Metrics는 비즈니스 KPI에 특화되어 있습니다. 인프라 메트릭은 CloudWatch Anomaly Detection이 담당하고, "매출이 떨어졌다", "주문량이 줄었다" 같은 비즈니스 이상은 Lookout이 담당합니다. 핵심 차별점은 다차원 기여도 분석입니다 — 단순히 "주문이 줄었다"가 아니라 "한국 리전의 전자제품 카테고리에서 줄었다"까지 자동 분석해 줍니다.
{cue: transition}
이제 가장 흥미로운 부분 — Gen AI로 운영을 어떻게 혁신하는지 봅시다.
:::

---
<!-- Slide 7: GenAI for Operations -->

## Generative AI for Operations

::: left
### Amazon Q in CloudWatch
- 자연어로 CloudWatch 데이터 분석
- "왜 이 Lambda가 느려졌어?"에 대한 설명 생성
- 로그 패턴 요약 및 근본 원인 제안
- **자연어 → PromQL/CloudWatch Insights 쿼리 자동 변환**

### Amazon Q Developer
- IDE에서 운영 코드 자동 생성
- "DynamoDB throttle 알람 설정해줘"
- IaC (CloudFormation/CDK) 자동 생성
- 코드 리뷰에서 운영 이슈 사전 탐지

### Amazon Bedrock Agent
- 커스텀 AIOps 챗봇 구축
- 사내 운영 문서 + AWS 데이터 통합
- RAG 기반 인시던트 자동 대응 가이드
:::

::: right
### Bedrock Agent 아키텍처
```
사용자 질문
    ↓
Bedrock Agent (Claude)
    ↓
┌─────────────────────────────┐
│ Knowledge Base               │
│ ├─ 운영 Runbook (S3)        │
│ ├─ 장애 이력 DB (OpenSearch) │
│ └─ AWS 공식 문서            │
├─────────────────────────────┤
│ Action Groups               │
│ ├─ CloudWatch 쿼리 실행     │
│ ├─ Lambda 호출 (복구 액션)   │
│ └─ Jira 티켓 생성           │
└─────────────────────────────┘
    ↓
"DynamoDB 테이블 X의 RCU가
 포화 상태입니다. 과거 유사 사례에서는
 Auto Scaling을 활성화하여 해결했습니다.
 지금 바로 적용할까요?"
```

### 도입 단계
1. **Q in CloudWatch** — 즉시 사용 (설정 불필요) {.click}
2. **Q Developer** — IDE 플러그인 설치 {.click}
3. **Bedrock Agent** — 커스텀 구축 (2-4주) {.click}
:::

:::notes
{timing: 4min}
GenAI가 운영을 바꾸고 있습니다. 세 가지 도구를 소개합니다.

Amazon Q in CloudWatch는 바로 쓸 수 있습니다. CloudWatch 콘솔에서 자연어로 "지난 1시간 동안 에러가 가장 많은 Lambda는?"이라고 물으면, 자동으로 Logs Insights 쿼리를 생성하고 결과를 요약해 줍니다. 이전에는 PromQL이나 Logs Insights 쿼리 문법을 알아야 했는데, 이제는 자연어면 충분합니다.

두 번째 Amazon Q Developer는 IDE에서 운영 코드를 자동 생성합니다. "DynamoDB throttle이 발생하면 SNS로 알림 보내는 CloudFormation 템플릿 만들어줘"라고 하면 바로 생성됩니다.

가장 강력한 것은 Bedrock Agent입니다. 오른쪽 아키텍처를 보시면, Knowledge Base에 AnyCompany의 운영 Runbook, 과거 장애 이력, AWS 문서를 넣고, Action Group에 CloudWatch 쿼리, Lambda 호출, Jira 티켓 생성을 연결합니다. 그러면 "서비스가 느린데?"라는 질문에 과거 유사 사례를 찾아서 구체적 해결책을 제안하고, 승인하면 바로 실행까지 합니다.

Bedrock Agent 구축은 2-4주 정도 걸리지만, 운영 팀의 생산성을 크게 높여줍니다.
{cue: transition}
GenAI 활용을 구체적인 아키텍처로 정리해 보겠습니다.
:::

---
<!-- Slide 8: AIOps Event Correlation -->
@type: canvas

## AIOps 이벤트 상관 분석 — 노이즈에서 인사이트로

:::canvas
@width: 960
@height: 400

# Noise (many alerts)
box "ELB 5xx\n↑ 300%" 20,20 105,40 fill:#3a1a1a border:#FF5C85 step:0
box "Lambda\nDuration ↑" 20,70 105,40 fill:#3a1a1a border:#FF5C85 step:0
box "DDB Read\nThrottle" 20,120 105,40 fill:#3a1a1a border:#FF5C85 step:0
box "API GW\nLatency ↑" 20,170 105,40 fill:#3a1a1a border:#FF5C85 step:0
box "CW Alarm\nCPU 92%" 20,220 105,40 fill:#3a1a1a border:#FF5C85 step:0
box "SQS Queue\nDepth ↑" 20,270 105,40 fill:#3a1a1a border:#FF5C85 step:0
text "6개 알람" 72,330 size:13 color:#FF5C85 step:0

# Correlation Engine
box "DevOps Guru\nCorrelation\nEngine" 210,100 140,80 fill:#232f3e border:#AD5CFF step:1

# Arrows: alerts -> engine
arrow 125,40 210,120 #FF5C85 step:1
arrow 125,90 210,130 #FF5C85 step:1
arrow 125,140 210,140 #FF5C85 step:1
arrow 125,190 210,150 #FF5C85 step:1
arrow 125,240 210,160 #FF5C85 step:1
arrow 125,290 210,170 #FF5C85 step:1

# CloudTrail Events
box "CloudTrail\nEvents" 210,230 140,50 fill:#232f3e border:#41B3FF step:1
text "UpdateTable (RCU: 100→5)" 280,300 size:10 color:#41B3FF step:1
arrow 280,230 280,180 #41B3FF step:1

# Grouped Insight
arrow 350,140 440,100 #AD5CFF step:2
box "Insight:\nDynamoDB\nCapacity\nExhaustion" 440,60 150,100 fill:#161D26 border:#FBD332 step:2
text "Root Cause: RCU 축소\n(100 → 5 by deploy)" 515,180 size:11 color:#FBD332 step:2
text "Severity: HIGH" 515,200 size:11 color:#FF5C85 step:2

# Recommendation
arrow 590,110 680,80 #FBD332 step:3
box "권고:\n1. RCU 원복 (100)\n2. Auto Scaling\n   활성화\n3. Deploy 롤백\n   검토" 680,30 150,130 fill:#161D26 border:#00E500 step:3

# Auto-remediation
arrow 830,95 880,95 #00E500 step:4
box "EventBridge\n→ Lambda\n→ RCU 원복" 880,60 70,70 fill:#161D26 border:#FF9900 step:4

# Timeline
text "6개 알람\n(노이즈)" 55,365 size:11 color:#FF5C85 step:0
text "상관 분석" 260,365 size:11 color:#AD5CFF step:1
text "1개 인사이트\n(신호)" 495,365 size:11 color:#FBD332 step:2
text "권고 사항" 735,365 size:11 color:#00E500 step:3
text "자동 복구" 895,365 size:11 color:#FF9900 step:4
:::

:::notes
{timing: 4min}
이 Canvas가 AIOps의 핵심 가치를 가장 잘 보여줍니다.

Step 0 — 어느 날 갑자기 6개의 알람이 동시에 울립니다. ELB 5xx 증가, Lambda Duration 증가, DynamoDB Read Throttle, API Gateway Latency 증가, CPU 92%, SQS Queue 적체. 온콜 엔지니어가 이 6개를 보면 어디서부터 봐야 할지 혼란스럽겠죠?

Step 1 — DevOps Guru의 Correlation Engine이 이 6개 알람과 같은 시간대의 CloudTrail 이벤트를 분석합니다. CloudTrail에서 "DynamoDB UpdateTable — RCU 100에서 5로 축소"라는 배포 이벤트를 발견합니다.

Step 2 — 6개 알람이 하나의 Insight로 그룹핑됩니다: "DynamoDB Capacity Exhaustion". 근본 원인은 누군가의 배포로 RCU가 100에서 5로 줄어든 것. 6개 알람 → 1개 인사이트로 노이즈가 83% 감소합니다.

Step 3 — 구체적 권고가 나옵니다. RCU 원복, Auto Scaling 활성화, 배포 롤백 검토.

Step 4 — EventBridge가 이 Insight를 받아서 Lambda로 자동 RCU 원복을 실행합니다.

이게 사람이 하면 30분, DevOps Guru가 하면 5분입니다.
{cue: transition}
Block 2의 핵심을 정리하겠습니다.
:::

---
<!-- Slide 9: Composite Alarms -->

## CloudWatch Composite Alarms — 알람 전략

::: left
### 문제: 알람 폭풍
- 하나의 장애 → 수십 개 알람 동시 발생
- 온콜 엔지니어 알람 피로 (Alert Fatigue)
- "어떤 알람이 진짜 중요한지" 판단 불가

### 해결: Composite Alarm
- 여러 개별 알람을 **논리 조합** (AND/OR/NOT)
- 조건 조합이 충족될 때만 알림
- **suppress-on-recovery**: 하위 알람이 곧 복구되면 불필요한 알림 억제

### 예시 구성
```
ServiceHealth Composite Alarm
├── AND
│   ├── ELB_5xx_Rate > 5% (child alarm)
│   ├── Backend_Latency_P99 > 2s (child alarm)
│   └── NOT (Maintenance_Window) (suppressor)
```
:::

::: right
### CloudFormation 설정
```yaml
CompositeServiceAlarm:
  Type: AWS::CloudWatch::CompositeAlarm
  Properties:
    AlarmName: AnyCompany-ServiceHealth
    AlarmRule: >-
      ALARM("ELB-5xx-Rate")
      AND
      ALARM("Backend-P99-Latency")
      AND
      NOT ALARM("Maintenance-Window")
    AlarmActions:
      - !Ref PagerDutyTopic
    ActionsSuppressor: MaintenanceWindow
    ActionsSuppressorWaitPeriod: 120
    ActionsSuppressorExtensionPeriod: 60
```

### 베스트 프랙티스
- **L1 알람** (개별 메트릭) → 대시보드 전용
- **L2 Composite** (서비스 단위) → Slack 알림
- **L3 Composite** (비즈니스 영향) → PagerDuty 호출
- 유지보수 윈도우 **Suppressor** 필수 설정
:::

:::notes
{timing: 3min}
알람 전략도 AIOps에서 매우 중요합니다. Composite Alarm은 알람 피로를 해결하는 CloudWatch 네이티브 기능입니다.

왼쪽 예시를 보시면, ELB 5xx 비율이 5% 이상이고 Backend P99 Latency가 2초를 넘고, 유지보수 윈도우가 아닐 때만 PagerDuty를 호출합니다. 개별 알람이 잠깐 울렸다 꺼지는 건 무시합니다.

3계층 구조를 권장합니다. L1은 개별 메트릭 알람으로 대시보드에서만 확인합니다. L2는 서비스 단위 Composite로 Slack에 보냅니다. L3는 비즈니스 영향도 기반으로 PagerDuty로 온콜 호출합니다. 이렇게 하면 온콜 엔지니어가 받는 알림 수가 80% 이상 줄어듭니다.

ActionsSuppressor는 유지보수 윈도우 동안 알림을 억제하는 기능인데, WaitPeriod 120초로 설정하면 유지보수 시작 후 2분간은 알림을 보류했다가, 그 이후에도 계속 문제면 알립니다.
{cue: transition}
Block 2를 마무리하겠습니다.
:::

---
<!-- Slide 10: Block 2 Key Takeaways -->
@transition: fade

## Block 2 — Key Takeaways

::: left
### 핵심 포인트
- **DevOps Guru** — 이벤트 상관 분석 + 사전 예측으로 MTTR 대폭 단축 {.click}
- **CloudWatch AD** — Random Cut Forest 기반 동적 밴드, stddev 2~3 권장 {.click}
- **Composite Alarms** — 3계층(L1/L2/L3) 전략으로 알람 피로 80% 감소 {.click}
- **CodeGuru + Lookout** — 코드 레벨 + 비즈니스 레벨 이상 탐지 보완 {.click}
- **Gen AI (Q + Bedrock)** — 자연어 분석 + 커스텀 AIOps Agent 구축 {.click}
:::

::: right
### AnyCompany 체크포인트
- [ ] DevOps Guru Production 스택 활성화
- [ ] CloudWatch Anomaly Detection 핵심 SLI에 적용
- [ ] Composite Alarm 3계층 구조 설계
- [ ] Amazon Q in CloudWatch 팀 내 시범 사용
- [ ] Bedrock Agent 기반 AIOps 챗봇 PoC 계획

### 다음 블록 예고
Block 3에서는 이 서비스들을 **AnyCompany 환경에 맞게 조합**하는 구현 전략과 단계별 로드맵을 다룹니다.
:::

:::notes
{timing: 2min}
Block 2를 정리합니다.

이 블록에서 다룬 ML 서비스들은 각각 다른 레벨을 담당합니다. DevOps Guru는 인프라 이벤트 상관 분석, CloudWatch AD는 메트릭 이상 탐지, CodeGuru는 코드 성능, Lookout은 비즈니스 KPI, GenAI는 자연어 인터페이스를 담당합니다.

한 가지 강조하고 싶은 것은, 이 서비스들을 한꺼번에 다 도입하지 마세요. Block 3에서 단계별 로드맵을 제시하겠습니다.

5분 브레이크 후 마지막 블록으로 돌아오겠습니다.
{cue: transition}
잠시 쉬겠습니다!
:::

---
<!-- Slide 11: Thank You Block 2 -->
@type: thankyou

## Block 2 완료

ML-Powered Operations & Anomaly Detection

:::notes
{timing: 0.5min}
Block 2가 끝났습니다. 5분 후 마지막 블록을 시작하겠습니다.
:::
