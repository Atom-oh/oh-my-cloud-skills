---
remarp: true
block: 02-intelligent-analysis
---

@type: cover

# AIOps: 지능형 클라우드 운영
Block 2 — 지능형 분석과 ML 기반 운영 (30 min)

Junseok Oh
Sr. Solutions Architect
AWS

:::notes
{timing: 1min}
{cue: 인사 및 블록 소개}
Block 2에서는 AWS의 ML 기반 운영 도구들을 심층적으로 다룹니다. DevOps Guru, Lookout for Metrics, CloudWatch Anomaly Detection, X-Ray 등 지능형 분석 서비스의 아키텍처와 실제 활용 패턴을 살펴보겠습니다. 이 블록을 통해 Rule 기반 모니터링의 한계를 넘어 ML이 어떻게 운영 효율성을 높이는지 이해하게 될 것입니다.
:::

---

@type: canvas
@canvas-id: devops-guru-arch

## DevOps Guru 아키텍처

:::canvas
icon cw "CloudWatch" at 80,120 size 48 step 1
icon xray "X-Ray" at 80,220 size 48 step 1
icon config "Config" at 80,320 size 48 step 1
box sources "Data Sources" at 55,380 size 100,30 color #3B48CC step 1

icon guru "DevOps-Guru" at 300,220 size 64 step 2
box ml "ML Analysis Engine" at 260,290 size 140,30 color #FF9900 step 2

icon insight "CloudWatch" at 520,150 size 48 step 3
box reactive "Reactive Insight" at 480,210 size 130,30 color #D93025 step 3

icon proactive "CloudWatch" at 520,280 size 48 step 4
box proactive-box "Proactive Insight" at 480,340 size 130,30 color #1A73E8 step 4

icon sns "SNS" at 720,220 size 48 step 5
box notify "Notification" at 695,280 size 100,30 color #FF9900 step 5

icon lambda "Lambda" at 880,220 size 48 step 6
box remediate "Auto Remediation" at 840,280 size 130,30 color #FF9900 step 6

arrow sources -> ml "메트릭/트레이스" step 2
arrow ml -> reactive "이상 탐지" step 3
arrow ml -> proactive-box "예측 분석" step 4
arrow reactive -> notify "알림" step 5
arrow proactive-box -> notify "알림" step 5
arrow notify -> remediate "트리거" step 6
:::

:::notes
{timing: 4min}
{cue: step 애니메이션으로 데이터 흐름 설명}
DevOps Guru의 핵심 아키텍처를 단계별로 설명합니다. Step 1: CloudWatch 메트릭, X-Ray 트레이스, Config 변경 이력이 데이터 소스로 수집됩니다. Step 2: ML 엔진이 이 데이터를 분석하여 정상 패턴을 학습합니다. Step 3-4: Reactive Insight는 현재 발생 중인 이상을, Proactive Insight는 미래에 발생할 수 있는 문제를 예측합니다. Step 5-6: SNS를 통해 알림을 보내고, Lambda로 자동 복구를 트리거할 수 있습니다. 화살표 키로 각 단계를 순차적으로 보여주세요.
:::

---

@type: tabs

## DevOps Guru 인사이트 유형

:::tabs
### Reactive Insight

**현재 발생 중인 이상 징후 탐지**

- 애플리케이션 성능 저하 감지 {.click}
- 리소스 고갈 패턴 식별 {.click}
- 최근 배포와의 상관관계 분석 {.click}

**실제 예시:**
> "Lambda 함수 `order-processor`의 duration이 p99 기준 300% 증가했습니다.
> 2시간 전 DynamoDB 테이블 `orders`의 쓰기 용량 조절과 연관됩니다."

---

### Proactive Insight

**미래에 발생할 문제 예측**

- 리소스 한계 도달 시점 예측 {.click}
- 비용 이상 증가 패턴 탐지 {.click}
- 성능 저하 조기 경보 {.click}

