---
remarp: true
block: 03-automation-maturity
---

@type: cover
@background: ../common/pptx-theme/images/Picture_13.png
@badge: ../common/pptx-theme/images/Picture_8.png

# AIOps: 지능형 클라우드 운영
Block 3 — 자동화와 운영 성숙도 (30 min)

Junseok Oh
Sr. Solutions Architect
AWS

:::notes
{timing: 1min}
{cue: 환영}
Block 3의 시작입니다. 이번 블록에서는 AIOps의 핵심인 자동화 파이프라인과 운영 성숙도 모델을 다룹니다.
Block 1에서 관측성 기반을, Block 2에서 ML 기반 분석을 배웠으니, 이제 이를 실제 자동 복구로 연결하는 방법을 설명합니다.
30분 동안 EventBridge 기반 자동화부터 운영 성숙도 5단계까지 다루겠습니다.
:::

---
@type: canvas
@canvas-id: eventbridge-automation

## EventBridge 이벤트 기반 자동화

:::canvas
icon eb "Amazon-EventBridge" at 400,80 size 56 step 1
box eb-label "EventBridge" at 355,145 size 150,28 color #FF4F8B step 1

icon cw "Amazon-CloudWatch" at 100,80 size 48 step 2
box cw-label "CloudWatch" at 60,135 size 130,24 color #FF4F8B step 2

icon devops "Amazon-DevOps-Guru" at 100,220 size 48 step 2
box devops-label "DevOps Guru" at 55,275 size 140,24 color #FF4F8B step 2

icon ec2 "Amazon-EC2" at 100,360 size 48 step 2
box ec2-label "EC2 Events" at 60,415 size 130,24 color #FF9900 step 2

arrow cw-label -> eb-label "alarm events" step 3
arrow devops-label -> eb-label "insights" step 3
arrow ec2-label -> eb-label "state change" step 3

icon lambda "AWS-Lambda" at 650,80 size 48 step 4
box lambda-label "Lambda" at 615,135 size 120,24 color #FF9900 step 4

icon sfn "AWS-Step-Functions" at 650,220 size 48 step 4
box sfn-label "Step Functions" at 600,275 size 150,24 color #FF4F8B step 4

icon sns "Amazon-SNS" at 650,360 size 48 step 4
box sns-label "SNS" at 625,415 size 100,24 color #FF4F8B step 4

arrow eb-label -> lambda-label "rule match" step 5
arrow eb-label -> sfn-label "workflow trigger" step 5
arrow eb-label -> sns-label "notification" step 5
:::

:::notes
{timing: 3min}
{cue: 다이어그램 단계별 설명}
EventBridge는 AWS의 서버리스 이벤트 버스로, 모든 자동화의 중심 허브입니다.

Step 1: EventBridge가 중앙에 위치합니다.
Step 2: 이벤트 소스들 - CloudWatch Alarm, DevOps Guru Insight, EC2 상태 변경 등이 이벤트를 발생시킵니다.
Step 3: 각 소스에서 EventBridge로 이벤트가 흘러갑니다.
Step 4: 타겟 서비스들 - Lambda로 즉시 처리, Step Functions로 복잡한 워크플로우, SNS로 알림.
Step 5: 규칙 매칭을 통해 적절한 타겟으로 라우팅됩니다.

핵심: "이벤트 소스 → EventBridge 규칙 → 타겟 액션"의 패턴을 기억하세요.
:::

---
@type: tabs

## Lambda 자동 복구 패턴

::: tab EC2 Auto-Recovery
### EC2 인스턴스 자동 복구

**트리거**: CloudWatch Alarm (StatusCheckFailed)

```python
import boto3

def handler(event, context):
    ec2 = boto3.client('ec2')
    instance_id = event['detail']['instance-id']

    # 인스턴스 상태 확인
    response = ec2.describe_instance_status(
        InstanceIds=[instance_id]
    )

    # 복구 실행
    ec2.reboot_instances(InstanceIds=[instance_id])

    return {'status': 'recovered', 'instance': instance_id}
```

**검증**: 재부팅 후 상태 재확인
:::

