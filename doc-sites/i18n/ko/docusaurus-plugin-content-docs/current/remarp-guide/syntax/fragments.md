---
sidebar_position: 3
title: "단계별 표시"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="프래그먼트-애니메이션" />
<span id="인라인-문법" />
<span id="블록-문법" />
<span id="순서-지정" />
<span id="애니메이션-타입" />
<span id="속성-문법" />
<span id="클래스-문법" />
<span id="애니메이션-타입-레퍼런스" />
<span id="애니메이션-쇼케이스" />
<span id="블록에-애니메이션-적용" />
<span id="조합-예제" />
<span id="순서와-애니메이션-조합" />
<span id="리스트-항목별-프래그먼트" />
<span id="단계별-설명" />
<span id="프래그먼트-키보드-조작" />


# 단계별 표시

단계별 표시로 콘텐츠를 순서대로 보여 줍니다. 개별 요소에 `{.click}`을 추가하거나 관련 콘텐츠를 `:::click`으로 묶습니다.

```markdown
## Review sequence

- Inspect the diff {.click order=1}
- Reproduce the issue {.click order=2 .fade-up}
- Verify the fix {.click order=3 animation=highlight}

:::click order=4 animation=grow
### Evidence
Record the check and the result together.
:::
```

## 순서 지정 {#ordering}

인라인 `{.click}` 항목과 `:::click` 블록을 섞거나 여러 열에 콘텐츠를 배치할 때는 모든 표시 요소에 `order=N`을 명시합니다. 번호가 없는 최상위 click 블록은 기본 인덱스가 0부터 시작하므로, 화면상 뒤에 있는 명시적 번호 항목보다 먼저 나타날 수 있습니다. 같은 인덱스의 요소는 함께 표시할 수 있습니다.

## 효과 {#effects}

프레임워크는 fade-in/up/down/left/right, grow, shrink, highlight, highlight-red, highlight-green, strike, fade-out 표시 클래스를 제공합니다. 클래스나 `animation=` 속성으로 효과를 지정할 수 있습니다. 움직임은 읽기 쉽게 유지하고 강조 효과는 절제해서 사용합니다.

## 조작 {#controls}

Right/Space는 다음 슬라이드로 이동하기 전에 다음 내용을 표시합니다. Left는 지원되는 경우 이전 단계의 내용을 숨긴 뒤 뒤로 이동합니다. Up/Down은 등록된 슬라이드 동작이나 상호작용 제어를 먼저 수행하고, 해당 동작이 없으면 단계별 표시·슬라이드 탐색으로 전환합니다. 탭이나 Canvas 단계와 함께 사용할 때는 실제 덱에서 테스트합니다.