**실제 예시:**
> "현재 RDS 인스턴스 `prod-db`의 스토리지 증가율을 분석한 결과,
> 14일 내에 프로비저닝된 IOPS 한계에 도달할 것으로 예측됩니다."

---

### Anomaly Detection

**ML 기반 이상 패턴 식별**

- 계절성(seasonality) 자동 학습 {.click}
- 트렌드 변화 감지 {.click}
- Multi-metric 상관관계 분석 {.click}

**실제 예시:**
> "매주 월요일 09:00 트래픽 급증은 정상 패턴입니다.
> 그러나 오늘 화요일 14:00의 급증은 이전 패턴과 일치하지 않는 이상 징후입니다."

:::

:::notes
{timing: 4min}
{cue: 각 탭을 클릭하며 설명, 실제 예시 강조}
세 가지 인사이트 유형의 차이를 명확히 설명합니다. Reactive Insight는 '지금 문제가 있다'를 알려주고, Proactive Insight는 '곧 문제가 생길 것이다'를 예측하며, Anomaly Detection은 정상/비정상을 ML로 구분합니다. 실제 예시를 통해 각 유형이 어떤 상황에서 발생하는지 구체적으로 보여주세요. 청중에게 각자의 환경에서 어떤 유형이 가장 유용할지 질문해보는 것도 좋습니다.
:::

---

@type: content

## Lookout for Metrics

::: left
### 비즈니스 KPI 이상 탐지

- 매출, 주문량, 사용자 수 등 비즈니스 메트릭 모니터링 {.click}
- 최대 19개 차원(dimension)으로 세분화 분석 {.click}
- 이상 발생 시 근본 원인 자동 추론 {.click}
- 75+ 개 기여 요인(contributor) 자동 식별 {.click}
- Severity Score로 우선순위 결정 {.click}
:::

::: right
### 지원 데이터 소스

| 소스 | 연결 방식 |
|------|----------|
| **Amazon S3** | CSV/JSON 파일 직접 업로드 {.click} |
| **CloudWatch** | 메트릭 네임스페이스 연결 {.click} |
| **Amazon RDS** | Aurora/MySQL/PostgreSQL 직접 쿼리 {.click} |
| **Amazon Redshift** | SQL 기반 데이터 추출 {.click} |
| **AppFlow** | SaaS 데이터 연동 (Salesforce, Zendesk 등) {.click} |

:::

:::notes
{timing: 3min}
{cue: 좌우 컬럼 번갈아 설명}
Lookout for Metrics는 DevOps Guru와 다르게 비즈니스 KPI에 특화되어 있습니다. 왼쪽에서는 어떤 종류의 메트릭을 분석할 수 있는지, 오른쪽에서는 어떤 데이터 소스를 지원하는지 설명합니다. 핵심 차별점은 '차원 분석'입니다 - 예를 들어 매출 하락 시 어떤 지역, 어떤 제품, 어떤 채널에서 문제가 발생했는지 자동으로 드릴다운합니다. AppFlow 연동으로 Salesforce 같은 SaaS 데이터도 분석할 수 있다는 점을 강조하세요.
:::

---

@type: content

## CloudWatch Anomaly Detection

ML 기반으로 메트릭의 예상 범위(band)를 자동 계산하고, 이탈 시 알람을 발생시킵니다.

### 주요 특징

- 2주간의 학습 기간으로 계절성/트렌드 파악 {.click}
- 시간대별, 요일별 패턴 자동 학습 {.click}
- 임계값 수동 설정 불필요 - ML이 동적으로 결정 {.click}
- 기존 CloudWatch Alarm과 완전 통합 {.click}

### Anomaly Detection Alarm 설정 예시