::: tab ECS 재시작
### ECS 서비스 자동 재시작

**트리거**: 태스크 unhealthy 이벤트

```python
import boto3

def handler(event, context):
    ecs = boto3.client('ecs')
    cluster = event['detail']['clusterArn']
    service = event['detail']['serviceName']

    # 강제 새 배포로 태스크 교체
    ecs.update_service(
        cluster=cluster,
        service=service,
        forceNewDeployment=True
    )

    return {'status': 'restarted', 'service': service}
```

**검증**: 새 태스크 Running 상태 확인
:::

::: tab RDS Failover
### RDS 자동 Failover 처리

**트리거**: RDS 이벤트 (failover 시작)

```python
import boto3

def handler(event, context):
    rds = boto3.client('rds')
    db_instance = event['detail']['SourceIdentifier']

    # Failover 상태 모니터링
    response = rds.describe_db_instances(
        DBInstanceIdentifier=db_instance
    )

    # 애플리케이션 연결 풀 갱신 알림
    notify_app_teams(db_instance, 'failover_complete')

    return {'status': 'failover_handled', 'db': db_instance}
```

**검증**: Reader/Writer 엔드포인트 정상 확인
:::

:::notes
{timing: 4min}
{cue: 탭 전환하며 각 패턴 설명}
세 가지 대표적인 자동 복구 패턴입니다. 탭을 클릭하여 각각 살펴보겠습니다.

EC2 Auto-Recovery: StatusCheckFailed 알람 발생 시 인스턴스를 자동 재부팅합니다. 하드웨어 장애 시 다른 호스트로 마이그레이션됩니다.

ECS 재시작: 태스크가 unhealthy 상태가 되면 forceNewDeployment로 새 태스크를 시작합니다. 기존 태스크는 draining 후 종료됩니다.

RDS Failover: Multi-AZ 구성에서 자동 failover 발생 시, 애플리케이션에 알림을 보내 연결 풀을 갱신하도록 합니다.

공통 패턴: 트리거 → 상태 확인 → 복구 액션 → 검증의 4단계입니다.
:::

---
@type: content

## Systems Manager 자동화 문서

AWS Systems Manager Automation은 복잡한 운영 작업을 코드로 정의합니다.

::: left
### Automation 문서 구성요소

- **schemaVersion**: 문서 버전 (0.3) {.click}
- **description**: 자동화 설명 {.click}
- **mainSteps**: 실행할 단계들 {.click}
- **assumeRole**: 실행 IAM 역할 {.click}
- **parameters**: 입력 파라미터 {.click}
:::

::: right
### ECS 서비스 재시작 문서 예시

```yaml
schemaVersion: '0.3'
description: Restart unhealthy ECS service
assumeRole: '{{AutomationAssumeRole}}'
parameters:
  ClusterName:
    type: String
  ServiceName:
    type: String
mainSteps:
  - name: describeService
    action: aws:executeAwsApi
    inputs:
      Service: ecs
      Api: DescribeServices
      cluster: '{{ClusterName}}'
      services:
        - '{{ServiceName}}'
  - name: updateService
    action: aws:executeAwsApi
    inputs:
      Service: ecs
      Api: UpdateService
      cluster: '{{ClusterName}}'
      service: '{{ServiceName}}'
      forceNewDeployment: true
```
:::

:::notes
{timing: 3min}
{cue: 코드 블록 설명}
Systems Manager Automation은 AWS API 호출을 YAML로 정의하여 복잡한 운영 작업을 자동화합니다.

왼쪽의 구성요소를 하나씩 클릭하며 설명합니다:
- schemaVersion은 문서 형식 버전입니다
- mainSteps가 핵심으로, 순차적으로 실행할 AWS API 호출들을 정의합니다

오른쪽 예시는 ECS 서비스 재시작 문서입니다:
1. describeService: 현재 서비스 상태 조회
2. updateService: forceNewDeployment로 새 태스크 강제 시작

Automation 문서는 EventBridge 타겟으로 직접 연결하거나, Lambda에서 호출할 수 있습니다.
:::

