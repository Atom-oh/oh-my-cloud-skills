# Authoring Rules & Patterns

A collection of the detailed rules, tables, and copy-paste templates applied during authoring. SKILL.md covers only the workflow and gates;
refer to this document when **actually writing/validating slides**.

---

## 1. Validation — Rejection Loop (mandatory before build)

> **Overcoming LLM spatial-reasoning limits**: language models cannot self-detect layout, alignment, or
> overlap issues on a 2D canvas. `validate` is an **externalized rejection loop** that mechanically
> catches structural/cognitive defects before the build.

```bash
python3 {skill-dir}/scripts/remarp_to_slides.py validate {repo}/{slug}/
```

**Validation rules (rejection criteria)**:

| Rule | Severity | What it checks | Auto-fix guidance |
|------|--------|---------|-------------|
| `TYPE_MISMATCH` | WARNING | A numbered+timed pattern is present but `@type: agenda` is missing | Add `@type: agenda` |
| `INTERACTIVE_FIRST` | WARNING | 4+ bullets but no cards/tabs used | Convert to `:::html` grid cards or a tab pattern |
| `CONTENT_OVERFLOW` | CRITICAL | 8+ bullets or 12+ elements on a single slide | Split into multiple slides |
| `CANVAS_COMPLEXITY` | CRITICAL/WARN | 5+/8+ visual elements on the canvas | Switch to `:::html` + `:::css` + flow utilities |
| `CANVAS_OVERLAP` | CRITICAL | Canvas element bounding boxes overlap | Adjust coordinates (minimum 40px gap) |
| `FRAGMENT_ORDER` | WARNING | Multi-column layout with no explicit `order=N` | Add `{.click order=N}` (td-lr order) |
| `MISSING_NOTES` | WARNING | `:::notes` block missing | Write 150+ character speaker notes |
| `NOTE_STRUCTURE` | WARNING | Content slide notes lack a `[Summary]` hierarchy | Add `[Summary]` (3–5 bullets) at the top of `:::notes` |
| `TITLE_LENGTH` | WARNING | Slide title exceeds 28 characters | Shorten to a headline of 28 characters or fewer (§3 Slide Title Voice) |
| `STATIC_HTML` | WARNING | 3+ `:::html` elements with no fragments | Add `fragment fade-up` + `data-fragment-index` |

**Rejection loop**: write → validate → if CRITICAL exists, fix and re-validate (up to 3 times) → otherwise review WARNINGs → build.

**Verdict**: `❌ REJECT` (CRITICAL≥1, build forbidden) · `⚠️ REVIEW` (WARNING≥6) · `⚠️ PASS WITH WARNINGS` (1–5) · `✅ PASS`.

> ⚠️ Running `build` while CRITICAL issues exist produces a Frankenstein layout.

---

## 2. Forbidden — AI-slide tells

Each tell links to an enforcing **lint rule id** (machine-detected) or a review gate (`content-review-agent`).

| Anti-pattern (AI-slide tell) | Why it's a tell | Use instead | Enforcement (lint rule / gate) |
|--------------------------|----------------|------|--------------------------|
| Hardcoded hex (raw 6-digit color values) | Ignores theme tokens, locks into a single theme | Semantic role tokens like `var(--accent)` | `RAW_HEX` (lint) |
| Inline color/spacing style (color/padding written directly in `style=`) | Bypasses the token system, breaks consistency | Token classes (`.card-grid`, `.metric-card`) + `:::css` | `INLINE_STYLE` (lint) |
| Raw rgba color functions | Can't adapt to theme, hardcoded shadows/overlays | `var(--surface-*)`, `color-mix()` tokens | `RAW_RGBA` (lint) |
| Magic-number/off-scale spacing (px values outside the 4/8px scale) | Uneven spacing | Spacing-scale tokens (`var(--space-*)`) | `OFF_SCALE` (lint) + token system |
| Wall-of-text bullets (8+ lines) | Overloads a single slide, becomes unreadable | Split the slide or break into cards/tabs | `CONTENT_OVERFLOW` (lint) |
| Dark-only / generic blue-teal default | Reads as an "AI default theme" | **Light-default** dual theme + role tokens | dual-theme (light default) |
| Gradient text headings · decorative gradient orbs · empty bottom space | Meaningless decoration, zero information density | Fill the space with content/visual hierarchy, remove decoration | Guideline (review gate) |
| Encyclopedia-tone descriptive titles ("2026 Frontier AI Model Trends") | Flat label, no edge | Assertive/argumentative/question/twist headline (28 chars or fewer) | Slide Title Voice (gate) + `TITLE_LENGTH` (length-only lint) |
| Freeform / missing speaker notes | Not presentable, no structure | `[Summary]`-structured notes with 5 tiers (150+ chars) | `NOTE_STRUCTURE` / `MISSING_NOTES` (lint) |

> Items with a rule id are caught mechanically by `validate` (§1); gate items (decoration, title voice) are penalized by `content-review-agent`.

---

## 3. Slide Title Voice

