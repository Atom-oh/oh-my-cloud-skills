---
sidebar_position: 3
title: 프래그먼트 애니메이션
---

# 프래그먼트 애니메이션

프래그먼트는 Space 또는 화살표 키로 순차적으로 나타나는 요소입니다. Remarp에서는 `{.click}` 구문으로 간단하게 프래그먼트를 만들 수 있습니다.

## 인라인 문법

요소 끝에 `{.click}`을 추가하면 클릭 시 나타나는 프래그먼트가 됩니다:

```markdown
## Build Process

1. Code commit triggers pipeline {.click}
2. Unit tests run in parallel {.click}
3. Integration tests validate APIs {.click}
4. Deployment to staging {.click}
5. Canary deployment to production {.click}
```

## 블록 문법

여러 요소를 하나의 프래그먼트로 묶으려면 `:::click` 블록을 사용합니다:

```markdown
## Deployment Stages

:::click
### Stage 1: Build
- Compile source code
- Run linters
- Generate artifacts
:::

:::click
### Stage 2: Test
- Unit tests
- Integration tests
- Security scans
:::

:::click
### Stage 3: Deploy
- Blue/green deployment
- Health checks
- Rollback capability
:::
```

## 순서 지정

`order` 속성으로 나타나는 순서를 명시적으로 지정할 수 있습니다:

```markdown
## Out of Order Reveal

Item shown third {.click order=3}

Item shown first {.click order=1}

Item shown second {.click order=2}
```

:::tip
`order`를 지정하지 않으면 문서에 나타난 순서대로 표시됩니다.
:::

## 애니메이션 타입

`animation` 속성 또는 클래스로 애니메이션 효과를 지정합니다:

### 속성 문법

```markdown
- Fade from below {.click animation=fade-up}
- Grow in size {.click animation=grow}
- Highlight yellow {.click animation=highlight}
```

### 클래스 문법

```markdown
- Fade from below {.click .fade-up}
- Grow in size {.click .grow}
- Highlight yellow {.click .highlight}
```

## 애니메이션 타입 레퍼런스

| 클래스 | 효과 |
|--------|------|
| `.fade-in` | 페이드 인 (기본값) |
| `.fade-up` | 아래에서 위로 페이드 인 |
| `.fade-down` | 위에서 아래로 페이드 인 |
| `.fade-left` | 오른쪽에서 왼쪽으로 페이드 인 |
| `.fade-right` | 왼쪽에서 오른쪽으로 페이드 인 |
| `.grow` | 0%에서 100%로 확대 |
| `.shrink` | 150%에서 100%로 축소 |
| `.highlight` | 노란색 배경 하이라이트 |
| `.highlight-red` | 빨간색 배경 하이라이트 |
| `.highlight-green` | 초록색 배경 하이라이트 |
| `.strike` | 취소선 |
| `.fade-out` | 페이드 아웃 (요소 제거용) |

## 애니메이션 쇼케이스

```markdown
## Animation Showcase

- Fade in (default) {.click}
- Fade from above {.click .fade-down}
- Fade from below {.click .fade-up}
- Fade from left {.click .fade-left}
- Fade from right {.click .fade-right}
- Grow in size {.click .grow}
- Shrink in size {.click .shrink}
- Highlight yellow {.click .highlight}
- Highlight red {.click .highlight-red}
- Highlight green {.click .highlight-green}
- Strikethrough {.click .strike}
- Fade out {.click .fade-out}
```

## 블록에 애니메이션 적용

`:::click` 블록에도 애니메이션을 적용할 수 있습니다:

```markdown
:::click animation=grow
### Phase 1: Planning
전체 블록이 클릭 시 grow 애니메이션으로 나타남.
:::

:::click animation=fade-up
### Phase 2: Implementation
아래에서 위로 슬라이드하며 나타남.
:::
```

## 조합 예제

### 순서와 애니메이션 조합

```markdown
## Key Takeaways

- Most important point {.click order=1 .highlight}
- Second point {.click order=2 .fade-up}
- Third point {.click order=3 .fade-up}
- Conclusion {.click order=4 .grow}
```

### 리스트 항목별 프래그먼트

```markdown
## AWS Services Overview

- **Compute**: EC2, Lambda, ECS {.click .fade-right}
- **Storage**: S3, EBS, EFS {.click .fade-right}
- **Database**: RDS, DynamoDB, Aurora {.click .fade-right}
- **Networking**: VPC, Route 53, CloudFront {.click .fade-right}
```

### 단계별 설명

```markdown
## Step-by-Step Process

:::click
### Step 1
Configure your AWS credentials and set up the CLI.
:::

:::click animation=fade-up
### Step 2
Create an S3 bucket for your application assets.
:::

:::click animation=fade-up
### Step 3
Deploy your Lambda function using SAM.
:::

:::click animation=grow
### Done!
Your serverless application is now live.
:::
```

## 프래그먼트 키보드 조작

| 키 | 동작 |
|----|------|
| `Space` | 다음 프래그먼트 표시, 없으면 다음 슬라이드 |
| `→` | 다음 프래그먼트/슬라이드 |
| `←` | 이전 슬라이드 (프래그먼트는 리셋) |
| `↓` | Canvas 슬라이드에서 다음 스텝 |
| `↑` | Canvas 슬라이드에서 이전 스텝 |
