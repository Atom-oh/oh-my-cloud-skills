---
sidebar_position: 1
title: Content 슬라이드
---

# Content 슬라이드

Content 슬라이드는 가장 기본적인 슬라이드 유형으로, 일반적인 텍스트, 리스트, 이미지 등의 콘텐츠를 표시합니다.

## 기본 문법

```markdown
---

## Slide Title

Content goes here. You can use:

- Bullet points
- **Bold text**
- *Italic text*
- `inline code`
```

## 디렉티브

| 디렉티브 | 설명 |
|----------|------|
| `@type: content` | 명시적으로 content 타입 지정 (선택사항) |
| `@layout` | 레이아웃 지정 (two-column, three-column 등) |
| `@background` | 배경 색상/이미지 |
| `@transition` | 전환 효과 |
| `@timing` | 예상 발표 시간 |

## 예제

### 기본 콘텐츠

```markdown
---

## AWS Lambda Benefits

AWS Lambda provides several key benefits:

- **No server management**: Focus on your code, not infrastructure
- **Automatic scaling**: Handles any workload automatically
- **Pay per use**: Only pay for compute time consumed
- **Built-in fault tolerance**: Runs across multiple AZs
```

### 프래그먼트가 있는 콘텐츠

```markdown
---

## Migration Steps

Follow these steps to migrate your application:

1. Assess current infrastructure {.click}
2. Plan the migration strategy {.click}
3. Set up AWS environment {.click}
4. Migrate data and applications {.click}
5. Test and validate {.click}
6. Go live and optimize {.click}
```

### 2단 레이아웃

```markdown
---
@layout: two-column

## Before and After

::: left
### Current State
- Monolithic application
- Single database
- Manual deployments
- Limited scalability
:::

::: right
### Target State
- Microservices architecture
- Distributed databases
- CI/CD pipeline
- Auto-scaling enabled
:::
```

### 배경과 타이밍

```markdown
---
@background: linear-gradient(135deg, #232F3E, #1a1a2e)
@timing: 3min

## Key Takeaways

Remember these important points:

- Start small, iterate quickly {.click .highlight}
- Monitor everything {.click .highlight}
- Automate wherever possible {.click .highlight}
```

## 렌더링

Content 슬라이드는 다음과 같은 HTML 구조로 렌더링됩니다:

```html
<div class="slide">
  <div class="slide-header">
    <h2>Slide Title</h2>
  </div>
  <div class="slide-body">
    <!-- Content here -->
  </div>
</div>
```

## 팁

:::tip
Content 슬라이드는 가장 자주 사용되는 유형입니다. `@type: content`를 명시하지 않아도 기본적으로 content로 처리됩니다.
:::

:::info
슬라이드당 3-5개의 핵심 포인트를 유지하는 것이 좋습니다. 너무 많은 정보는 청중의 집중을 분산시킵니다.
:::
