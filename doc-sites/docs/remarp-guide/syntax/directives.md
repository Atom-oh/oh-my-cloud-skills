---
sidebar_position: 2
title: "Directives"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="디렉티브" />
<span id="기본-문법" />
<span id="디렉티브-레퍼런스" />
<span id="type" />
<span id="layout" />
<span id="transition" />
<span id="background" />
<span id="timing" />
<span id="canvas-id" />
<span id="ref" />
<span id="class" />
<span id="animation" />
<span id="디렉티브-조합-예제" />
<span id="compare-슬라이드" />
<span id="canvas-애니메이션-슬라이드" />
<span id="참조가-있는-콘텐츠-슬라이드" />


# Directives

Directives begin with `@` and belong before the slide heading/content, immediately after a slide separator.

```markdown
---
@type: compare
@layout: two-column
@transition: fade
@timing: 3min
@ref: "https://docs.aws.amazon.com/wellarchitected/" "AWS Well-Architected"

## Compare the options
```

## Reference {#reference}

| Directive | Purpose |
| --- | --- |
| `@type` | Explicit slide type, including content, code, compare, Canvas, quiz, tabs, timeline, checklist |
| `@layout` | Default, two-column, three-column, grid-2x2, split-left, or split-right layout |
| `@transition` | Entry transition such as none, fade, slide, convex, concave, or zoom |
| `@background` | Slide color, gradient, or image background |
| `@timing` | Speaking time such as `3min` or `90s` |
| `@canvas-id` | Unique Canvas element identifier |
| `@ref` | Quoted source URL and label; repeat for several references |
| `@class` | Additional CSS classes |
| `@animation` | Slide animation class |

Global background settings can provide a default; a slide directive overrides that default. Prefer semantic classes and theme variables when authoring custom styles.

## Detection and explicit types {#detection-and-explicit-types}

The parser can infer some types from headings, checkboxes, code, or Canvas content. Use an explicit type when the intent matters, especially checklist versus quiz, or tabs versus comparison. Layout blocks (`:::left`, `:::right`, `:::col`, `:::cell`) structure content within the selected layout.

The parser also contains specialized directives used by generated decks. Consult its source and the current skill references before documenting an additional option.

[Parser and directive handling](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py)
