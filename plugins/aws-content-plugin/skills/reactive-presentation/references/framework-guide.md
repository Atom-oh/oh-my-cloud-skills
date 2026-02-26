# Reactive Presentation Framework Reference

## Shared Framework Files (in `common/`)

### theme.css
Dark theme with CSS variables. Key variables:
```
--bg-primary: #0f1117    --bg-secondary: #1a1d2e   --bg-tertiary: #232740
--bg-card: #1e2235       --surface: #282d45         --border: #2d3250
--accent: #6c5ce7        --accent-light: #a29bfe    --accent-glow: rgba(108,92,231,.3)
--green: #00b894         --yellow: #fdcb6e          --red: #e17055
--blue: #74b9ff          --cyan: #00cec9            --orange: #f39c12
--font-main: Pretendard  --font-mono: JetBrains Mono
```

Key CSS classes:
- `.slide-deck` — outer container (16:9 enforced via max-width/max-height, letterboxed with black bars on non-16:9 displays)
- `.slide` — each slide (position: absolute, hidden by default)
- `.slide.active` — visible slide
- `.title-slide` — centered title layout with gradient text
- `.slide-header` / `.slide-body` — content structure within a slide
- `.columns`, `.col-2`, `.col-3` — multi-column layouts
- `.card`, `.card.highlight` — content cards with hover effects
- `.badge-green`, `.badge-yellow`, `.badge-red`, `.badge-blue` — colored badges
- `.btn`, `.btn-primary`, `.btn-sm`, `.btn-group` — buttons
- `.tab-bar` + `.tab-btn` + `.tab-content` — tabbed content
- `.code-block` with `.comment`, `.keyword`, `.string`, `.key`, `.value`, `.number` — syntax highlighting
- `.canvas-container` + `.canvas-controls` — canvas wrapper
- `.progress-bar` — auto-created by SlideFramework
- `.callout-info`, `.callout-warning`, `.callout-danger`, `.callout-success` — callout boxes
- `.timeline` + `.timeline-step` + `.timeline-dot` + `.timeline-connector` — horizontal timelines
- `.checklist` — interactive checklist items (click to toggle)
- `.compare-toggle` + `.compare-btn` + `.compare-content` — comparison toggles
- `.node-grid` + `.node-ready/.node-cordoned/.node-terminating/.node-empty` — node status grid
- `.pain-quote` — customer quote highlight (yellow border)
- `.metric-card` + `.metric-value` + `.metric-label` — large metric display
- `.event-log` with `.event-info/.event-warn/.event-error/.event-ok` — scrolling event log
- `.slider-container` + `input[type="range"]` + `.slider-value` — range sliders

### theme.css — Viewport Scaling & 16:9 Enforcement

The theme uses viewport-relative font sizing for automatic FHD/4K scaling:
```css
html { font-size: clamp(14px, 2.2vh, 52px); }  /* ~24px at 1080p, ~48px at 4K */
body { background: #000; }  /* black letterbox bars */
.slide-deck { max-width: calc(100vh * 16/9); max-height: calc(100vw * 9/16); }
```

All `rem`-based sizing scales automatically. Canvas elements need manual proportional handling (see slide-patterns.md §5).

### slide-framework.js
`SlideFramework` class — instantiate with `new SlideFramework({ onSlideChange: fn })`.

Features:
- Keyboard: ←→ (prev/next), Space/PageDown (next), PageUp (prev), Home/End, F (fullscreen), Esc
- Touch: swipe left/right on mobile
- URL hash: `#3` jumps to slide 3
- Auto-creates: progress bar, slide counter, nav hint (scoped to `.slide-deck`)
- `deck.next()`, `deck.prev()`, `deck.goTo(index)`

Auto-inits on DOMContentLoaded: `initTabs()`, `initChecklists()`, `initCompareToggles()`.

**presenterNotes**: Pass `{ 1: 'note', 2: 'note', ... }` (1-indexed). Use `\n` for line breaks — the presenter view uses `white-space: pre-wrap` so newlines render properly. Keep notes 3-5 lines with bullet points for quick scanning during presentation.

