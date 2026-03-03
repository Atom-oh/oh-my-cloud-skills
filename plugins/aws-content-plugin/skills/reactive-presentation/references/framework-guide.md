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
- Keyboard: ←→ (prev/next), Space/PageDown (next), PageUp (prev), Home/End, ↑↓ (cycle tabs/compare on current slide, or step animation if registered), F (fullscreen), N (speaker notes panel toggle), P (presenter view), Esc (exit fullscreen), 1-9 (jump to slide)
- Touch: swipe left/right on mobile
- URL hash: `#3` jumps to slide 3
- Auto-creates: progress bar, slide counter, nav hint (scoped to `.slide-deck`)
- `deck.next()`, `deck.prev()`, `deck.goTo(index)`
- `deck.registerSlideAction(slideIndex, { up, down })` — register custom ↑↓ handlers for a slide (e.g., animation step control). Takes priority over auto-detected tabs/compare.

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
- `TimelineAnimation(steps, duration)` — `steps=[{at: 0.1, action: fn}]`, `.play()`, `.pause()`, `.reset()`, `.setSpeed(s)`, `.update(dt)`. **Step control**: `nextStep()`, `prevStep()`, `goToStep(n)` — for keyboard-driven step-through. Register with `deck.registerSlideAction(slideIndex, { down: () => tl.nextStep(), up: () => tl.prevStep() })`.
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

### export-utils.js
`ExportUtils` object — provides PDF export and ZIP download for presentation TOC pages.

**PDF Export**: Fetches all block HTML files, extracts slides, opens a print-optimized view for browser "Save as PDF".
- Discovers blocks from `.block-card` anchor links on the TOC page
- Extracts `<style>` and `.slide` elements from each block via DOMParser
- Builds a 16:9 landscape print layout with all slides stacked
- Canvas animations show `[Interactive Animation]` placeholder in print
- Uses `<base>` tag for correct relative path resolution

**ZIP Download**: Bundles all presentation files into a ZIP archive for offline viewing.
- Loads JSZip (~100KB) from CDN on demand
- Includes: block HTMLs, TOC index.html, common/ framework files, and all referenced images
- Automatically discovers images by scanning HTML/CSS for `<img src>`, CSS `url()`, and JS `.src` patterns
- Captures AWS icons, pptx-theme backgrounds, logos, and any other referenced images
- Deduplicates URLs via Set before fetching; skips failures silently
- Maintains directory structure: `{slug}/` + `common/`

**API**:
- `ExportUtils.exportPDF({ title })` — open print dialog with all slides
- `ExportUtils.downloadZIP({ slug })` — download ZIP archive
- `ExportUtils.getBlockFiles()` → `string[]` — list of block HTML filenames
- `ExportUtils.getSlug()` → `string` — presentation directory name from URL

**HTML pattern for TOC pages**:
```html
<div class="export-toolbar">
  <button class="export-btn" onclick="ExportUtils.exportPDF({ title: 'Title' })">
    <svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
    Export PDF
  </button>
  <button class="export-btn" onclick="ExportUtils.downloadZIP()">
    <svg viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
    Download ZIP
  </button>
</div>
<script src="../common/export-utils.js"></script>
```

**CSS classes** (defined in theme.css):
- `.export-toolbar` — flex container centered with gap
- `.export-btn` — dark button with icon + label, accent hover
- `.export-overlay` — fixed fullscreen progress overlay
- `.export-progress-text` — status message
- `.export-progress-track` / `.export-progress-bar` — animated progress bar

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
  // Read footer_text and logo path from theme-manifest.json (when PPTX theme extracted)
  const deck = new SlideFramework({
    footer: '© 2025, Amazon Web Services, Inc.',  // from theme-manifest.json → footer_text
    logoSrc: '../common/pptx-theme/images/logo_1.png',  // from theme-manifest.json → logos[0]
    presenterNotes: { 1: 'Note for slide 1\nSecond line', 2: 'Note for slide 2' },
    onSlideChange: (index, slide) => {
      // trigger animations when entering specific slides
    }
  });
  // block-specific logic