The slide title (`## heading`) is a **headline** readable in one second — carrying an edge through assertion/argument/question/twist, at **28 characters or fewer**.
The subtitle ends in a **noun form** (nominalized endings like `~화/~등극/~재편/~본격화` in Korean, or the equivalent noun-phrase construction in English) at **45 characters or fewer**.
✅ "Costs got cheaper, models got smarter"  ❌ "2026 Frontier AI Model Trends" (a flat label).
**Level gate**: `level` 100–200 should prefer headlines; 300–400 also allows descriptive titles (API names, config keys).
Exceeding 28 characters triggers `validate`'s `TITLE_LENGTH` warning. Full examples: [slide-patterns.md](slide-patterns.md) "Slide Title Voice".

---

## 4. Interactive Design (★ Top Priority)

> **Key point: the more information-dense a slide is, the more interactive it should be.** 3 tabs × 3 cards beats 10 lines of bullets.
> The default pattern is "lay out data as visual cards + progressively reveal via tabs/toggles."

1. **Split into tabs**: 3+ subsections on the same topic → separate into tabs
2. **Card grid**: 4+ listed items → `.card-grid` token class (bullet lists forbidden)
3. **Self-contained**: every interaction is completed via an inline onclick inside `:::html` (no dependency on external JS)
4. **Visual hierarchy**: colors only via semantic role tokens (`var(--accent/--info/--success/--warning/--danger)`). Hardcoded hex/rgba and flat backgrounds are forbidden
5. **`:::html` reactive**: 3+ sibling elements should appear sequentially via `class="fragment fade-up" data-fragment-index="N"` (static HTML is forbidden)

> **Theme**: light by default. Dark mode is set via `class="… theme-dark"` on the deck root. Per-slide dark mode uses `@theme: dark`. All colors auto-adapt to both via theme.css tokens.

### Self-contained tab pattern (copy-paste)

Works without slide-framework.js. Colors are handled by theme.css's `.tab-set`/`.tab-btn.active`/`.metric-card`/`.callout` (inline styles forbidden). Use when the data has 3+ categories:

```markdown
:::html
<div class="tab-set" onclick="(function(e){var b=e.target.closest('.tab-btn');if(!b)return;var bar=b.parentNode,p=bar.parentNode,i=[].indexOf.call(bar.children,b);bar.querySelectorAll('.tab-btn').forEach(function(x){x.classList.remove('active')});b.classList.add('active');p.querySelectorAll('.tc').forEach(function(c,j){c.hidden=j!==i})})(event)">
  <button class="tab-btn active">Tab 1</button>
  <button class="tab-btn">Tab 2</button>
  <button class="tab-btn">Tab 3</button>
</div>
<div class="tc">
  <div class="card-grid">
    <div class="metric-card"><strong class="text-accent">Card Title</strong><div class="on-surface-muted">Description</div></div>
    <div class="metric-card"><strong class="text-success">Next Step</strong><div class="on-surface-muted">Description</div></div>
  </div>
</div>
<div class="tc" hidden>
  <div class="card-grid">
    <div class="callout callout-info"><strong class="text-info">item-1</strong> — Description</div>
    <div class="callout callout-warning"><strong class="text-warning">item-2</strong> — Description</div>
  </div>
</div>
<div class="tc" hidden>
  <div class="card-grid">
    <div class="callout callout-success"><strong class="text-success">Type A</strong><div class="on-surface-muted">Details here</div></div>
    <div class="callout callout-info"><strong class="text-accent">Type B</strong><div class="on-surface-muted">Details here</div></div>
  </div>
</div>
:::

:::css
.text-accent  { color: var(--accent);  font-weight: var(--weight-bold); }
.text-info    { color: var(--info);    font-weight: var(--weight-bold); }
.text-success { color: var(--success); font-weight: var(--weight-bold); }
.text-warning { color: var(--warning); font-weight: var(--weight-bold); }
.text-danger  { color: var(--danger);  font-weight: var(--weight-bold); }
.on-surface-muted { color: var(--on-surface-muted); font-size: var(--text-sm); }
:::
```

**Semantic color roles** (instead of hardcoded hex):

| Role | Token | Subtle background | Class helper | Usage |
|------|------|------------|-------------|------|
| accent | `var(--accent)` | `var(--accent-subtle)` | `.text-accent` | default/input/source |
| success | `var(--success)` | `var(--success-subtle)` | `.callout-success` | success/result/automation |
| warning | `var(--warning)` | `var(--warning-subtle)` | `.callout-warning` | warning/processing/AI |
| info | `var(--info)` | `var(--info-subtle)` | `.callout-info` | secondary/streaming/analysis |
| danger | `var(--danger)` | `var(--danger-subtle)` | `.callout-danger` | error/risk/alert |

Surfaces/text use `var(--surface-1/2/3)`, `var(--on-surface)`, `var(--on-surface-muted)`. Full reference: [colors-reference.md](colors-reference.md).

### Converting bullet lists to cards

**Before (ineffective)**: `- CloudWatch Agent: metric collection` … a list of bullets
**After (effective)** — `.card-grid` + `.metric-card` (colors from theme.css):
```html
<div class="card-grid">
  <div class="metric-card"><strong class="text-accent">CloudWatch Agent</strong><div class="on-surface-muted">Metric collection</div></div>
  <!-- ... repeat ... -->
</div>
```
> ⛔ If you're about to put 4+ bullets on one slide, STOP → convert to grid cards + color differentiation instead.

