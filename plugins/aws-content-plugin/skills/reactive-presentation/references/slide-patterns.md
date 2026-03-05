# Slide Design Patterns

## Common Slide Types

### 0a. Session Cover — With PPTX Theme (Required — first slide of every block HTML file)

Every block HTML file MUST start with a session cover slide matching the AWS PPTX template layout. Uses the extracted background image (`Picture_13.png`), left-aligned text positioning, and AWS branding elements. Speaker info (name, affiliation) is stored in the project's auto-memory (`MEMORY.md`) and reused automatically. If not found, ask the user.

```html
<!-- Session Cover — PPTX layout -->
<div class="slide" style="background:url('../common/pptx-theme/images/Picture_13.png') center/cover no-repeat; padding:0; overflow:hidden;">
  <h1 style="position:absolute; left:5%; top:48%; font-size:2.8rem; color:#fff; font-weight:300; line-height:1.2; width:53%; margin:0;">Session Title</h1>
  <p style="position:absolute; left:5%; top:62%; font-size:1.3rem; color:rgba(255,255,255,0.8); width:53%; margin:0;">Subtitle or Session Focus</p>
  <div style="position:absolute; left:5%; top:76%;">
    <p style="font-size:1.05rem; color:#fff; font-weight:600; margin:0;">Speaker Name</p>
    <p style="font-size:0.9rem; color:rgba(255,255,255,0.65); margin:6px 0 0 0;">Speaker Title</p>
    <p style="font-size:0.9rem; color:rgba(255,255,255,0.65); margin:2px 0 0 0;">Company</p>
  </div>
  <img src="../common/pptx-theme/images/Picture_8.png" alt="" style="position:absolute; right:5%; bottom:10%; width:8%; pointer-events:none;" />
</div>
```

Key elements:
- **PPTX background**: `Picture_13.png` (dark blue/purple gradient) covers entire slide
- **Left-aligned layout**: all text at `left:5%`, matching AWS template positioning
- **Title at ~50% vertical**: large (2.8rem), light weight (300), white text
- **Subtitle at ~62%**: smaller (1.3rem), slightly transparent white
- **Speaker info at ~76-83%**: name (bold white) + title + company (subdued white)
- **AWS smile badge**: `Picture_8.png` at bottom-right (8% width)
- **AWS logo**: handled by SlideFramework's `logoSrc` option — do NOT add a manual `logo_1.png` to the cover slide (causes duplicate overlap)
- Uses `padding:0` to allow background to fill edge-to-edge
- Do NOT use `.title-slide` class (it adds centering that conflicts with left-aligned layout)
- This is separate from block title slides (§1) — Session Cover appears as the **first slide of EVERY block HTML file**, block titles appear per-block

**Remarp `@badge` directive**: To include the AWS smile badge in a PPTX cover, add `@badge` to the slide directives:
```markdown
---
@type: cover
@background: ../common/pptx-theme/images/Picture_13.png
@badge: ../common/pptx-theme/images/Picture_8.png
---
```
The converter reads `@badge` and renders `<img>` at `position:absolute; right:5%; bottom:10%; width:8%`.

### 0b. Session Cover — CSS-Only Fallback (No PPTX)

When no PPTX template is provided, use this CSS-only cover with a dark gradient background. Speaker info is optional — omit the speaker `<div>` if the user chose "skip".

```html
<!-- Session Cover — CSS-only fallback -->
<div class="slide" style="background:linear-gradient(135deg, #1a1f35 0%, #0d1117 50%, #161b2e 100%); padding:0; overflow:hidden; position:relative;">
  <div style="position:absolute; top:-20%; right:-10%; width:60%; height:80%; background:radial-gradient(ellipse, rgba(108,92,231,0.15) 0%, transparent 70%); pointer-events:none;"></div>
  <div style="position:absolute; left:5%; top:42%; width:80px; height:3px; background:linear-gradient(90deg, #6c5ce7, #a29bfe); border-radius:2px;"></div>
  <h1 style="position:absolute; left:5%; top:45%; font-size:2.8rem; color:#fff; font-weight:300; line-height:1.2; width:60%; margin:0;">Session Title</h1>
  <p style="position:absolute; left:5%; top:60%; font-size:1.3rem; color:rgba(255,255,255,0.7); width:60%; margin:0;">Subtitle</p>
  <div style="position:absolute; left:5%; top:75%;">
    <p style="font-size:1.05rem; color:#fff; font-weight:600; margin:0;">Speaker Name</p>
    <p style="font-size:0.9rem; color:rgba(255,255,255,0.6); margin:6px 0 0 0;">Speaker Title</p>
    <p style="font-size:0.9rem; color:rgba(255,255,255,0.6); margin:2px 0 0 0;">Company</p>
  </div>
</div>
```

