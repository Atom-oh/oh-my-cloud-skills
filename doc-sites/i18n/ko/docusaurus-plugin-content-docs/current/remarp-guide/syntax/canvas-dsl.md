---
sidebar_position: 5
title: "Canvas DSL"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="기본-문법" />
<span id="도형-요소" />
<span id="box-박스" />
<span id="circle-원" />
<span id="icon-아이콘" />
<span id="지원되는-서비스-이름" />
<span id="전체-경로-참조" />
<span id="arrow-화살표" />
<span id="orthogonal-라우팅" />
<span id="group-그룹" />
<span id="스텝-기반-애니메이션" />
<span id="프리셋-dsl" />
<span id="eks-scaling-프리셋" />
<span id="지원되는-프리셋" />
<span id="프리셋-액션" />
<span id="mermaid-통합" />
<span id="지원되는-mermaid-다이어그램-타입" />
<span id="html-architecture-대안" />
<span id="canvas-vs-html-architecture-비교" />
<span id="css-유틸리티-클래스" />
<span id="javascript-escape-hatch" />
<span id="전체-예제" />


# Canvas DSL

Canvas DSL은 작은 단계별 다이어그램을 표현합니다. 상자·아이콘이 최대 네 개인 선형 흐름에 사용합니다. 그룹, 분기 화살표, 계층형 아키텍처나 더 큰 다이어그램에는 HTML/CSS를 사용합니다. 정적 AWS 아키텍처는 Draw.io 내보내기 결과를 사용할 수 있습니다.

## 예제 {#example}

```markdown
---
@type: canvas
@canvas-id: request-flow

## Request flow

:::canvas
box client "Client" at 40,150 size 100,50 color accent step 1
box api "API" at 220,150 size 100,50 color blue step 2
box store "Store" at 400,150 size 100,50 color green step 3
arrow client -> api "request" step 4
arrow api -> store "write" step 5
:::
```

## 요소 {#elements}

```text
box <id> "<label>" at <x>,<y> size <width>,<height> color <color> [step <n>]
circle <id> "<label>" at <x>,<y> radius <r> color <color> [step <n>]
icon <id> "<service-or-path>" at <x>,<y> size <s> [step <n>]
arrow <from-id> -> <to-id> "<label>" [color <color>] [style dashed|dotted] [step <n>]
group "<label>" containing <id1>, <id2> [color <color>] [step <n>]
```

컴파일러는 이름이 지정된 색상 `accent`, `blue`, `green`, `yellow`, `red`, `cyan`을 인식합니다. 다른 색상에는 여섯 자리 16진수 값을 사용합니다.

파서는 그룹을 인식하지만 현재 작성 정책에서는 그룹이 있는 아키텍처에 HTML/CSS를 사용합니다. 아이콘 이름은 제공된 아이콘 매핑으로 해석합니다. 사용자 지정 아이콘에는 확인된 로컬 경로를 사용합니다. 모든 마케팅용 서비스명이 지원되는 별칭이라고 가정하지 않습니다.

## 단계와 연결 경로 {#steps-and-routing}

`step`이 없는 요소는 즉시 표시되고, 번호가 있는 단계는 순서대로 나타납니다. Up/Down은 등록된 Canvas 제어 기능을 사용합니다. 화살표는 컴파일러의 연결 경로와 앵커를 사용하지만 자동 경로 설정이 겹침 검사를 대신하지는 않습니다. 검증기는 시각적 요소의 복잡도와 상자·아이콘 경계의 겹침을 확인하며 그룹도 복잡도 수에 포함합니다. 현재 분기 검사는 예시 화살표 문법이 생성하는 `from_id` 필드를 인식하지 못합니다. 그룹·분기 작성 정책을 명시적으로 적용해야 하며, 검증 보고서에 문제가 없다는 사실만으로 해당 정책이 검사되었다고 볼 수는 없습니다.

## 확장 {#extensions}

지원되는 환경에서는 `:::canvas mermaid`와 `:::canvas js`로 통합할 수 있습니다. 프리셋 문법은 CanvasPresets 조회로 파싱되며, 해당 런타임 프리셋이 실제로 제공될 때만 작동합니다. 프리셋 이름이 파싱된다는 사실만으로 번들에 구현이 포함되어 있다고 판단하지 않습니다.

## HTML 대안 {#html-alternative}

`.flow-h`/`.flow-v`, `.flow-group`, `.flow-box`, `.flow-arrow`, `.icon-item`을 의미 기반 테마 토큰과 함께 사용합니다. `data-fragment-index`로 순차 표시를 지원합니다. 계산기와 시뮬레이션은 실제 HTML 제어 요소와 스크립트 상태로 구현하고 브라우저에서 테스트합니다.

[DSL 파서와 컴파일러](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py)
