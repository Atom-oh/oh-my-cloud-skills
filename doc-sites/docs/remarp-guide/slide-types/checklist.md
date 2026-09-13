---
sidebar_position: 7
title: "Checklist slides"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="checklist-슬라이드" />
<span id="기본-문법" />
<span id="디렉티브" />
<span id="문법" />
<span id="예제" />
<span id="배포-전-체크리스트" />
<span id="환경-설정-체크리스트" />
<span id="yaml-피드백이-있는-체크리스트" />
<span id="yaml-피드백이-있는-경우" />
<span id="인터랙션" />
<span id="팁" />


# Checklist slides

Track completion without quiz scoring.

## Source {#source}

```markdown
---
@type: checklist

## Review checklist

- [ ] Source reviewed
- [ ] Relevant checks passed
- [ ] Links verified
- [ ] Remaining limits recorded
```

## Rendering and interaction {#rendering-and-interaction}

Use `@type: checklist` so checkboxes are not inferred as a quiz. Clicking toggles the item state and its checked class. Supported nested code feedback can reveal a configuration example; inspect the compiled result and keep the example scoped to the item. Split a long checklist into meaningful groups.

Add speaker notes and run source validation before building. Test the slide in the generated deck; the HTML structure and CSS classes are implementation details, not a substitute for checking behavior.

See [directives](../syntax/directives.md), [speaker notes](../syntax/speaker-notes.md), and [keyboard controls](../keyboard-shortcuts.md).
