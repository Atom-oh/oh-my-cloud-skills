# Canvas Authoring Guide

> **MANDATORY**: read this before writing any `:::canvas` block. The grammar is
> strict (variants silently fail to parse) and the coordinate formula is required —
> LLM spatial reasoning is weak, so place boxes by formula, not by "imagination".
> The `validate` command (rejection loop) backstops overlaps (`CANVAS_OVERLAP`)
> and unknown icon names (`UNKNOWN_ICON` — bare service names must be
> ICON_NAME_MAP aliases like `EKS`, or pass an explicit file path).
>
> **Theme constraint**: canvas colors (`Colors`) are resolved relative to the deck root theme.
> Do not place a canvas on a slide whose `@theme` differs from the deck theme
> (e.g. `@theme: dark` inside a light deck) — the contrast will break.

## Canvas DSL syntax (must be followed exactly)

> **Caution**: the parser only recognizes the exact syntax below. Bracket syntax `[x=..., y=...]` or other variants will not work.

```
box <id> "<label>" at <x>,<y> size <w>,<h> color <#hex> [step <n>]
icon <id> "<service-name>" at <x>,<y> size <s> [step <n>]
arrow <from-id> -> <to-id> "<label>" [color <#hex>] [step <n>]
group "<label>" containing <id1>, <id2> [color <#hex>] [step <n>]
```

Example:
```markdown
:::canvas
box api "API Gateway" at 100,180 size 130,55 color #FF9900 step 1
box lambda "Lambda" at 320,180 size 130,55 color #FF9900 step 2
box db "DynamoDB" at 540,180 size 130,55 color #3B48CC step 3
arrow api -> lambda "invoke" step 2
arrow lambda -> db "query" step 3
:::
```

## Canvas coordinate formulas (mandatory — corrects for LLM spatial reasoning)

> **Principle**: do not place coordinates by "imagination." Calculate them with the formulas below.
> LLMs have weak spatial reasoning, so formula-based placement is mandatory.

**Canvas coordinate system**: 960 × 400 (BASE_W × BASE_H), with a 40px safe-area margin

**Horizontal N-box straight-line flow** (A → B → C → ...):
```
gap = (880 - N * box_width) / (N - 1)     # 880 = 960 - 40*2 margin
x[i] = 40 + i * (box_width + gap)         # i = 0, 1, 2, ...
y = 180                                    # vertical center
```

**Two-row layout** (top: source, bottom: target):
```
row1_y = 100                               # top row
row2_y = 280                               # bottom row
x[i] = 40 + i * (880 / cols_in_row)       # evenly distributed within each row
```

**Box size rules**:
```
width ≥ max(label_length × 9, 100)        # for English; use × 14 for Korean text
height = 55                                # default
min_gap = 40                               # minimum gap between boxes (edge-to-edge)
```

**Icon spacing rules**:
```
min_gap = 60                               # icon center-to-center
icon_size = 48                             # default icon size
x[i] = 40 + i * max(icon_size + min_gap, 880 / N)
```

**Self-check (always verify after writing)**:
1. Are all x values within the 40–880 range?
2. Are all y values within the 30–350 range?
3. Is the edge-to-edge distance between adjacent boxes ≥ 40px?
4. Did you confirm with the `validate` command that there's no CANVAS_OVERLAP?

## Fragment ordering rule (td-lr: Top-Down Left-Right)

> **Principle**: follow the reader's eye flow — **top to bottom, left to right**.

**Single column**: auto-increment in DOM order (default behavior)
```markdown
- Item A {.click}          ← order=1 (자동)
- Item B {.click}          ← order=2 (자동)
- Item C {.click}          ← order=3 (자동)
```

**Multi-column layout (:::left/:::right)** — **must use an explicit order**:
```markdown
::: left
- Left Top {.click order=1}
- Left Bottom {.click order=3}
:::

::: right
- Right Top {.click order=2}
- Right Bottom {.click order=4}
:::
```
Visual order: 1 (top-left) → 2 (top-right) → 3 (bottom-left) → 4 (bottom-right)

**Multi-column inside a `:::html` block**: set `data-fragment-index` directly:
```html
<div class="col-2">
  <div class="fragment fade-up" data-fragment-index="1">좌상</div>
  <div class="fragment fade-up" data-fragment-index="2">우상</div>
  <div class="fragment fade-up" data-fragment-index="3">좌하</div>
  <div class="fragment fade-up" data-fragment-index="4">우하</div>
</div>
```

## Content authoring rules

1. **Slide comment**: a `<!-- Slide N: Title (slide type) -->` comment is required right below each slide separator (`---`)
2. **Raw HTML**: inserting block HTML like `<div>` or `<table>` directly into markdown body text breaks it by wrapping it in a `<p>` tag → always use a `:::html` block instead
3. **AWS icon path**: use the `../common/aws-icons/services/Arch_{ServiceName}_48.svg` format (the full directory path `Architecture-Service-Icons_07312025/...` is forbidden)
