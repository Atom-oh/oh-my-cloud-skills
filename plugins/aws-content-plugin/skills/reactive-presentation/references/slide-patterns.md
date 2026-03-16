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

### 4b. Architecture Diagram Slide (Static Image)

전체 아키텍처 개요처럼 정적 구조를 보여줄 때 사용. draw.io로 제작한 PNG/SVG를 삽입.

```html
<div class="slide">
  <div class="slide-header"><h2>AWS AIOps Service Map</h2></div>
  <div class="slide-body" style="display:flex; align-items:center; justify-content:center;">
    <img src="diagrams/aiops-service-map.png" class="slide-img" style="max-width:90%; max-height:85%;" />
  </div>
</div>
```

Canvas와의 선택 기준:
- step animation이 필요 → Canvas (`@type: canvas`)
- 정적 아키텍처 한눈에 → Diagram Image (`@type: content` + `@img:`)

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

### 15. Dashboard Slide

KPI cards at top with a chart grid below. Ideal for executive summaries, operational dashboards, and metric overviews.

```html
<div class="slide">
  <div class="slide-header"><h2>Operations Dashboard</h2></div>
  <div class="slide-body">
    <!-- KPI Row -->
    <div class="kpi-row" style="display:flex; gap:16px; margin-bottom:20px;">
      <div class="kpi-card" style="flex:1; background:var(--bg-card); border:1px solid var(--border); border-radius:8px; padding:16px; text-align:center;">
        <div class="kpi-value" style="font-size:2rem; font-weight:700; color:var(--accent);">99.9%</div>
        <div class="kpi-label" style="font-size:0.85rem; color:var(--text-muted);">Availability</div>
        <div class="kpi-delta" style="font-size:0.75rem; color:var(--green);">+0.2%</div>
      </div>
      <div class="kpi-card" style="flex:1; background:var(--bg-card); border:1px solid var(--border); border-radius:8px; padding:16px; text-align:center;">
        <div class="kpi-value" style="font-size:2rem; font-weight:700; color:var(--accent);">1.2s</div>
        <div class="kpi-label" style="font-size:0.85rem; color:var(--text-muted);">Avg Latency</div>
        <div class="kpi-delta" style="font-size:0.75rem; color:var(--green);">-15%</div>
      </div>
      <div class="kpi-card" style="flex:1; background:var(--bg-card); border:1px solid var(--border); border-radius:8px; padding:16px; text-align:center;">
        <div class="kpi-value" style="font-size:2rem; font-weight:700; color:var(--accent);">847</div>
        <div class="kpi-label" style="font-size:0.85rem; color:var(--text-muted);">Active Pods</div>
        <div class="kpi-delta" style="font-size:0.75rem; color:var(--red);">+12%</div>
      </div>
    </div>
    <!-- Chart Grid -->
    <div class="dashboard-grid" style="display:grid; grid-template-columns:1fr 1fr; gap:16px; flex:1;">
      <div class="chart-container" style="background:var(--bg-card); border:1px solid var(--border); border-radius:8px; padding:16px;">
        <canvas id="bar-chart"></canvas>
      </div>
      <div class="chart-container" style="background:var(--bg-card); border:1px solid var(--border); border-radius:8px; padding:16px;">
        <canvas id="doughnut-chart"></canvas>
      </div>
    </div>
  </div>
</div>

<script>
(function() {
  Chart.defaults.animation = false;

  // Bar Chart
  const barCtx = document.getElementById('bar-chart');
  if (barCtx) {
    new Chart(barCtx, {
      type: 'bar',
      data: {
        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
        datasets: [{
          label: 'Requests (K)',
          data: [12, 19, 15, 25, 22],
          backgroundColor: 'rgba(108, 92, 231, 0.7)',
          borderColor: 'rgba(108, 92, 231, 1)',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#94a3b8' } } },
        scales: {
          x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148, 163, 184, 0.1)' } },
          y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148, 163, 184, 0.1)' } }
        }
      }
    });
  }

  // Doughnut Chart
  const doughnutCtx = document.getElementById('doughnut-chart');
  if (doughnutCtx) {
    new Chart(doughnutCtx, {
      type: 'doughnut',
      data: {
        labels: ['Compute', 'Storage', 'Network', 'Other'],
        datasets: [{
          data: [45, 25, 20, 10],
          backgroundColor: ['#6c5ce7', '#00cec9', '#fdcb6e', '#636e72']
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'right', labels: { color: '#94a3b8' } } }
      }
    });
  }
})();
</script>
```

**Remarp equivalent:**

```markdown
---
@type: content
---
## Operations Dashboard

:::html
<div class="kpi-row" style="display:flex; gap:16px; margin-bottom:20px;">
  <div class="kpi-card" style="flex:1; background:var(--bg-card); border:1px solid var(--border); border-radius:8px; padding:16px; text-align:center;">
    <div class="kpi-value" style="font-size:2rem; font-weight:700; color:var(--accent);">99.9%</div>
    <div class="kpi-label" style="font-size:0.85rem; color:var(--text-muted);">Availability</div>
    <div class="kpi-delta" style="font-size:0.75rem; color:var(--green);">+0.2%</div>
  </div>
  <!-- Additional KPI cards... -->
</div>
<div class="dashboard-grid" style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">
  <div class="chart-container" style="background:var(--bg-card); border:1px solid var(--border); border-radius:8px; padding:16px;">
    <canvas id="bar-chart"></canvas>
  </div>
  <div class="chart-container" style="background:var(--bg-card); border:1px solid var(--border); border-radius:8px; padding:16px;">
    <canvas id="doughnut-chart"></canvas>
  </div>
</div>
:::

:::script
Chart.defaults.animation = false;
// Chart initialization code...
:::
```