For complex interactions (sliders, simulators, dashboards), use `:::html` + `:::script` + `:::css`. Templates/examples: [interactive-patterns-guide.md](interactive-patterns-guide.md).

---

## 5. Slide Type Decision Guide

> ⛔ Write an explicit `@type` on every slide. Do not rely on auto-detect. `agenda`/`tabs`/`steps` in particular are mandatory.

| Content Type | Slide Pattern | Interactive Element |
|---|---|---|
| Architecture overview (static) | Diagram Image | draw.io → PNG/SVG, `@img:` |
| Step-by-step flow (≤4 boxes) | Canvas Animation | `:::canvas` DSL, step ↑↓ |
| Multi-layer architecture (5+ boxes) | HTML Architecture | `:::html` + `:::css` flexbox/grid (§6) |
| A vs B comparison | Compare Toggle | `.compare-toggle` buttons |
| Config variants | Tab Content | `.tab-bar` + YAML code |
| Step-by-step process | Timeline | `.timeline` animated steps |
| Monitoring/dashboard (5+ boxes) | `:::html` + `:::script` | Stat panels + node grid |
| Parameter exploration / calculator | Slider | `input[type=range]` + live output |
| Best practices | Checklist | `.checklist` click-to-toggle |
| YAML/code example | Code Block | `.code-block` syntax spans |
| Customer problem | Pain Quote | `.pain-quote` + challenge list |
| Session agenda/table of contents | Agenda | `@type: agenda` numbered dots + time |
| Block summary | Quiz (for a quiz) / Content (Key Takeaways) | `data-quiz` with 3–4 questions / summary list |
| Block closing | Thank You | Gradient heading + TOC link |
| Simulator/dashboard/tester/builder (VPA, Grafana, Regex, YAML, mode, cost) | `:::html` + `:::script` | sliders/inputs → live output |

### Canvas DSL vs `:::html` (important)

> For complex diagrams/interactions, prefer `:::html` + `:::css` (+`:::script`). Canvas DSL is for simple boxes+arrows only.

| Complexity | Approach | Example |
|--------|------|------|
| **Simple** (≤4 boxes + arrows) | `:::canvas` DSL allowed | A→B→C |
| **Medium** (5+ boxes, multi-layer) | `:::html` + `:::css` required (canvas forbidden) | 3-tier, service map, ecosystem |
| **Complex** (interaction + computation) | `:::html` + `:::script` required | sliders, calculators, dashboards |
| **Static architecture** | `@img:` + draw.io | full AWS architecture, VPC |

### Canvas vs Diagram

| Criterion | Canvas (`@type: canvas`) | Diagram (`@img:`) |
|------|--------------------------|---------------------|
| Purpose | step-by-step flow animation | see the whole architecture at a glance |
| Advantage | ↑↓ step-by-step narration | accurate complex layout/arrows |
| Production | code the Canvas DSL directly | draw.io/architecture-diagram → PNG/SVG |

**Principle**: if animation doesn't add explanatory power, use a diagram image instead. For complex diagrams, prefer `:::html`+`:::css`.

> Before writing `:::canvas`, you must read [canvas-authoring-guide.md](canvas-authoring-guide.md) — DSL syntax, the required coordinate formula, and fragment ordering.

---

## 6. HTML Architecture Pattern (required for 5+ boxes)

```markdown
## Service Pipeline

:::html
<div class="flow-h">
  <div class="flow-group bg-blue" data-fragment-index="1">
    <div class="flow-group-label">수집</div>
    <div class="icon-item"><img src="common/aws-icons/services/Arch_Amazon-CloudWatch_48.svg"><span>CloudWatch</span></div>
    <div class="icon-item"><img src="common/aws-icons/services/Arch_AWS-X-Ray_48.svg"><span>X-Ray</span></div>
  </div>
  <div class="flow-arrow">→</div>
  <div class="flow-group bg-orange" data-fragment-index="2">
    <div class="flow-group-label">분석</div>
    <div class="flow-box">DevOps Guru</div>
    <div class="flow-box">Bedrock</div>
  </div>
  <div class="flow-arrow">→</div>
  <div class="flow-group bg-pink" data-fragment-index="3">
    <div class="flow-group-label">대응</div>
    <div class="flow-box">EventBridge</div>
    <div class="flow-box">Lambda</div>
  </div>
</div>
:::
```

- `flow-h`/`flow-group`/`flow-box`/`flow-arrow`: theme.css utilities (no custom CSS needed, stage height/width auto-uniform)
- `bg-blue`/`bg-orange`/`bg-pink`: color utilities · `data-fragment-index="N"`: sequential reveal per group
- AWS icons: `common/aws-icons/services/Arch_{Name}_48.svg`

> ⛔ Before using canvas: 5+ boxes+icons → canvas is forbidden, use the HTML pattern above. Canvas is allowed only for a single-direction straight line (A→B→C).
