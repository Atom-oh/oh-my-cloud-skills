---
sidebar_position: 4
title: 레이아웃
---

# 레이아웃

Remarp는 fenced div 문법(`:::`)을 사용하여 다양한 레이아웃을 지원합니다.

## Two-Column 레이아웃

가장 일반적인 레이아웃으로, 왼쪽과 오른쪽으로 콘텐츠를 나눕니다.

```markdown
---
@layout: two-column

## Feature Comparison

::: left
### Pros
- Fast deployment
- Lower cost
- Easy maintenance
:::

::: right
### Cons
- Limited customization
- Vendor lock-in
- Learning curve
:::
```

:::info
`::: left`와 `::: right` 블록은 반드시 `@layout: two-column`과 함께 사용해야 합니다.
:::

## Three-Column 레이아웃

세 개의 컬럼으로 콘텐츠를 나눕니다. 가격 비교나 옵션 표시에 유용합니다.

```markdown
---
@layout: three-column

## Service Options

::: col
### Basic
- 10 GB storage
- 1 vCPU
- $5/month
:::

::: col
### Standard
- 100 GB storage
- 2 vCPU
- $20/month
:::

::: col
### Premium
- 1 TB storage
- 8 vCPU
- $100/month
:::
```

## Grid 2x2 레이아웃

2x2 그리드로 네 개의 영역을 구성합니다. AWS Well-Architected 필러 같은 구조에 적합합니다.

```markdown
---
@layout: grid-2x2

## AWS Pillars

::: cell
### Operational Excellence
Automate, document, iterate
:::

::: cell
### Security
Defense in depth, least privilege
:::

::: cell
### Reliability
Fault tolerance, recovery
:::

::: cell
### Performance
Right-size, monitor, optimize
:::
```

## Split 레이아웃

한쪽에는 콘텐츠, 다른 쪽에는 이미지나 다이어그램을 배치합니다.

### Split Left (왼쪽 콘텐츠)

```markdown
---
@layout: split-left
@background: url(architecture.png) right/50% no-repeat

## Architecture Overview

::: left
The system uses a microservices architecture with:
- API Gateway for routing
- Lambda for compute
- DynamoDB for storage
:::
```

### Split Right (오른쪽 콘텐츠)

```markdown
---
@layout: split-right
@background: url(diagram.png) left/50% no-repeat

## System Components

::: right
Key components include:
- Load balancer
- Application servers
- Database cluster
:::
```

## 레이아웃 선택 가이드

| 용도 | 레이아웃 | 예시 |
|------|----------|------|
| A vs B 비교 | `two-column` | 서비스 비교, 장단점 |
| 3가지 옵션 | `three-column` | 가격 티어, 서비스 레벨 |
| 4가지 카테고리 | `grid-2x2` | 4개 필러, 사분면 분석 |
| 이미지 + 설명 | `split-left` / `split-right` | 아키텍처 다이어그램 설명 |

## 레이아웃과 프래그먼트 조합

레이아웃 내에서도 프래그먼트를 사용할 수 있습니다:

```markdown
---
@layout: two-column

## Migration Steps

::: left
### Current State
- Monolithic application {.click}
- Single database {.click}
- Manual deployments {.click}
:::

::: right
### Target State
- Microservices {.click}
- Distributed databases {.click}
- CI/CD pipeline {.click}
:::
```

## 중첩된 구조

컬럼 내부에 다른 요소들을 자유롭게 배치할 수 있습니다:

```markdown
---
@layout: two-column

## Configuration Examples

::: left
### YAML Format

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
```
:::

::: right
### JSON Format

```json
{
  "apiVersion": "v1",
  "kind": "ConfigMap"
}
```
:::
```

## 레이아웃 없는 기본 슬라이드

`@layout` 디렉티브를 지정하지 않으면 단일 컬럼 기본 레이아웃이 적용됩니다:

```markdown
---

## Simple Content Slide

This is a regular slide without any special layout.

- Point 1
- Point 2
- Point 3
```