### 16. Chart Slide

Single Chart.js chart filling the slide body. Use for detailed data visualization when one chart needs full focus.

#### Bar Chart Variant

```html
<div class="slide">
  <div class="slide-header"><h2>Weekly Request Volume</h2></div>
  <div class="slide-body" style="display:flex; align-items:center; justify-content:center;">
    <div class="chart-container" style="width:90%; height:80%;">
      <canvas id="full-bar-chart"></canvas>
    </div>
  </div>
</div>

<script>
(function() {
  Chart.defaults.animation = false;
  const ctx = document.getElementById('full-bar-chart');
  if (ctx) {
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
        datasets: [{
          label: 'Requests (M)',
          data: [2.4, 3.1, 2.8, 3.5],
          backgroundColor: 'rgba(108, 92, 231, 0.7)',
          borderColor: 'rgba(108, 92, 231, 1)',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#94a3b8' } } },
        scales: {
          x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148, 163, 184, 0.1)' } },
          y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148, 163, 184, 0.1)' } }
        }
      }
    });
  }
})();
</script>
```

#### Line Chart Variant

```html
<div class="slide">
  <div class="slide-header"><h2>Latency Trend</h2></div>
  <div class="slide-body" style="display:flex; align-items:center; justify-content:center;">
    <div class="chart-container" style="width:90%; height:80%;">
      <canvas id="line-chart"></canvas>
    </div>
  </div>
</div>

<script>
(function() {
  Chart.defaults.animation = false;
  const ctx = document.getElementById('line-chart');
  if (ctx) {
    new Chart(ctx, {
      type: 'line',
      data: {
        labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
        datasets: [{
          label: 'P99 Latency (ms)',
          data: [120, 95, 180, 220, 150, 110],
          borderColor: '#00cec9',
          backgroundColor: 'rgba(0, 206, 201, 0.1)',
          fill: true,
          tension: 0.3
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#94a3b8' } } },
        scales: {
          x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148, 163, 184, 0.1)' } },
          y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148, 163, 184, 0.1)' } }
        }
      }
    });
  }
})();
</script>
```

#### Doughnut Chart Variant

```html
<div class="slide">
  <div class="slide-header"><h2>Cost Breakdown</h2></div>
  <div class="slide-body" style="display:flex; align-items:center; justify-content:center;">
    <div class="chart-container" style="width:60%; height:80%;">
      <canvas id="doughnut-full"></canvas>
    </div>
  </div>
</div>

<script>
(function() {
  Chart.defaults.animation = false;
  const ctx = document.getElementById('doughnut-full');
  if (ctx) {
    new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['EC2', 'RDS', 'S3', 'Lambda', 'Other'],
        datasets: [{
          data: [40, 25, 15, 12, 8],
          backgroundColor: ['#6c5ce7', '#00cec9', '#fdcb6e', '#e17055', '#636e72']
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'right', labels: { color: '#94a3b8', font: { size: 14 } } }
        }
      }
    });
  }
})();
</script>
```

#### CSS-Only Pie Chart (No JavaScript)

```html
<div class="slide">
  <div class="slide-header"><h2>Resource Allocation</h2></div>
  <div class="slide-body" style="display:flex; align-items:center; justify-content:center; gap:40px;">
    <!-- Conic-gradient pie chart -->
    <div style="width:200px; height:200px; border-radius:50%; background:conic-gradient(
      var(--accent) 0% 45%,
      var(--cyan) 45% 70%,
      #fdcb6e 70% 85%,
      var(--text-muted) 85% 100%
    );"></div>
    <!-- Legend -->
    <div style="display:flex; flex-direction:column; gap:12px;">
      <div style="display:flex; align-items:center; gap:8px;">
        <span style="width:16px; height:16px; background:var(--accent); border-radius:4px;"></span>
        <span>Compute (45%)</span>
      </div>
      <div style="display:flex; align-items:center; gap:8px;">
        <span style="width:16px; height:16px; background:var(--cyan); border-radius:4px;"></span>
        <span>Storage (25%)</span>
      </div>
      <div style="display:flex; align-items:center; gap:8px;">
        <span style="width:16px; height:16px; background:#fdcb6e; border-radius:4px;"></span>
        <span>Network (15%)</span>
      </div>
      <div style="display:flex; align-items:center; gap:8px;">
        <span style="width:16px; height:16px; background:var(--text-muted); border-radius:4px;"></span>
        <span>Other (15%)</span>
      </div>
    </div>
  </div>
</div>
```

#### CSS-Only SVG Bar Chart (No JavaScript)