```yaml
AlarmName: cpu-anomaly-detection
MetricName: CPUUtilization
Namespace: AWS/EC2
Stat: Average
Period: 300
EvaluationPeriods: 3
ComparisonOperator: LessThanLowerOrGreaterThanUpperThreshold
ThresholdMetricId: ad1
Metrics:
  - Id: m1
    MetricStat:
      Metric:
        MetricName: CPUUtilization
        Namespace: AWS/EC2
      Period: 300
      Stat: Average
  - Id: ad1
    Expression: ANOMALY_DETECTION_BAND(m1, 2)
```

:::notes
{timing: 3min}
{cue: YAML 코드 블록 하이라이트하며 설명}
CloudWatch Anomaly Detection의 가장 큰 장점은 '임계값을 몰라도 된다'는 것입니다. CPU 80%가 문제인지 90%가 문제인지 정하기 어려운 상황에서 ML이 알아서 판단합니다. YAML 예시에서 `ANOMALY_DETECTION_BAND(m1, 2)`는 예상 범위의 2 표준편차를 의미합니다. 숫자를 높이면 더 관대해지고, 낮추면 더 민감해집니다. 2주간 학습이 필요하므로 새 리소스에는 바로 적용하기 어렵다는 점도 언급하세요.
:::

---

@type: canvas
@canvas-id: xray-service-map

## X-Ray 분산 트레이싱

:::canvas
icon client "Mobile" at 60,200 size 48 step 1
box client-box "Client" at 40,260 size 90,30 color #232F3E step 1

icon apigw "API-Gateway" at 220,200 size 48 step 2
box apigw-box "API Gateway" at 190,260 size 110,30 color #FF9900 step 2
text latency1 "45ms" at 140,180 size 60,20 color #666666 step 2

icon lambda "Lambda" at 400,120 size 48 step 3
box lambda-box "Order Service" at 365,180 size 120,30 color #FF9900 step 3
text latency2 "120ms" at 310,100 color #D93025 step 3

icon lambda2 "Lambda" at 400,280 size 48 step 3
box lambda2-box "Auth Service" at 365,340 size 120,30 color #FF9900 step 3
text latency3 "30ms" at 310,260 color #666666 step 3

icon ddb "DynamoDB" at 600,120 size 48 step 4
box ddb-box "Orders Table" at 565,180 size 120,30 color #3B48CC step 4
text latency4 "85ms" at 500,100 color #D93025 step 4

icon cognito "Cognito" at 600,280 size 48 step 5
box cognito-box "User Pool" at 565,340 size 120,30 color #FF9900 step 5
text latency5 "25ms" at 500,260 color #666666 step 5

arrow client-box -> apigw-box "request" step 2
arrow apigw-box -> lambda-box "invoke" step 3
arrow apigw-box -> lambda2-box "auth" step 3
arrow lambda-box -> ddb-box "query" step 4
arrow lambda2-box -> cognito-box "verify" step 5
:::

**Service Map에서 병목 식별:** 빨간색 latency(120ms, 85ms)가 성능 저하 원인

:::notes
{timing: 4min}
{cue: step 애니메이션으로 요청 흐름 추적, 병목 지점 강조}
X-Ray Service Map을 통해 분산 시스템의 요청 흐름을 시각화합니다. Step별로 요청이 어떻게 전파되는지 보여주세요. Client → API Gateway → Lambda (병렬로 Order/Auth) → DynamoDB/Cognito. 빨간색 latency 텍스트로 표시된 120ms, 85ms가 병목입니다. Order Service Lambda의 DynamoDB 쿼리가 느린 것이 전체 응답 시간에 영향을 주고 있습니다. 실제 운영에서는 이런 병목을 찾아 DynamoDB DAX 캐시 적용이나 쿼리 최적화를 검토합니다.
:::

---

@type: steps

## 실전 패턴: 장애 시나리오 분석

:::steps
### Step 1: CloudWatch Alarm 발생
- **트리거:** API Gateway 5xx Error Rate > 5%
- **초기 정보:** 에러 급증 시작 시간, 영향받는 엔드포인트
- **조치:** 인시던트 생성, 온콜 엔지니어 호출

