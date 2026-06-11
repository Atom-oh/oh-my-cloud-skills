# Design Tokens — SINGLE SOURCE OF TRUTH

> **All sizes, colors, fonts, and spacing for AWS architecture diagrams come from THIS file.**
> Other references (`SKILL.md`, `best-practices.md`, `layout-patterns.md`,
> `drawio-xml-guide.md`, the agent) must match these values — never restate a different
> number. When in doubt, this file wins. Values are grounded in the actual
> `templates/*.drawio` (the cleanest exemplars), so generated diagrams stay consistent
> with the templates.

The #1 cause of "amateur-looking" output is the skill contradicting itself (icons at
40/48/60/78, public-vs-private subnet colors swapped between files). One canonical set
fixes that — the LLM stops guessing.

---

## 1. Icon sizes (pick ONE — enforced)

| Token | Size | Use |
|-------|------|-----|
| **`icon.standard`** | **78 × 78** | **DEFAULT for every service/resource icon.** Use this unless a documented exception applies. |
| `icon.dense` | 48 × 48 | EXCEPTION ONLY: a dense diagram with ≥ 16 icons where 78 would overflow the canvas. Must be uniform — never mix 78 and 48 in the same diagram. |

- **Never** use 40 or 60 — they are retired. A diagram uses exactly ONE icon size for all icons.
- Icon **label**: separate text cell below the icon, height ~25–30, centered on the icon's x-center.

## 2. Container colors (grounded in `templates/*.drawio`)

| Container | `strokeColor` | `fillColor` | `fontColor` | aws4 group shape |
|-----------|---------------|-------------|-------------|------------------|
| AWS Cloud | `#232F3E` | none | `#232F3E` | `group_aws_cloud` |
| Region | `#00A4A6` | none | `#147EBA` | `group_region` (dashed) |
| VPC | `#879196` | none | `#879196` | `group_vpc` |
| **Public subnet** | **`#7AA116`** (green) | `#F2F6E8` | `#248814` | `group_public_subnet` |
| **Private subnet** | **`#00A4A6`** (teal) | `#E6F6F7` | `#147EBA` | `group_private_subnet` |
| Security group / Inspection | `#C7131F` (red) | `#FEE7E7` | `#C62828` | `group_security_group` |
| Availability Zone | `#00A4A6` | none | `#147EBA` | dashed border |
| Corporate / On-prem (IDC) | `#5A6C86` | `#E6E6E6` | `#5A6C86` | `group_corporate_data_center` |
| Managed-services band | `#FF9900` (orange) | `#263238` | `#FFFFFF` | plain rounded box |

> **Public = green, Private = teal.** This matches the templates (Web Tier = green,
> App/Data Tier = teal). Do not swap them.
>
> ⚠️ **Subnets use `group_public_subnet` / `group_private_subnet` — NOT `group_security_group`.**
> The security-group icon is a padlock glyph at top-left: it (1) overlaps and clips the
> subnet label and (2) misreads as a security boundary. The subnet group shapes carry the
> correct border style (public = solid, private = dashed) and leave the label clear.

## 3. Edge / connector styles

| Token | Color | Width | Dash | Use |
|-------|-------|-------|------|-----|
| `edge.sync` | `#545B64` | 1.5 | solid | request / API call (data path) |
| `edge.async` | `#545B64` | 1.5 | `8 8` | event / message / queue |
| `edge.mgmt` | `#879196` | 1 | `4 4`, opacity 60 | logging / monitoring / IAM (de-emphasized) |
| `edge.highlight` | `#FF9900` | 2.5 | solid | the one path being emphasized |

- Routing: **orthogonal** (`edgeStyle=orthogonalEdgeStyle;rounded=0`). Route through
  whitespace lanes; never cross an icon's box. Use `scripts/route_edges.py`.
- **Edge budget: ≤ 12 visible edges.** Above that, switch to the numbered-flow pattern
  (badges ①②③ + a text legend) instead of drawing every connection.

## 4. Typography

| Token | Family | Size | Weight |
|-------|--------|------|--------|
| `font.title` | Helvetica / Amazon Ember | 16 | bold |
| `font.container-label` | Helvetica / Amazon Ember | 12 | bold |
| `font.icon-label` | Helvetica / Amazon Ember | 10 | normal |
| `font.edge-label` | Helvetica / Amazon Ember | 9 | normal |

## 5. Spacing & grid (the "breathing room" budget)

| Token | Value | Meaning |
|-------|-------|---------|
| `grid.base` | 10 px | every coordinate is a multiple of 10 (snap) |
| `grid.placement` | 80 px | icon-cell pitch (78 icon + margin) |
| `space.icon-gap` | ≥ 60 px | center-to-center between sibling icons (27 px is too tight) |
| `space.container-pad-top` | 50 px | room for the container label |
| `space.container-pad` | 30 px | sides / bottom inner padding |
| `space.icon-to-edge` | ≥ 40 px | icon to its container's edge |
| `space.subnet-gap` | 40 px | between sibling subnets |
| `space.canvas-margin` | ≥ 40 px | no element within 40 px of the canvas edge |

## 6. Verification (gate before export)

1. `scripts/validate_drawio.py <file>` — XML / silent-killer check (truncation guard).
2. `scripts/lint_layout.py <file>` — **layout QA, two layers**:
   - *geometry*: grid alignment, sibling-spacing uniformity, child-in-parent containment,
     icon overlap, edge-budget.
   - *design* (the "looks finished like a PPT" layer): icon-size discipline (78 + at most
     one nested 48 tier; 40/60/64 are retired), every icon labeled, container breathing
     room, a title present, consistent Amazon Ember/Helvetica type.
   Prints `score /100 [geometry · design]`; **non-zero exit = below threshold → do NOT
   export, fix first.** Use `--json` for the breakdown.
