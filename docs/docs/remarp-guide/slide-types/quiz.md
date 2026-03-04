---
sidebar_position: 4
title: Quiz 슬라이드
---

# Quiz 슬라이드

Quiz 슬라이드는 인터랙티브 퀴즈를 표시합니다. 청중 참여를 유도하거나 학습 내용을 점검할 때 사용합니다.

## 기본 문법

```markdown
---
@type: quiz

## Knowledge Check

**Q1: Which service provides serverless compute?**
- [ ] EC2
- [x] Lambda
- [ ] ECS
- [ ] EKS
```

## 디렉티브

| 디렉티브 | 설명 |
|----------|------|
| `@type: quiz` | Quiz 타입 지정 |

## 자동 감지

`[x]` 또는 `[ ]` 체크박스가 있으면 자동으로 Quiz 타입으로 감지됩니다.

## 문법

- `[ ]` - 오답 선택지
- `[x]` - 정답 선택지
- 여러 개의 `[x]`가 있으면 복수 정답

## 예제

### 단일 정답 퀴즈

```markdown
---
@type: quiz

## Quick Check

**Q1: Lambda maximum timeout?**
- [ ] 5 minutes
- [x] 15 minutes
- [ ] 30 minutes
- [ ] 60 minutes

**Q2: Lambda pricing is based on?**
- [ ] Provisioned capacity
- [x] Request count + duration
- [ ] Fixed monthly fee
```

### 복수 정답 퀴즈

```markdown
---
@type: quiz

## Select All That Apply

**Q: Lambda supports which runtimes? (Select all)**
- [x] Python
- [x] Node.js
- [x] Java
- [ ] COBOL
- [x] Go
- [x] .NET
```

### 설명이 포함된 퀴즈

```markdown
---
@type: quiz

## Architecture Quiz

Consider a serverless web application that needs to:
- Handle HTTP requests
- Process data asynchronously
- Store results in a database

**Which architecture pattern is most appropriate?**

- [ ] EC2 + RDS
- [x] API Gateway + Lambda + DynamoDB
- [ ] ECS + Aurora
- [ ] EKS + DocumentDB
```

## 렌더링

Quiz 슬라이드는 다음과 같은 HTML 구조로 렌더링됩니다:

```html
<div class="slide">
  <div class="slide-header"><h2>Knowledge Check</h2></div>
  <div class="slide-body">
    <div class="quiz" data-quiz="q1">
      <div class="quiz-question">Question text?</div>
      <div class="quiz-options">
        <button class="quiz-option" data-correct="false">A) Wrong</button>
        <button class="quiz-option" data-correct="true">B) Correct</button>
        <button class="quiz-option" data-correct="false">C) Wrong</button>
      </div>
      <div class="quiz-feedback"></div>
    </div>
  </div>
</div>
```

## 인터랙션

- 선택지를 클릭하면 정답/오답 피드백이 표시됩니다
- 정답은 녹색, 오답은 빨간색으로 하이라이트됩니다
- 복수 정답인 경우 모든 정답을 선택해야 합니다

## 팁

:::tip
퀴즈는 발표 중간에 청중의 집중을 환기시키는 데 효과적입니다. 3-5분마다 간단한 퀴즈를 삽입해 보세요.
:::

:::info
복수 정답 퀴즈는 "(Select all)" 또는 "(복수 선택)"을 명시하여 청중에게 알려주세요.
:::

:::warning
퀴즈 선택지는 4개 이하로 유지하는 것이 좋습니다. 너무 많은 선택지는 혼란을 줄 수 있습니다.
:::
