---
remarp: true
block: architecture
---

@type: cover
@background: ../common/pptx-theme/images/Picture_13.png
@badge: ../common/pptx-theme/images/Picture_8.png

# AIOps on AWS
AIOps 핵심 아키텍처와 AWS 서비스

@speaker: Junseok Oh
@title: Sr. Solutions Architect, AWS
@company: AnyCompany Technical Session

:::notes
{timing: 1min}
두 번째 블록을 시작하겠습니다. 이번 블록에서는 AWS 서비스를 중심으로 AIOps 아키텍처를 구체적으로 다룹니다. 각 서비스가 어떤 역할을 하고, 어떻게 연동하는지 실제 구성까지 살펴보겠습니다.

{cue: transition} 먼저 AIOps의 기반이 되는 관측성 파이프라인부터 보겠습니다.
:::

---

@type: canvas
@canvas-id: observability-pipeline

## 관측성 데이터 파이프라인

:::canvas
box app "Application (EKS/Lambda/EC2)" at 30,120 size 150,60 color #FF9900 step 1

box cw_agent "CloudWatch Agent" at 240,40 size 130,45 color #41B3FF step 2
box otel "ADOT Collector" at 240,110 size 130,45 color #41B3FF step 2
box fluent "Fluent Bit" at 240,180 size 130,45 color #41B3FF step 2

arrow app -> cw_agent "" step 2
arrow app -> otel "" step 2
arrow app -> fluent "" step 2

box cw_metrics "CloudWatch Metrics" at 430,20 size 140,45 color #AD5CFF step 3
box cw_logs "CloudWatch Logs" at 430,90 size 140,45 color #AD5CFF step 3
box xray "X-Ray Traces" at 430,160 size 140,45 color #AD5CFF step 3
box cw_ei "Application Signals" at 430,230 size 140,45 color #AD5CFF step 3

arrow cw_agent -> cw_metrics "" step 3
arrow fluent -> cw_logs "" step 3
arrow otel -> xray "" step 3
arrow otel -> cw_ei "" step 3

box anomaly "Anomaly Detection" at 630,50 size 140,50 color #00E500 step 4
box insight "Log Insights" at 630,140 size 140,50 color #00E500 step 4
box devguru "DevOps Guru" at 630,230 size 140,50 color #00E500 step 4

arrow cw_metrics -> anomaly "" step 4
arrow cw_logs -> insight "" step 4
arrow cw_ei -> devguru "" step 4
:::

:::notes
{timing: 3min}
AIOps의 첫 번째 단계는 데이터 수집입니다. 데이터 품질이 AIOps 결과의 80%를 결정합니다.

왼쪽의 애플리케이션에서 세 가지 에이전트로 데이터를 수집합니다. CloudWatch Agent는 시스템 메트릭과 커스텀 메트릭을, ADOT(AWS Distro for OpenTelemetry) Collector는 분산 트레이스를, Fluent Bit은 로그를 수집합니다.

EKS 환경이라면 ADOT을 DaemonSet으로 배포하는 것을 추천합니다. OpenTelemetry 표준을 따르기 때문에 벤더 락인 없이 메트릭, 로그, 트레이스를 모두 수집할 수 있습니다.

중앙의 CloudWatch에 데이터가 모이면, 오른쪽의 분석 레이어가 작동합니다. Anomaly Detection이 메트릭 이상을 탐지하고, Log Insights가 로그 패턴을 분석하고, DevOps Guru가 Application Signals 데이터를 기반으로 종합적인 인사이트를 제공합니다.

{cue: question} 여기서 핵심 포인트는 Application Signals입니다. 이것은 CloudWatch의 비교적 새로운 기능으로, APM 수준의 서비스 맵과 SLI/SLO 모니터링을 제공합니다.

{cue: transition} 이제 각 분석 서비스를 하나씩 깊이 있게 살펴보겠습니다.
:::

---

## CloudWatch Anomaly Detection

::: left
### 작동 원리

- **2주간 메트릭 학습** → 동적 baseline 생성 {.click}
- 계절성, 트렌드, 주기 패턴 자동 반영 {.click}
- Band 밖 이탈 시 ANOMALY_DETECTION_BAND 알림 {.click}
- 표준편차 기반 민감도 조절 (기본 2σ) {.click}
:::