---
@type: content
@layout: two-column

## Incident Manager 통합

::: left
### Incident Manager 핵심 기능

- **대응 계획 (Response Plan)** {.click}
  - 사전 정의된 복구 절차
  - 자동 런북 실행
- **에스컬레이션 (Escalation)** {.click}
  - 담당자 자동 호출
  - 시간 기반 단계별 확대
- **타임라인 (Timeline)** {.click}
  - 인시던트 전체 기록
  - 사후 분석용 데이터
- **협업 채널** {.click}
  - Slack/Teams 연동
  - 실시간 상태 공유
:::

::: right
### 통합 포인트

- **CloudWatch Alarms** {.click}
  - 알람 → 인시던트 자동 생성
  - 심각도 기반 대응 계획 선택
- **DevOps Guru Insights** {.click}
  - 이상 탐지 → 인시던트 연결
  - 권장 조치 자동 포함
- **EventBridge Rules** {.click}
  - 커스텀 이벤트 패턴 매칭
  - 복합 조건 인시던트 트리거
- **SSM Automation** {.click}
  - 인시던트 발생 시 런북 자동 실행
  - 복구 결과 타임라인에 기록
:::

:::notes
{timing: 3min}
{cue: 좌우 컬럼 번갈아 설명}
Incident Manager는 AWS의 통합 인시던트 관리 서비스입니다.

왼쪽 - 핵심 기능:
대응 계획으로 사전에 복구 절차를 정의해두고, 인시던트 발생 시 자동으로 실행합니다.
에스컬레이션은 담당자가 응답하지 않으면 자동으로 다음 단계 담당자에게 알립니다.
타임라인은 모든 이벤트를 기록하여 사후 분석(Post-Mortem)에 활용합니다.

오른쪽 - 통합 포인트:
CloudWatch 알람이 발생하면 자동으로 인시던트가 생성됩니다.
DevOps Guru의 이상 탐지 결과도 인시던트로 연결됩니다.
SSM Automation 런북이 인시던트와 함께 자동 실행됩니다.

핵심: 탐지 → 인시던트 생성 → 자동 대응 → 기록의 전체 사이클이 통합됩니다.
:::

---
@type: canvas
@canvas-id: automation-pipeline

## 자동화 파이프라인 전체 흐름

:::canvas
box detection "Detection" at 50,180 size 120,50 color #FF4F8B step 1
icon cw "Amazon-CloudWatch" at 75,100 size 36 step 1
icon devops "Amazon-DevOps-Guru" at 125,100 size 36 step 1

box routing "Routing" at 220,180 size 120,50 color #FF9900 step 2
icon eb "Amazon-EventBridge" at 265,100 size 40 step 2

box execution "Execution" at 390,180 size 120,50 color #FF9900 step 3
icon lambda "AWS-Lambda" at 405,100 size 32 step 3
icon ssm "AWS-Systems-Manager" at 455,100 size 32 step 3

box notification "Notification" at 560,180 size 130,50 color #FF4F8B step 4
icon sns "Amazon-SNS" at 580,100 size 32 step 4
icon im "AWS-Systems-Manager_Incident-Manager" at 635,100 size 32 step 4

box verification "Verification" at 740,180 size 130,50 color #3B48CC step 5
icon cw2 "Amazon-CloudWatch" at 790,100 size 36 step 5

arrow detection -> routing "event" step 2 animate-path
arrow routing -> execution "rule match" step 3 animate-path
arrow execution -> notification "result" step 4 animate-path
arrow notification -> verification "check" step 5 animate-path

box auto-close "Auto-Close" at 740,280 size 130,40 color #1D8102 step 5
arrow verification -> auto-close "success" step 5
:::

:::notes
{timing: 4min}
{cue: 파이프라인 단계별 설명}
전체 자동화 파이프라인을 5단계로 보여드립니다. 화살표 키로 각 단계를 진행하세요.

Step 1 - Detection (탐지):
CloudWatch Alarm 또는 DevOps Guru Insight가 이상을 감지합니다.

