# Semantic Color Token Reference

Reactive-presentation colors are expressed as **semantic role tokens, not hardcoded hex values**.
Tokens are defined in `assets/design-tokens.css` and bound to actual values within the
`.theme-light` (default) / `.theme-dark` scopes of `assets/theme.css`. Slides and templates
always use `var(--*)` tokens, so they automatically adapt to light/dark theme switching and to
PPTX brand extraction (Phase 1).

> **Theme default**: light is the default. To switch back to dark, apply `class="… theme-dark"`
> to the deck root element (frontmatter `theme: { mode: dark }`). Because tokens are used, the
> same markup renders with correct contrast in both themes.
>
> **Palette identity**: the default theme is grounded in AWS's own design language — light mode
> uses a console-gray canvas (`#eaedee`) + white cards + Squid Ink–family text (`#0f141a`; the
> brand reference color Squid Ink itself is `#232F3E`) + a Smile Orange accent (`#ec7211`) +
> Cloudscape blue text accent (`#0972d3`); dark mode uses squid-ink night (`#0f1b2a` family) +
> `#ff9900`. The old warm-paper look is available as an opt-in via `theme: { preset: paper }`.
> For background/selection principles, see [design-direction.md](design-direction.md).

---

## Role Tokens (top priority for use)

### Surfaces & Text

| Token | Role | Usage |
|------|------|------|
| `--surface-1` | The lowest-level surface (deck/slide background) | `background: var(--surface-1)` |
| `--surface-2` | Card/panel surface | `background: var(--surface-2)` |
| `--surface-3` | Borders/dividers/grid lines on top of surfaces | `border-color: var(--surface-3)` |
| `--on-surface` | Body text on a surface | `color: var(--on-surface)` |
| `--on-surface-muted` | Secondary/caption text, chart axis labels | `color: var(--on-surface-muted)` |

### Accent & Status

Each role has 3 tokens: **base** (fill/stroke), **`-subtle`** (light background tint), and
**`-on`** (text placed on top of base).

| Role | base | subtle background | on (text) | Meaning |
|------|------|-------------|-------------|------|
| accent | `--accent` | `--accent-subtle` | `--accent-on` | Primary emphasis, input/source, primary CTA |
| info | `--info` | `--info-subtle` | `--info-on` | Secondary information, streaming/analytics |
| success | `--success` | `--success-subtle` | `--success-on` | Success, results, automation |
| warning | `--warning` | `--warning-subtle` | `--warning-on` | Warning, in-progress, AI/inference |
| danger | `--danger` | `--danger-subtle` | `--danger-on` | Error, risk, alert |

**Usage pattern**:

```css
/* Card: surface + body text */
.metric-card { background: var(--surface-2); color: var(--on-surface); border: 1px solid var(--surface-3); }

/* Status badge: base fill + on text (guarantees contrast) */
.badge-warn  { background: var(--warning); color: var(--warning-on); }

/* Light emphasis area: subtle tint + base border + role text */
.callout-info { background: var(--info-subtle); border: 1px solid var(--info); color: var(--on-surface); }

/* Accent text */
.text-accent { color: var(--accent); }
```

> Old legacy aliases (`--blue`, `--cyan`, `--green`, `--yellow`, `--red`, `--text-muted`) may
> still remain in theme.css for backward compatibility, but **new content should use the role
> tokens above.** Mapping: blue/cyan→`--info`/`--accent`, green→`--success`, yellow/orange→`--warning`,
> red→`--danger`, text-muted→`--on-surface-muted`.

---

## Scale Tokens (spacing, radius, typography, shadow)

Non-color design values also use tokens. Instead of hardcoded px/rem:

| Group | Token | Usage |
|------|------|------|
| Spacing (8px grid) | `--space-1`…`--space-8` | `padding`, `gap`, `margin` |
| Radius | `--radius-sm` / `--radius-md` / `--radius-lg` / `--radius-pill` | `border-radius` |
| Type scale | `--text-xs`…`--text-4xl` | `font-size` |
| Type role | `--leading-tight/normal/relaxed`, `--weight-regular/medium/semibold/bold` | line-height, weight |
| Tracking | `--tracking-tight/normal/wide` | tight for display titles, wide for eyebrows/labels |
| Typeface | `--font-display` / `--font-main` / `--font-mono` | h1/h2 display, body, data/code |
| Shadow | `--shadow-1/2/3`, `--shadow-glow` | `box-shadow` |
| Motion | `--duration-fast/normal/slow` | transition/animation |
| Z ladder | `--z-base/nav/overlay/modal/toast` | `z-index` |

---

## Token-backed Primitive Classes

Most slides combine theme.css's **primitive classes** rather than using `var(--*)` directly
(since the classes consume the tokens, theme adaptation is automatic):

| Class | Role |
|--------|------|
| `.card-grid` | Auto-fit responsive card grid |
| `.metric-card` | Surface card (KPI/metric) |
| `.callout` + `.callout-info/-warning/-danger/-success` | Status-specific emphasis boxes |
| `.comparison` | Comparison surface box |
| `.tab-set` / `.tab-btn`(+`.active`) | Tab bar (active is filled with accent) |
| `.flow-group` / `.flow-h` / `.flow-box` / `.flow-arrow` | Architecture flow layout |

---

## Canvas & JSON colors (named tokens)

Runtime rendering paths receive **named tokens** instead of hex values.

- **Canvas DSL** (`:::canvas`): `box id "label" at X,Y size W,H color <name>` — `<name>` is
  `accent`, `green`, `yellow`, `red`, `blue`, or `cyan` (resolved via animation-utils.js
  `Colors.*`, adapting to theme/PPTX).
- **slides.json**: use the same named tokens (`accent`, `cyan`, `yellow`, `red`, `muted`, etc.)
  in the `"color"` / `"colors"` fields.
- **Chart.js**: read tokens via `getComputedStyle(document.documentElement).getPropertyValue('--accent')`
  (see slide-patterns.md §16).

---

## PPTX brand extraction → tokens (Phase 1)

When a `.pptx` template is provided, `extract_pptx_theme.py` extracts brand colors and rebinds
the role tokens in `theme-override.css`. That is, **the extracted brand colors flow into
`--accent`, `--surface-*`, etc.**, and propagate to every token-based slide at once. Slide
markup does not change — only the token values change.

The PPTX MCP tools (`mcp__ppt__*`) don't accept tokens directly; they take `[r, g, b]` arrays,
so pass the RGB values from the extracted manifest (`theme-manifest.json`) directly. Even then,
map them to the same semantic roles (accent/surface/on-surface). Example:

```yaml
# Surface background = surface role, text = on-surface role (values from the manifest)
mcp__ppt__add_table:
  header_bg_color: <theme-manifest surface RGB>
  header_font_color: <theme-manifest on-surface RGB>
mcp__ppt__add_shape:
  fill_color: <theme-manifest accent RGB>   # accent role
```

---

## Accessibility

1. **Contrast ratio**: body text must have at least 4.5:1 contrast against the surface. The
   `--on-surface` / `--on-surface-muted` combinations with `--surface-*`, and the `-on` tokens
   paired with each status base, are defined to satisfy this contrast.
2. **Color-blindness consideration**: don't convey meaning through color alone — pair it with
   icons/labels (especially for success/danger).
3. **Consistency**: use the same role token for the same meaning (e.g., "success" is always
   `--success`).
