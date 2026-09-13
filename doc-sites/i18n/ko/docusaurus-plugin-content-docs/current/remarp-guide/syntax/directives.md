---
sidebar_position: 2
title: "지시문"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="디렉티브" />
<span id="기본-문법" />
<span id="디렉티브-레퍼런스" />
<span id="type" />
<span id="layout" />
<span id="transition" />
<span id="background" />
<span id="timing" />
<span id="canvas-id" />
<span id="ref" />
<span id="class" />
<span id="animation" />
<span id="디렉티브-조합-예제" />
<span id="compare-슬라이드" />
<span id="canvas-애니메이션-슬라이드" />
<span id="참조가-있는-콘텐츠-슬라이드" />


# 지시문

지시문은 `@`로 시작하며, 슬라이드 구분자 바로 뒤이자 제목·콘텐츠 앞에 배치합니다.

```markdown
---
@type: compare
@layout: two-column
@transition: fade
@timing: 3min
@ref: "https://docs.aws.amazon.com/wellarchitected/" "AWS Well-Architected"

## Compare the options
```

## 참고표 {#reference}

| 지시문 | 목적 |
| --- | --- |
| `@type` | content, code, compare, Canvas, quiz, tabs, timeline, checklist 등의 슬라이드 유형 명시 |
| `@layout` | Default, two-column, three-column, grid-2x2, split-left 또는 split-right 레이아웃 |
| `@transition` | none, fade, slide, convex, concave, zoom 등의 진입 전환 |
| `@background` | 슬라이드의 단색, 그라데이션 또는 이미지 배경 |
| `@timing` | `3min` 또는 `90s` 등의 발표 시간 |
| `@canvas-id` | 고유한 Canvas 요소 식별자 |
| `@ref` | 따옴표로 감싼 출처 URL과 레이블; 여러 참조는 반복 지정 |
| `@class` | 추가 CSS 클래스 |
| `@animation` | 슬라이드 애니메이션 클래스 |

전역 배경 설정으로 기본값을 지정할 수 있으며 슬라이드 지시문이 이를 재정의합니다. 사용자 지정 스타일에는 의미 기반 클래스와 테마 변수를 우선 사용합니다.

## 자동 감지와 명시적 유형 {#detection-and-explicit-types}

파서는 제목, 체크박스, 코드나 Canvas 콘텐츠로 일부 유형을 추론합니다. 특히 checklist와 quiz, tabs와 비교처럼 의도를 구분해야 할 때는 유형을 명시합니다. 레이아웃 블록(`:::left`, `:::right`, `:::col`, `:::cell`)은 선택된 레이아웃 안에서 콘텐츠를 구성합니다.

파서에는 생성된 덱에서 사용하는 특수 지시문도 있습니다. 추가 옵션을 문서화하기 전에 파서 소스와 현재 스킬 참고 문서를 확인합니다.

[파서와 지시문 처리](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py)