Step 2 - Routing (라우팅):
EventBridge가 이벤트를 수신하고, 규칙에 따라 적절한 타겟으로 라우팅합니다.

Step 3 - Execution (실행):
Lambda 함수 또는 SSM Automation이 실제 복구 작업을 수행합니다.

Step 4 - Notification (알림):
SNS로 담당자에게 알리고, Incident Manager에 인시던트를 기록합니다.

Step 5 - Verification (검증):
CloudWatch로 복구 상태를 확인하고, 정상이면 자동으로 인시던트를 종료합니다.

이 5단계가 AIOps 자동화의 핵심 루프입니다. 각 단계를 자동화할수록 MTTR이 단축됩니다.
:::

---
@type: steps
@steps-shape: circle

## 운영 성숙도 모델

- **Level 1: 수동 운영 (Manual)**
  모든 작업을 수동으로 수행, 문서화된 절차 없음
- **Level 2: 자동 알림 (Alerting)**
  모니터링 및 알림 체계 구축, 수동 대응
- **Level 3: 자동 진단 (Auto-Diagnosis)**
  이상 탐지 및 근본 원인 자동 분석, 권장 조치 제안
- **Level 4: 자동 복구 (Auto-Remediation)**
  사전 정의된 복구 절차 자동 실행, 인적 개입 최소화
- **Level 5: 예측 운영 (Predictive)**
  장애 예측 및 선제적 조치, 지속적 최적화

:::notes
{timing: 4min}
{cue: 각 레벨 순차 설명}
운영 성숙도 5단계 모델입니다. 대부분의 조직은 Level 2-3 사이에 있습니다.

Level 1 - 수동 운영:
장애 발생 시 담당자가 수동으로 진단하고 복구합니다. 문서화된 절차가 없어 속인 의존적입니다.

Level 2 - 자동 알림:
CloudWatch, Datadog 등으로 모니터링하고 알림을 받습니다. 하지만 대응은 여전히 수동입니다.

Level 3 - 자동 진단:
DevOps Guru, X-Ray 등이 근본 원인을 분석하고 권장 조치를 제안합니다. AIOps의 시작점입니다.

Level 4 - 자동 복구:
EventBridge + Lambda + SSM으로 자동 복구 파이프라인을 구축합니다. 오늘 배운 내용의 목표 수준입니다.

Level 5 - 예측 운영:
ML 기반으로 장애를 예측하고 선제적으로 조치합니다. Lookout for Metrics, Forecast 활용.

AnyCompany는 현재 어느 레벨에 계신가요? 목표는 Level 4입니다.
:::

---
@type: steps
@steps-shape: arrow

## AIOps 도입 로드맵

- **Phase 1 (1-3개월): 관측성 기반 구축**
  CloudWatch Container Insights, X-Ray 트레이싱, 로그 중앙화
- **Phase 2 (3-6개월): ML 기반 이상 탐지**
  DevOps Guru 활성화, Lookout for Metrics 연동, 알람 통합
- **Phase 3 (6-12개월): 자동 복구 파이프라인**
  EventBridge 규칙 설계, Lambda 복구 함수, SSM Automation 런북
- **Phase 4 (12개월+): 예측 운영과 지속 개선**
  예측 모델 구축, Chaos Engineering, 피드백 루프 최적화

:::notes
{timing: 3min}
{cue: 타임라인 단계별 설명}
AIOps 도입을 위한 현실적인 로드맵입니다.

Phase 1 (1-3개월):
먼저 관측성 기반을 구축합니다. Container Insights로 EKS 메트릭, X-Ray로 분산 트레이싱, CloudWatch Logs Insights로 로그 분석 환경을 갖춥니다.

Phase 2 (3-6개월):
DevOps Guru를 활성화하여 ML 기반 이상 탐지를 시작합니다. 기존 알람과 통합하여 노이즈를 줄입니다.

Phase 3 (6-12개월):
오늘 배운 자동 복구 파이프라인을 구축합니다. 가장 빈번한 장애 유형부터 자동화를 시작하세요.