Key elements:
- **CSS gradient background**: dark gradient (`#1a1f35` → `#0d1117` → `#161b2e`) — no PPTX image dependency
- **Decorative glow**: subtle radial gradient (`rgba(108,92,231,0.15)`) for visual depth
- **Accent line**: purple gradient line (`#6c5ce7` → `#a29bfe`) above the title
- **Left-aligned layout**: matches §0a positioning for visual consistency
- **Speaker info at ~75%**: same structure as §0a (omit entire `<div>` if user chose "skip")
- Uses `padding:0` and `position:relative` for edge-to-edge layout
- Do NOT use `.title-slide` class (same rule as §0a)

#### Session Cover Selection Matrix

| PPTX | Speaker | Pattern | Notes |
|------|---------|---------|-------|
| Yes | Yes | §0a full | PPTX background + speaker + AWS badge |
| Yes | Skip | §0a without speaker div | PPTX background + AWS badge |
| Skip | Yes | §0b full | CSS gradient + accent line + speaker |
| Skip | Skip | §0b without speaker div | CSS gradient + accent line only |

### 1. Title Slide (per-block)
```html
<div class="slide title-slide">
  <h1>Presentation Title</h1>
  <p class="subtitle">Topic Name</p>
  <p class="meta">Date / Author / Event</p>
</div>
```

### 2. Pain Point / Customer Quote Slide
```html
<div class="slide">
  <div class="slide-header"><h2>Pain Point Title</h2></div>
  <div class="slide-body">
    <div class="pain-quote">"Customer quote about the problem"</div>
    <div class="pain-quote">"Another quote"</div>
    <ul>
      <li>Challenge 1</li>
      <li>Challenge 2</li>
    </ul>
  </div>
</div>
```

### 3. Comparison Toggle Slide
```html
<div class="slide">
  <div class="slide-header"><h2>A vs B vs C</h2></div>
  <div class="slide-body">
    <div class="compare-toggle">
      <button class="compare-btn active" data-compare="a">Option A</button>
      <button class="compare-btn" data-compare="b">Option B</button>
      <button class="compare-btn" data-compare="c">Option C</button>
    </div>
    <div class="compare-content active" data-compare="a">
      <!-- Option A details with table or cards -->
    </div>
    <div class="compare-content" data-compare="b">
      <!-- Option B details -->
    </div>
    <div class="compare-content" data-compare="c">
      <!-- Option C details -->
    </div>
  </div>
</div>
```

### 4. Tab-based Content Slide
```html
<div class="slide">
  <div class="slide-header"><h2>Topic Variants</h2></div>
  <div class="slide-body">
    <div class="tab-bar">
      <button class="tab-btn active" data-tab="t1">Tab 1</button>
      <button class="tab-btn" data-tab="t2">Tab 2</button>
    </div>
    <div class="tab-content active" data-tab="t1">
      <div class="code-block"><span class="comment"># Config</span>
<span class="key">key</span>: <span class="value">value</span></div>
    </div>
    <div class="tab-content" data-tab="t2">
      <!-- Tab 2 content -->
    </div>
  </div>
</div>
```

### 5. Canvas Animation Slide
```html
<div class="slide">
  <div class="slide-header"><h2>Animation Title</h2></div>
  <div class="slide-body">
    <div class="canvas-container" style="flex:1">
      <canvas id="my-canvas"></canvas>
    </div>
    <div class="btn-group" style="justify-content:center; margin-top:12px">
      <button class="btn btn-primary" onclick="startAnimation()">Play</button>
      <button class="btn" onclick="resetAnimation()">Reset</button>
    </div>
  </div>
</div>
```
JavaScript pattern (**proportional scaling — required for FHD/4K**):

All canvas animations MUST use proportional scaling with `ResizeObserver` so they fill the container at any resolution. Never use `setupCanvas()` alone — it sets `max-width` in pixels which breaks on larger screens.