::: right
### 설정 예시

```yaml
# CloudWatch Alarm - Anomaly Detection
AlarmName: api-latency-anomaly
MetricName: p99Latency
Namespace: MyApp/API
ComparisonOperator:
  LessThanLowerOrGreaterThanUpperThreshold
ThresholdMetricId: ad1
Metrics:
  - Id: m1
    MetricStat:
      Metric:
        MetricName: p99Latency
      Period: 300
      Stat: Average
  - Id: ad1
    Expression: ANOMALY_DETECTION_BAND(m1, 2)
```
:::

:::notes
{timing: 3min}
CloudWatch Anomaly Detection은 AIOps의 가장 쉬운 시작점입니다. 설정이 간단하면서도 효과가 큽니다.

작동 원리를 보면, 활성화하면 ML 모델이 최소 2주간의 메트릭 데이터를 학습합니다. 이때 일별, 주별 계절성 패턴을 자동으로 인식합니다. 예를 들어, 월요일 아침 트래픽이 급증하는 패턴이 있다면 이것을 정상으로 학습합니다.

오른쪽의 설정 예시를 보면, 핵심은 ANOMALY_DETECTION_BAND 함수입니다. 두 번째 파라미터 '2'가 표준편차입니다. 2를 사용하면 약 95% 신뢰구간을 의미합니다. 이 값을 1로 줄이면 민감도가 높아지고, 3으로 올리면 정말 심각한 이상만 탐지합니다.

실무 팁을 하나 드리면, 처음에는 2σ로 시작해서 false positive가 많으면 3σ로, 놓치는 이상이 있으면 1.5σ로 조절하세요. 메트릭별로 다르게 설정하는 것이 좋습니다. Latency는 2σ, Error Rate는 1.5σ로 더 민감하게 설정하는 식입니다.

{cue: transition} 다음은 더 높은 수준의 분석을 제공하는 DevOps Guru입니다.
:::

---

## Amazon DevOps Guru

:::click
### 핵심 기능
- **ML 기반 이상 탐지**: 70+ AWS 서비스의 메트릭 자동 분석
- **관련 이벤트 그룹핑**: Insight 단위로 연관 이벤트 묶음
- **근본 원인 추적**: 배포, 설정 변경, 리소스 변경과 연결
- **권장 조치**: 각 Insight에 대한 구체적 해결 방안 제시
:::

:::click
### Insight 유형
| 유형 | 설명 | 예시 |
|------|------|------|
| **Reactive** | 이미 발생한 이상 | Lambda 에러율 급증 + API GW 5xx 증가 |
| **Proactive** | 발생 예측되는 이상 | DynamoDB 읽기 용량 소진 임박 |
:::

:::click
### 커버리지 설정
```bash
# CloudFormation 스택 기반 (권장)
aws devops-guru update-resource-collection \
  --action ADD \
  --resource-collection '{"CloudFormation":{"StackNames":["prod-*"]}}'

# 태그 기반
aws devops-guru update-resource-collection \
  --action ADD \
  --resource-collection '{"Tags":[{"AppBoundaryKey":"app","TagValues":["myapp"]}]}'
```
:::

:::notes
{timing: 3min}
DevOps Guru는 AIOps Level 3를 구현하는 핵심 서비스입니다. 단순한 이상 탐지를 넘어서 "왜 이 문제가 발생했는가"까지 분석합니다.

70개 이상의 AWS 서비스에서 메트릭을 자동으로 수집하고 ML로 분석합니다. 가장 강력한 기능은 관련 이벤트 그룹핑입니다. Lambda 에러율 급증, API Gateway 5xx 증가, DynamoDB 쓰기 지연 — 이 세 이벤트를 하나의 Insight로 묶어서 "DynamoDB 쓰기 용량 초과가 근본 원인"이라고 알려줍니다.

Proactive Insight도 중요합니다. 문제가 발생하기 전에 "이 추세라면 3시간 후 DynamoDB 읽기 용량이 소진됩니다"라고 경고합니다.

커버리지 설정은 CloudFormation 스택 기반을 권장합니다. prod-로 시작하는 모든 스택을 모니터링하면 새 서비스가 추가될 때 자동으로 포함됩니다. 태그 기반도 가능하지만 태그 관리가 잘 되어 있어야 합니다.

