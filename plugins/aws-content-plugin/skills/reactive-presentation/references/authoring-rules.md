# Authoring Rules & Patterns

A collection of detailed authoring rules, tables, and copy-paste templates. SKILL.md holds only
the workflow and gates; refer to this document **when actually authoring/validating slides**.

---

## 1. Validation — Rejection Loop (required before build)

> **Overcoming an LLM's limits at spatial reasoning**: language models cannot self-detect
> layout, alignment, or overlap on a 2D canvas. `validate` is an **externalized rejection loop**
> that mechanically detects structural/cognitive defects before build.

```bash
python3 {skill-dir}/scripts/remarp_to_slides.py validate {repo}/{slug}/
```

**Validation rules (rejection criteria)**:

| Rule | Severity | What it checks | Auto-fix guidance |
|------|--------|---------|-------------|
| `TYPE_MISMATCH` | WARNING | A numbered+timed pattern exists but `@type: agenda` is missing | Add `@type: agenda` |
| `INTERACTIVE_FIRST` | WARNING | 4+ bullets → cards/tabs not used | Convert to a `:::html` grid-card or tab pattern |
| `CONTENT_OVERFLOW` | CRITICAL | 8+ bullets or 12+ elements on one slide | Split across multiple slides |
| `CANVAS_COMPLEXITY` | CRITICAL/WARN | 5+/8+ visual elements on the canvas | Switch to `:::html` + `:::css` + flow utilities |
| `CANVAS_OVERLAP` | CRITICAL | Canvas element bounding boxes overlap | Adjust coordinates (minimum 40px gap) |
| `FRAGMENT_ORDER` | WARNING | A multi-column layout without explicit `order=N` | Add `{.click order=N}` (top-down, left-right order) |
| `MISSING_NOTES` | WARNING | Missing `:::notes` block | Write 150+ character speaker notes |
| `NOTE_STRUCTURE` | WARNING | A content slide's notes lack the `[요약]` ("Summary") hierarchy | Add `[요약]` ("Summary") (3-5 bullets) at the top of `:::notes` |
| `TITLE_LENGTH` | WARNING | Slide title exceeds 28 characters | Shorten to a headline of 28 characters or fewer (§3 Slide Title Voice) |
| `STATIC_HTML` | WARNING | 3+ `:::html` elements but no fragments | Add `fragment fade-up` + `data-fragment-index` |

**Rejection loop**: author → validate → if CRITICAL, fix and re-validate (up to 3 times) → otherwise review WARNINGs → build.

**Verdict**: `❌ REJECT` (CRITICAL≥1, build forbidden) · `⚠️ REVIEW` (WARNING≥6) · `⚠️ PASS WITH WARNINGS` (1-5) · `✅ PASS`.

---

## 2. Forbidden — AI-slide tells

Each tell is enforced by a **lint rule id** (machine-detected) or by the review gate (`content-review-agent`).

| Anti-pattern (AI-slide tell) | Why it reads as AI-generated | Use instead | Enforcement (lint rule / gate) |
|--------------------------|----------------|------|--------------------------|
| Hardcoded hex (raw 6-digit color values) | Ignores theme tokens, locks the deck to a single theme | Semantic role tokens like `var(--accent)` | `RAW_HEX` (lint) |
| Inline color/spacing style (color/padding written directly in `style=`) | Bypasses the token system, breaks consistency | Token classes (`.card-grid`, `.metric-card`) + `:::css` | `INLINE_STYLE` (lint) |
| Raw rgba color functions | Cannot adapt to theme, hardcoded shadows/overlays | `var(--surface-*)`, `color-mix()` tokens | `RAW_RGBA` (lint) |
| Magic-number/off-scale spacing (px outside the 4/8px scale) | Uneven spacing | Spacing-scale tokens (`var(--space-*)`) | `OFF_SCALE` (lint) + token system |
| Wall-of-text bullets (8+ lines) | Overloads one slide, unreadable | Split the slide or break into cards/tabs | `CONTENT_OVERFLOW` (lint) |
| Dark-only theme / generic blue-teal default | Reads as "AI default theme" | **Light-default** dual theme + role tokens | dual-theme (light default) |
| Gradient-text headings, decorative gradient orbs, empty lower-half space | Meaningless decoration, zero information density | Fill the area with content/visual hierarchy, remove decoration | guideline (review gate) |
| Encyclopedia-tone descriptive titles (e.g. "2026 Frontier AI Model Trends") | Flat label, no edge | Assertive/argumentative/question/twist headline (≤28 chars) | Slide Title Voice (gate) + `TITLE_LENGTH` (lint checks length only) |
| Free-form or missing speaker notes | Cannot be presented from, no structure | `[요약]` ("Summary") five-tier structured notes (150+ chars) | `NOTE_STRUCTURE` / `MISSING_NOTES` (lint) |

> Items with a rule id are mechanically caught by `validate` (§1); gate items (decoration, title voice) are deducted for by `content-review-agent`.

---

## 3. Slide Title Voice