```html
<div class="slide">
  <div class="slide-header"><h2>Service Comparison</h2></div>
  <div class="slide-body" style="display:flex; align-items:center; justify-content:center;">
    <svg viewBox="0 0 400 200" style="width:80%; max-height:80%;">
      <!-- Bars -->
      <rect x="50" y="20" width="60" height="140" fill="var(--accent)" rx="4"/>
      <rect x="130" y="60" width="60" height="100" fill="var(--cyan)" rx="4"/>
      <rect x="210" y="40" width="60" height="120" fill="#fdcb6e" rx="4"/>
      <rect x="290" y="80" width="60" height="80" fill="#e17055" rx="4"/>
      <!-- Labels -->
      <text x="80" y="180" fill="var(--text-secondary)" text-anchor="middle" font-size="12">EKS</text>
      <text x="160" y="180" fill="var(--text-secondary)" text-anchor="middle" font-size="12">ECS</text>
      <text x="240" y="180" fill="var(--text-secondary)" text-anchor="middle" font-size="12">Lambda</text>
      <text x="320" y="180" fill="var(--text-secondary)" text-anchor="middle" font-size="12">EC2</text>
      <!-- Values -->
      <text x="80" y="12" fill="var(--text-muted)" text-anchor="middle" font-size="10">70%</text>
      <text x="160" y="52" fill="var(--text-muted)" text-anchor="middle" font-size="10">50%</text>
      <text x="240" y="32" fill="var(--text-muted)" text-anchor="middle" font-size="10">60%</text>
      <text x="320" y="72" fill="var(--text-muted)" text-anchor="middle" font-size="10">40%</text>
    </svg>
  </div>
</div>
```

**Remarp equivalent:**

```markdown
---
@type: content
---
## Weekly Request Volume

:::html
<div class="chart-container" style="width:90%; height:80%; margin:auto;">
  <canvas id="full-bar-chart"></canvas>
</div>
:::

:::script
Chart.defaults.animation = false;
const ctx = document.getElementById('full-bar-chart');
new Chart(ctx, {
  type: 'bar',
  data: { /* ... */ },
  options: { /* ... */ }
});
:::
```

### 17. KPI / Metric Slide

Large numbers with delta indicators for highlighting key metrics. Use for status updates, performance summaries, and goal tracking.

```html
<div class="slide">
  <div class="slide-header"><h2>Monthly Performance</h2></div>
  <div class="slide-body">
    <div class="kpi-row" style="display:flex; gap:20px; justify-content:center; flex-wrap:wrap;">
      <div class="kpi-card" style="min-width:180px; background:var(--bg-card); border:1px solid var(--border); border-radius:12px; padding:24px; text-align:center;">
        <div class="kpi-value" style="font-size:3rem; font-weight:700; color:var(--accent);">$2.4M</div>
        <div class="kpi-label" style="font-size:0.9rem; color:var(--text-muted); margin-top:8px;">Revenue</div>
        <div class="kpi-delta" style="font-size:0.85rem; color:var(--green); margin-top:4px;">+18% MoM</div>
      </div>
      <div class="kpi-card" style="min-width:180px; background:var(--bg-card); border:1px solid var(--border); border-radius:12px; padding:24px; text-align:center;">
        <div class="kpi-value" style="font-size:3rem; font-weight:700; color:var(--cyan);">99.95%</div>
        <div class="kpi-label" style="font-size:0.9rem; color:var(--text-muted); margin-top:8px;">Uptime SLA</div>
        <div class="kpi-delta" style="font-size:0.85rem; color:var(--green); margin-top:4px;">+0.05%</div>
      </div>
      <div class="kpi-card" style="min-width:180px; background:var(--bg-card); border:1px solid var(--border); border-radius:12px; padding:24px; text-align:center;">
        <div class="kpi-value" style="font-size:3rem; font-weight:700; color:#fdcb6e;">142ms</div>
        <div class="kpi-label" style="font-size:0.9rem; color:var(--text-muted); margin-top:8px;">P95 Latency</div>
        <div class="kpi-delta" style="font-size:0.85rem; color:var(--green); margin-top:4px;">-23ms</div>
      </div>
      <div class="kpi-card" style="min-width:180px; background:var(--bg-card); border:1px solid var(--border); border-radius:12px; padding:24px; text-align:center;">
        <div class="kpi-value" style="font-size:3rem; font-weight:700; color:#e17055;">12</div>
        <div class="kpi-label" style="font-size:0.9rem; color:var(--text-muted); margin-top:8px;">Open Incidents</div>
        <div class="kpi-delta" style="font-size:0.85rem; color:var(--red); margin-top:4px;">+3</div>
      </div>
    </div>
  </div>
</div>
```

#### Variant with Sparkline SVG

