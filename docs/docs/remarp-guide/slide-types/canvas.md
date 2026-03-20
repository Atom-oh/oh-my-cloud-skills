---
sidebar_position: 3
title: Canvas 슬라이드
---

# Canvas 슬라이드

Canvas 슬라이드는 Canvas DSL을 사용하여 단계별 애니메이션 다이어그램을 표시합니다.

:::danger 4-Box Rule - Canvas 사용 전 필수 점검
Canvas는 **단순한 다이어그램에만** 사용합니다:

1. **박스+아이콘 총 개수 세기** - **4개 이하만** canvas 허용
2. **5개 이상이면 canvas 금지** - [HTML Architecture 패턴](#html-architecture-대안-박스-5-이상) 사용
3. 단방향 직선 흐름(A->B->C)만 canvas 허용
4. 다계층, 그룹, 분기가 있으면 `:::html` + `:::css` 필수

**STOP 자가 점검**: Canvas 코드를 작성하기 전에 확인하세요:
- [ ] 박스+아이콘 총 개수가 4개 이하인가?
- [ ] 단방향 직선 흐름(A->B->C->D)인가?
- [ ] 다계층, 그룹, 분기 화살표가 없는가?

하나라도 "아니오"라면 **canvas 사용을 중단**하고 `:::html` + `:::css` 패턴을 사용하세요.
:::

## 기본 문법

```markdown
---
@type: canvas
@canvas-id: my-diagram

## Architecture Diagram

:::canvas
box api "API Gateway" at 100,150 size 120,60 color #FF9900
box lambda "Lambda" at 300,150 size 120,60 color #4CAF50
arrow api -> lambda "invoke" step 1
:::
```

## 디렉티브

| 디렉티브 | 설명 |
|----------|------|
| `@type: canvas` | Canvas 타입 지정 (필수) |
| `@canvas-id` | Canvas 요소의 고유 ID (필수) |
| `@timing` | 예상 발표 시간 |
| `@background` | 배경 색상 |

## Canvas DSL 요소

자세한 Canvas DSL 문법은 [Canvas DSL](../syntax/canvas-dsl.md) 문서를 참조하세요.

### 요약

| 요소 | 문법 |
|------|------|
| Box | `box <id> "<label>" at x,y size w,h color #HEX` |
| Circle | `circle <id> "<label>" at x,y radius r color #HEX` |
| Icon | `icon <id> "<service>" at x,y size s` |
| Arrow | `arrow <from> -> <to> "<label>"` (직교 경로 자동 라우팅) |
| Group | `group "<label>" containing id1, id2, ...` |

## 예제

### 기본 아키텍처 다이어그램

```markdown
---
@type: canvas
@canvas-id: simple-arch
@timing: 3min

## Simple Architecture

:::canvas
box client "Client" at 50,150 size 80,40 color #232F3E step 1

icon apigw "API-Gateway" at 180,140 size 48 step 2
icon lambda "Lambda" at 320,140 size 48 step 3
icon dynamo "DynamoDB" at 460,140 size 48 step 4

arrow client -> apigw "HTTPS" step 5
arrow apigw -> lambda "invoke" step 5
arrow lambda -> dynamo "query" step 6
:::
```

### 데이터 파이프라인

```markdown
---
@type: canvas
@canvas-id: data-pipeline

## Data Processing Pipeline

:::canvas
icon s3in "S3" at 50,150 size 48 step 1
box source "Raw Data" at 30,210 size 90,30 color #3B48CC step 1

icon lambda "Lambda" at 200,150 size 48 step 2
box transform "Transform" at 180,210 size 90,30 color #FF9900 step 2

icon s3out "S3" at 350,150 size 48 step 3
box dest "Processed" at 330,210 size 90,30 color #3B48CC step 3

arrow source -> transform "trigger" step 4
arrow transform -> dest "write" step 5
:::

:::notes
{timing: 5min}
{cue: demo}
각 단계를 ↑↓ 키로 순서대로 보여주세요.
:::
```

### 그룹이 있는 아키텍처

```markdown
---
@type: canvas
@canvas-id: vpc-arch

## VPC Architecture

:::canvas
group "VPC" containing apigw, lambda, rds color=#232F3E step 1

icon apigw "API-Gateway" at 100,150 size 48 step 2
icon lambda "Lambda" at 250,150 size 48 step 3
icon rds "RDS" at 400,150 size 48 step 4

arrow apigw -> lambda "invoke" step 5
arrow lambda -> rds "query" style dashed step 6
:::
```

## 키보드 조작

| 키 | 동작 |
|----|------|
| `↓` | 다음 스텝으로 진행 |
| `↑` | 이전 스텝으로 돌아가기 |
| `←` / `→` | 이전/다음 슬라이드 |

## 렌더링

Canvas 슬라이드는 다음과 같은 HTML 구조로 렌더링됩니다:

```html
<div class="slide">
  <div class="slide-header"><h2>Title</h2></div>
  <div class="slide-body">
    <div class="canvas-container">
      <canvas id="my-diagram"></canvas>
    </div>
    <div class="btn-group">
      <button class="btn btn-primary" onclick="play()">Play</button>
      <button class="btn" onclick="reset()">Reset</button>
    </div>
  </div>
</div>
```

## 팁

:::tip
Canvas 슬라이드는 아키텍처 흐름을 단계별로 설명할 때 매우 효과적입니다. 발표 중 `↑`/`↓` 키로 각 단계를 제어하세요.
:::

:::warning
복잡한 다이어그램은 스텝을 5-7개 이하로 유지하세요. 너무 많은 스텝은 청중의 집중을 분산시킵니다.
:::

:::info
화살표는 직교(orthogonal) 라우팅으로 자동 변환됩니다. 대각선 대신 L자형/Z자형 직각 꺾임 경로가 생성되어 draw.io 스타일의 깔끔한 다이어그램이 만들어집니다. 자세한 내용은 [Canvas DSL — Arrow](../syntax/canvas-dsl.md#arrow-화살표) 문서를 참조하세요.
:::

:::info
Canvas DSL로 표현하기 어려운 복잡한 애니메이션은 `:::canvas js` 블록으로 JavaScript를 직접 작성할 수 있습니다.
:::

## HTML Architecture 대안 (박스 5+ 이상)

박스 5개 이상의 아키텍처/파이프라인은 **반드시** `:::html` + `:::css` 패턴을 사용합니다. Canvas DSL은 복잡한 레이아웃에서 요소 겹침과 정렬 문제가 발생하기 쉽습니다.

```markdown
## Service Pipeline

:::html
<div class="flow-h">
  <div class="flow-group bg-blue" data-fragment-index="1">
    <div class="flow-group-label">수집</div>
    <div class="icon-item"><img src="../common/aws-icons/services/Arch_Amazon-CloudWatch_48.svg"><span>CloudWatch</span></div>
    <div class="icon-item"><img src="../common/aws-icons/services/Arch_AWS-X-Ray_48.svg"><span>X-Ray</span></div>
  </div>
  <div class="flow-arrow">-></div>
  <div class="flow-group bg-orange" data-fragment-index="2">
    <div class="flow-group-label">분석</div>
    <div class="flow-box">DevOps Guru</div>
    <div class="flow-box">Bedrock</div>
  </div>
  <div class="flow-arrow">-></div>
  <div class="flow-group bg-pink" data-fragment-index="3">
    <div class="flow-group-label">대응</div>
    <div class="flow-box">EventBridge</div>
    <div class="flow-box">Lambda</div>
  </div>
</div>
:::
```

### HTML Architecture 장점

| 항목 | Canvas DSL | HTML Architecture |
|------|------------|-------------------|
| 정렬/간격 | 수동 좌표 계산 필요 | flexbox/grid 자동 처리 |
| 반응형 | 고정 크기 | 자동 조정 |
| 그룹화 | group 문법 제한적 | 자유로운 중첩 가능 |
| 순차 등장 | `step N` | `data-fragment-index="N"` |
| 유지보수 | 좌표 수정 번거로움 | CSS만 수정 |

### CSS 유틸리티 클래스

theme.css에서 제공하는 유틸리티 (커스텀 CSS 불필요):

- `flow-h` / `flow-v`: 수평/수직 플로우 컨테이너
- `flow-group`: 요소 그룹 (배경색 적용)
- `flow-group-label`: 그룹 라벨
- `flow-box`: 박스 요소
- `flow-arrow`: 화살표
- `icon-item`: 아이콘 + 라벨
- `bg-blue`, `bg-orange`, `bg-pink`, `bg-green`: 색상 유틸리티

## Canvas Prompt (LLM 지원)

`:::prompt` 블록으로 자연어로 원하는 다이어그램을 설명하면,
에이전트가 Canvas JS 코드를 자동 생성합니다.

```markdown
---
@type: canvas
@canvas-id: eks-flow

## EKS Communication Flow

:::prompt
EKS worker node의 kubelet이 control plane의 API server와
통신하는 모습. AWS 아이콘 사용.
Step 1: Control Plane (API Server) 표시
Step 2: Worker Node (kubelet) 표시
Step 3: 양방향 통신 화살표
:::
```

:::tip
`:::prompt`는 `:::canvas prompt`의 축약형입니다.
프롬프트를 수정한 뒤 "반영해주세요"로 재빌드하면 자동으로 Canvas JS로 변환됩니다.
:::

:::info
Canvas DSL로 직접 작성하고 싶다면 `:::canvas` 블록을,
JavaScript로 세밀한 제어가 필요하면 `:::canvas js` 블록을 사용하세요.
:::