---

### Step 2: X-Ray 트레이스 분석
- **목표:** 어느 서비스에서 에러가 시작되었는지 추적
- **확인 사항:** Service Map에서 빨간색 노드 식별
- **발견:** `payment-service` Lambda에서 timeout 다수 발생

---

### Step 3: DevOps Guru 인사이트 확인
- **Reactive Insight:** "payment-service 성능 저하 탐지"
- **연관 이벤트:** 30분 전 RDS 인스턴스 failover 발생
- **추천 조치:** RDS connection pool 설정 검토

---

### Step 4: 근본 원인 식별
- **원인 체인:** RDS failover → DNS 전파 지연 → Lambda cold start 증가 → Connection timeout
- **증거:** CloudWatch Logs에서 connection refused 에러 확인
- **결론:** RDS Proxy 미사용으로 인한 connection 관리 문제

---

### Step 5: 자동 복구 실행
- **즉시 조치:** Lambda concurrency 일시 증가 (수동)
- **장기 해결:** RDS Proxy 도입 (자동화된 connection pooling)
- **검증:** Error rate 정상화, DevOps Guru insight 해소 확인
:::

:::notes
{timing: 4min}
{cue: 각 Step을 클릭하며 실제 장애 대응 흐름 설명}
실제 장애 시나리오를 5단계로 분석하는 패턴입니다. 핵심 메시지는 '단일 도구로는 부족하고, 여러 도구를 조합해야 한다'는 것입니다. CloudWatch Alarm은 '문제가 있다'만 알려주고, X-Ray는 '어디서 발생했다'를 보여주고, DevOps Guru는 '왜 발생했는지'와 '어떻게 해결할지'를 추천합니다. 청중에게 비슷한 경험이 있는지 물어보고, 각자의 환경에서 이 패턴을 어떻게 적용할 수 있을지 생각해보게 하세요.
:::

---

@type: compare

## ML 기반 vs Rule 기반 탐지 비교

::: left
### ML 기반 탐지

**장점**
- 임계값 설정 불필요 — 자동 학습 {.click}
- 계절성, 트렌드 변화 자동 반영 {.click}
- 알 수 없는 이상 패턴(unknown unknowns) 탐지 가능 {.click}
- False positive 감소 (컨텍스트 인식) {.click}

**단점**
- 2주 이상의 학습 기간 필요 {.click}
- 블랙박스 — 왜 알람이 발생했는지 설명 어려움 {.click}
- 새로운 워크로드에 즉시 적용 불가 {.click}

**적합한 상황**
> 패턴이 복잡하고 변동성이 큰 메트릭, 적절한 임계값을 모르는 경우
:::

::: right
### Rule 기반 탐지

**장점**
- 즉시 적용 가능 — 학습 기간 없음 {.click}
- 명확한 동작 — 왜 알람이 발생했는지 설명 가능 {.click}
- 규정 준수(Compliance) 요구사항 충족 용이 {.click}
- 비용 효율적 {.click}

**단점**
- 수동으로 임계값 튜닝 필요 {.click}
- 계절성 반영 어려움 (야간/주말 다른 임계값 필요) {.click}
- 알려진 패턴(known knowns)만 탐지 {.click}

**적합한 상황**
> SLA 기반 명확한 임계값이 있는 경우, 즉시 모니터링이 필요한 신규 서비스
:::

:::notes
{timing: 3min}
{cue: 좌우 비교하며 trade-off 강조}
ML 기반과 Rule 기반은 경쟁 관계가 아니라 보완 관계입니다. 핵심 메시지는 '둘 다 사용하라'입니다. Rule 기반은 '확실히 문제인 상황' (예: 디스크 90% 이상)에 사용하고, ML 기반은 '정상이 뭔지 모르는 상황' (예: 사용자 행동 패턴)에 사용합니다. 실무에서는 Critical 알람은 Rule 기반으로, Warning 수준 모니터링은 ML 기반으로 구성하는 것을 권장합니다.
:::