```html
<div class="slide">
  <div class="slide-header"><h2>Trend Metrics</h2></div>
  <div class="slide-body">
    <div class="kpi-row" style="display:flex; gap:20px; justify-content:center;">
      <div class="kpi-card" style="min-width:220px; background:var(--bg-card); border:1px solid var(--border); border-radius:12px; padding:24px;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
          <div>
            <div class="kpi-value" style="font-size:2.5rem; font-weight:700; color:var(--accent);">8,432</div>
            <div class="kpi-label" style="font-size:0.85rem; color:var(--text-muted);">Daily Active Users</div>
          </div>
          <div class="kpi-delta" style="font-size:0.8rem; color:var(--green);">+12%</div>
        </div>
        <!-- Sparkline SVG -->
        <svg viewBox="0 0 100 30" style="width:100%; height:30px; margin-top:12px;">
          <polyline
            points="0,25 15,20 30,22 45,15 60,18 75,10 90,8 100,5"
            fill="none"
            stroke="var(--accent)"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <polyline
            points="0,25 15,20 30,22 45,15 60,18 75,10 90,8 100,5 100,30 0,30"
            fill="url(#sparkGradient)"
          />
          <defs>
            <linearGradient id="sparkGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="var(--accent)" stop-opacity="0.3"/>
              <stop offset="100%" stop-color="var(--accent)" stop-opacity="0"/>
            </linearGradient>
          </defs>
        </svg>
      </div>
      <div class="kpi-card" style="min-width:220px; background:var(--bg-card); border:1px solid var(--border); border-radius:12px; padding:24px;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
          <div>
            <div class="kpi-value" style="font-size:2.5rem; font-weight:700; color:var(--cyan);">$48.2K</div>
            <div class="kpi-label" style="font-size:0.85rem; color:var(--text-muted);">Monthly Spend</div>
          </div>
          <div class="kpi-delta" style="font-size:0.8rem; color:var(--red);">+8%</div>
        </div>
        <svg viewBox="0 0 100 30" style="width:100%; height:30px; margin-top:12px;">
          <polyline
            points="0,20 15,18 30,22 45,19 60,25 75,22 90,28 100,25"
            fill="none"
            stroke="var(--cyan)"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
      </div>
    </div>
  </div>
</div>
```

**Remarp equivalent:**

```markdown
---
@type: content
---
## Monthly Performance

:::html
<div class="kpi-row" style="display:flex; gap:20px; justify-content:center; flex-wrap:wrap;">
  <div class="kpi-card" style="min-width:180px; background:var(--bg-card); border:1px solid var(--border); border-radius:12px; padding:24px; text-align:center;">
    <div class="kpi-value" style="font-size:3rem; font-weight:700; color:var(--accent);">$2.4M</div>
    <div class="kpi-label" style="font-size:0.9rem; color:var(--text-muted); margin-top:8px;">Revenue</div>
    <div class="kpi-delta" style="font-size:0.85rem; color:var(--green); margin-top:4px;">+18% MoM</div>
  </div>
  <!-- Additional KPI cards... -->
</div>
:::
```

### 18. Infographic Slide

Visual data storytelling with hero stats, icon grids, progress bars, and comparison visuals.

```html
<div class="slide">
  <div class="slide-header"><h2>Cloud Migration Progress</h2></div>
  <div class="slide-body">
    <!-- Hero Stat -->
    <div style="display:flex; align-items:center; justify-content:center; gap:20px; margin-bottom:24px;">
      <img src="../assets/aws-icons/Architecture-Service-Icons_07312025/Arch_Migration-Transfer/64/Arch_AWS-Migration-Hub_64.svg" alt="Migration" style="width:64px; height:64px;">
      <div class="stat-highlight" style="font-size:4rem; font-weight:700; color:var(--accent);">78%</div>
      <div style="font-size:1.2rem; color:var(--text-secondary);">Workloads Migrated</div>
    </div>

    <!-- Icon + Text Grid -->
    <div class="col-3" style="gap:16px; margin-bottom:24px;">
      <div class="card" style="display:flex; align-items:center; gap:12px; padding:16px;">
        <img src="../assets/aws-icons/Architecture-Service-Icons_07312025/Arch_Compute/48/Arch_Amazon-EC2_48.svg" alt="EC2" style="width:40px;">
        <div>
          <div style="font-weight:600;">142 Instances</div>
          <div style="font-size:0.85rem; color:var(--text-muted);">Compute layer</div>
        </div>
      </div>
      <div class="card" style="display:flex; align-items:center; gap:12px; padding:16px;">
        <img src="../assets/aws-icons/Architecture-Service-Icons_07312025/Arch_Database/48/Arch_Amazon-RDS_48.svg" alt="RDS" style="width:40px;">
        <div>
          <div style="font-weight:600;">24 Databases</div>
          <div style="font-size:0.85rem; color:var(--text-muted);">Data layer</div>
        </div>
      </div>
      <div class="card" style="display:flex; align-items:center; gap:12px; padding:16px;">
        <img src="../assets/aws-icons/Architecture-Service-Icons_07312025/Arch_Storage/48/Arch_Amazon-S3_48.svg" alt="S3" style="width:40px;">
        <div>
          <div style="font-weight:600;">8.2 PB Storage</div>
          <div style="font-size:0.85rem; color:var(--text-muted);">Object storage</div>
        </div>
      </div>
    </div>

    <!-- Progress Bars -->
    <div style="display:flex; flex-direction:column; gap:12px;">
      <div>
        <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
          <span>Compute Migration</span>
          <span style="color:var(--text-muted);">92%</span>
        </div>
        <div style="height:8px; background:var(--border); border-radius:4px; overflow:hidden;">
          <div style="width:92%; height:100%; background:var(--accent); border-radius:4px;"></div>
        </div>
      </div>
      <div>
        <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
          <span>Database Migration</span>
          <span style="color:var(--text-muted);">75%</span>
        </div>
        <div style="height:8px; background:var(--border); border-radius:4px; overflow:hidden;">
          <div style="width:75%; height:100%; background:var(--cyan); border-radius:4px;"></div>
        </div>
      </div>
      <div>
        <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
          <span>Application Testing</span>
          <span style="color:var(--text-muted);">60%</span>
        </div>
        <div style="height:8px; background:var(--border); border-radius:4px; overflow:hidden;">
          <div style="width:60%; height:100%; background:#fdcb6e; border-radius:4px;"></div>
        </div>
      </div>
    </div>
  </div>
</div>
```

