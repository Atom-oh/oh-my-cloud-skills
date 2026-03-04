---
sidebar_position: 2
title: 빠른 시작
---

# 빠른 시작

5분 만에 Remarp로 첫 프레젠테이션을 만들어 봅니다.

## 1. 파일 만들기

`my-talk.remarp.md` 파일을 생성합니다:

```markdown
---
remarp: true
title: "My First Remarp Presentation"
author: "Your Name"
lang: ko

theme:
  source: "./company-template.pptx"   # 또는 skip
  footer: "© 2026 My Company"

transition:
  type: fade
  duration: 350
---

# My First Remarp Presentation

Your Name | 2026

:::notes
{timing: 1min}
인사하고 자기소개.
:::

---

## 핵심 포인트

- 첫 번째 포인트{.click}
- 두 번째 포인트{.click}
- 세 번째 포인트{.click animation=fade-up}

:::notes
{timing: 3min}
**핵심**: 각 포인트를 클릭하며 설명.
{cue: question} "질문 있으신가요?"
:::

---
@type compare
@layout two-column

## 비교

::: left
### Option A
- 빠른 배포
- 간단한 구성
:::

::: right
### Option B
- 높은 확장성
- 세밀한 제어
:::

---
@type canvas
@canvas-id arch-flow

## 아키텍처

:::canvas width=960 height=400
box "API GW" at 50,170 size 130x60 color=accent
box "Lambda" at 260,170 size 130x60 color=green
box "DynamoDB" at 470,170 size 130x60 color=blue

arrow from "API GW" to "Lambda" at step=1 animate=draw
arrow from "Lambda" to "DynamoDB" at step=2 animate=draw

group "VPC" at 30,100 size 580x180 color=border
:::

:::notes
{timing: 5min}
{cue: demo} 아키텍처 흐름을 step별로 보여주기.
:::
```

## 2. HTML 빌드

```bash
python3 remarp_to_slides.py build my-talk.remarp.md
```

## 3. 브라우저에서 열기

생성된 HTML 파일을 브라우저에서 열면 프레젠테이션이 완성됩니다.

## 기본 조작법

| 키 | 동작 |
|----|------|
| `←` `→` | 이전/다음 슬라이드 |
| `Space` | 다음 프래그먼트 또는 다음 슬라이드 |
| `F` | 전체 화면 |
| `N` | 스피커 노트 패널 |
| `P` | 프레젠터 뷰 |

## 핵심 문법 요약

### 슬라이드 구분

`---` 줄로 슬라이드를 구분합니다:

```markdown
# 슬라이드 1 내용

---

# 슬라이드 2 내용
```

### 디렉티브

`@` 접두사로 슬라이드 속성을 지정합니다:

```markdown
---
@type canvas
@layout two-column
@transition zoom
```

### 프래그먼트

`{.click}`으로 클릭 시 나타나는 요소를 만듭니다:

```markdown
- 첫 번째{.click}
- 두 번째{.click animation=fade-up}
```

### 컬럼 레이아웃

`::: left`와 `::: right`로 2단 레이아웃을 구성합니다:

```markdown
@layout two-column

::: left
왼쪽 내용
:::

::: right
오른쪽 내용
:::
```

## 다음 단계

- [Frontmatter](./syntax/frontmatter.md) - 프레젠테이션 전역 설정
- [디렉티브](./syntax/directives.md) - 슬라이드별 속성 지정
- [프래그먼트 애니메이션](./syntax/fragments.md) - 클릭 애니메이션 상세
- [Canvas DSL](./syntax/canvas-dsl.md) - 다이어그램 작성법
