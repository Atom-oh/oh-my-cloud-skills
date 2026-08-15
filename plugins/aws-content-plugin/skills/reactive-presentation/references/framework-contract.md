# Framework Contract — HTML-First Deck Authoring

This document **replaces the compiler**: instead of Remarp syntax, Claude reads this contract and the golden example at `assets/example-deck/`, then writes slide HTML directly.
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

A fixed 1920×1080 design canvas: `.slide-deck` is scaled down as a whole to fit the viewport via
`transform: scale(min(100vw/1920, 100vh/1080))`. Inside a slide, absolute px coordinates are safe to
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
  logo, ref container, thumbnail sidebar (scales the 1920px content down).
- **Key map** (default): `←→ Space PageUp/Down` move + fragment · `↑↓` slideAction →
  interactive cycling (canvas step/tabs/compare) → fragment · `Home/End` · `P` presenter ·
  `F` fullscreen · `O` overview · `S` sidebar · `Esc`. Remap via `window.__remarpKeys`.
- If a slide contains an `<img>`, footer/logo/page number are auto-hidden.
- `data-transition="fade|slide|zoom"` for per-slide transitions.
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
  (shown via `.active`). Also cyclable with ↑↓ keys.
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
| Cards | `.card-grid` `.card` `.metric-card` `.metric-value/.metric-label` `.kpi-row/.kpi-card/.kpi-value/.kpi-label/.kpi-delta` `.badge(-blue/-green/-red/-yellow/-up/-down)` | For 4+ items, use cards instead of bullets |
| Callouts | `.callout` `.callout-info/-success/-warning/-danger` `.pain-quote` `.stat-highlight` | |
| Layout | `.columns` `.col-2/.col-3` `.columns-1-2/-2-1/-3` `.grid-2x2/.grid-3x2` `.center-content` | |
| Flow (HTML architecture) | `.flow-h/.flow-v` `.flow-group` `.flow-box` `.flow-arrow` `.flow-col` `.flow-step` `.flow-desc` `.icon-item` + `.bg-blue/-orange/-pink/-green/-purple/-red/-dark/-accent` | The default mechanism for 5+ box diagrams; stage height/width auto-normalize |
| Tabs/compare | `.tab-bar/.tab-btn/.tab-content` `.tab-set` (self-contained) `.compare-toggle/.compare-btn/.compare-content/.compare-highlight` | Auto-init per §4 |
| Timeline/steps | `.timeline/.timeline-step/-dot/-label/-desc/-connector` `.steps-container` `.steps--horizontal/--vertical/--circle/--rect/--icon` `.step-item/-marker/-label/-desc` `.agenda-timeline/.agenda-step/-dot/-label/-connector` | |
| Checklist/quiz | `.checklist` `.checklist-detail` `.quiz`+`data-quiz` `.quiz-option`+`data-correct` | §4/§7 |
| Code | `.code-block` `.code-label` + `.keyword/.string/.comment/.number/.function` span | Highlight either directly via spans or with the highlight.js CDN |
| Dashboard | `.dashboard-grid` `.node-grid/.node-cell(-ready/-cordoned/-terminating/-empty)` `.event-log` `.data-table` `.qos-card/.qos-display` `.simulator-layout/.simulator-results` `.slider-container/-group/-row/-value` `.command-card/-header/-output` `.chart-container` `.yaml-output` `.mode-selector/-btn/-content` `.alert-toggle` | Interactive dashboards/simulators |
| Typography helpers | `.eyebrow` `.heading-group` `.text-blue/-green/-orange/-pink/-purple/-red/-icon` | |
| Canvas | `.canvas-container` (aspect-ratio 960/400) `.canvas-controls` | |
| Buttons | `.btn/.btn-primary/.btn-sm/.btn-group` `.export-toolbar/.export-btn` | |
| Framework-only (do not use directly) | `.progress-bar` `.slide-counter/-number/-footer/-logo/-ref` `.nav-hint` `.slide-sidebar/.sidebar-thumb*` `.overview-mode` `.presenter-*` `.export-overlay/-progress*` | Generated/managed by JS |

## 7. Quiz (quiz-component.js)

```html
<div class="quiz" data-quiz="q1">
  <p class="quiz-question">질문?</p>
  <div class="quiz-options">
    <button class="quiz-option" data-correct="false">A) 오답</button>
    <button class="quiz-option" data-correct="true">B) 정답</button>
  </div>
</div>
```
Auto-initialized. `quizManager.reset(id)/resetAll()/getScore()`.

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
- `scripts/deck_assets.py` copies only referenced icons into `common/aws-icons/`
  and reports any unresolved names. (Never copy all 811.)

## 10. Authoring Rules (summary — see design-direction.md for detail)

- Colors: role tokens only — raw hex/rgba/inline style are forbidden (`check_deck.py` RAW_HEX/RAW_RGBA/INLINE_STYLE).
- Spacing: 8px grid tokens only (OFF_SCALE).
- 4+ bullets → card grid; 8+ → split into multiple slides.
- Title: ≤28-character headline (declarative/claim/question/twist); subtitle: noun-form ending (체언 종결), ≤45 characters.
- Every content slide needs a `<template class="notes">` of 150+ characters.
- Light is the default of a dual theme — dark-only is forbidden. Every color must work in both themes.
- Minimize deck-local `<style>`; when a rule is generalizable, patch it into the skill's
  `assets/theme.css` and bump the framework version (no per-deck reinvention — check_deck.py warns on duplication).