#### Progress Ring Variant (SVG)

```html
<div class="slide">
  <div class="slide-header"><h2>Team Capacity</h2></div>
  <div class="slide-body" style="display:flex; justify-content:center; gap:40px; align-items:center;">
    <!-- Progress Ring 1 -->
    <div style="text-align:center;">
      <svg width="120" height="120" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r="50" fill="none" stroke="var(--border)" stroke-width="10"/>
        <circle cx="60" cy="60" r="50" fill="none" stroke="var(--accent)" stroke-width="10"
          stroke-dasharray="314" stroke-dashoffset="63" stroke-linecap="round"
          transform="rotate(-90 60 60)"/>
        <text x="60" y="65" text-anchor="middle" fill="var(--text-primary)" font-size="24" font-weight="700">80%</text>
      </svg>
      <div style="margin-top:8px; color:var(--text-secondary);">Dev Team</div>
    </div>
    <!-- Progress Ring 2 -->
    <div style="text-align:center;">
      <svg width="120" height="120" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r="50" fill="none" stroke="var(--border)" stroke-width="10"/>
        <circle cx="60" cy="60" r="50" fill="none" stroke="var(--cyan)" stroke-width="10"
          stroke-dasharray="314" stroke-dashoffset="94" stroke-linecap="round"
          transform="rotate(-90 60 60)"/>
        <text x="60" y="65" text-anchor="middle" fill="var(--text-primary)" font-size="24" font-weight="700">70%</text>
      </svg>
      <div style="margin-top:8px; color:var(--text-secondary);">Ops Team</div>
    </div>
    <!-- Progress Ring 3 -->
    <div style="text-align:center;">
      <svg width="120" height="120" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r="50" fill="none" stroke="var(--border)" stroke-width="10"/>
        <circle cx="60" cy="60" r="50" fill="none" stroke="#fdcb6e" stroke-width="10"
          stroke-dasharray="314" stroke-dashoffset="157" stroke-linecap="round"
          transform="rotate(-90 60 60)"/>
        <text x="60" y="65" text-anchor="middle" fill="var(--text-primary)" font-size="24" font-weight="700">50%</text>
      </svg>
      <div style="margin-top:8px; color:var(--text-secondary);">QA Team</div>
    </div>
  </div>
</div>
```

Progress ring formula: `stroke-dashoffset = circumference * (1 - percentage/100)` where circumference = 2 * pi * r = 314 for r=50.

#### Horizontal Comparison Bars

```html
<div class="slide">
  <div class="slide-header"><h2>Service Comparison</h2></div>
  <div class="slide-body">
    <div style="display:flex; flex-direction:column; gap:20px; max-width:600px; margin:0 auto;">
      <div>
        <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
          <span style="font-weight:600;">EKS</span>
          <span style="color:var(--text-muted);">Performance: 95</span>
        </div>
        <div style="display:flex; height:24px; background:var(--border); border-radius:4px; overflow:hidden;">
          <div style="width:95%; background:var(--accent);"></div>
        </div>
      </div>
      <div>
        <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
          <span style="font-weight:600;">ECS</span>
          <span style="color:var(--text-muted);">Performance: 82</span>
        </div>
        <div style="display:flex; height:24px; background:var(--border); border-radius:4px; overflow:hidden;">
          <div style="width:82%; background:var(--cyan);"></div>
        </div>
      </div>
      <div>
        <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
          <span style="font-weight:600;">Lambda</span>
          <span style="color:var(--text-muted);">Performance: 78</span>
        </div>
        <div style="display:flex; height:24px; background:var(--border); border-radius:4px; overflow:hidden;">
          <div style="width:78%; background:#fdcb6e;"></div>
        </div>
      </div>
    </div>
  </div>
</div>
```

**Remarp equivalent:**

```markdown
---
@type: content
---
## Cloud Migration Progress

:::html
<!-- Hero Stat -->
<div style="display:flex; align-items:center; justify-content:center; gap:20px; margin-bottom:24px;">
  <img src="../assets/aws-icons/Architecture-Service-Icons_07312025/Arch_Migration-Transfer/64/Arch_AWS-Migration-Hub_64.svg" alt="Migration" style="width:64px;">
  <div class="stat-highlight" style="font-size:4rem; font-weight:700; color:var(--accent);">78%</div>
  <div style="font-size:1.2rem; color:var(--text-secondary);">Workloads Migrated</div>
</div>

<!-- Progress Bars -->
<div style="display:flex; flex-direction:column; gap:12px;">
  <div>
    <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
      <span>Compute Migration</span><span style="color:var(--text-muted);">92%</span>
    </div>
    <div style="height:8px; background:var(--border); border-radius:4px; overflow:hidden;">
      <div style="width:92%; height:100%; background:var(--accent);"></div>
    </div>
  </div>
</div>
:::
```

### 19. Data Table Slide

