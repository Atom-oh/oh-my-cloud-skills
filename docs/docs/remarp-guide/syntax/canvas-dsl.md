---
sidebar_position: 5
title: Canvas DSL
---

# Canvas DSL

Canvas DSL은 애니메이션 다이어그램을 선언적으로 작성하는 도메인 특화 언어입니다. 복잡한 JavaScript 없이도 단계별로 나타나는 아키텍처 다이어그램을 만들 수 있습니다.

## 기본 문법

```markdown
---
@type: canvas
@canvas-id: simple-arch

## Simple Architecture

:::canvas
box api "API Gateway" at 100,200 size 120,60 color #FF9900
box lambda "Lambda" at 300,200 size 120,60 color #FF9900
box dynamo "DynamoDB" at 500,200 size 120,60 color #3B48CC

arrow api -> lambda "invoke"
arrow lambda -> dynamo "read/write"
:::
```

:::tip
`@canvas-id`는 해당 canvas 요소의 고유 식별자입니다. 여러 canvas 슬라이드가 있을 때 구분하는 데 사용됩니다.
:::

## 도형 요소

### Box (박스)

사각형 박스를 그립니다.

```
box <id> "<label>" at <x>,<y> size <width>,<height> color <color> [step <n>]
```

```markdown
:::canvas
box user "User" at 50,100 size 80,40 color #232F3E
box web "Web App" at 200,100 size 100,50 color #FF9900 step 2
box db "Database" at 400,100 size 100,50 color #3B48CC step 3
:::
```

| 속성 | 설명 |
|------|------|
| `id` | 요소 식별자 (arrow 연결에 사용) |
| `label` | 박스 안에 표시될 텍스트 |
| `at x,y` | 왼쪽 상단 좌표 |
| `size w,h` 또는 `size wxh` | 너비와 높이 |
| `color` | 배경 색상 (CSS 색상 또는 `accent`, `green` 등 키워드) |
| `step n` | 해당 스텝에서 나타남 |

### Circle (원)

원을 그립니다.

```
circle <id> "<label>" at <x>,<y> radius <r> color <color> [step <n>]
```

```markdown
:::canvas
circle start "Start" at 50,100 radius 30 color #4CAF50
circle process "Process" at 200,100 radius 40 color #FF9900 step 2
circle end "End" at 350,100 radius 30 color #f44336 step 3
:::
```

### Icon (아이콘)

AWS 서비스 아이콘을 표시합니다.

```
icon <id> "<aws-service>" at <x>,<y> size <s> [step <n>]
```

```markdown
:::canvas
icon gw "API-Gateway" at 100,150 size 48
icon fn "Lambda" at 250,150 size 48 step 2
icon table "DynamoDB" at 400,150 size 48 step 3
:::
```

#### 지원되는 서비스 이름

| 이름 | 아이콘 |
|------|--------|
| `Lambda` | AWS Lambda |
| `EKS` | Amazon Elastic Kubernetes Service |
| `API-Gateway` | Amazon API Gateway |
| `DynamoDB` | Amazon DynamoDB |
| `S3` | Amazon S3 |
| `CloudWatch` | Amazon CloudWatch |
| `EC2` | Amazon EC2 |
| `VPC` | Virtual Private Cloud |
| `RDS` | Amazon RDS |
| `SQS` | Amazon SQS |
| `SNS` | Amazon SNS |
| `CloudFront` | Amazon CloudFront |
| `Route53` | Amazon Route 53 |
| `Cognito` | Amazon Cognito |
| `StepFunctions` | AWS Step Functions |
| `Fargate` | AWS Fargate |
| `ECS` | Amazon ECS |
| `ALB` | Elastic Load Balancing |
| `IAM` | AWS IAM |
| `KMS` | AWS KMS |

#### 전체 경로 참조

```markdown
:::canvas
icon custom "../common/aws-icons/services/Arch_Amazon-S3_48.svg" at 100,250 size 48
:::
```

### Arrow (화살표)

요소 간 연결을 그립니다.

```
arrow <from-id> -> <to-id> "<label>" [color <color>] [style <dashed|dotted>] [step <n>]
```

```markdown
:::canvas
box a "Service A" at 50,100 size 100,50 color #232F3E
box b "Service B" at 250,100 size 100,50 color #232F3E

arrow a -> b "HTTP" step 2
arrow b -> a "Response" color #4CAF50 style dashed step 3
:::
```

| 속성 | 설명 |
|------|------|
| `from-id -> to-id` | 시작과 끝 요소 |
| `label` | 화살표 레이블 |
| `color` | 화살표 색상 |
| `style` | `dashed` 또는 `dotted` |
| `step n` | 해당 스텝에서 나타남 |

### Group (그룹)

여러 요소를 묶는 경계 박스를 그립니다.

```
group "<label>" containing <id1>, <id2>, ... [color <color>] [step <n>]
```

