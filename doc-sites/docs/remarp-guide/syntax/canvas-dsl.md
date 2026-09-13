---
sidebar_position: 5
title: "Canvas DSL"
---

{/* Legacy section links retained after the English rewrite. */}
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

Canvas DSL describes a small stepwise diagram. Use it for at most four boxes/icons in a linear flow. Groups, branching arrows, layered architectures, and larger diagrams use HTML/CSS; static AWS architecture can use a Draw.io export.

## Example

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

## Elements

```text
box <id> "<label>" at <x>,<y> size <width>,<height> color <color> [step <n>]
circle <id> "<label>" at <x>,<y> radius <r> color <color> [step <n>]
icon <id> "<service-or-path>" at <x>,<y> size <s> [step <n>]
arrow <from-id> -> <to-id> "<label>" [color <color>] [style dashed|dotted] [step <n>]
group "<label>" containing <id1>, <id2> [color <color>] [step <n>]
```

The compiler resolves the named colors `accent`, `blue`, `green`, `yellow`, `red`, and `cyan`. Use six-digit hex colors for other values.

The parser recognizes groups, but current authoring policy sends grouped architecture to HTML/CSS. Icon names resolve through the shipped icon mapping; use a verified local path for a custom icon. Do not assume every marketing service name is an accepted alias.

## Steps and routing

Elements without `step` appear immediately; numbered steps reveal them in sequence. Up/Down uses the registered Canvas controls. Arrows use the compiler's routing and anchors, but automatic routing does not replace overlap inspection. The validator checks visual-element complexity and overlapping box/icon bounds; groups contribute to the complexity count. Its branching check does not currently recognize the `from_id` field produced by the demonstrated arrow syntax. Apply the group/branching authoring policy explicitly; a clean validation report is not proof that policy was checked.

## Extensions

`:::canvas mermaid` and `:::canvas js` provide integration paths where supported. Preset syntax is parsed into a CanvasPresets lookup; it only works when the corresponding runtime preset is actually supplied. A parsed preset name is not proof that the bundle includes its implementation.

## HTML alternative

Use `.flow-h`/`.flow-v`, `.flow-group`, `.flow-box`, `.flow-arrow`, and `.icon-item` with semantic theme tokens. `data-fragment-index` supports ordered reveal. Calculators and simulations use actual HTML controls and script state, tested in the browser.

[DSL parser and compiler](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py)