```javascript
(function() {
  const canvas = document.getElementById('my-canvas');
  if (!canvas) return;
  const container = canvas.parentElement;
  const BASE_W = 960, BASE_H = 400; // design dimensions

  // Proportional resize: canvas fills container, drawing stays in BASE coords
  function resizeCanvas() {
    const cw = container.clientWidth;
    const ch = container.clientHeight;
    if (cw <= 0 || ch <= 0) {
      setupCanvas('my-canvas', BASE_W, BASE_H); // fallback when hidden
      return;
    }
    const dpr = window.devicePixelRatio || 1;
    const scale = cw / BASE_W;
    const scaledH = Math.min(Math.round(BASE_H * scale), ch);
    canvas.width = Math.round(cw * dpr);
    canvas.height = Math.round(scaledH * dpr);
    canvas.style.width = cw + 'px';
    canvas.style.height = scaledH + 'px';
    canvas.style.maxWidth = 'none';
    const c = canvas.getContext('2d');
    c.setTransform(1, 0, 0, 1, 0, 0);
    c.scale(scale * dpr, scale * dpr);
  }
  resizeCanvas();

  const ctx = canvas.getContext('2d');
  const width = BASE_W, height = BASE_H;

  // All coordinates use BASE_W x BASE_H — ctx.scale handles the rest
  function draw() {
    ctx.clearRect(0, 0, width, height);
    drawBox(ctx, 50, 100, 150, 60, 'Component A', Colors.accent);
    // ... more drawing in BASE coordinate space
  }

  draw();
  new ResizeObserver(() => { resizeCanvas(); draw(); }).observe(container);

  // Register ↑↓ for manual step control
  deck.registerSlideAction(SLIDE_INDEX, {
    down: () => timeline.nextStep(),
    up: () => timeline.prevStep(),
  });
})();
```

Key rules:
- `BASE_W`/`BASE_H` = design dimensions (typically 960×350~400)
- `scale = containerWidth / BASE_W` — proportional scale factor
- `ctx.scale(scale * dpr, scale * dpr)` — all drawing auto-scales
- All drawing coordinates stay in BASE space — never use pixel offsets for actual screen size
- `ResizeObserver` triggers resize + redraw on container size changes
- `canvas.style.maxWidth = 'none'` — removes the pixel cap from `setupCanvas()`

### 6. Interactive Slider Slide
```html
<div class="slide">
  <div class="slide-header"><h2>Parameter Explorer</h2></div>
  <div class="slide-body">
    <div class="slider-container">
      <label>Parameter:</label>
      <input type="range" min="0" max="100" value="50" oninput="updateParam(this.value)">
      <span class="slider-value" id="param-val">50</span>
    </div>
    <div id="param-output"><!-- dynamic output --></div>
  </div>
</div>
```

### 7. Interactive Checklist Slide
```html
<div class="slide">
  <div class="slide-header"><h2>Checklist</h2></div>
  <div class="slide-body">
    <ul class="checklist">
      <li><span class="check"></span> Item 1</li>
      <li><span class="check"></span> Item 2</li>
    </ul>
  </div>
</div>
```

### 7b. Checklist with YAML Feedback
When a checklist item is checked, a YAML code snippet slides down below the item text showing the relevant config. Uses CSS-only animation — no extra JS needed (the framework already toggles `.checked` on `<li>` click).

**Required CSS** (add to `<style>` block in the HTML file):
```css
.check-yaml {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.3s ease;
  margin-top: 0;
}
.checklist li.checked .check-yaml {
  max-height: 200px;
  margin-top: 8px;
}
.check-yaml .code-block {
  font-size: .72rem;
  margin: 0;
  padding: 8px 10px;
}
```

**HTML pattern:**
```html
<ul class="checklist">
  <li>
    <span class="check"></span>
    <div>
      <strong>Bottlerocket AMI 사용</strong>
      <div class="check-yaml">
        <div class="code-block">
<span class="comment"># NodeClass</span>
<span class="key">spec</span>:
  <span class="key">amiSelectorTerms</span>:
    - <span class="key">alias</span>: <span class="string">bottlerocket@latest</span></div>
      </div>
    </div>
  </li>
  <li>
    <span class="check"></span>
    <div>
      <strong>다양한 인스턴스 타입 허용</strong>
      <div class="check-yaml">
        <div class="code-block">
<span class="comment"># NodePool</span>
<span class="key">spec</span>:
  <span class="key">template</span>:
    <span class="key">spec</span>:
      <span class="key">requirements</span>:
        - <span class="key">key</span>: <span class="string">karpenter.k8s.aws/instance-family</span>
          <span class="key">operator</span>: <span class="string">In</span>
          <span class="key">values</span>: [<span class="string">m7i</span>, <span class="string">m7g</span>, <span class="string">c7i</span>]</div>
      </div>
    </div>
  </li>
</ul>
```