The slide title (`## heading`) must be a **headline** readable in one second — carry edge via an assertion/argument/question/twist, **28 characters or fewer**.
Subtitles must end in **체언 종결** ("noun-form ending" — nominal endings like `~화/~등극/~재편/~본격화`, etc.), **45 characters or fewer**.
✅ "비용은 싸졌고, 모델은 똑똑해졌다" (Costs went down, models got smarter) ❌ "2026년 Frontier AI 모델 동향" (2026 Frontier AI Model Trends — a flat, encyclopedic label).
**Level gate**: for `level` 100-200, a headline is recommended; 300-400 also allows descriptive titles (API names, config keys).
Exceeding 28 characters triggers `validate`'s `TITLE_LENGTH` warning. Full examples: [slide-patterns.md](slide-patterns.md) "Slide Title Voice".

---

## 4. Interactive Design (★ highest priority)

> **Core rule: the more information a slide holds, the more interactive it must be.** 10 bullet lines < 3 tabs × 3 cards each.
> The default pattern is "lay data out as visual cards + reveal progressively via tabs/toggles."

1. **Split into tabs**: 3+ sub-items of the same topic → separate into tabs
2. **Card grid**: 4+ listed items → use the `.card-grid` token class (bullet lists forbidden)
3. **Self-contained**: every interaction is completed via an inline onclick inside `:::html` (no external JS dependency)
4. **Visual hierarchy**: color must use only semantic role tokens (`var(--accent/--info/--success/--warning/--danger)`). Hardcoded hex/rgba and solid-color backgrounds are forbidden
5. **`:::html` reactive**: 3+ peer elements must appear sequentially via `class="fragment fade-up" data-fragment-index="N"` (static HTML forbidden)

> **Theme**: light by default. Dark mode is set via `class="… theme-dark"` on the deck root. Per-slide dark mode uses `@theme: dark`. All colors auto-adapt to both via theme.css tokens.

### Self-contained Tab Pattern (copy-paste)

Works without slide-framework.js. Colors are handled by theme.css's `.tab-set`/`.tab-btn.active`/`.metric-card`/`.callout` (no inline styles). Use when data has 3+ categories:

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

| Role | Token | Subtle background | Class helper | Use case |
|------|------|------------|-------------|------|
| accent | `var(--accent)` | `var(--accent-subtle)` | `.text-accent` | Primary/input/source |
| success | `var(--success)` | `var(--success-subtle)` | `.callout-success` | Success/result/automation |
| warning | `var(--warning)` | `var(--warning-subtle)` | `.callout-warning` | Warning/processing/AI |
| info | `var(--info)` | `var(--info-subtle)` | `.callout-info` | Supplementary/streaming/analytics |
| danger | `var(--danger)` | `var(--danger-subtle)` | `.callout-danger` | Error/risk/alert |

Surfaces/text use `var(--surface-1/2/3)`, `var(--on-surface)`, `var(--on-surface-muted)`. Full reference: [colors-reference.md](colors-reference.md).

### Bullet List → Card Conversion

**Before (ineffective)**: `- CloudWatch Agent: metric collection` … a list of bullets
**After (effective)** — `.card-grid` + `.metric-card` (colors from theme.css):
```html
<div class="card-grid">
  <div class="metric-card"><strong class="text-accent">CloudWatch Agent</strong><div class="on-surface-muted">메트릭 수집</div></div>
  <!-- ... 반복 ... -->
</div>
```

Complex interactions (sliders, simulators, dashboards) use `:::html` + `:::script` + `:::css`. Templates/examples: [interactive-patterns-guide.md](interactive-patterns-guide.md).

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
| Block summary | Quiz (if quizzes are on) / Content (Key Takeaways) | `data-quiz` 3-4 questions / summary list |
| Block closing | Thank You | Gradient heading + TOC link |
| Simulator/dashboard/tester/builder (VPA, Grafana, Regex, YAML, Mode, cost) | `:::html` + `:::script` | sliders/inputs → live output |

### Canvas DSL vs `:::html` (important)

> For complex diagrams/interactions, prefer `:::html` + `:::css` (+`:::script`). The Canvas DSL is for simple boxes+arrows only.

| Complexity | Approach | Example |
|--------|------|------|
| **Simple** (≤4 boxes + arrows) | `:::canvas` DSL allowed | A→B→C |
| **Medium** (5+ boxes, multi-tier) | `:::html` + `:::css` required (canvas forbidden) | 3-tier, service map, ecosystem |
| **Complex** (interaction + computation) | `:::html` + `:::script` required | Slider, calculator, dashboard |
| **Static architecture** | `@img:` + draw.io | Full AWS architecture, VPC |

### Canvas vs Diagram

| Criterion | Canvas (`@type: canvas`) | Diagram (`@img:`) |
|------|--------------------------|---------------------|
| Purpose | Step-by-step flow animation | Full architecture at a glance |
| Advantage | Sequential ↑↓ step explanation | Accurate for complex layout/arrows |
| Authoring | Code the Canvas DSL directly | draw.io/architecture-diagram → PNG/SVG |

**Principle**: if the animation doesn't add explanatory power, use a diagram image instead. For complex diagrams, prefer `:::html`+`:::css`.

> Before using `:::canvas`, always read [canvas-authoring-guide.md](canvas-authoring-guide.md) — DSL syntax, required coordinate formulas, fragment order.

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
- `bg-blue`/`bg-orange`/`bg-pink`: color utilities · `data-fragment-index="N"`: sequential per-group reveal
- AWS icons: `common/aws-icons/services/Arch_{Name}_48.svg`

> The canon for the Canvas-vs-HTML threshold is the complexity table in §5 — validate's `CANVAS_COMPLEXITY` backstops it against the same criteria.