{cue: transition} 이제 DevOps Guru의 실제 활용 아키텍처를 살펴보겠습니다.
:::

---

@type: canvas
@canvas-id: devops-guru-arch

## DevOps Guru 연동 아키텍처

:::canvas
box app "EKS Workloads" at 30,80 size 120,50 color #FF9900 step 1
box lambda "Lambda Functions" at 30,160 size 120,50 color #FF9900 step 1
box rds "RDS / Aurora" at 30,240 size 120,50 color #FF9900 step 1

box devguru "Amazon DevOps Guru" at 250,150 size 160,70 color #AD5CFF step 2

arrow app -> devguru "" step 2
arrow lambda -> devguru "" step 2
arrow rds -> devguru "" step 2

box insight "Insight Generated" at 490,80 size 130,50 color #00E500 step 3
box sns "Amazon SNS" at 490,160 size 130,50 color #FF9900 step 3
box eb "Amazon EventBridge" at 490,240 size 130,50 color #FF9900 step 4

arrow devguru -> insight "" step 3
arrow devguru -> sns "" step 3
arrow devguru -> eb "" step 4

box slack "Slack / PagerDuty" at 690,110 size 120,45 color #41B3FF step 3
box ssm "SSM Automation" at 690,200 size 120,45 color #41B3FF step 4
box jira "Jira / OpsItem" at 690,270 size 120,45 color #41B3FF step 4

arrow sns -> slack "" step 3
arrow eb -> ssm "" step 4
arrow eb -> jira "" step 4
:::

:::notes
{timing: 3min}
DevOps Guru를 중심으로 한 연동 아키텍처입니다.

왼쪽의 워크로드들 — EKS, Lambda, RDS — 에서 메트릭이 자동으로 DevOps Guru로 흐릅니다. 별도 에이전트 설치 없이 CloudWatch 메트릭을 ML로 분석합니다.

DevOps Guru가 Insight를 생성하면 두 가지 경로로 전달됩니다. SNS를 통해 Slack이나 PagerDuty로 알림이 가고, EventBridge를 통해 자동화 워크플로우가 트리거됩니다.

EventBridge 연동이 핵심입니다. DevOps Guru Insight 이벤트를 EventBridge 룰로 잡아서, SSM Automation 문서를 실행하거나 Jira 티켓을 자동 생성할 수 있습니다. 예를 들어 "RDS CPU 이상" Insight가 오면 자동으로 Read Replica를 추가하는 SSM 문서를 실행하는 것이 가능합니다.

이것이 바로 Level 3에서 Level 4로 넘어가는 경계입니다 — 이상 탐지에서 자동 복구로의 전환입니다.

{cue: transition} CloudWatch의 최신 AI 기능들도 함께 살펴보겠습니다.
:::

---

## CloudWatch AI/ML 기능 총정리

@type: tabs

::: tab "Anomaly Detection"
### Anomaly Detection
- **대상**: 모든 CloudWatch 메트릭
- **학습 기간**: 최소 2주 (14일)
- **모델**: 자체 ML 모델 (계절성, 트렌드)
- **비용**: 메트릭당 $3/월
- **권장 적용**: Latency (p99), Error Rate, 주요 비즈니스 메트릭

```
ANOMALY_DETECTION_BAND(m1, 2)  # 2σ band
```
:::

::: tab "Log Anomaly Detection"
### Log Anomaly Detection
- **대상**: CloudWatch Logs 로그 그룹
- **방식**: 로그 패턴 자동 클러스터링 + 빈도 이상 탐지
- **핵심**: 새로운 로그 패턴 출현 자동 감지
- **비용**: Log Insights 요금에 포함
- **활용**: 배포 후 새로운 에러 패턴 즉시 탐지

```bash
# Log Anomaly Detection 활성화
aws logs put-account-policy \
  --policy-name log-anomaly \
  --policy-type LOG_ANOMALY_DETECTION \
  --policy-document '{}'
```
:::