Key points:
- Each `<li>` wraps the text and `.check-yaml` inside a `<div>` (keeps layout clean)
- `.check-yaml` uses `max-height: 0` → `max-height: 200px` transition (adjust max-height if YAML is longer)
- The `.code-block` inside uses the same syntax highlighting spans as regular code blocks
- No JavaScript needed — the existing `initChecklists()` in `slide-framework.js` handles the `.checked` toggle

### 8. Code with Syntax Highlighting
```html
<div class="code-block"><span class="comment"># Comment</span>
<span class="key">apiVersion</span>: <span class="string">karpenter.sh/v1</span>
<span class="key">kind</span>: <span class="string">NodePool</span>
<span class="key">spec</span>:
  <span class="key">template</span>:
    <span class="key">requirements</span>:
      - <span class="key">key</span>: <span class="string">instance-category</span>
        <span class="key">values</span>: [<span class="value">"m"</span>, <span class="value">"c"</span>]
</div>
```

### 9. Timeline / Flow Slide
```html
<div class="timeline">
  <div class="timeline-step done">
    <div class="timeline-dot">1</div>
    <div class="timeline-label">Step 1</div>
  </div>
  <div class="timeline-connector done"></div>
  <div class="timeline-step active">
    <div class="timeline-dot">2</div>
    <div class="timeline-label">Step 2</div>
  </div>
  <div class="timeline-connector"></div>
  <div class="timeline-step">
    <div class="timeline-dot">3</div>
    <div class="timeline-label">Step 3</div>
  </div>
</div>
```

### 10. Quiz Summary Slide
```html
<div class="slide">
  <div class="slide-header"><h2>Summary & Quiz</h2></div>
  <div class="slide-body" style="overflow-y:auto">
    <div class="col-2" style="margin-bottom:16px">
      <div class="card"><div class="card-title">Key Point 1</div><p>Detail</p></div>
      <div class="card"><div class="card-title">Key Point 2</div><p>Detail</p></div>
    </div>
    <div class="quiz" data-quiz="q1">
      <div class="quiz-question">1. Question text?</div>
      <div class="quiz-options">
        <button class="quiz-option" data-correct="false">A) Wrong</button>
        <button class="quiz-option" data-correct="true">B) Correct</button>
        <button class="quiz-option" data-correct="false">C) Wrong</button>
        <button class="quiz-option" data-correct="false">D) Wrong</button>
      </div>
      <div class="quiz-feedback"></div>
    </div>
  </div>
</div>
```

### 11. Metric Cards / Dashboard Slide
```html
<div class="col-3">
  <div class="card metric-card">
    <div class="metric-value" id="m1">0</div>
    <div class="metric-label">Label</div>
  </div>
  <!-- more metric cards -->
</div>
```

### 12. Event Log Panel
```html
<div class="event-log" id="log">
  <div><span class="timestamp">[10:30:01]</span> <span class="event-info">INFO</span> Event message</div>
  <div><span class="timestamp">[10:30:02]</span> <span class="event-error">ERROR</span> Error message</div>
</div>
```

## Canvas Animation Patterns

### 화살표 선택: drawArrow vs drawElbowArrow

Canvas 화살표는 연결 거리와 방향에 따라 함수를 선택합니다:

```javascript
// ✅ 순수 수평 (dy=0) → drawArrow
drawArrow(ctx, 200, 215, 260, 215, Colors.accent);

// ✅ 순수 수직 (dx=0) → drawArrow
drawArrow(ctx, 530, 195, 530, 240, Colors.blue, true);

// ✅ 근거리 연결 (dx < 80 AND dy < 80) → drawArrow
drawArrow(ctx, 200, 160, 240, 152, Colors.accent);

// ✅ 그룹 간 대각선 (dx ≥ 80) → drawElbowArrow
drawElbowArrow(ctx, 400, 152, 450, 100, Colors.cyan);
drawElbowArrow(ctx, 160, 120, 260, 170, Colors.blue, true);

// ❌ 금지: drawArrow + drawText('→') 동시 사용 (arrowhead 중복)
// drawArrow(ctx, 280, 190, 330, 190, Colors.accent);
// drawText(ctx, '→', 305, 194, ...);  // ← 삭제해야 함
```

