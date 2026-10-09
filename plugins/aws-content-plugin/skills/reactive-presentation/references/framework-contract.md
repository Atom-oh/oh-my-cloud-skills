# Framework Contract — Generated HTML and Advanced Source Blocks

This document describes the renderer contract used by the Remarp compiler and by advanced `:::html`/`:::script` source blocks. New decks are authored in Remarp and compiled; do not independently edit their generated HTML. The skeleton below also supports explicitly requested legacy/manual HTML decks, with `assets/example-deck/` as a reference.
Everything here is derived from the actual code in `assets/` — if this document disagrees with the code, that's a bug (`tests/structure/test-reactive-design-tokens.sh` enforces token coverage).

## 1. Deck Skeleton (required DOM)

`theme.css` and `slide-framework.js` require this structure:

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Deck Title</title>
  <link rel="stylesheet" href="./common/theme.css">
  <!-- PPTX 테마 추출 시에만: -->
  <link rel="stylesheet" href="./common/pptx-theme/theme-override.css">
</head>
<body>
<div class="slide-deck">                <!-- 정확히 1개. theme-dark를 여기 붙이면 덱 전체 다크 -->
  <div class="slide">                   <!-- 슬라이드마다 1개 -->
    <div class="slide-header">
      <h2>제목 (≤28자 헤드라인)</h2>
      <p class="subtitle">부제 (체언 종결, ≤45자)</p>
    </div>
    <div class="slide-body">
      <!-- 콘텐츠 -->
    </div>
    <template class="notes" data-timing="3min">
[요약]
- 핵심 3~5 불릿
구어체 스피커 스크립트 (150자+, 권장 300~500).
{cue: demo} 마커 사용 가능.
    </template>
  </div>
  <!-- ... more .slide ... -->
</div>
<script src="./common/animation-utils.js"></script>
<script src="./common/slide-framework.js"></script>
<script src="./common/quiz-component.js"></script>
<script src="./common/presenter-view.js"></script>
<script>
  // presenterNotes: top-level const — export_pptx.py가 이 형태로 읽는다.
  // <template class="notes">를 쓰면 생략 가능 (프레임워크가 DOM에서 수집).
  const deck = new SlideFramework({
    footer: '© 2026 Company — Session Title',
    logoSrc: './common/logo.png',        // 선택
    logoDarkSrc: './common/logo-w.png',  // 선택: 다크 슬라이드용 밝은 로고
    pagination: true,                    // true: "N / M" 페이지 번호
    sidebar: true,                       // 좌측 썸네일 사이드바 (S 토글)
    onSlideChange: (index, slide) => {}  // 선택
  });
