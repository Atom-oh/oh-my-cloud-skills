---
sidebar_position: 3
title: "Canvas slides"
---

{/* Legacy section links retained after the English rewrite. */}
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


# Canvas slides

Show a small linear process with stepwise drawing.

## Source {#source}

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

## Rendering and interaction {#rendering-and-interaction}

The compiler resolves the named colors `accent`, `blue`, `green`, `yellow`, `red`, and `cyan`. Use six-digit hex colors for other values.

Use a unique canvas ID and inspect actual bounds and arrow routing. Current authoring policy permits at most four boxes/icons in a simple flow. Larger, grouped, or branching architecture uses HTML/CSS; interactive calculators use HTML controls and script state. Up/Down drives registered steps. A prompt or preset requires its corresponding compiler/runtime support; it is not automatically a working animation.

Add speaker notes and run source validation before building. Test the slide in the generated deck; the HTML structure and CSS classes are implementation details, not a substitute for checking behavior.

## Related links {#related-links}

- [Canvas DSL](../syntax/canvas-dsl.md)
- [Canvas DSL — Arrow](../syntax/canvas-dsl.md#elements)