Styled data table with alternating rows, hover effects, and status badges.

```html
<div class="slide">
  <div class="slide-header"><h2>Cluster Status</h2></div>
  <div class="slide-body" style="overflow-x:auto;">
    <table class="data-table" style="width:100%; border-collapse:collapse; font-size:0.9rem;">
      <thead>
        <tr style="background:var(--bg-card); border-bottom:2px solid var(--border);">
          <th style="padding:12px 16px; text-align:left; color:var(--text-muted); font-weight:600;">Cluster</th>
          <th style="padding:12px 16px; text-align:left; color:var(--text-muted); font-weight:600;">Region</th>
          <th style="padding:12px 16px; text-align:right; color:var(--text-muted); font-weight:600;">Nodes</th>
          <th style="padding:12px 16px; text-align:right; color:var(--text-muted); font-weight:600;">CPU %</th>
          <th style="padding:12px 16px; text-align:right; color:var(--text-muted); font-weight:600;">Memory %</th>
          <th style="padding:12px 16px; text-align:center; color:var(--text-muted); font-weight:600;">Status</th>
        </tr>
      </thead>
      <tbody>
        <tr style="border-bottom:1px solid var(--border);">
          <td style="padding:12px 16px; font-weight:500;">prod-cluster-01</td>
          <td style="padding:12px 16px; color:var(--text-secondary);">us-east-1</td>
          <td style="padding:12px 16px; text-align:right;">24</td>
          <td style="padding:12px 16px; text-align:right;">68%</td>
          <td style="padding:12px 16px; text-align:right;">72%</td>
          <td style="padding:12px 16px; text-align:center;">
            <span class="badge-up" style="background:var(--green); color:#fff; padding:4px 12px; border-radius:12px; font-size:0.75rem;">Healthy</span>
          </td>
        </tr>
        <tr style="border-bottom:1px solid var(--border); background:var(--bg-card);">
          <td style="padding:12px 16px; font-weight:500;">prod-cluster-02</td>
          <td style="padding:12px 16px; color:var(--text-secondary);">eu-west-1</td>
          <td style="padding:12px 16px; text-align:right;">18</td>
          <td style="padding:12px 16px; text-align:right;">45%</td>
          <td style="padding:12px 16px; text-align:right;">52%</td>
          <td style="padding:12px 16px; text-align:center;">
            <span class="badge-up" style="background:var(--green); color:#fff; padding:4px 12px; border-radius:12px; font-size:0.75rem;">Healthy</span>
          </td>
        </tr>
        <tr style="border-bottom:1px solid var(--border);">
          <td style="padding:12px 16px; font-weight:500;">staging-cluster</td>
          <td style="padding:12px 16px; color:var(--text-secondary);">us-west-2</td>
          <td style="padding:12px 16px; text-align:right;">8</td>
          <td style="padding:12px 16px; text-align:right;">82%</td>
          <td style="padding:12px 16px; text-align:right;">78%</td>
          <td style="padding:12px 16px; text-align:center;">
            <span style="background:#fdcb6e; color:#1a1f35; padding:4px 12px; border-radius:12px; font-size:0.75rem;">Warning</span>
          </td>
        </tr>
        <tr style="border-bottom:1px solid var(--border); background:var(--bg-card);">
          <td style="padding:12px 16px; font-weight:500;">dev-cluster</td>
          <td style="padding:12px 16px; color:var(--text-secondary);">ap-northeast-1</td>
          <td style="padding:12px 16px; text-align:right;">4</td>
          <td style="padding:12px 16px; text-align:right;">25%</td>
          <td style="padding:12px 16px; text-align:right;">30%</td>
          <td style="padding:12px 16px; text-align:center;">
            <span class="badge-down" style="background:var(--red); color:#fff; padding:4px 12px; border-radius:12px; font-size:0.75rem;">Degraded</span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</div>

<style>
.data-table tbody tr:hover {
  background: rgba(108, 92, 231, 0.1) !important;
}
</style>
```

#### Highlight Column Pattern