### presenter-view.js
`PresenterView` class — opened by pressing P key. PowerPoint-style layout with:

**Layout**: Top bar (title + timer + counter) → slide previews → horizontal splitter → notes area → nav buttons.

**Draggable splitters**:
- **Horizontal splitter**: Between slide previews and notes. Default ratio: 38% slides / 62% notes.
- **Vertical splitter**: Between current slide and next slide preview. Default ratio: 55% / 45%.
- Both splitters persist position in `localStorage` (`pv-h-ratio`, `pv-v-ratio`).
- Drag overlay prevents text selection during resize.

**Notes area**: Large font (1.3rem) with `white-space: pre-wrap`. Auto-scrollable. Dominates the view for easy reading while presenting.

**Font loading**: Loads Pretendard Variable and JetBrains Mono via CDN. Sets `<meta charset="UTF-8">` and `lang="ko"`.

**Sync**: Uses `BroadcastChannel('slide-sync')` to sync slide navigation between main window and presenter view.

### animation-utils.js
Canvas drawing primitives and animation helpers.

**Colors object**: `Colors.bg`, `.accent`, `.green`, `.yellow`, `.red`, `.blue`, `.cyan`, `.textPri`, `.textSec`, `.textMuted`

**Functions**:
- `setupCanvas(canvasId, width, height)` → `{ canvas, ctx, width, height }` (handles DPR scaling)
- `drawRoundRect(ctx, x, y, w, h, r, fill, stroke)`
- `drawBox(ctx, x, y, w, h, label, color, textColor)` — labeled rounded rectangle with word wrap
- `drawArrow(ctx, x1, y1, x2, y2, color, dashed)` — line with arrowhead
- `drawCircle(ctx, x, y, r, fill, stroke)`
- `drawText(ctx, text, x, y, {color, weight, size, font, align, baseline})`

**Classes**:
- `AnimationLoop(drawFn)` — `.start()`, `.stop()`, `.restart()`, passes elapsed seconds to drawFn
- `TimelineAnimation(steps, duration)` — `steps=[{at: 0.1, action: fn}]`, `.play()`, `.pause()`, `.reset()`, `.setSpeed(s)`, `.update(dt)`
- `ParticleSystem(count, bounds)` — decorative floating particles

**Easing**: `Ease.linear`, `.inOut`, `.out`, `.in`, `.elastic`, `.bounce`
**Helpers**: `lerp(a, b, t)`, `clamp(v, min, max)`

### quiz-component.js
`QuizManager` singleton (auto-instantiated as `quizManager`).

HTML structure:
```html
<div class="quiz" data-quiz="q1">
  <div class="quiz-question">Question?</div>
  <div class="quiz-options">
    <button class="quiz-option" data-correct="false">A) Wrong</button>
    <button class="quiz-option" data-correct="true">B) Right</button>
  </div>
  <div class="quiz-feedback"></div>
</div>
```

Methods: `quizManager.reset(id)`, `.resetAll()`, `.getScore()` → `{total, correct, pct}`

## HTML Template Structure

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Block Title</title>
  <link rel="stylesheet" href="../common/theme.css">
  <style>/* block-specific overrides */</style>
</head>
<body>
<div class="slide-deck">
  <div class="slide title-slide">
    <h1>Title</h1>
    <p class="subtitle">Subtitle</p>
    <p class="meta">Meta info</p>
  </div>

  <div class="slide">
    <div class="slide-header"><h2>Slide Title</h2></div>
    <div class="slide-body">
      <!-- content -->
    </div>
  </div>

  <!-- more slides... -->
</div>

<script src="../common/animation-utils.js"></script>
<script src="../common/slide-framework.js"></script>
<script src="../common/quiz-component.js"></script>
<script>
  const deck = new SlideFramework({
    onSlideChange: (index, slide) => {
      // trigger animations when entering specific slides
    }
  });
  // block-specific logic
</script>
</body>
</html>
```
