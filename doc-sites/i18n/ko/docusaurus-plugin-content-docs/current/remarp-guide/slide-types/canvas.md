---
sidebar_position: 3
title: "Canvas 슬라이드"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="canvas-슬라이드" />
<span id="기본-문법" />
<span id="디렉티브" />
<span id="canvas-dsl-요소" />
<span id="요약" />
<span id="예제" />
<span id="기본-아키텍처-다이어그램" />
<span id="데이터-파이프라인" />
<span id="그룹이-있는-아키텍처" />
<span id="키보드-조작" />
<span id="렌더링" />
<span id="팁" />
<span id="html-architecture-대안-박스-5-이상" />
<span id="html-architecture-장점" />
<span id="css-유틸리티-클래스" />
<span id="canvas-prompt-llm-지원" />


# Canvas 슬라이드

작은 선형 프로세스를 단계별 그리기로 보여 줍니다.

## 소스 {#source}

```markdown
---
@type: canvas
@canvas-id: build-flow

## Build flow

:::canvas
box source "Source" at 40,150 size 100,50 color accent step 1
box build "Build" at 220,150 size 100,50 color blue step 2
box check "Check" at 400,150 size 100,50 color green step 3
arrow source -> build "compile" step 4
arrow build -> check "verify" step 5
:::
```

## 렌더링과 상호작용 {#rendering-and-interaction}

컴파일러는 이름이 지정된 색상 `accent`, `blue`, `green`, `yellow`, `red`, `cyan`을 인식합니다. 다른 색상에는 여섯 자리 16진수 값을 사용합니다.

고유한 Canvas ID를 사용하고 실제 경계와 화살표 경로를 확인합니다. 현재 작성 정책은 단순 흐름에서 상자·아이콘을 최대 네 개까지 허용합니다. 규모가 크거나 그룹·분기가 있는 아키텍처에는 HTML/CSS를, 인터랙티브 계산기에는 HTML 제어 요소와 스크립트 상태를 사용합니다. Up/Down으로 등록된 단계를 진행합니다. 프롬프트나 프리셋은 해당 컴파일러·런타임의 지원이 필요하며, 그 자체로 작동하는 애니메이션이 되지는 않습니다.

빌드 전에 발표자 노트를 추가하고 소스를 검증합니다. 생성된 덱에서 슬라이드를 테스트합니다. HTML 구조와 CSS 클래스는 구현 세부 사항이며 동작 확인을 대신할 수 없습니다.

## 관련 링크 {#related-links}

- [Canvas DSL](../syntax/canvas-dsl.md)
- [Canvas DSL — 화살표](../syntax/canvas-dsl.md#elements)