::: tab "Application Signals"
### Application Signals (APM)
- **대상**: EKS, EC2, Lambda 워크로드
- **수집**: ADOT + CloudWatch Agent 자동 계측
- **기능**: 서비스 맵, SLI/SLO, 종속성 추적
- **핵심**: 코드 변경 없이 APM 수준 관측성
- **비용**: 트레이스 수 기준 과금

```yaml
# EKS ADOT add-on으로 자동 계측
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig
addons:
  - name: adot
    version: latest
```
:::

::: tab "Natural Language Query"
### Natural Language Query
- **대상**: CloudWatch Logs, Metrics
- **방식**: 자연어로 로그/메트릭 질의
- **예시**: "지난 1시간 동안 5xx 에러가 가장 많은 API는?"
- **활용**: 장애 대응 시 빠른 데이터 탐색
- **상태**: GA (2025~)

> "Show me the Lambda functions with the highest error rate in the last hour"
:::

:::notes
{timing: 4min}
CloudWatch의 AI/ML 기능을 탭별로 정리했습니다.

Anomaly Detection은 이미 설명드렸고, 실무에서는 모든 메트릭에 적용하지 마세요. 핵심 비즈니스 메트릭 — API Latency p99, Error Rate, 주문 처리량 같은 것에만 적용하는 것이 비용 대비 효과적입니다. 메트릭당 월 3달러이므로 100개면 300달러입니다.

Log Anomaly Detection은 강력합니다. 배포 후 기존에 없던 새로운 에러 패턴이 나타나면 즉시 알려줍니다. "이 에러 메시지는 이전에 한 번도 본 적 없는 패턴입니다" — 이런 알림이 옵니다.

Application Signals는 APM 기능입니다. ADOT를 설치하면 코드 변경 없이 서비스 간 호출 관계, 레이턴시, 에러율을 자동으로 수집합니다. Datadog이나 New Relic 같은 APM을 별도로 도입하지 않아도 기본적인 APM을 AWS 네이티브로 구현할 수 있습니다.

Natural Language Query는 장애 대응 시 유용합니다. 복잡한 Log Insights 쿼리를 작성할 필요 없이 자연어로 질문하면 됩니다.

{cue: transition} 이제 Amazon Q Developer의 운영 지원 기능을 보겠습니다.
:::

---

## Amazon Q Developer — 운영 지원

::: left
### 주요 기능

- **자연어 트러블슈팅** {.click}
  - "이 ECS 서비스가 왜 계속 재시작하지?"
  - "RDS 연결이 가끔 끊기는 원인은?"

- **콘솔 통합** {.click}
  - CloudWatch, EC2, ECS 콘솔에서 직접 질문
  - 컨텍스트 인식 — 현재 보고 있는 리소스 기반 답변

- **운영 조사 (Investigation)** {.click}
  - CloudWatch 알람 트리거 → 자동 조사 시작
  - 관련 메트릭, 로그, 변경사항 자동 수집
  - 근본 원인 분석 보고서 생성
:::

::: right
### 활용 시나리오

```
[03:00 AM] CloudWatch Alarm triggered
  ↓ EventBridge Rule
[03:00] Amazon Q Investigation 시작
  ↓ 자동 분석
[03:02] 분석 결과:
  - RDS CPU 95% (baseline: 40%)
  - 원인: slow query (table scan)
  - 관련: 02:55 배포 (new feature)
  - 권장: 해당 쿼리에 인덱스 추가
  ↓ SNS → Slack
[03:02] 엔지니어에게 요약 전달
```
:::

:::notes
{timing: 3min}
Amazon Q Developer는 AWS 운영의 AI 어시스턴트입니다. 세 가지 핵심 기능을 살펴보겠습니다.

첫째, 자연어 트러블슈팅입니다. AWS 콘솔에서 "이 ECS 서비스가 왜 재시작하는지" 물어보면, 해당 서비스의 로그, 메트릭, 이벤트를 분석해서 답변합니다.

둘째, 콘솔 통합입니다. EC2 인스턴스 상세 페이지에서 Q를 호출하면, 그 인스턴스의 컨텍스트를 이미 알고 있습니다. "이 인스턴스 왜 느려?"라고 물어보면 해당 인스턴스의 CPU, 메모리, 네트워크를 분석합니다.

