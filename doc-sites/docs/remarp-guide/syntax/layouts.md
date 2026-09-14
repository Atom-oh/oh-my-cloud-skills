---
sidebar_position: 4
title: "Layouts"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="레이아웃" />
<span id="two-column-레이아웃" />
<span id="three-column-레이아웃" />
<span id="grid-2x2-레이아웃" />
<span id="split-레이아웃" />
<span id="split-left-왼쪽-콘텐츠" />
<span id="split-right-오른쪽-콘텐츠" />
<span id="레이아웃-선택-가이드" />
<span id="레이아웃과-프래그먼트-조합" />
<span id="중첩된-구조" />
<span id="json-format" />


# Layouts

Set `@layout` before slide content and use the corresponding block containers.

```markdown
---
@layout: two-column

## Review and verify

:::left
### Review
- Inspect changed behavior {.click order=1}
- Check source evidence {.click order=2}
:::

:::right
### Verify
- Run relevant checks {.click order=3}
- Record limits {.click order=4}
:::
```

## Layout choices {#layout-choices}

| Layout | Containers | Use |
| --- | --- | --- |
| Default | Ordinary Markdown | One message or a focused list |
| `two-column` | `:::left`, `:::right` | Paired ideas or code/explanation |
| `three-column` | Three `:::col` blocks | Comparable features or stages |
| `grid-2x2` | Four `:::cell` blocks | Four related categories |
| `split-left` | Left content with background area | Text beside a visual |
| `split-right` | Right content with background area | Visual beside text |

Use explicit fragment order across columns. Keep nested blocks simple enough for the parser and inspect the generated result; for complex cards or grouped diagrams use `:::html` plus `:::css` with the framework's layout classes.