Phase 4 (12개월 이후):
예측 모델을 구축하고, Chaos Engineering으로 복원력을 검증합니다. 지속적인 개선 사이클을 운영합니다.

권장: 한 번에 모든 것을 하려 하지 말고, 각 Phase를 완료한 후 다음으로 진행하세요.
:::

---
@type: content

## AnyCompany 맞춤 권장사항

현재 상태 분석과 다음 단계 권장사항입니다.

::: left
### 즉시 적용 가능 (Quick Wins)

1. **DevOps Guru 연동** {.click}
   - 현재 CloudWatch 알람 기반 → DevOps Guru 활성화
   - 기존 리소스 자동 검색, 추가 설정 최소화
   - 2주 내 이상 탐지 시작

2. **X-Ray 트레이싱 활성화** {.click}
   - 마이크로서비스 간 호출 가시성 확보
   - Lambda, API Gateway 자동 계측
   - 병목 구간 즉시 식별 가능
:::

::: right
### 중기 과제 (3-6개월)

3. **EventBridge 자동 복구 파이프라인** {.click}
   - 빈번한 장애 패턴 Top 3 자동화
   - EC2 재시작, ECS 재배포, RDS failover
   - SSM Automation 런북 라이브러리 구축

4. **Incident Manager 도입** {.click}
   - 대응 프로세스 표준화
   - 에스컬레이션 정책 수립
   - 사후 분석(Post-Mortem) 체계화
:::

:::notes
{timing: 4min}
{cue: AnyCompany 맞춤 제안}
AnyCompany의 현재 상태를 기반으로 구체적인 권장사항입니다.

즉시 적용 가능한 Quick Wins:

1. DevOps Guru 활성화
현재 CloudWatch 알람만 사용 중이시라면, DevOps Guru를 켜는 것만으로 ML 기반 이상 탐지가 가능합니다.
기존 CloudFormation 스택을 선택하면 자동으로 리소스를 검색합니다.

2. X-Ray 트레이싱
마이크로서비스 환경에서 서비스 간 호출 흐름을 시각화합니다.
Lambda, API Gateway는 콘솔에서 체크박스만 켜면 됩니다.

중기 과제:

3. 자동 복구 파이프라인
가장 빈번한 장애 유형 3가지를 먼저 자동화하세요.
오늘 보여드린 Lambda 패턴을 참고하시면 됩니다.

4. Incident Manager
대응 프로세스를 표준화하고, 사후 분석 체계를 갖추세요.
MTTR 측정과 개선의 기반이 됩니다.

질문 있으시면 세션 후 개별 상담 가능합니다.
:::

---
@type: content

## 감사합니다

::: left
### Key Takeaways

- **EventBridge**가 자동화의 중심 허브 {.click}
- **Lambda + SSM Automation**으로 복구 자동화 {.click}
- **Incident Manager**로 대응 프로세스 표준화 {.click}
- **운영 성숙도 Level 4**를 목표로 단계별 도입 {.click}
:::

::: right
### 다음 단계

- [AWS DevOps Guru 시작하기](https://docs.aws.amazon.com/devops-guru/)
- [EventBridge 패턴 라이브러리](https://serverlessland.com/patterns)
- [Incident Manager 설정 가이드](https://docs.aws.amazon.com/incident-manager/)

**Contact**
Junseok Oh | ohjs@amazon.com
:::

[← 목차로 돌아가기](index.html)

:::notes
{timing: 1min}
{cue: 마무리, Q&A 안내}
Block 3 자동화와 운영 성숙도를 마칩니다.

Key Takeaways를 클릭하며 복습합니다:
1. EventBridge는 모든 이벤트의 중앙 허브입니다
2. Lambda와 SSM Automation으로 복구를 자동화합니다
3. Incident Manager로 대응 프로세스를 표준화합니다
4. Level 4 자동 복구를 목표로 단계별로 도입하세요

90분 세션 전체를 완료하셨습니다. 수고하셨습니다!
오른쪽 링크들은 추가 학습 자료입니다.
질문이 있으시면 지금 받겠습니다. 또는 이메일로 연락 주세요.
:::