가장 강력한 건 운영 조사 기능입니다. 오른쪽 시나리오를 보세요. 새벽 3시에 알람이 트리거되면 Amazon Q가 자동으로 조사를 시작합니다. 2분 만에 "RDS CPU가 95%인데, 원인은 02:55에 배포된 새 기능의 slow query"라고 분석 결과를 Slack으로 보내줍니다. 엔지니어가 일어나서 볼 때쯤이면 이미 원인 분석이 끝나있습니다.

{cue: transition} 이제 자동 복구까지 연결하는 EventBridge + SSM 아키텍처를 보겠습니다.
:::

---

@type: canvas
@canvas-id: auto-remediation

## 자동 복구 아키텍처

:::canvas
box alarm "CloudWatch Alarm" at 30,60 size 130,50 color #41B3FF step 1
box devguru2 "DevOps Guru Insight" at 30,140 size 130,50 color #AD5CFF step 1
box health "AWS Health Event" at 30,220 size 130,50 color #00E500 step 1

box eb "Amazon EventBridge" at 230,130 size 150,70 color #FF9900 step 2

arrow alarm -> eb "" step 2
arrow devguru2 -> eb "" step 2
arrow health -> eb "" step 2

box rule1 "High CPU -> Scale Out" at 440,40 size 170,50 color #41B3FF step 3
box rule2 "Memory Leak -> Restart" at 440,110 size 170,50 color #AD5CFF step 3
box rule3 "AZ Impaired -> Failover" at 440,180 size 170,50 color #00E500 step 3
box rule4 "Unknown -> Create Ticket" at 440,250 size 170,50 color #FBD332 step 3

arrow eb -> rule1 "" step 3
arrow eb -> rule2 "" step 3
arrow eb -> rule3 "" step 3
arrow eb -> rule4 "" step 3

box ssm "SSM Runbook" at 680,40 size 120,50 color #FF9900 step 4
box ssm2 "SSM Runbook" at 680,110 size 120,50 color #FF9900 step 4
box ssm3 "SSM Runbook" at 680,180 size 120,50 color #FF9900 step 4
box jira "Jira + PagerDuty" at 680,250 size 120,50 color #FBD332 step 4

arrow rule1 -> ssm "" step 4
arrow rule2 -> ssm2 "" step 4
arrow rule3 -> ssm3 "" step 4
arrow rule4 -> jira "" step 4
:::

:::notes
{timing: 3min}
이것이 AIOps Level 4의 핵심 아키텍처입니다 — 자동 복구입니다.

왼쪽에서 세 가지 이벤트 소스가 EventBridge로 흘러들어옵니다. CloudWatch Alarm, DevOps Guru Insight, AWS Health Event — 이 세 가지가 대부분의 운영 이벤트를 커버합니다.

EventBridge에서 이벤트 패턴 매칭 룰을 설정합니다. High CPU면 Scale Out Runbook을 실행하고, Memory Leak이면 Rolling Restart를, AZ 장애면 Failover를 실행합니다. 패턴에 매칭되지 않는 미지의 이벤트는 Jira 티켓을 생성하고 PagerDuty로 엔지니어를 호출합니다.

핵심 설계 원칙은 "알려진 문제는 자동화, 모르는 문제는 사람에게" 입니다. 모든 것을 자동화하려고 하면 위험합니다. 신뢰할 수 있는 패턴만 자동화하고, 나머지는 분석 결과와 함께 사람에게 넘기세요.

SSM Runbook은 단계별 승인(approval step)을 포함할 수 있습니다. 처음에는 "자동 분석 + 수동 승인 + 자동 실행"으로 시작하고, 신뢰가 쌓이면 승인 단계를 제거하는 점진적 접근을 권장합니다.

{cue: transition} SSM Automation Runbook의 실제 예시를 보겠습니다.
:::

---

## SSM Automation Runbook 예시

@type: tabs

