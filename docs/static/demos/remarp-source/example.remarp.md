---
remarp: true
version: 1
title: "Remarp Feature Tour"
author: "Cloud Skills Team"
date: 2026-03-04
lang: ko

blocks:
  - name: tour
    title: "Remarp Feature Tour"
    duration: 10

theme:
  accent: "#6c5ce7"

transition:
  default: slide
  duration: 400
---

---
remarp: true
block: tour
---

# Remarp Feature Tour
마크다운으로 만드는 인터랙티브 프레젠테이션

:::notes
{timing: 1min}
Remarp의 핵심 기능을 직접 보여주는 메타 데모입니다.
:::

---

## Click Animations

요소를 순서대로 나타나게 하는 `{.click}` 문법:

- Remarp는 마크다운 기반입니다 {.click}
- 슬라이드 구분은 `---` 로 합니다 {.click}
- `@type` 디렉티브로 슬라이드 유형을 지정합니다 {.click}
- `{.click}` 으로 클릭 애니메이션을 추가합니다 {.click}

:::notes
{timing: 2min}
각 항목을 클릭하며 순차 공개 기능을 설명합니다.
:::

---
@type: compare

## Compare Layout

::: left
### Marp (기존)
- 정적 슬라이드만 지원
- 제한된 레이아웃
- 애니메이션 없음
- 텍스트 중심
:::

::: right
### Remarp (확장)
- 인터랙티브 슬라이드
- 다양한 레이아웃 프리셋
- Click / Canvas 애니메이션
- Quiz, Tabs, Timeline 지원
:::

:::notes
{timing: 2min}
좌우 비교 레이아웃으로 Marp vs Remarp 차이를 보여줍니다.
:::

---
@type: canvas
@canvas-id: arch-demo

## Canvas DSL

:::canvas
icon gw "API-Gateway" at 100,150 size 48 step 1
box api "API Layer" at 75,210 size 100,30 color #FF9900 step 1

icon fn "Lambda" at 300,150 size 48 step 2
box compute "Compute" at 275,210 size 100,30 color #FF9900 step 2

icon db "DynamoDB" at 500,150 size 48 step 3
box storage "Storage" at 475,210 size 100,30 color #3B48CC step 3

arrow api -> compute "invoke" step 4
arrow compute -> storage "read/write" step 4
:::

:::notes
{timing: 2min}
{cue: demo}
Canvas DSL로 아키텍처 다이어그램을 선언적으로 작성합니다.
화살표 키로 step별 애니메이션을 확인하세요.
:::

---

## Code Blocks

코드 블록에 파일명과 라인 하이라이트를 추가할 수 있습니다:

```python {filename="handler.py" highlight="3-5"}
import json

def handler(event, context):
    user_id = event['pathParameters']['userId']
    action = event.get('action', 'read')

    return {
        'statusCode': 200,
        'body': json.dumps({'userId': user_id})
    }
```

:::notes
{timing: 1min}
코드 블록의 하이라이트 기능을 시연합니다.
:::

---
@type: quiz

## Quick Quiz

**Q1: Remarp 슬라이드 구분 기호는?**
- [ ] `===`
- [x] `---`
- [ ] `***`
- [ ] `+++`

**Q2: 클릭 애니메이션 문법은?**
- [ ] `[click]`
- [ ] `(click)`
- [x] `{.click}`
- [ ] `@click`

:::notes
{timing: 2min}
{cue: question}
퀴즈로 핵심 문법을 복습합니다.
:::

---

## Start Building!

Remarp로 나만의 프레젠테이션을 만들어 보세요.

:::click
### 핵심 정리
- `remarp: true` frontmatter로 시작
- `---` 로 슬라이드 구분
- `@type` 디렉티브로 레이아웃 지정
- `{.click}`, `:::canvas`, `[x]/[ ]` 로 인터랙션 추가
:::

:::notes
{timing: 1min}
마무리 슬라이드. 다운로드 버튼으로 이 소스를 받아볼 수 있습니다.
:::