</script>
</body>
</html>
```

- Cover/section slides may use a free layout without `.slide-header`/`.slide-body` —
  but the top-level element must still be `.slide`.
- Keep the convention: first slide = Session Cover, last slide = Thank You (with a table-of-contents link).
- Speaker notes: `<template class="notes">` is recommended (no escaping needed, clean diffs).
  The legacy `const presenterNotes = {1: "...", ...}` + `presenterNotes:` option still works.
  If both are present, the option object takes priority.

## 2. Theme Tokens (theme.css)

**3 scopes**: `:root, .theme-light` (default — AWS Console light) · `.theme-dark` (squid-ink
night; class applied to the deck root or to individual `.slide` elements) · `.preset-paper` (warm look, only when explicitly selected).
Brand colors extracted from a PPTX arrive as `--pptx-accent1/dk1/lt1/dk2/lt2` and always take priority
(`--accent: var(--pptx-accent1, #ec7211)`).

**Semantic roles (colors must always use these tokens — raw hex/rgba is forbidden and caught by `check_deck.py`):**

| Role | Token | Subtle bg | On-color | Purpose |
|----|------|------------|-------|------|
| accent | `--accent` | `--accent-subtle` | `--accent-on` | Emphasis/input/source (light: Smile orange #ec7211) |
| info | `--info` | `--info-subtle` | `--info-on` | Secondary/analysis (Cloudscape blue) |
| success | `--success` | `--success-subtle` | `--success-on` | Success/result |
| warning | `--warning` | `--warning-subtle` | `--warning-on` | Warning/processing |
| danger | `--danger` | `--danger-subtle` | `--danger-on` | Error/risk |

**Surface/text**: `--surface-1/2/3` (card background levels) · `--on-surface` ·
`--on-surface-muted` · `--bg-primary` (page canvas) · `--border` · `--border-focus`.

**Legacy aliases** (for compatibility with old markup/canvas code; new code should prefer role tokens):
`--green/--yellow/--red/--blue/--orange` (+`-bg`) → routed to role tokens ·
`--cyan`/`--pink` (scope-specific unique hues — canvas diagrams depend on these being distinct from blue/red) ·
`--bg-secondary/tertiary/card` · `--surface` · `--text-primary/secondary/muted/accent` ·
`--accent-light` · `--accent-glow` · `--shadow-glow`.

**design-tokens.css (imported by theme.css via @import)**:

| Group | Tokens |
|------|------|
| Type scale (modular 1.25) | `--text-xs` `--text-sm` `--text-base` `--text-lg` `--text-xl` `--text-2xl` `--text-3xl` `--text-4xl` |
| Projection type roles (fit-era defaults; 1rem = 24px) | `--fs-title` `--fs-subtitle` `--fs-body` `--fs-card` `--fs-caption` `--leading-body` |
| Line height | `--leading-tight` `--leading-normal` `--leading-relaxed` |
| Weight | `--weight-regular` `--weight-medium` `--weight-semibold` `--weight-bold` |
| Letter spacing | `--tracking-tight` `--tracking-normal` `--tracking-wide` |
| Spacing (8px grid — no magic-number px, enforced by the OFF_SCALE lint) | `--space-1` `--space-2` `--space-3` `--space-4` `--space-5` `--space-6` `--space-7` `--space-8` |
| Rounding | `--radius-sm` `--radius-md` `--radius-lg` `--radius-pill` |
| Shadow | `--shadow-1` `--shadow-2` `--shadow-3` `--shadow-glow` |
| Motion | `--duration-fast` `--duration-normal` `--duration-slow` `--ease-out` |
| z-index | `--z-base` `--z-nav` `--z-overlay` `--z-modal` `--z-toast` |

**Fonts**: `--font-display` (Space Grotesk→Pretendard, headings) · `--font-main` (Pretendard) ·
`--font-mono` (JetBrains Mono).

**Sizing**: `--slide-width/height`, `--slide-ratio-w/h` (default 16/9) — redefine only for non-16:9 decks.

## 3. Scaling Model

A fixed 1920×1080 design canvas: `.slide-deck` is scaled as a whole by `transform: scale(var(--deck-scale))`.
`SlideFramework.updateDeckScale()` sets `--deck-scale` to `min(availW/1920, availH/1080)`, where `availW`
excludes the 220px sidebar while it is visible, and recomputes it on resize and fullscreen changes. Inside a slide, absolute px coordinates are safe to
use (the whole canvas scales together). **Never use viewport units (vw/vh) for content sizing** —
they respond a second time outside the scale transform, breaking proportions.

## 4. SlideFramework API (slide-framework.js)

```js
new SlideFramework({ footer, logoSrc, logoDarkSrc, presenterNotes, pagination,
                     sidebar, onSlideChange })
deck.registerSlideAction(slideIndex, { up: fn, down: fn })  // ↑↓ 키 가로채기; false 반환 시 슬라이드 이동
deck.goTo(i) / deck.next() / deck.prev()
```

- Auto-generated by the framework: progress bar, slide counter/number, nav hint, footer,
  logo, ref container, thumbnail sidebar (scales the 1920px content down; the clones drop every
  `id` so `getElementById()` keeps returning the live slide element, and carry the slide's
  `theme-dark`/`theme-light` class).
- **Key map** (default): `←→ Space PageUp/Down` move + fragment · `↑↓` slideAction →
  interactive cycling (canvas step/tabs/compare) → fragment · `Home/End` · `P` presenter ·
  `F` fullscreen · `O` overview · `S` sidebar · `Esc`. Remap via `window.__remarpKeys`.
- Footer/logo/page number/refs are auto-hidden only on a **full-bleed** slide: the slide (or an
  element in it) carries `data-hide-chrome` or `.full-bleed`, or one `<img>` covers at least 60% of
  the slide area. Inline images — service icons, a diagram or screenshot in a column — keep the
  chrome. `data-keep-chrome` on the `.slide` always keeps it (it wins over every hide rule).
- `data-transition="fade|slide|zoom"` for per-slide transitions.
- `data-fit="auto|shrink|off"` on a `.slide` (or on `.slide-deck` as the deck default) selects the
  ReactiveFit mode for that slide's `.slide-body` content — see §11.
- `data-refs='[{"url":"…","label":"…"}]'` → reference links at the bottom.
- Slide deep-linking via the URL hash `#N`.

**Fragments**: `class="fragment fade-up" data-fragment-index="N"` — revealed sequentially with
Space/→. Elements sharing the same index reveal together. Animations: `fade-in/up/down/left/right, grow, shrink,
highlight(-red/-green), strike, fade-out`.

**Canvas step slides**: attach `slide.__canvasStep = (dir) => bool` to the slide element —
↑↓ then drives the step, and returning `false` at the boundary lets the slide advance instead.
(Or use `registerSlideAction`.)

**Auto-initialized components** (via `initTabs/initChecklists/
initCompareToggles` on DOMContentLoaded):
- Tabs: `.tab-bar > .tab-btn[data-tab="id"]` + sibling `.tab-content[data-tab="id"]`
  (shown via `.active`). Also cyclable with ↑↓ keys. `initTabs` groups the bar's sibling
  panels into one `.tab-panels` stack (authors may write `.tab-panels` directly): all panels
  share one grid cell and inactive ones are `visibility: hidden`, so the stack is as tall as
  the tallest panel — switching tabs never moves the tab bar, and ReactiveFit sizes the
  slide for the tallest panel. A tab click toggles every `.tab-content` under the bar's
  parent, so content that changes per tab but sits below the panels (e.g. a one-line rule
  callout) goes in a second `.tab-panels` stack with the same `data-tab` ids: it then keeps
  one position for every tab instead of following each panel's height.
- Self-contained tabs (`.tab-set` + sibling `.tc` panels toggled by the inline handler in
  authoring-rules.md): the framework stacks the `.tc` panels the same way; a `.tc[hidden]`
  panel stays laid out and only `visibility: hidden`, so the fit covers the tallest panel.
- Checklist: `.checklist li` click-to-toggle (+ `.checklist-detail` expand).
- Compare: `.compare-toggle > .compare-btn[data-compare]` + `.compare-content[data-compare]`;
  highlight mode when the container has `data-compare-mode="side-by-side"`.
- Self-contained tabs that must work without the framework's JS may also use the inline onclick
  pattern (see the golden example).

## 5. Canvas Animation (animation-utils.js)

**Required pattern** — every canvas must apply proportional scaling + DPR correction (for FHD/4K support):

```js
(function() {
  const BASE_W = 960, BASE_H = 400;
  const canvas = document.getElementById('my-canvas');
  const ctx = canvas.getContext('2d');
  let step = 0; const MAX_STEP = 3;
  function draw() {
    const dpr = window.devicePixelRatio || 1;
    // 반드시 clientWidth/Height (레이아웃 px) — getBoundingClientRect()는
    // transform 반영 시각 px라 덱 스케일과 이중 적용되어 캔버스가 넘친다.
    const pw = canvas.parentElement.clientWidth;
    const ph = canvas.parentElement.clientHeight;
    const scale = Math.min(pw / BASE_W, ph / BASE_H);
    canvas.width = BASE_W * scale * dpr; canvas.height = BASE_H * scale * dpr;
    canvas.style.width = BASE_W * scale + 'px'; canvas.style.height = BASE_H * scale + 'px';
    ctx.setTransform(1,0,0,1,0,0); ctx.scale(scale * dpr, scale * dpr);
    ctx.clearRect(0, 0, BASE_W, BASE_H);
    refreshThemeColors();
    // ... BASE_W/BASE_H 좌표계로 그리기 ...
    if (step >= 1) drawArrow(ctx, 180, 200, 260, 200, Colors.accent);
  }
  new ResizeObserver(draw).observe(canvas.parentElement);
  const slide = canvas.closest('.slide');
  slide.__canvasStep = (dir) => {
    const n = step + (dir === 'next' ? 1 : -1);
    if (n < 0 || n > MAX_STEP) return false;   // 슬라이드 이동 허용
    step = n; draw(); return true;
  };
  draw();
})();
```

**Drawing helpers** (take BASE-coordinate arguments): `drawBox(ctx,x,y,w,h,label,color)` ·
`drawArrow(ctx,x1,y1,x2,y2,color,dashed,showHead)` · `drawOrthogonalArrow(ctx,points,color)` ·
`drawCircle` · `drawText(ctx,text,x,y,{size,color,weight,align})` ·
`drawGroup(ctx,x,y,w,h,label,color)` (dashed group box) · `drawIcon(ctx,src,x,y,size)` ·
`drawPod` · `drawNode` · `drawCluster` · `drawRoundRect`.

**Colors**: `Colors.accent/.blue/.green/.yellow/.red/.cyan/.pink/...` — read from CSS variables,
so they adapt to the theme automatically. Call `refreshThemeColors()` after a theme switch (the pattern above
already calls it on every draw). `withAlpha(color, a)` · `resolveColor(ref)`.

**Utilities**: `AnimationLoop(drawFn)` · `TimelineAnimation(steps, duration)` ·
`ParticleSystem` · `Ease.linear/inOut/out/in/elastic/bounce` · `lerp` · `clamp`.

**5 presets** — `CanvasPresets[type](ctx, config, step, w, h)`:
`eks-pod-scaling` · `eks-node-scaling` · `traffic-flow` · `rolling-update` · `failover`.
Call directly, passing only a config object.

**Complexity rule**: canvas is for ≤4 boxes with unidirectional arrows only. Use the HTML flow
utility (§6) for 5+ boxes or multi-tier diagrams. Use a static draw.io PNG/SVG `<img>` for full architecture diagrams.

## 6. CSS Component Inventory (theme.css)

| Group | Classes | Notes |
|------|--------|------|
| Cards | `.card-grid` `.card` `.metric-card` `.card-desc` `.card-text` (left-aligned sentence card) `.card-note`/`.card-note-label` (divider + muted label for a card's secondary line) `.metric-value/.metric-label` `.kpi-row/.kpi-card/.kpi-value/.kpi-label/.kpi-delta` `.badge(-blue/-green/-red/-yellow/-up/-down)` | For 4+ items, use cards instead of bullets |
| Callouts | `.callout` `.callout-info/-success/-warning/-danger` `.pain-quote` `.stat-highlight` | |
| Layout | `.columns` `.col-2/.col-3` `.columns-1-2/-2-1/-3` `.grid-2x2/.grid-3x2` `.center-content` | |
| Flow (HTML architecture) | `.flow-h/.flow-v` `.flow-group` `.flow-box` `.flow-arrow` `.flow-col` `.flow-step` `.flow-desc` `.icon-item` + `.bg-blue/-orange/-pink/-green/-purple/-red/-dark/-accent` | The default mechanism for 5+ box diagrams; stage height/width auto-normalize |
| Tabs/compare | `.tab-bar/.tab-btn/.tab-content` `.tab-panels` (panel stack) `.tab-set` (self-contained) `.compare-toggle/.compare-btn/.compare-content/.compare-highlight` | Auto-init per §4 |
| Timeline/steps | `.timeline/.timeline-step/-dot/-label/-desc/-connector` `.steps-container` `.steps--horizontal/--vertical/--circle/--rect/--icon` `.step-item/-marker/-label/-desc` `.agenda-timeline/.agenda-step/-dot/-label/-connector` | |
| Checklist/quiz | `.checklist` `.checklist-detail` `.quiz`+`data-quiz` `.quiz-option`+`data-correct` | §4/§7 |
| Code | `.code-block` `.code-label` + `.keyword/.string/.comment/.number/.function` span | Highlight either directly via spans or with the highlight.js CDN. Inside the fit box the block never scrolls — it takes part in fit (§11). Inline `<code>` in text is mono, same size, unbroken |
| Dashboard | `.dashboard-grid` `.node-grid/.node-cell(-ready/-cordoned/-terminating/-empty)` `.event-log` `.data-table` `.qos-card/.qos-display` `.simulator-layout/.simulator-results` `.slider-container/-group/-row/-value` `.command-card/-header/-output` `.chart-container` `.yaml-output` `.mode-selector/-btn/-content` `.alert-toggle` | Interactive dashboards/simulators |
| Typography helpers | `.eyebrow` `.heading-group` `.text-blue/-green/-orange/-pink/-purple/-red/-icon` (also win on h1-h4) `.nowrap` | |
| Canvas | `.canvas-container` (aspect-ratio 960/400) `.canvas-controls` | |
| Buttons | `.btn/.btn-primary/.btn-sm/.btn-group` `.export-toolbar/.export-btn` | |
| Framework-only (do not use directly) | `.progress-bar` `.slide-counter/-number/-footer/-logo/-ref` `.nav-hint` `.slide-sidebar/.sidebar-thumb*` `.overview-mode` `.presenter-*` `.export-overlay/-progress*` | Generated/managed by JS |

## 7. Quiz (quiz-component.js)

```html
<div class="quiz" data-quiz="q1">
  <p class="quiz-question">질문?</p>
  <div class="quiz-options">
    <button class="quiz-option" data-correct="false" data-explain="왜 오답인지">A) 오답</button>
    <button class="quiz-option" data-correct="true" data-explain="왜 정답인지">B) 정답</button>
  </div>
  <div class="quiz-feedback" aria-live="polite"></div>
</div>
```
Auto-initialized. `quizManager.reset(id)/resetAll()/getScore()`.
- A click writes a text result (✓ 정답입니다! / × 오답입니다…) plus the option's `data-explain`
  (else the quiz's `data-explain`) into `.quiz-feedback`, so the result is never conveyed by colour
  alone (WCAG 1.4.1). A quiz without `.quiz-feedback` gets one appended (with `aria-live="polite"`).
- Prefer per-option `data-explain`: a quiz-level explanation is also shown on a wrong answer and
  would give the answer away.
- Revealing the feedback adds height after the slide was fitted, so the component re-fits the slide
  with `ReactiveFit.fitSlide(slide, { force: true, shrinkOnly: true })`.

## 8. Presenter View & Export

- **P key** → opens a new `PresenterView` window: current + next slide, notes (cue/timing rendered),
  elapsed timer, drag-to-split. Notes are sourced from §1's `presenterNotes`/`<template class="notes">`.
- **export-utils.js** (loaded only from toc.html): `ExportUtils.exportPDF({title})` ·
  `exportPPTX({title})` (html2canvas + PptxGenJS CDN) · `downloadZIP()`.
- High-quality PPTX uses the headless path: `scripts/export_pptx.py <deck-dir>/ -o out.pptx`
  (Playwright pixel capture + includes speaker notes).

## 9. AWS Icons

- Official icons are required (for architecture/service-introduction slides) — no arbitrary artwork.
- Path: `common/aws-icons/services/Arch_{Service}_48.svg`, etc.
- `scripts/remarp_to_slides.py build` copies referenced official icons into `common/aws-icons/`; source validation reports unknown Canvas icon names. (Never copy all 811.)

## 10. Authoring Rules (summary — see design-direction.md for detail)

- Colors: role tokens only — raw hex/rgba/inline style are forbidden (`check_deck.py` RAW_HEX/RAW_RGBA/INLINE_STYLE).
- Spacing: 8px grid tokens only (OFF_SCALE).
- 4+ bullets → card grid; 8+ → split into multiple slides.
- Title: ≤28-character headline (declarative/claim/question/twist); subtitle: noun-form ending, ≤45 characters.
- Every content slide needs `:::notes` in Remarp source (150+ characters recommended). Manual HTML can use `<template class="notes">`.
- Light is the default of a dual theme — dark-only is forbidden. Every color must work in both themes.
- Minimize deck-local `<style>`; when a rule is generalizable, patch it into the skill's
  `assets/theme.css` and bump the framework version (no per-deck reinvention — check_deck.py warns on duplication).

## 11. Fit Contract (ReactiveFit)

`slide-framework.js` ships a PPT-style autofit engine that sizes each slide's `.slide-body`
content with CSS `zoom`. Author at the role tokens (§2) and let the engine do the sizing — do not
hand-shrink type to make a slide fit.

**API** (`window.ReactiveFit`):

```js
window.ReactiveFit = { MIN: 0.82, MAX: 1.35, TARGET: 0.94, fitSlide, fitAll }
ReactiveFit.fitSlide(slideEl, { force, shrinkOnly })  // → applied zoom (number) or null when skipped
ReactiveFit.fitAll({ force, shrinkOnly })             // fitSlide on every .slide-deck .slide (each in try/catch)
```

- `force: true` re-measures even when a cached `data-fit-scale` exists; without it the cached value is returned.
- `shrinkOnly: true` never regrows past the cached scale (used after tab/compare switches so type stays stable).

**Modes** — resolved from the slide's `data-fit`, else the `.slide-deck`'s `data-fit`, else `auto`
(value is trimmed/lower-cased; anything other than `shrink`/`off` means `auto`):

| Mode | Zoom range | Behavior |
|------|-----------|----------|
| `auto` | 0.82–1.35 | Default. Grows sparse slides and shrinks dense ones |
| `shrink` | 0.82–1.0 | Only reduces; never enlarges |
| `off` | — | Layout untouched; an existing `.fit-box` has its inline `zoom` cleared and the fit attributes are removed |

In Remarp, `@fit: auto|shrink|off` on a slide emits `data-fit` on that slide's div; frontmatter
`fit:` is the deck default (`@fit` wins; YAML `fit: off` is accepted). Unknown values are an
`INVALID_FIT` WARNING in `validate`.

**Skip rules** (`fitSlide` returns `null`, nothing is wrapped or zoomed): the element is not a
`.slide`, the deck is in `.overview-mode`, the slide has no `.slide-body` (cover/title/thank-you),
mode is `off`, or the slide contains `canvas`, `iframe`, `.archify`, `.archify-diagram` or `.mermaid`
(pixel-exact or asynchronously rendered content). `MIN` is 0.82 so the 22px `--fs-caption` floor never
renders below the 18px `MIN_FONT` FAIL line.

**`.fit-box` wrapping**: on first fit the engine moves every child node of `.slide-body` into a
runtime `<div class="fit-box">` and applies `zoom` to that box. It picks the largest zoom whose
visual height fits 94% (`TARGET`) of the body height with no horizontal overflow — try the upper
bound, then `MIN`, then a 6-step binary search between them, floored to 3 decimals. Fragments are
forced `.visible` while measuring (transitions disabled via a `fit-measuring` class) so the fully
revealed layout is what fits. Consequences for deck scripts and `:::script`/`:::css` blocks:

- Do not rely on `.slide-body`'s direct children — after init they are children of `.fit-box`.
  Theme rules use `:is(.slide-body, .fit-box) > X` for this reason.
- Percent-based heights inside the box resolve against an auto-height parent; cap images and
  fixed-size widgets in `rem` (which scales with the zoom), not `%`.
- Code blocks take part in fit: inside `.fit-box`, `.code-block` has no inner scroll
  (`overflow: visible`, `max-height: none`) and widens to its longest line
  (`width: max-content; min-width: 100%`), so a long or tall listing makes ReactiveFit shrink
  the slide — and `FIT_OVERFLOW` fires if it still does not fit at `MIN` — instead of being
  clipped or scrolled. Do not cap code with `%` heights or `overflow-y: auto`; trim the
  listing or split the slide. A slide that genuinely needs a scrolling listing opts out with
  `data-fit="off"` (`@fit: off`). Start `<pre>` right after `.code-label` with no whitespace:
  `.code-block` is `white-space: pre`, so indentation between the tags renders as blank lines.
- Tabbed slides are measured with every panel stacked (§4), i.e. at the tallest panel, so the
  tab-click re-fit (`shrinkOnly`) keeps the same zoom.

**Result attributes** on the `.slide`:

- `data-fit-scale="<zoom>"` — the applied zoom; also the cache key for non-forced calls.
- `data-fit-overflow=""` — present only when content still overflows at `MIN` (0.82); the fit
  stays at `MIN` (0.82). Split the slide.

**When it runs**:

- `SlideFramework.init()` → `fitAll()` over all slides (hidden slides are made measurable
  temporarily), then `fitAll({ force: true })` again after `document.fonts.ready`.
- `showSlide()` → `fitSlide(next)` (cached, so cheap after the first pass).
- Tab (`.tab-btn`) and compare (`.compare-btn`) clicks → `fitSlide(slide, { force: true, shrinkOnly: true })`.
- Gates and export: `scripts/measure_deck.py` and `scripts/export_pptx.py` call
  `ReactiveFit.fitSlide(slide, { force: true })` right after showing each slide, so measurements
  and PPTX captures see the fitted layout (export treats a fit failure as best-effort).

**measure_deck.py density rules** (measured once per slide at canvas step 0; de-duplicated across
viewports/themes):

- `UNDERFILL` — WARN when visible `.slide-body` content spans < 55% of the body height (slides without `.slide-header`/`.slide-body` and `.title-slide/.cover-slide/.section-slide/.closing-slide` are exempt).
- `MIN_FONT` — effective text size (`computed font-size × zoom`) below 22px (11pt): WARN, or FAIL when the smallest is below 18px; one finding per slide naming the smallest element.
- `FIT_OVERFLOW` — FAIL when the slide carries `data-fit-overflow` (content does not fit even at the minimum fit scale — split the slide).
- `DECK_OFFSCREEN` — FAIL when the scaled `.slide-deck` box is not fully inside the viewport, checked once per viewport with the sidebar as the deck loads it and with it hidden (all other rules measure relative to the slide, so a deck pushed partly off-screen would pass them). `.slide-deck` therefore uses `margin: 0`: auto margins on a box taller or wider than the viewport resolve to 0 and disable `body`'s centering.