### Animated Component Flow
Draw boxes → animate arrows appearing → highlight active component:
```javascript
function drawFlow(ctx, progress) {
  // Static boxes
  drawBox(ctx, 50, 100, 150, 60, 'Component A', Colors.accent);
  drawBox(ctx, 300, 100, 150, 60, 'Component B', Colors.green);
  // Animated arrow (appears when progress > 0.3)
  if (progress > 0.3) {
    drawArrow(ctx, 200, 130, 300, 130, Colors.accent);
  }
}
```

### Timeline Simulation
Use TimelineAnimation for step-by-step processes:
```javascript
const timeline = new TimelineAnimation([
  { at: 0.0, action: () => setStep(0) },
  { at: 0.15, action: () => setStep(1) },
  { at: 0.35, action: () => setStep(2) },
  { at: 0.6, action: () => setStep(3) },
  { at: 0.85, action: () => setStep(4) },
], 10); // 10 second duration

let lastTime = 0;
const anim = new AnimationLoop((elapsed) => {
  const dt = elapsed - lastTime;
  lastTime = elapsed;
  timeline.update(dt);
  // redraw based on current step
});
```

### Node Grid Dashboard
Track node state in array, redraw on changes:
```javascript
const nodes = Array.from({length: 12}, (_, i) => ({
  id: i, status: i < 8 ? 'ready' : 'empty', cpu: Math.random() * 60
}));

function drawNodes(ctx) {
  const cols = 4, cellSize = 64, gap = 8;
  nodes.forEach((n, i) => {
    const x = (i % cols) * (cellSize + gap);
    const y = Math.floor(i / cols) * (cellSize + gap);
    const color = { ready: Colors.green, cordoned: Colors.yellow,
                    terminating: Colors.red, empty: Colors.border }[n.status];
    drawRoundRect(ctx, x, y, cellSize, cellSize, 8, color + '33', color);
  });
}
```

### 13. Thank You / Closing Slide (Required)

Every block HTML file **must** end with a Thank You slide as the last slide. This signals the end of the block clearly and provides navigation to the TOC page and the next block.

There are two variants depending on whether the block is a middle block or the final block.

#### 13a. Middle Block (has next block)

The "다음" button is `btn-primary` (highlighted CTA), and the TOC button is `btn` (secondary).

```html
<!-- Slide N: Thank You -->
<div class="slide">
  <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; gap:24px; text-align:center;">
    <h1 style="font-size:3rem; background:linear-gradient(135deg, var(--accent-light), var(--cyan)); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;">Thank You</h1>
    <p style="color:var(--text-secondary); font-size:1.1rem;">Block N — 블록 제목 완료</p>
    <div style="display:flex; gap:16px; margin-top:20px;">
      <a href="index.html" class="btn btn-sm" style="text-decoration:none;">← 목차로 돌아가기</a>
      <a href="NN-next-block.html" class="btn btn-primary btn-sm" style="text-decoration:none;">다음: Block N+1 →</a>
    </div>
  </div>
</div>
```

#### 13b. Final Block (last block of the presentation)

No next block link. The TOC button becomes `btn-primary` (promoted to primary CTA). Add a congratulations line.

```html
<!-- Slide N: Thank You -->
<div class="slide">
  <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; gap:24px; text-align:center;">
    <h1 style="font-size:3rem; background:linear-gradient(135deg, var(--accent-light), var(--cyan)); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;">Thank You</h1>
    <p style="color:var(--text-secondary); font-size:1.1rem;">Block N — 블록 제목 완료</p>
    <p style="color:var(--text-muted); font-size:1rem; margin-top:8px;">수고하셨습니다!</p>
    <div style="display:flex; gap:16px; margin-top:20px;">
      <a href="index.html" class="btn btn-primary btn-sm" style="text-decoration:none;">← 목차로 돌아가기</a>
    </div>
  </div>
</div>
```

Key elements:
- Gradient text "Thank You" heading (accent-light → cyan)
- Block completion description (e.g., "Block 2 — 노드 라이프사이클 & 모니터링 완료")
- **← 목차로 돌아가기** button: always present, links to `index.html` (TOC page)
- **다음: Block N+1 →** button: present for middle blocks only, links to the next block HTML file
- Button style rule: the primary action (`btn-primary`) is "다음" for middle blocks, "목차로 돌아가기" for the final block
- Final block adds a congratulations message (e.g., "수고하셨습니다!")

