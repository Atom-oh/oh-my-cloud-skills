---
sidebar_position: 2
title: 디렉티브
---

# 디렉티브

디렉티브는 개별 슬라이드의 동작을 제어합니다. `---` 슬라이드 구분선 바로 다음에 `@` 접두사로 작성합니다.

## 기본 문법

```markdown
---
@type: compare
@layout: two-column
@transition: zoom
@background: linear-gradient(135deg, #232F3E, #1a1a2e)
@class: highlight-slide
@timing: 3min
@canvas-id: arch-flow

## Slide Title
```

:::tip
디렉티브는 슬라이드 내용 전에 작성해야 합니다. 제목(`##`)이나 본문보다 먼저 나와야 합니다.
:::

## 디렉티브 레퍼런스

### @type

슬라이드의 유형을 지정합니다.

| 값 | 설명 |
|----|------|
| `content` | 기본 콘텐츠 슬라이드 |
| `compare` | A vs B 비교 슬라이드 (토글 버튼) |
| `canvas` | Canvas 애니메이션 슬라이드 |
| `quiz` | 인터랙티브 퀴즈 슬라이드 |
| `tabs` | 탭 기반 콘텐츠 슬라이드 |
| `timeline` | 타임라인 시각화 슬라이드 |
| `checklist` | 인터랙티브 체크리스트 슬라이드 |
| `code` | 코드 중심 슬라이드 |

```markdown
---
@type: compare

## EC2 vs Lambda
```

:::info
일부 타입은 콘텐츠에서 자동 감지됩니다:
- `# ` (H1)으로 시작 - Title 슬라이드
- 여러 `### ` 헤딩 - `compare`
- `[x]` / `[ ]` 체크박스 - `quiz`
- 10줄 이상 코드 펜스 - `code`
- `:::canvas` 블록 - `canvas`
:::

### @layout

슬라이드의 레이아웃을 지정합니다.

| 값 | 설명 |
|----|------|
| `default` | 기본 단일 컬럼 |
| `two-column` | 2단 레이아웃 (`::: left`, `::: right` 사용) |
| `three-column` | 3단 레이아웃 (`::: col` 사용) |
| `grid-2x2` | 2x2 그리드 (`::: cell` 사용) |
| `split-left` | 왼쪽 콘텐츠 + 오른쪽 배경 |
| `split-right` | 왼쪽 배경 + 오른쪽 콘텐츠 |

```markdown
---
@layout: two-column

## Feature Comparison

::: left
### Pros
- Fast deployment
- Lower cost
:::

::: right
### Cons
- Limited customization
- Learning curve
:::
```

### @transition

해당 슬라이드로 진입할 때의 전환 효과를 지정합니다.

| 값 | 설명 |
|----|------|
| `none` | 전환 효과 없음 |
| `fade` | 페이드 인/아웃 |
| `slide` | 슬라이드 (기본값) |
| `convex` | 볼록 3D 효과 |
| `concave` | 오목 3D 효과 |
| `zoom` | 줌 인/아웃 |

```markdown
---
@transition: zoom

## Important Announcement
```

### @background

> **글로벌 기본 배경:** frontmatter에서 `backgroundColor:` 또는 `backgroundImage:`로 모든 슬라이드의 기본 배경을 설정할 수 있습니다. 개별 슬라이드의 `@background` 디렉티브가 글로벌 설정을 오버라이드합니다.

슬라이드 배경을 지정합니다. CSS 색상, 그라데이션, 이미지 URL을 사용할 수 있습니다.

```markdown
---
@background: #1a1d2e

## Dark Background Slide
```

```markdown
---
@background: linear-gradient(135deg, #232F3E, #1a1a2e)

## Gradient Background
```

```markdown
---
@background: url(./images/hero.png) center/cover no-repeat

## Image Background
```

### @timing

해당 슬라이드의 예상 발표 시간을 지정합니다. 프레젠터 뷰에서 참고용으로 표시됩니다.

| 형식 | 예시 |
|------|------|
| 분 단위 | `3min`, `5min` |
| 초 단위 | `90s`, `120s` |

```markdown
---
@timing: 3min

## Complex Topic

This slide needs more explanation time.
```

### @canvas-id

`@type: canvas` 슬라이드에서 canvas 요소의 ID를 지정합니다.

```markdown
---
@type: canvas
@canvas-id: architecture-flow

## System Architecture

:::canvas
box api "API" at 100,150 size 120,60 color #FF9900
:::
```

### @ref

슬라이드에 참조 링크를 추가합니다. 프레젠터 뷰에서 확인할 수 있습니다.

```markdown
---
@type: content
@ref: "https://docs.aws.amazon.com/lambda/" "Lambda Documentation"
@ref: "https://aws.amazon.com/blogs/compute/" "AWS Compute Blog"

## Lambda Best Practices

Content here...
```

여러 개의 `@ref`를 추가할 수 있습니다. 각 `@ref`는 URL과 레이블을 따옴표로 감싸서 작성합니다.

### @class

슬라이드에 추가 CSS 클래스를 적용합니다.

```markdown
---
@class: highlight-slide important

## Critical Information
```

### @animation

슬라이드 전체에 적용할 애니메이션 클래스를 지정합니다.

```markdown
---
@animation: fade-in

## Animated Slide Entry
```

## 디렉티브 조합 예제

### Compare 슬라이드

```markdown
---
@type: compare
@layout: two-column
@transition: fade

## Serverless vs Traditional

::: left
### Traditional
- Provision servers
- Manage capacity
- Pay for idle time
:::

::: right
### Serverless
- No servers to manage
- Auto-scales to zero
- Pay per execution
:::
```

### Canvas 애니메이션 슬라이드

```markdown
---
@type: canvas
@canvas-id: data-flow
@timing: 5min
@background: #0f1117

## Data Pipeline

:::canvas width=960 height=400
icon s3 "S3" at 50,150 size 48 step 1
icon lambda "Lambda" at 200,150 size 48 step 2
icon dynamo "DynamoDB" at 350,150 size 48 step 3

arrow s3 -> lambda "trigger" step 4
arrow lambda -> dynamo "write" step 5
:::
```

### 참조가 있는 콘텐츠 슬라이드

```markdown
---
@type: content
@timing: 3min
@ref: "https://docs.aws.amazon.com/wellarchitected/" "Well-Architected Framework"
@ref: "https://aws.amazon.com/architecture/" "AWS Architecture Center"

## AWS Well-Architected Framework

Six pillars of the framework:

1. Operational Excellence{.click}
2. Security{.click}
3. Reliability{.click}
4. Performance Efficiency{.click}
5. Cost Optimization{.click}
6. Sustainability{.click}
```
