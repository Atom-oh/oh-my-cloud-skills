# Design System — AWS Confidential Dark

> Auto-generated from `sampleLayout.pptx` by `extract_pptx_theme.py`.
> This document defines the visual language that must be followed when
> creating new slides.  Treat every token below as a **constraint**, not
> a suggestion.  Consistency > creativity.

## 1. Slide Canvas

| Property | Value |
|----------|-------|
| Aspect ratio | **16:9** |
| Resolution | 1280 × 720 px |
| EMU | 12192000 × 6858000 |

All content must be designed for this aspect ratio.  Do not stretch or
crop to fit a different ratio.

## 2. Color System

Semantic color tokens mapped from the PPTX theme scheme.
Use semantic names (not raw hex) so the palette can be
swapped without touching individual slides.

```yaml
color_tokens:
  background: "#161D26"  # Slide background
  text_primary: "#FFFFFF"  # Headings and body text
  text_secondary: "#F3F3F7"  # Captions, labels, muted text
  primary: "#41B3FF"  # Primary brand / accent (CTA, links, highlights)
  secondary: "#AD5CFF"  # Secondary accent (gradients, hover, subtle emphasis)
  accent: "#00E500"  # Tertiary accent (success, positive indicators)
  danger: "#FF5C85"  # Error / destructive actions
  warning: "#FF693C"  # Caution indicators
  info: "#FBD332"  # Informational highlights
  link: "#41B1E8"  # Hyperlinks and interactive text
```