### 14. Speaker Notes (presenterNotes)

Add presenter speaking notes via the `presenterNotes` option in `SlideFramework`. Notes appear in the presenter view (P key).

**IMPORTANT: Use `\n` line breaks** for readability. The presenter view uses `white-space: pre-wrap`, so `\n` renders as line breaks.

```javascript
const deck = new SlideFramework({
  logoSrc: '../common/pptx-theme/images/logo_1.png',
  presenterNotes: {
    1: '환영합니다. 이 블록에서는 Auto Mode 아키텍처를 다룹니다.\n약 35분 소요 예정이며, 중간에 데모가 포함됩니다.\n\n핵심 메시지: 관리형 Karpenter로 운영 부담 감소.',
    2: 'Auto Mode의 핵심 가치를 설명하세요.\n- 관리형 Karpenter + 관리형 애드온의 결합\n- 기존 MNG 대비 운영 부담 크게 감소\n\n청중에게 질문: 현재 어떤 노드 관리 방식을 사용하시나요?',
    3: 'Play 버튼을 클릭하여 애니메이션을 시연하세요.\n각 컴포넌트가 나타날 때마다 역할을 설명합니다.\n\n시연 후 질문을 받으세요.'
  },
  onSlideChange: (index, slide) => { /* ... */ }
});
```

Notes formatting guide:
- Use `\n` for line breaks within a note (NOT `<br>` — notes use `textContent`)
- Use `\n\n` for paragraph separation
- Keep notes 3-5 lines per slide for readability
- Include: what to say, what to demo, timing hints, audience interaction cues
- Use `-` or `•` for bullet points within notes
- Korean with English technical terms

## Slide Count Guidelines

| Duration | Slides | Pace |
|----------|--------|------|
| 20 min | 8-10 | ~2 min/slide |
| 25 min | 10-12 | ~2.2 min/slide |
| 35 min | 14-16 | ~2.3 min/slide |
| 60 min | 24-28 | ~2.3 min/slide |

Interactive/animated slides take longer — budget 3-4 min each.

---

## JSON Authoring Mode (권장)

> **권장**: 새 프레젠테이션은 `slides.json` + `slide-renderer.js` 방식으로 작성합니다.
> 기존 Raw HTML 방식은 레거시로 유지되며, 특수한 커스터마이징이 필요한 경우에만 사용합니다.

### slides.json 구조

```jsonc
{
  "meta": {
    "title": "프레젠테이션 제목",
    "block": 1,
    "blockTitle": "Block Title",
    "duration": "30min",
    "lang": "ko"
  },
  "slides": [ /* slide objects */ ]
}
```

### 슬라이드 타입별 JSON 스키마

#### §0 Cover (Session Cover)

```jsonc
// §0a — PPTX 배경 사용
{
  "type": "cover",
  "title": "EKS Auto Mode Deep Dive",
  "subtitle": "Fundamentals (30min)",
  "pptxBackground": "../common/pptx-theme/images/Picture_13.png",
  "badgeSrc": "../common/pptx-theme/images/Picture_8.png",
  "speaker": { "name": "홍길동", "title": "SA", "company": "AWS" },
  "notes": "환영 인사. 이 세션에서 다룰 내용 소개."
}

// §0b — CSS-only (PPTX 없음, pptxBackground 생략)
{
  "type": "cover",
  "title": "EKS Auto Mode Deep Dive",
  "subtitle": "Fundamentals (30min)",
  "speaker": { "name": "홍길동", "title": "SA", "company": "AWS" }
}
```

#### §1 Title

```json
{
  "type": "title",
  "title": "Fundamentals",
  "subtitle": "핵심 개념과 아키텍처",
  "meta": "2026.03 / Speaker / Event"
}
```

#### §2 Content

```json
{
  "type": "content",
  "title": "EKS Auto Mode란?",
  "body": "<p>EKS Auto Mode는...</p><ul><li>자동 노드 관리</li><li>관리형 애드온</li></ul>",
  "notes": "핵심 가치를 설명합니다."
}
```

#### §3 Compare Toggle

```json
{
  "type": "compare",
  "title": "Managed vs Auto Mode",
  "options": [
    { "id": "managed", "label": "Managed Node Groups", "html": "<ul><li>수동 AMI 관리</li></ul>" },
    { "id": "auto", "label": "Auto Mode", "html": "<ul><li>자동 AMI 업데이트</li></ul>" }
  ]
}
```

