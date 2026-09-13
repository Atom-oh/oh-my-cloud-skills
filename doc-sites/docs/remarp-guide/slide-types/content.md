---
sidebar_position: 1
title: "Content slides"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="content-슬라이드" />
<span id="기본-문법" />
<span id="디렉티브" />
<span id="예제" />
<span id="기본-콘텐츠" />
<span id="프래그먼트가-있는-콘텐츠" />
<span id="2단-레이아웃" />
<span id="배경과-타이밍" />
<span id="렌더링" />
<span id="팁" />


# Content slides

Use for a focused statement, list, table, code excerpt, or image.

## Source

```markdown
---
@type: content
@timing: 2min

## Verify the change

- Read the affected path {.click order=1}
- Exercise the behavior {.click order=2}
- Report the result {.click order=3}
```

## Rendering and interaction

The default layout is a single content area. Add column layout blocks when comparison helps, and use background/timing directives where appropriate. Keep a single main message, a readable hierarchy, and notes explaining the practical implication.

Add speaker notes and run source validation before building. Test the slide in the generated deck; the HTML structure and CSS classes are implementation details, not a substitute for checking behavior.
