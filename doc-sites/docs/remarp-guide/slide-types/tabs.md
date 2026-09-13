---
sidebar_position: 5
title: "Tabs slides"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="tabs-슬라이드" />
<span id="기본-문법" />
<span id="디렉티브" />
<span id="구조" />
<span id="예제" />
<span id="언어별-코드-예제" />
<span id="배포-옵션" />
<span id="sam" />
<span id="cdk" />
<span id="cloudformation" />
<span id="pulumi" />


# Tabs slides

Group alternative code, configuration, or explanations under selectable tabs.

## Source

```markdown
---
@type: tabs

## Validation modes

### Source
Inspect syntax and configuration before building.

### Browser
Check rendered content, controls, and navigation.
```

## Rendering and interaction

Each third-level heading becomes a tab label and its following content becomes the panel. Use explicit `@type: tabs`, keep labels short, and test both tab buttons and Up/Down cycling. For code examples, use a longer outer Markdown fence when demonstrating nested code fences.

Add speaker notes and run source validation before building. Test the slide in the generated deck; the HTML structure and CSS classes are implementation details, not a substitute for checking behavior.

See [directives](../syntax/directives.md), [speaker notes](../syntax/speaker-notes.md), and [keyboard controls](../keyboard-shortcuts.md).