---

@type: content

## AIOps 분석 도구 선택 가이드

상황별로 최적의 AWS 서비스를 선택하세요:

| 분석 요구사항 | 추천 서비스 | 핵심 기능 |
|--------------|------------|----------|
| 메트릭 이상 탐지 | **CloudWatch Anomaly Detection** | ML 기반 동적 임계값 {.click} |
| 애플리케이션 운영 이상 | **DevOps Guru** | 인사이트 + 추천 조치 {.click} |
| 비즈니스 KPI 이상 | **Lookout for Metrics** | 다차원 기여 요인 분석 {.click} |
| 분산 시스템 병목 | **X-Ray** | Service Map + 트레이스 {.click} |
| 로그 기반 이상 탐지 | **CloudWatch Logs Insights** | 패턴 분석 + 쿼리 {.click} |
| 컨테이너 워크로드 | **Container Insights + DevOps Guru** | EKS/ECS 통합 모니터링 {.click} |

### 통합 권장 아키텍처

```
CloudWatch Metrics ──┬── Anomaly Detection Alarm ──┐
                     │                              │
X-Ray Traces ────────┼── DevOps Guru ──────────────┼── SNS ── Lambda (자동 복구)
                     │                              │
CloudWatch Logs ─────┴── Logs Insights ────────────┘
```

:::notes
{timing: 2min}
{cue: 테이블 행별로 클릭하며 설명, 통합 아키텍처 다이어그램으로 마무리}
도구 선택 가이드를 정리합니다. 핵심은 '하나의 도구로 모든 것을 해결하려 하지 마라'입니다. 각 도구는 특화된 영역이 있습니다. CloudWatch Anomaly Detection은 메트릭, DevOps Guru는 애플리케이션 전체, Lookout for Metrics는 비즈니스 KPI, X-Ray는 분산 추적입니다. 통합 아키텍처에서 보여주듯이 여러 소스를 DevOps Guru로 통합하고, 최종적으로 SNS + Lambda로 자동화하는 것이 권장 패턴입니다.
:::

---

@type: content

## Key Takeaways

### Block 2에서 배운 핵심 내용

1. **DevOps Guru는 Reactive + Proactive 인사이트를 제공합니다** {.click}
   - 현재 문제뿐 아니라 미래 문제도 예측
   - 근본 원인 분석과 추천 조치까지 자동화

2. **ML 기반 탐지는 Rule 기반과 보완적으로 사용하세요** {.click}
   - Critical 알람은 Rule 기반 (명확한 SLA)
   - Warning 모니터링은 ML 기반 (동적 임계값)

3. **X-Ray + DevOps Guru 조합이 장애 분석의 핵심입니다** {.click}
   - X-Ray로 '어디서' 문제가 발생했는지 추적
   - DevOps Guru로 '왜' 발생했는지, '어떻게' 해결할지 확인

---

### 다음 블록 예고

**Block 3: 자동화 성숙도 모델**에서는 수동 대응에서 완전 자동화까지의 성숙도 단계와 EventBridge, Systems Manager, Lambda를 활용한 자동 복구 구현을 다룹니다.

[← 목차로 돌아가기](./index.html)

:::notes
{timing: 2min}
{cue: Key Takeaways 강조, 질문 받기}
Block 2의 핵심을 3가지로 정리합니다. 청중에게 질문이 있는지 확인하고, 특히 DevOps Guru와 Lookout for Metrics의 차이, ML 기반 탐지의 학습 기간 등에 대한 질문이 나올 수 있습니다. 다음 Block 3에서는 이러한 탐지 결과를 어떻게 자동화된 복구로 연결하는지 다룰 것임을 예고합니다. 5분 휴식 후 Block 3를 시작합니다.
:::
