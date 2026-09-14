---
sidebar_position: 2
title: "Compare slides"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="compare-슬라이드" />
<span id="기본-문법" />
<span id="디렉티브" />
<span id="자동-감지" />
<span id="예제" />
<span id="서비스-비교" />
<span id="아키텍처-패턴-비교" />
<span id="two-column과-함께-사용" />
<span id="렌더링" />
<span id="키보드-조작" />
<span id="팁" />


# Compare slides

Compare two or more alternatives with selectable content.

## Source {#source}

```markdown
---
@type: compare

## Build choices

### Local
Fast iteration with the current checkout.

### CI
Repeatable checks in the configured workflow.
```

## Rendering and interaction {#rendering-and-interaction}

Third-level headings identify alternatives. The parser can infer comparison from repeated headings, but use an explicit type to distinguish it from tabs or timeline. Test option buttons and Up/Down cycling; Left/Right continues ordinary navigation. Use matching criteria across alternatives.

Add speaker notes and run source validation before building. Test the slide in the generated deck; the HTML structure and CSS classes are implementation details, not a substitute for checking behavior.

See [directives](../syntax/directives.md), [speaker notes](../syntax/speaker-notes.md), and [keyboard controls](../keyboard-shortcuts.md).
