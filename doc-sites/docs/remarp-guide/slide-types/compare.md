---
sidebar_position: 2
title: Compare 슬라이드
---

# Compare 슬라이드

Compare 슬라이드는 두 가지 이상의 옵션을 토글 버튼으로 비교할 수 있는 인터랙티브 슬라이드입니다.

## 기본 문법

```markdown
---
@type: compare

## EC2 vs Lambda

### EC2
- Full control over instance
- Persistent compute
- Pay per hour
- Best for: Long-running workloads

### Lambda
- Serverless, no management
- Event-driven
- Pay per invocation
- Best for: Short, bursty workloads
```

## 디렉티브

| 디렉티브 | 설명 |
|----------|------|
| `@type: compare` | Compare 타입 지정 (필수) |
| `@layout` | 레이아웃 (기본적으로 토글 버튼 사용) |
| `@transition` | 전환 효과 |
| `@timing` | 예상 발표 시간 |

## 자동 감지

여러 `### ` 헤딩이 있으면 자동으로 Compare 타입으로 감지됩니다.

## 예제

### 서비스 비교

```markdown
---
@type: compare

## Storage Options

### S3
- Object storage
- 11 nines durability
- Pay per GB stored
- Best for: Static assets, backups

### EBS
- Block storage
- Attached to EC2
- Pay per provisioned GB
- Best for: Database volumes

### EFS
- File storage
- Shared across instances
- Pay per GB used
- Best for: Shared file systems
```

### 아키텍처 패턴 비교

```markdown
---
@type: compare

## Monolith vs Microservices

### Monolith
**Advantages:**
- Simple to develop
- Easy to deploy
- Single codebase

**Challenges:**
- Scaling limitations
- Technology lock-in
- Large deployments

### Microservices
**Advantages:**
- Independent scaling
- Technology flexibility
- Smaller deployments

**Challenges:**
- Distributed complexity
- Network latency
- Operational overhead
```

### Two-Column과 함께 사용

```markdown
---
@type: compare
@layout: two-column

## Database Comparison

::: left
### RDS
- Managed relational database
- MySQL, PostgreSQL, Oracle, SQL Server
- Automated backups and patching
- Multi-AZ deployment available
:::

::: right
### DynamoDB
- Fully managed NoSQL
- Key-value and document
- Single-digit millisecond latency
- Auto-scaling built-in
:::
```

## 렌더링

Compare 슬라이드는 토글 버튼이 있는 형태로 렌더링됩니다:

```html
<div class="slide">
  <div class="slide-header"><h2>A vs B</h2></div>
  <div class="slide-body">
    <div class="compare-toggle">
      <button class="compare-btn active" data-compare="a">Option A</button>
      <button class="compare-btn" data-compare="b">Option B</button>
    </div>
    <div class="compare-content active" data-compare="a">
      <!-- Option A content -->
    </div>
    <div class="compare-content" data-compare="b">
      <!-- Option B content -->
    </div>
  </div>
</div>
```

## 키보드 조작

| 키 | 동작 |
|----|------|
| `↑` / `↓` | 비교 옵션 전환 |
| `←` / `→` | 이전/다음 슬라이드 |

## 팁

:::tip
Compare 슬라이드는 2-4개의 옵션 비교에 가장 적합합니다. 5개 이상의 옵션이 있다면 Tabs 슬라이드를 고려하세요.
:::

:::info
각 옵션의 장단점을 균형 있게 제시하여 청중이 스스로 판단할 수 있도록 하세요.
:::