#### §4 Tabs

```json
{
  "type": "tabs",
  "title": "Configuration Options",
  "tabs": [
    { "label": "Basic", "html": "<div class='code-block'>...</div>" },
    { "label": "Advanced", "html": "<div class='code-block'>...</div>" }
  ]
}
```

#### §5 Canvas Animation

```json
{
  "type": "canvas",
  "title": "Traffic Flow Animation",
  "canvasId": "flow-canvas",
  "animationModule": "./animations/slide-05-flow.js",
  "controls": ["play", "reset", "step"],
  "notes": "Play 버튼을 클릭하여 데모."
}
```

Canvas 애니메이션은 별도 JS 모듈로 작성합니다. 모듈 규격:
```javascript
// animations/slide-05-flow.js
export function init(canvasId, slideIndex, deck) {
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext('2d');
  // proportional scaling 패턴 사용 (§5 참조)
}
```

#### §6 Slider

```json
{
  "type": "slider",
  "title": "Parameter Explorer",
  "label": "Replicas",
  "min": 1,
  "max": 20,
  "value": 3,
  "sliderId": "replica-slider",
  "outputHtml": "<p>초기 출력</p>"
}
```

#### §7 Checklist

```jsonc
{
  "type": "checklist",
  "title": "Migration Checklist",
  "items": [
    "VPC 설정 확인",              // 단순 문자열
    "IAM 역할 생성",
    {                              // §7b — YAML 피드백 포함
      "label": "Bottlerocket AMI 사용",
      "yaml": "<span class='comment'># NodeClass</span>\n<span class='key'>spec</span>:\n  <span class='key'>amiSelectorTerms</span>:\n    - <span class='key'>alias</span>: <span class='string'>bottlerocket@latest</span>"
    }
  ]
}
```

#### §8 Code

```json
{
  "type": "code",
  "title": "NodePool Configuration",
  "description": "Karpenter NodePool 기본 설정:",
  "code": "<span class='key'>apiVersion</span>: <span class='string'>karpenter.sh/v1</span>\n<span class='key'>kind</span>: <span class='string'>NodePool</span>"
}
```

#### §9 Timeline

```json
{
  "type": "timeline",
  "title": "Migration Steps",
  "activeStep": 1,
  "steps": [
    { "label": "Plan", "desc": "현재 클러스터 분석" },
    { "label": "Prepare", "desc": "IAM/네트워크 준비" },
    { "label": "Migrate", "desc": "워크로드 이전" }
  ]
}
```

#### §10 Quiz

```json
{
  "type": "quiz",
  "title": "Knowledge Check",
  "questions": [
    {
      "question": "EKS Auto Mode의 핵심 이점은?",
      "options": [
        { "text": "A) 자동 노드 관리", "correct": true },
        { "text": "B) 무료 사용", "correct": false },
        { "text": "C) GPU 전용", "correct": false }
      ]
    }
  ]
}
```

#### §11 Cards

```json
{
  "type": "cards",
  "title": "Key Metrics",
  "columns": 3,
  "cards": [
    { "metric": "99.9%", "label": "Uptime" },
    { "metric": "< 2s", "label": "Scaling Time" },
    { "title": "Feature", "text": "Description text" }
  ]
}
```

#### §13 Thank You

```jsonc
// Middle block (다음 블록 있음)
{
  "type": "thankyou",
  "message": "Block 1 — Fundamentals 완료",
  "tocHref": "index.html",
  "nextBlock": { "href": "../block-02/index.html", "label": "다음: Block 2" }
}

// Final block (마지막)
{
  "type": "thankyou",
  "message": "Block 3 — Advanced 완료"
}
```

### JSON vs Raw HTML 선택 가이드

| 상황 | 방식 | 이유 |
|------|------|------|
| 새 프레젠테이션 | JSON (권장) | 일관성, 수정 용이성 |
| 표준 슬라이드 타입 (13종) | JSON | 렌더러가 HTML 보장 |
| Canvas 애니메이션 | JSON + 별도 JS 모듈 | 애니메이션만 커스텀 |
| 기존 프레젠테이션 수정 | Raw HTML (기존 유지) | 마이그레이션 선택사항 |
| 매우 특수한 레이아웃 | Raw HTML | JSON 스키마에 없는 경우 |