::: tab "Auto Scaling"
### ECS Auto-Scale Runbook
```yaml
description: AIOps - ECS Service Scale Out
schemaVersion: '0.3'
parameters:
  ClusterName:
    type: String
  ServiceName:
    type: String
  DesiredCount:
    type: Integer
    default: 4
mainSteps:
  - name: getCurrentCount
    action: aws:executeAwsApi
    inputs:
      Service: ecs
      Api: DescribeServices
      cluster: '{{ClusterName}}'
      services: ['{{ServiceName}}']
    outputs:
      - Name: currentCount
        Selector: $.services[0].desiredCount
        Type: Integer

  - name: scaleOut
    action: aws:executeAwsApi
    inputs:
      Service: ecs
      Api: UpdateService
      cluster: '{{ClusterName}}'
      service: '{{ServiceName}}'
      desiredCount: '{{DesiredCount}}'

  - name: waitStable
    action: aws:waitForAwsResourceProperty
    inputs:
      Service: ecs
      Api: DescribeServices
      cluster: '{{ClusterName}}'
      services: ['{{ServiceName}}']
      PropertySelector: $.services[0].deployments[0].runningCount
      DesiredValues: ['{{DesiredCount}}']
```
:::

::: tab "Rolling Restart"
### EKS Rolling Restart Runbook
```yaml
description: AIOps - EKS Deployment Rolling Restart
schemaVersion: '0.3'
parameters:
  ClusterName:
    type: String
  Namespace:
    type: String
  DeploymentName:
    type: String
mainSteps:
  - name: updateKubeconfig
    action: aws:runCommand
    inputs:
      DocumentName: AWS-RunShellScript
      Parameters:
        commands:
          - aws eks update-kubeconfig
              --name {{ClusterName}}
          - kubectl rollout restart deployment
              {{DeploymentName}}
              -n {{Namespace}}

  - name: verifyRollout
    action: aws:runCommand
    inputs:
      DocumentName: AWS-RunShellScript
      Parameters:
        commands:
          - kubectl rollout status deployment
              {{DeploymentName}}
              -n {{Namespace}}
              --timeout=300s
```
:::

::: tab "EventBridge Rule"
### EventBridge Rule 설정
```json
{
  "source": ["aws.devops-guru"],
  "detail-type": ["DevOps Guru New Insight Open"],
  "detail": {
    "insightSeverity": ["HIGH"],
    "resourceCollection": {
      "cloudFormation": {
        "stackNames": [{
          "prefix": "prod-"
        }]
      }
    }
  }
}
```

Target 설정:
```json
{
  "Arn": "arn:aws:ssm:ap-northeast-2:
    123456789:automation-definition/
    AIOps-AutoScale",
  "Input": {
    "ClusterName": "prod-cluster",
    "ServiceName": "<$.detail.resourceName>"
  }
}
```
:::

:::notes
{timing: 4min}
실제 SSM Automation Runbook 예시를 3가지 탭으로 보여드리겠습니다.

첫 번째 탭은 ECS Auto-Scale입니다. 현재 task 수를 확인하고, 원하는 수로 스케일 아웃하고, 안정화될 때까지 대기합니다. aws:waitForAwsResourceProperty 단계가 핵심인데, 스케일 아웃 후 실제로 컨테이너가 뜰 때까지 기다립니다.

두 번째 탭은 EKS Rolling Restart입니다. 메모리 릭이 감지되면 kubectl rollout restart로 Pod를 순차 재시작합니다. rollout status로 완료를 확인하는 것도 포함됩니다.

세 번째 탭이 이 Runbook들을 트리거하는 EventBridge Rule입니다. DevOps Guru에서 HIGH severity Insight가 prod-으로 시작하는 스택에서 발생하면 SSM Automation을 실행합니다. detail에서 resourceName을 추출해서 파라미터로 넘기는 부분이 중요합니다.

실무 팁으로, 처음 구축할 때는 Runbook 마지막에 SNS 알림 단계를 추가해서 "자동으로 이런 조치를 수행했습니다"라고 팀에 알려주세요. 자동화가 무엇을 했는지 가시성을 유지하는 것이 중요합니다.

{cue: transition} 이제 GenAI를 활용한 AIOps 고급 패턴을 살펴보겠습니다.
:::

---

## Bedrock 기반 AIOps Agent

::: left
### 아키텍처 개요

**Bedrock Agent** + **Knowledge Base**로 커스텀 AIOps 에이전트 구축 {.click}

- **Knowledge Base**: 운영 매뉴얼, Runbook, 과거 장애 보고서 {.click}
- **Agent Tools**: CloudWatch API, SSM, ECS/EKS API {.click}
- **활용**: 자연어로 운영 작업 수행 {.click}

