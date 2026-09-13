---
sidebar_position: 3
title: "Fragments"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="프래그먼트-애니메이션" />
<span id="인라인-문법" />
<span id="블록-문법" />
<span id="순서-지정" />
<span id="애니메이션-타입" />
<span id="속성-문법" />
<span id="클래스-문법" />
<span id="애니메이션-타입-레퍼런스" />
<span id="애니메이션-쇼케이스" />
<span id="블록에-애니메이션-적용" />
<span id="조합-예제" />
<span id="순서와-애니메이션-조합" />
<span id="리스트-항목별-프래그먼트" />
<span id="단계별-설명" />
<span id="프래그먼트-키보드-조작" />


# Fragments

Fragments reveal content in steps. Add `{.click}` to one element or wrap related content in `:::click`.

```markdown
## Review sequence

- Inspect the diff {.click order=1}
- Reproduce the issue {.click order=2 .fade-up}
- Verify the fix {.click order=3 animation=highlight}

:::click order=4 animation=grow
### Evidence
Record the check and the result together.
:::
```

## Ordering

Use explicit `order=N` on every fragment when mixing inline `{.click}` items with `:::click` blocks or arranging content across columns. An unnumbered top-level click block defaults to an index starting at zero, so it can reveal before explicitly numbered items later in the visual order. Elements sharing an index can appear together.

## Effects

The framework includes fade-in/up/down/left/right, grow, shrink, highlight, highlight-red, highlight-green, strike, and fade-out fragment classes. Effects can be specified with a class or `animation=` attribute. Keep motion readable and use emphasis sparingly.

## Controls

Right/Space reveals the next fragment before advancing the slide. Left hides a previous fragment where available before moving back. Up/Down first use registered slide actions or interactive controls, then fall back to fragment/slide navigation. Test the actual deck when combining fragments with tabs or Canvas steps.