**Theme type**: Dark.  Text must be light (#fff / #ccc).
Avoid pure white on pure black — use the token values above.

<details><summary>Raw PPTX scheme colors (reference)</summary>

| Slot | Hex |
|------|-----|
| dk1 | `#000000` |
| lt1 | `#FFFFFF` |
| dk2 | `#161D26` |
| lt2 | `#F3F3F7` |
| accent1 | `#41B3FF` |
| accent2 | `#AD5CFF` |
| accent3 | `#00E500` |
| accent4 | `#FF5C85` |
| accent5 | `#FF693C` |
| accent6 | `#FBD332` |
| hlink | `#41B1E8` |
| folHlink | `#41B1E8` |

</details>

## 3. Typography

```yaml
typography:
  heading:
    family: "Calibri Light"
    weights: [400, 700]       # regular + bold
    usage: "Slide titles, section headers, callout text"
  body:
    family: "Calibri"
    weights: [400, 600]       # regular + semibold
    usage: "Body text, bullets, labels, speaker notes"
```

### Type Scale (recommended)

| Level | Size | Weight | Use |
|-------|------|--------|-----|
| H1 | 2.5 rem | 700 | Cover slide title |
| H2 | 1.8 rem | 700 | Slide title |
| H3 | 1.3 rem | 600 | Sub-heading |
| Body | 1.0 rem | 400 | Bullet text, paragraphs |
| Caption | 0.8 rem | 400 | Footer, labels, annotations |
| Code | 0.9 rem (mono) | 400 | Code blocks |

> If `Calibri Light` or `Calibri` is not a system font, add a `@import` or
> `@font-face` declaration.  Never fall back to a visually different
> typeface silently.

## 4. Iconography

```yaml
icons:
  style: "rounded"           # rounded | sharp | outlined | filled
  corner_radius: 4px         # icon container rounding
  size_default: 48px         # standard icon size on content slides
  size_small: 24px           # inline / label icons
  size_large: 64px           # hero / feature highlight
  color: "inherit"           # icons inherit text color by default
  accent_color: "primary"    # highlighted icons use the primary token
```

### Rules

- **Consistency**: all icons on a single slide must use the same style
  (`rounded`).  Do not mix rounded and sharp icons.
- **AWS service icons**: use the official SVG from
  `skills/reactive-presentation/assets/aws-icons/`.  Keep the original
  multi-color fill — do not monochrome AWS icons.
- **Generic icons**: prefer a single icon library (e.g. Lucide, Phosphor,
  Material Symbols) across the entire presentation.
- **Sizing**: icons next to text should be vertically centered and match
  the text line height.
- **Padding**: maintain ≥ 8 px clear space around every icon.

## 5. Spacing & Grid

```yaml
layout:
  aspect_ratio: "16:9"
  safe_area:
    top: 10%                  # below header region
    bottom: 10%               # above footer region
    left: 5%
    right: 5%
  grid:
    columns: 12
    gutter: 16px
    margin: 40px              # outer margin
spacing_scale:               # 4-px base unit
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  xxl: 48px
```

### Rules

- Content must **never** overlap the header or footer regions.
- Use multiples of the 4 px base unit for all padding and margins.
- Two-column layouts: use 50/50 split with `md` gutter.
- Three-column layouts: use 33/33/33 split with `md` gutter.
- Maintain consistent vertical rhythm — every element should snap
  to the spacing scale.

## 6. Shapes & Corners

```yaml
shapes:
  border_radius:
    none: 0px                 # tables, code blocks
    sm: 4px                   # tags, badges, small chips
    md: 8px                   # cards, content boxes, tooltips
    lg: 16px                  # hero cards, feature panels
    full: 9999px              # pills, avatar circles
  border:
    width: 1px
    color: "text_secondary"   # use semantic token
    style: "solid"
  shadow:
    none: "none"
    sm: "0 1px 2px rgba(0,0,0,0.1)"
    md: "0 4px 12px rgba(0,0,0,0.15)"
    lg: "0 8px 24px rgba(0,0,0,0.2)"
```

### Rules

- **Cards and containers**: use `md` radius (8 px).
- **Buttons and badges**: use `sm` radius (4 px) or `full` for pills.
- **Images inside cards**: clip to parent's border-radius.
- **Do not mix** rounded and sharp containers on the same slide.
- **Elevation (shadow)**: use sparingly; on dark backgrounds prefer
  a subtle border or glow over a drop shadow.

## 7. Decorative Patterns

No decorative elements detected on the slide master.

### Layout Decorative Vocabulary

The following decorative pattern categories were found across
slide layouts.  Use these as the design vocabulary when adding
visual elements to slides.

**gradient_panel** (11 instances)

  - `roundRect` 39.6484%×100.0% fill=gradient (from "1_Agenda Slide 2 alternate")
    gradient: #F3F3F7 → #41B3FF
  - `rect` 65.5603%×100.0% fill=gradient (from "Title Only Gradient 3")
    gradient: #F3F3F7 → #F3F3F7
  - `rect` 50.0%×100.0% fill=gradient (from "2_Two Content_Image")
    gradient: #000000 → #41B3FF

**circle_icon** (21 instances)

  - `ellipse` 9.5103%×16.9072% fill= (from "2_Agenda Slide 2 alternate 2")
  - `ellipse` 7.9545%×14.1414% fill=background (from "1_Four column with subheadings, circles multi")
  - `ellipse` 7.9545%×14.1414% fill=background (from "1_Four column with subheadings, circles multi")

**divider** (13 instances)

  - `line` 14.0817%×0.0% fill= (from "1_Agenda Slide 2 alternate")
  - `line` 27.7358%×0.0% fill= (from "2_Three column statistics layout")
  - `line` 27.7358%×0.0% fill= (from "2_Three column statistics layout")

**rounded_accent** (3 instances)

  - `roundRect` 24.5545%×4.2133% fill=solid (from "Title Slide 2A")
  - `roundRect` 24.5545%×4.2133% fill=solid (from "1_Title Slide 2B")
  - `roundRect` 92.1951%×83.2385% fill=solid (from "Quote")

**decorative_shape** (13 instances)

  - `rect` 50.625%×100.0% fill=solid (from "2_Agenda Slide 2 alternate 2")
  - `None` 58.2812%×65.3355% fill= (from "1_Agenda Slide 1")
  - `rect` 6.5502%×100.2003% fill= (from "2_Agenda Slide 1")


## 8. Header & Footer Regions

### Header (top 19.33%)

| Element | Type | Position (L%, T%) | Size (W%, H%) |
|---------|------|--------------------|----------------|
| Title Placeholder 19 | placeholder | 5.0, 4.4444 | 86.25, 19.3287 |

### Footer (bottom, height 15.0%)

**Footer text**: `© 2026, Amazon Web Services, Inc. or its affiliates. All rights reserved. Amazon Confidential and Trademark. | ‹#›`

| Element | Type | Position (L%, T%) | Size (W%, H%) |
|---------|------|--------------------|----------------|
| Picture 14 | image | 4.8827, 92.4176 | 3.0, 3.1909 |
| Date Placeholder 3 | placeholder — "2/23/26" | 6.875, 101.3889 | 22.5, 5.3241 |
| Footer Placeholder 4 | placeholder | 33.125, 101.3889 | 33.75, 5.3241 |
| Slide Number Placeholder 5 | placeholder — "‹#›" | 73.2382, 91.7104 | 22.5, 5.3241 |
| TextBox 10 | text — "© 2026, Amazon Web Services, Inc. or its affiliates. All rights reserved. Amazon Confidential and Trademark." | 9.3593, 93.1731 | 29.2306, 2.6927 |
| Slide Number Placeholder 5 | text — "‹#›" | 73.2382, 91.7104 | 22.5, 5.3241 |

> Header and footer are **fixed regions**.  Slide content must
> not intrude into these areas.

## 9. Logo & Branding

### Logo 1: `logo_1.png`

- **Position**: left 4.8827%, top 92.4176%
- **Size**: 3.0% × 3.1909%
- **Nearby text**: "2/23/26"

### Rules

- The logo must appear on **every slide** at the exact position above.
- Do not stretch, crop, or recolor the logo.
- Maintain clear space of at least the logo height around all edges.

## 10. Background

**Master background type**: `inherited`

### Rules

- Content slides: use the master background as-is.
- Title / cover slides: may use a layout-specific background
  (see `layout_details` in the manifest).
- Never use a background that clashes with the color tokens.

## 11. Motion & Transitions

```yaml
transitions:
  default: "slide"            # slide | fade | none
  duration: 400ms
  easing: "ease-out"
fragment_animations:
  default: "fade-up"          # fade-up | fade-in | zoom-in
  duration: 300ms
  stagger: 100ms              # delay between successive items
```

### Rules

- Use **one** transition type across the entire presentation.
- Fragment animations (`{.click}`) should use consistent direction.
- Avoid bounce, spin, or other playful animations in professional decks.
- Canvas animations follow their own timing (see `:::canvas` blocks).

## Design Checklist

Before finalizing any slide, verify:

- [ ] Colors use semantic tokens from §2 (no hardcoded hex)
- [ ] Typography follows the type scale from §3
- [ ] Icons follow the style rules from §4
- [ ] Content stays within the safe area from §5
- [ ] Shapes use the border-radius scale from §6
- [ ] Decorative elements match §7 exactly
- [ ] Header/footer regions are untouched per §8
- [ ] Logo appears at the correct position per §9
- [ ] Background matches the master template per §10
- [ ] Transitions are consistent per §11