> "prod-api 서비스의 지난 1시간 에러율을 확인하고,
> 50%를 넘으면 이전 버전으로 롤백해줘" {.click}
:::

::: right
### Agent Action Groups

```python
# Bedrock Agent - Action Group 정의
action_groups = [
    {
        "name": "CloudWatchActions",
        "actions": [
            "GetMetricData",
            "DescribeAlarms",
            "GetLogEvents"
        ]
    },
    {
        "name": "ECSActions",
        "actions": [
            "UpdateService",
            "DescribeServices",
            "ListTasks"
        ]
    },
    {
        "name": "SSMActions",
        "actions": [
            "StartAutomationExecution",
            "GetAutomationExecution"
        ]
    }
]
```
:::

:::notes
{timing: 3min}
이것은 AIOps Level 5를 향한 최신 접근법입니다. Amazon Bedrock Agent와 Knowledge Base를 활용해서 커스텀 AIOps 에이전트를 구축합니다.

Knowledge Base에 여러분 조직의 운영 매뉴얼, Runbook 문서, 과거 장애 보고서를 넣습니다. 그러면 Agent가 이 지식을 기반으로 판단합니다. "과거에 비슷한 상황에서 어떻게 해결했지?"를 AI가 참조할 수 있게 되는 겁니다.

Agent의 Action Group은 실제로 실행할 수 있는 AWS API를 정의합니다. CloudWatch에서 메트릭을 조회하고, ECS 서비스를 업데이트하고, SSM Runbook을 실행하는 것을 자연어 명령으로 할 수 있습니다.

예를 들어 "prod-api의 에러율 확인하고 50% 넘으면 롤백해줘"라고 하면, Agent가 CloudWatch API로 에러율을 확인하고, 조건에 맞으면 ECS 서비스를 이전 task definition으로 업데이트합니다.

다만 주의할 점은, 프로덕션 환경에서는 반드시 Human-in-the-Loop를 설정하세요. Agent가 제안만 하고 실행은 사람이 승인하는 방식으로 시작하는 것이 안전합니다.

{cue: transition} 이 블록의 핵심을 정리하겠습니다.
:::

---

## Block 2 — Key Takeaways

:::click
**관측성 파이프라인이 기반**: ADOT + CloudWatch로 메트릭/로그/트레이스 통합 수집
데이터 품질이 AIOps 결과의 80%를 결정합니다
:::

:::click
**DevOps Guru = L3 핵심 서비스**: 자동 이상 탐지 + 이벤트 상관분석 + 근본 원인 추적
CloudFormation 스택 기반 커버리지로 쉽게 시작 가능
:::

:::click
**EventBridge + SSM = L4 자동 복구**: 알려진 패턴은 자동화, 미지의 패턴은 사람에게
점진적 자동화 — 분석 → 승인 → 실행 → 완전 자동화
:::

:::click
**Bedrock Agent = 미래 방향**: 자연어 운영 + Knowledge Base 기반 의사결정
Human-in-the-Loop로 안전하게 시작
:::

:::notes
{timing: 2min}
두 번째 블록의 핵심을 네 가지로 정리합니다.

첫째, 관측성 파이프라인이 모든 것의 기반입니다. ADOT과 CloudWatch로 메트릭, 로그, 트레이스를 통합 수집하세요. 데이터가 부족하면 AI가 아무리 뛰어나도 좋은 결과를 낼 수 없습니다.

둘째, DevOps Guru가 Level 3의 핵심입니다. 활성화만 하면 ML이 자동으로 이상을 탐지하고 근본 원인을 추적합니다.

셋째, EventBridge와 SSM Automation으로 Level 4 자동 복구를 구현합니다. "알려진 문제는 자동화, 모르는 문제는 사람에게" — 이 원칙을 지키세요.

넷째, Bedrock Agent는 미래 방향입니다. 지금 당장은 PoC로 시작하고, 신뢰가 쌓이면 점진적으로 확대하세요.

{cue: transition} 다음 블록에서는 이 아키텍처를 실제로 어떻게 구현하고, 어떤 Best Practices를 따라야 하는지 구체적으로 다루겠습니다.
:::