```html
<div class="slide">
  <div class="slide-header"><h2>Feature Comparison</h2></div>
  <div class="slide-body" style="overflow-x:auto;">
    <table class="data-table" style="width:100%; border-collapse:collapse; font-size:0.9rem;">
      <thead>
        <tr style="background:var(--bg-card); border-bottom:2px solid var(--border);">
          <th style="padding:12px 16px; text-align:left;">Feature</th>
          <th style="padding:12px 16px; text-align:center;">Basic</th>
          <th style="padding:12px 16px; text-align:center; background:rgba(108,92,231,0.15); border-left:2px solid var(--accent); border-right:2px solid var(--accent);">Pro (Recommended)</th>
          <th style="padding:12px 16px; text-align:center;">Enterprise</th>
        </tr>
      </thead>
      <tbody>
        <tr style="border-bottom:1px solid var(--border);">
          <td style="padding:12px 16px;">Auto Scaling</td>
          <td style="padding:12px 16px; text-align:center;">-</td>
          <td style="padding:12px 16px; text-align:center; background:rgba(108,92,231,0.08); border-left:2px solid var(--accent); border-right:2px solid var(--accent); color:var(--green);">Yes</td>
          <td style="padding:12px 16px; text-align:center; color:var(--green);">Yes</td>
        </tr>
        <tr style="border-bottom:1px solid var(--border); background:var(--bg-card);">
          <td style="padding:12px 16px;">Multi-Region</td>
          <td style="padding:12px 16px; text-align:center;">-</td>
          <td style="padding:12px 16px; text-align:center; background:rgba(108,92,231,0.08); border-left:2px solid var(--accent); border-right:2px solid var(--accent); color:var(--green);">Yes</td>
          <td style="padding:12px 16px; text-align:center; color:var(--green);">Yes</td>
        </tr>
        <tr style="border-bottom:1px solid var(--border);">
          <td style="padding:12px 16px;">SLA</td>
          <td style="padding:12px 16px; text-align:center;">99%</td>
          <td style="padding:12px 16px; text-align:center; background:rgba(108,92,231,0.08); border-left:2px solid var(--accent); border-right:2px solid var(--accent); font-weight:600;">99.9%</td>
          <td style="padding:12px 16px; text-align:center;">99.99%</td>
        </tr>
        <tr style="border-bottom:1px solid var(--border); background:var(--bg-card);">
          <td style="padding:12px 16px;">Support</td>
          <td style="padding:12px 16px; text-align:center;">Email</td>
          <td style="padding:12px 16px; text-align:center; background:rgba(108,92,231,0.08); border-left:2px solid var(--accent); border-right:2px solid var(--accent);">24/7 Chat</td>
          <td style="padding:12px 16px; text-align:center;">Dedicated TAM</td>
        </tr>
      </tbody>
    </table>
  </div>
</div>
```

**Remarp equivalent:**

```markdown
---
@type: content
---
## Cluster Status

:::html
<table class="data-table" style="width:100%; border-collapse:collapse; font-size:0.9rem;">
  <thead>
    <tr style="background:var(--bg-card); border-bottom:2px solid var(--border);">
      <th style="padding:12px 16px; text-align:left; color:var(--text-muted);">Cluster</th>
      <th style="padding:12px 16px; text-align:left; color:var(--text-muted);">Region</th>
      <th style="padding:12px 16px; text-align:right; color:var(--text-muted);">Nodes</th>
      <th style="padding:12px 16px; text-align:center; color:var(--text-muted);">Status</th>
    </tr>
  </thead>
  <tbody>
    <tr style="border-bottom:1px solid var(--border);">
      <td style="padding:12px 16px;">prod-cluster-01</td>
      <td style="padding:12px 16px;">us-east-1</td>
      <td style="padding:12px 16px; text-align:right;">24</td>
      <td style="padding:12px 16px; text-align:center;">
        <span class="badge-up" style="background:var(--green); color:#fff; padding:4px 12px; border-radius:12px;">Healthy</span>
      </td>
    </tr>
  </tbody>
</table>
:::

:::css
.data-table tbody tr:hover {
  background: rgba(108, 92, 231, 0.1) !important;
}
:::
```

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

#### §15 Dashboard

```jsonc
{
  "type": "dashboard",
  "title": "Operations Dashboard",
  "kpis": [
    { "value": "99.9%", "label": "Availability", "delta": "+0.2%", "deltaType": "positive" },
    { "value": "1.2s", "label": "Avg Latency", "delta": "-15%", "deltaType": "positive" },
    { "value": "847", "label": "Active Pods", "delta": "+12%", "deltaType": "negative" }
  ],
  "charts": [
    {
      "id": "bar-chart",
      "type": "bar",
      "labels": ["Mon", "Tue", "Wed", "Thu", "Fri"],
      "datasets": [{ "label": "Requests (K)", "data": [12, 19, 15, 25, 22] }]
    },
    {
      "id": "doughnut-chart",
      "type": "doughnut",
      "labels": ["Compute", "Storage", "Network", "Other"],
      "datasets": [{ "data": [45, 25, 20, 10] }]
    }
  ],
  "notes": "KPI와 차트를 함께 보여주는 대시보드 슬라이드."
}
```

#### §16 Chart

```jsonc
// Bar chart
{
  "type": "chart",
  "title": "Weekly Request Volume",
  "chartType": "bar",
  "chartId": "weekly-bar",
  "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
  "datasets": [
    { "label": "Requests (M)", "data": [2.4, 3.1, 2.8, 3.5], "color": "accent" }
  ]
}

// Line chart
{
  "type": "chart",
  "title": "Latency Trend",
  "chartType": "line",
  "chartId": "latency-line",
  "labels": ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"],
  "datasets": [
    { "label": "P99 Latency (ms)", "data": [120, 95, 180, 220, 150, 110], "color": "cyan", "fill": true }
  ]
}

// Doughnut chart
{
  "type": "chart",
  "title": "Cost Breakdown",
  "chartType": "doughnut",
  "chartId": "cost-doughnut",
  "labels": ["EC2", "RDS", "S3", "Lambda", "Other"],
  "datasets": [
    { "data": [40, 25, 15, 12, 8], "colors": ["accent", "cyan", "#fdcb6e", "#e17055", "muted"] }
  ]
}

// CSS-only pie (no Chart.js)
{
  "type": "chart",
  "title": "Resource Allocation",
  "chartType": "css-pie",
  "segments": [
    { "label": "Compute", "percent": 45, "color": "accent" },
    { "label": "Storage", "percent": 25, "color": "cyan" },
    { "label": "Network", "percent": 15, "color": "#fdcb6e" },
    { "label": "Other", "percent": 15, "color": "muted" }
  ]
}
```

