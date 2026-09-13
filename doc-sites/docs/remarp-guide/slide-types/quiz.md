---
sidebar_position: 4
title: "Quiz slides"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="quiz-슬라이드" />
<span id="기본-문법" />
<span id="디렉티브" />
<span id="자동-감지" />
<span id="문법" />
<span id="예제" />
<span id="단일-정답-퀴즈" />
<span id="복수-정답-퀴즈" />
<span id="설명이-포함된-퀴즈" />
<span id="렌더링" />
<span id="인터랙션" />
<span id="팁" />


# Quiz slides

Ask a focused knowledge question and give feedback when an option is selected.

## Source

```markdown
---
@type: quiz

## Source of truth

**Which file defines this site's locale configuration?**
- [ ] A screenshot
- [x] docusaurus.config.ts
- [ ] A release announcement
```

## Rendering and interaction

`[x]` marks a correct answer and `[ ]` a distractor. Checkbox content may be inferred as quiz, so specify checklist explicitly for completion tracking. Keep options concise and explain the answer. Test the actual selection/feedback behavior; multiple marked answers do not by themselves establish a multi-select completion rule.

Add speaker notes and run source validation before building. Test the slide in the generated deck; the HTML structure and CSS classes are implementation details, not a substitute for checking behavior.