```markdown
:::canvas
box web1 "Web 1" at 100,100 size 80,40 color #FF9900
box web2 "Web 2" at 100,160 size 80,40 color #FF9900
box web3 "Web 3" at 100,220 size 80,40 color #FF9900

group "Auto Scaling Group" containing web1, web2, web3 color #232F3E
:::
```

## 스텝 기반 애니메이션

`step N`을 사용하여 요소가 나타나는 순서를 제어합니다:

```markdown
---
@type: canvas
@canvas-id: data-flow

## Data Pipeline

:::canvas
# Step 1: Source appears first
icon s3src "S3" at 50,150 size 48 step 1
box source "Source Bucket" at 30,210 size 90,30 color #3B48CC step 1

# Step 2: Processing layer
icon lambda "Lambda" at 200,150 size 48 step 2
box transform "Transform" at 180,210 size 90,30 color #FF9900 step 2

# Step 3: Destination
icon s3dst "S3" at 350,150 size 48 step 3
box dest "Dest Bucket" at 330,210 size 90,30 color #3B48CC step 3

# Step 4: Arrows connect everything
arrow source -> transform "trigger" step 4
arrow transform -> dest "write" step 4
:::
```

:::info
`step`이 없는 요소는 슬라이드 진입 시 즉시 표시됩니다. 스텝은 `↑`/`↓` 키로 제어합니다.
:::

## 프리셋 DSL

복잡한 패턴을 위한 프리셋 시스템을 제공합니다:

### EKS Scaling 프리셋

```markdown
:::canvas
preset eks-scaling {
  cluster "Production EKS" at 40,30
    node "node-1" pods=3 max=4
    node "node-2" pods=2 max=4
    node "node-3" pods=1 max=4

  step 1 scale-out node=0 "Add pod to node-1"
  step 2 scale-out node=1 "Add pod to node-2"
  step 3 add-node "Add new node"
  step 4 scale-out node=3 "Schedule to new node"
}
:::
```

### 지원되는 프리셋

| 프리셋 | 설명 |
|--------|------|
| `eks-scaling` | EKS 클러스터 스케일링 시각화 |
| `serverless-flow` | Lambda 이벤트 흐름 |
| `vpc-architecture` | VPC 네트워크 다이어그램 |
| `cicd-pipeline` | CI/CD 파이프라인 |
| `data-pipeline` | 데이터 처리 파이프라인 |

### 프리셋 액션

| 액션 | 파라미터 | 설명 |
|------|----------|------|
| `scale-out` | `node=N` | 지정된 노드에 Pod 추가 |
| `scale-in` | `node=N` | 지정된 노드에서 Pod 제거 |
| `add-node` | 없음 | 클러스터에 새 노드 추가 |
| `remove-node` | `node=N` | 클러스터에서 노드 제거 |
| `migrate` | `node=N to=M` | 노드 간 Pod 이동 |

## Mermaid 통합

`:::canvas mermaid` 변형으로 Mermaid 다이어그램을 임베드할 수 있습니다:

```markdown
:::canvas mermaid
graph LR
    A[Client] --> B[API Gateway]
    B --> C[Lambda]
    C --> D[DynamoDB]
:::
```

### 지원되는 Mermaid 다이어그램 타입

- `graph` / `flowchart` - 플로우 다이어그램
- `sequenceDiagram` - 시퀀스 다이어그램
- `classDiagram` - 클래스 다이어그램
- `stateDiagram` - 상태 다이어그램
- `erDiagram` - ER 다이어그램
- `gantt` - 간트 차트
- `pie` - 파이 차트

## JavaScript Escape Hatch

DSL로 표현하기 어려운 복잡한 애니메이션은 JavaScript로 직접 작성할 수 있습니다:

```markdown
:::canvas js
const canvas = document.getElementById('complex-animation');
const ctx = canvas.getContext('2d');

// Custom animation logic
function animate() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  // ... custom drawing code
  requestAnimationFrame(animate);
}
animate();
:::
```

## 전체 예제

```markdown
---
@type: canvas
@canvas-id: api-pattern
@timing: 5min

## API Backend Pattern

:::canvas
box client "Client" at 30,150 size 80,40 color #232F3E step 1

icon apigw "API-Gateway" at 150,140 size 48 step 2
icon lambda "Lambda" at 280,140 size 48 step 3
icon dynamo "DynamoDB" at 410,140 size 48 step 4

arrow client -> apigw "HTTPS" step 5
arrow apigw -> lambda "invoke" step 5
arrow lambda -> dynamo "query" step 6

group "AWS Cloud" containing apigw, lambda, dynamo color #232F3E step 1
:::

:::notes
{timing: 5min}
{cue: demo}
각 컴포넌트가 나타날 때마다 역할을 설명합니다.
Step 5에서 전체 흐름을 설명합니다.
:::
```