</script>
</body>
</html>
```

---

## JSON + Renderer Mode (권장)

> 새 프레젠테이션은 `slides.json` + `slide-renderer.js`로 작성하는 것을 권장합니다.
> AI가 JSON 데이터만 작성하면 렌더러가 일관된 HTML을 생성합니다.

### slide-renderer.js

`common/slide-renderer.js`는 JSON을 읽어 HTML 슬라이드를 동적으로 생성하는 클래스입니다.

**지원 슬라이드 타입 (13종):**

| Type | JSON `type` | 대응 패턴 | 설명 |
|------|-------------|----------|------|
| Session Cover | `cover` | §0a/§0b | PPTX 또는 CSS-only 커버 |
| Title | `title` | §1 | 블록 타이틀 |
| Content | `content` | §2 | 일반 콘텐츠 |
| Compare | `compare` | §3 | A vs B 토글 |
| Tabs | `tabs` | §4 | 탭 콘텐츠 |
| Canvas | `canvas` | §5 | 캔버스 애니메이션 |
| Slider | `slider` | §6 | 파라미터 슬라이더 |
| Checklist | `checklist` | §7/§7b | 체크리스트 (YAML 피드백 옵션) |
| Code | `code` | §8 | 코드 블록 |
| Timeline | `timeline` | §9 | 타임라인 |
| Quiz | `quiz` | §10 | 퀴즈 |
| Cards | `cards` | §11 | 카드/메트릭 |
| Thank You | `thankyou` | §13 | 마지막 슬라이드 |

### slides.json 전체 스키마

```jsonc
{
  "meta": {
    "title": "string — 프레젠테이션 제목 (footer에 사용)",
    "block": "number — 블록 번호",
    "blockTitle": "string — 블록 제목",
    "duration": "string — 예상 소요시간 (예: '30min')",
    "lang": "string — 언어 코드 ('ko' | 'en')"
  },
  "slides": [
    {
      "type": "cover | title | content | tabs | compare | canvas | quiz | checklist | timeline | cards | code | slider | thankyou",
      "title": "string — 슬라이드 제목 (대부분 타입에서 사용)",
      "notes": "string (optional) — 프레젠터 노트. \\n으로 줄바꿈",
      // ... type-specific fields (see slide-patterns.md JSON section)
    }
  ]
}
```

### Canvas 애니메이션 모듈 작성 가이드

Canvas 슬라이드는 JSON에서 `animationModule` 경로를 지정하면, 렌더러가 `import()`로 동적 로드합니다.

**모듈 규격:**

```javascript
// animations/slide-05-flow.js
export function init(canvasId, slideIndex, deck) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const container = canvas.parentElement;
  const ctx = canvas.getContext('2d');
  const BASE_W = 960, BASE_H = 400;

  // Proportional resize (필수 — FHD/4K 대응)
  function resizeCanvas() {
    const cw = container.clientWidth;
    const ch = container.clientHeight;
    if (cw <= 0 || ch <= 0) return;
    const dpr = window.devicePixelRatio || 1;
    const scale = cw / BASE_W;
    const scaledH = Math.min(Math.round(BASE_H * scale), ch);
    canvas.width = Math.round(cw * dpr);
    canvas.height = Math.round(scaledH * dpr);
    canvas.style.width = cw + 'px';
    canvas.style.height = scaledH + 'px';
    canvas.style.maxWidth = 'none';
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.scale(scale * dpr, scale * dpr);
  }

  function draw() {
    ctx.clearRect(0, 0, BASE_W, BASE_H);
    // All coordinates in BASE_W x BASE_H space
    drawBox(ctx, 50, 100, 150, 60, 'Component A', Colors.accent);
  }

  resizeCanvas();
  draw();
  new ResizeObserver(() => { resizeCanvas(); draw(); }).observe(container);

  // Optional: register ↑↓ step control
  // deck.registerSlideAction(slideIndex, {
  //   down: () => timeline.nextStep(),
  //   up: () => timeline.prevStep(),
  // });
}
```

**모듈 규칙:**
- `export function init(canvasId, slideIndex, deck)` — 필수 export
- `canvasId`: JSON에서 지정한 canvas element ID
- `slideIndex`: 슬라이드 인덱스 (registerSlideAction용)
- `deck`: .slide-deck DOM element (SlideFramework 접근용)
- 반드시 proportional scaling 패턴 사용 (ResizeObserver + BASE_W/BASE_H)
- `animation-utils.js`의 `drawBox`, `drawArrow`, `Colors`, `AnimationLoop`, `TimelineAnimation` 활용

### 블록 디렉토리 구조 (JSON 방식)

```
{presentation-slug}/
├── index.html                 # TOC 페이지
├── block-01/
│   ├── index.html             # 최소 보일러플레이트 (아래 참조)
│   ├── slides.json            # AI가 작성하는 콘텐츠 데이터
│   └── animations/            # Canvas 애니메이션 JS 모듈
│       ├── slide-05-flow.js
│       └── slide-08-arch.js
├── block-02/
│   ├── index.html
│   ├── slides.json
│   └── animations/
└── common/                    # 프레임워크 (기존과 동일)
    ├── theme.css
    ├── slide-framework.js
    ├── slide-renderer.js      # ← 새로 추가
    ├── animation-utils.js
    ├── quiz-component.js
    └── presenter-view.js
```

### index.html 보일러플레이트 (JSON 방식)

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Block 1: Fundamentals</title>
  <link rel="stylesheet" href="../common/theme.css">
</head>
<body>
<div class="slide-deck"></div>
<script src="../common/animation-utils.js"></script>
<script src="../common/quiz-component.js"></script>
<script src="../common/slide-framework.js"></script>
<script src="../common/slide-renderer.js"></script>
<script>
  new SlideRenderer({
    footer: '© 2026, Amazon Web Services',
    logoSrc: '../common/pptx-theme/images/logo_1.png'
  }).render('./slides.json');
</script>
</body>
</html>
```

### JSON 방식 vs Raw HTML 비교

| 관점 | JSON + Renderer | Raw HTML (레거시) |
|------|----------------|-------------------|
| AI 작성 일관성 | JSON 구조 → 항상 일관됨 | HTML 수작업 → 미세 차이 가능 |
| 수정 용이성 | JSON 필드 하나 변경 | HTML 전체에서 수정점 탐색 |
| 렌더링 품질 | Renderer가 HTML 보장 | AI 실수 가능 (닫는 태그 누락 등) |
| 빌드 스텝 | 없음 (런타임 렌더링) | 없음 |
| 디버깅 | JSON 검증 → 명확한 에러 | HTML 디버깅 어려움 |
| 커스터마이징 | 13종 표준 타입 + Canvas 모듈 | 무제한 |
| GitHub Pages | 그대로 배포 가능 | 그대로 배포 가능 |
| 기존 호환성 | 기존 HTML 영향 없음 | 기존 그대로 동작 |