#### §17 KPI

```jsonc
{
  "type": "kpi",
  "title": "Monthly Performance",
  "metrics": [
    { "value": "$2.4M", "label": "Revenue", "delta": "+18% MoM", "deltaType": "positive", "color": "accent" },
    { "value": "99.95%", "label": "Uptime SLA", "delta": "+0.05%", "deltaType": "positive", "color": "cyan" },
    { "value": "142ms", "label": "P95 Latency", "delta": "-23ms", "deltaType": "positive", "color": "#fdcb6e" },
    { "value": "12", "label": "Open Incidents", "delta": "+3", "deltaType": "negative", "color": "#e17055" }
  ]
}

// With sparklines
{
  "type": "kpi",
  "title": "Trend Metrics",
  "metrics": [
    {
      "value": "8,432",
      "label": "Daily Active Users",
      "delta": "+12%",
      "deltaType": "positive",
      "sparkline": [25, 20, 22, 15, 18, 10, 8, 5]
    },
    {
      "value": "$48.2K",
      "label": "Monthly Spend",
      "delta": "+8%",
      "deltaType": "negative",
      "sparkline": [20, 18, 22, 19, 25, 22, 28, 25]
    }
  ]
}
```

#### §18 Infographic

```jsonc
{
  "type": "infographic",
  "title": "Cloud Migration Progress",
  "heroStat": {
    "value": "78%",
    "label": "Workloads Migrated",
    "icon": "../assets/aws-icons/Architecture-Service-Icons_07312025/Arch_Migration-Transfer/64/Arch_AWS-Migration-Hub_64.svg"
  },
  "iconGrid": [
    { "icon": "ec2", "title": "142 Instances", "subtitle": "Compute layer" },
    { "icon": "rds", "title": "24 Databases", "subtitle": "Data layer" },
    { "icon": "s3", "title": "8.2 PB Storage", "subtitle": "Object storage" }
  ],
  "progressBars": [
    { "label": "Compute Migration", "percent": 92, "color": "accent" },
    { "label": "Database Migration", "percent": 75, "color": "cyan" },
    { "label": "Application Testing", "percent": 60, "color": "#fdcb6e" }
  ]
}

// Progress rings variant
{
  "type": "infographic",
  "title": "Team Capacity",
  "progressRings": [
    { "label": "Dev Team", "percent": 80, "color": "accent" },
    { "label": "Ops Team", "percent": 70, "color": "cyan" },
    { "label": "QA Team", "percent": 50, "color": "#fdcb6e" }
  ]
}

// Horizontal comparison bars
{
  "type": "infographic",
  "title": "Service Comparison",
  "comparisonBars": [
    { "label": "EKS", "value": 95, "color": "accent" },
    { "label": "ECS", "value": 82, "color": "cyan" },
    { "label": "Lambda", "value": 78, "color": "#fdcb6e" }
  ]
}
```

#### §19 Data Table

```jsonc
{
  "type": "datatable",
  "title": "Cluster Status",
  "columns": [
    { "key": "cluster", "label": "Cluster", "align": "left" },
    { "key": "region", "label": "Region", "align": "left" },
    { "key": "nodes", "label": "Nodes", "align": "right" },
    { "key": "cpu", "label": "CPU %", "align": "right" },
    { "key": "memory", "label": "Memory %", "align": "right" },
    { "key": "status", "label": "Status", "align": "center", "badge": true }
  ],
  "rows": [
    { "cluster": "prod-cluster-01", "region": "us-east-1", "nodes": 24, "cpu": "68%", "memory": "72%", "status": { "text": "Healthy", "type": "success" } },
    { "cluster": "prod-cluster-02", "region": "eu-west-1", "nodes": 18, "cpu": "45%", "memory": "52%", "status": { "text": "Healthy", "type": "success" } },
    { "cluster": "staging-cluster", "region": "us-west-2", "nodes": 8, "cpu": "82%", "memory": "78%", "status": { "text": "Warning", "type": "warning" } },
    { "cluster": "dev-cluster", "region": "ap-northeast-1", "nodes": 4, "cpu": "25%", "memory": "30%", "status": { "text": "Degraded", "type": "error" } }
  ],
  "hoverHighlight": true
}

// Highlight column variant
{
  "type": "datatable",
  "title": "Feature Comparison",
  "highlightColumn": "pro",
  "columns": [
    { "key": "feature", "label": "Feature", "align": "left" },
    { "key": "basic", "label": "Basic", "align": "center" },
    { "key": "pro", "label": "Pro (Recommended)", "align": "center" },
    { "key": "enterprise", "label": "Enterprise", "align": "center" }
  ],
  "rows": [
    { "feature": "Auto Scaling", "basic": "-", "pro": "Yes", "enterprise": "Yes" },
    { "feature": "Multi-Region", "basic": "-", "pro": "Yes", "enterprise": "Yes" },
    { "feature": "SLA", "basic": "99%", "pro": "99.9%", "enterprise": "99.99%" },
    { "feature": "Support", "basic": "Email", "pro": "24/7 Chat", "enterprise": "Dedicated TAM" }
  ]
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
