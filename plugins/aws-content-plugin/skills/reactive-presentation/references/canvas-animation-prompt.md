# Canvas Animation Prompt Reference

This document is the agent reference for converting `:::canvas prompt` (or shorthand `:::prompt`) natural language descriptions into Canvas JS code. When processing a `:::canvas prompt` or `:::prompt` block, read this document, analyze the prompt, generate Canvas JS, and replace the block with `:::canvas js`.

---

## Workflow

```
1. Read :::canvas prompt (or :::prompt) block text
2. Analyze prompt → choose approach (DSL / Preset / Custom JS)
3. Generate code following required patterns
4. Replace :::canvas prompt → :::canvas js in the .remarp.md file
5. Run converter to build HTML
```

---

## Decision Tree

```
Prompt Analysis
├── Mentions specific preset scenario?
│   ├── EKS pod/node scaling → CanvasPresets['eks-pod-scaling'] or ['eks-node-scaling']
│   ├── Traffic flow between services → CanvasPresets['traffic-flow']
│   ├── Rolling update → CanvasPresets['rolling-update']
│   └── Failover scenario → CanvasPresets['failover']
│
├── Simple static diagram with step reveals?
│   └── Use DSL (box/icon/arrow with step N) — no JS needed, use :::canvas DSL directly
│
├── Needs continuous animation (particles, pulsing, data streaming)?
│   └── Custom JS with AnimationLoop + ParticleSystem
│
├── Multi-phase timeline animation?
│   └── Custom JS with TimelineAnimation
│
├── Complex custom visualization?
│   └── Custom JS with setupCanvas + drawing primitives
│
├── Chart/Data visualization request?
│   ├── Simple pie/donut → CSS conic-gradient (no canvas needed) → see data-visualization-guide.md §3
│   ├── Bar/Line chart → Chart.js CDN or SVG inline → see data-visualization-guide.md §2
│   ├── KPI dashboard → HTML/CSS card grid → see data-visualization-guide.md §4
│   ├── Gauge/meter → Canvas JS drawGauge pattern → see §Canvas JS Chart Patterns below
│   └── Complex data visualization → Custom JS with canvas primitives → see §Canvas JS Chart Patterns below
│
└── Dashboard/Infographic layout?
    └── HTML/CSS slide (not canvas) → see data-visualization-guide.md
```

**Rule**: Prefer the simplest approach. DSL > Preset > Custom JS.

If the prompt can be expressed with the declarative `:::canvas` DSL (boxes, arrows, icons with steps), convert to DSL instead of JS. Only use `:::canvas js` when the prompt requires animation, presets, or logic beyond DSL capabilities.

---

## API Reference

### Setup

```javascript
// setupCanvas(canvasId, baseWidth, baseHeight) → { canvas, ctx, width, height }
const { canvas, ctx, width: W, height: H } = setupCanvas('my-canvas', 960, 400);
```

### Colors

```javascript
const Colors = {
  bg: '#0f1117',       bgSecond: '#1a1d2e',  surface: '#282d45',
  border: '#2d3250',   accent: '#6c5ce7',    accentLt: '#a29bfe',
  green: '#00b894',    yellow: '#fdcb6e',     red: '#e17055',
  blue: '#74b9ff',     cyan: '#00cec9',       pink: '#fd79a8',
  orange: '#f39c12',   textPri: '#e8eaf0',    textSec: '#9ba1b8',
  textMuted: '#6b7194'
};
// PPTX theme colors: Colors.pptxAccent1..6, Colors.pptxDk1, Colors.pptxLt1, etc.
// resolveColor('theme-accent1') → PPTX accent color or fallback
```

### Drawing Primitives

| Function | Signature | Description |
|----------|-----------|-------------|
| `drawBox` | `(ctx, x, y, w, h, label, color, textColor?)` | Rounded rect with centered label (auto word-wrap) |
| `drawArrow` | `(ctx, x1, y1, x2, y2, color?, dashed?)` | Arrow with arrowhead |
| `drawElbowArrow` | `(ctx, x1, y1, x2, y2, color?, dashed?)` | 꺽은선(Elbow) 화살표 — 그룹 간 연결용 |
| `drawCircle` | `(ctx, x, y, radius, fill?, stroke?)` | Circle with optional fill/stroke |
| `drawText` | `(ctx, text, x, y, opts?)` | Text with `{color, size, weight, font, align, baseline}` |
| `drawIcon` | `(ctx, src, x, y, size, onLoad?)` | Draw image/icon centered at (x,y). `src` can be Image or URL |
| `drawGroup` | `(ctx, x, y, w, h, label, color?)` | Dashed border group with label |
| `drawRoundRect` | `(ctx, x, y, w, h, radius, fill?, stroke?)` | Rounded rectangle primitive |
| `drawPod` | `(ctx, x, y, size, status, label?)` | K8s pod circle. Status: running/pending/failed/terminating/creating |
| `drawNode` | `(ctx, x, y, w, h, name, pods, maxPods, opts?)` | K8s node box with pod grid |
| `drawCluster` | `(ctx, x, y, w, h, name)` | K8s cluster dashed boundary |

### 화살표 선택 기준 (Arrow Selection Guide)

| 조건 | 함수 | 이유 |
|------|------|------|
| 순수 수평/수직 (dx=0 또는 dy=0) | `drawArrow` | 꺾을 필요 없음 |
| 근거리 연결 (dx < 80px AND dy < 80px) | `drawArrow` | 짧은 거리에 꺾임은 어색 |
| 그룹 간 대각선 연결 (dx ≥ 80) | `drawElbowArrow` | 깔끔한 직교 라우팅 |
| drawArrow + drawText('→') 조합 | ❌ 금지 | arrowhead 중복 — drawArrow가 이미 화살촉 포함 |

### Animation Classes

#### AnimationLoop

```javascript
const loop = new AnimationLoop((elapsed) => {
  ctx.clearRect(0, 0, W, H);
  // draw using elapsed (seconds since start)
});
loop.start();   // Start animation
loop.stop();    // Stop animation
loop.restart(); // Stop + start
```

#### TimelineAnimation

```javascript
const timeline = new TimelineAnimation([
  { at: 0.0, action: () => { /* step 1 */ } },
  { at: 0.3, action: () => { /* step 2 */ } },
  { at: 0.6, action: () => { /* step 3 */ } },
], 5); // 5 second duration

timeline.play();
timeline.pause();
timeline.reset();
timeline.nextStep();  // Manual step forward (keyboard ↑↓)
timeline.prevStep();  // Manual step backward
timeline.goToStep(2); // Jump to specific step
```

#### ParticleSystem

```javascript
const particles = new ParticleSystem(50, { w: W, h: H });
// In animation loop:
particles.update();
particles.draw(ctx);
```

### Easing Functions

```javascript
Ease.linear(t)   Ease.inOut(t)   Ease.out(t)
Ease.in(t)       Ease.elastic(t) Ease.bounce(t)
```

### Utility

```javascript
lerp(a, b, t)       // Linear interpolation
clamp(v, min, max)  // Clamp value
```

### Presets

```javascript
// CanvasPresets['preset-name'](ctx, config, step, width, height)
CanvasPresets['eks-pod-scaling'](ctx, config, step, W, H);
CanvasPresets['eks-node-scaling'](ctx, config, step, W, H);
CanvasPresets['traffic-flow'](ctx, config, step, W, H);
CanvasPresets['rolling-update'](ctx, config, step, W, H);
CanvasPresets['failover'](ctx, config, step, W, H);
```

**Preset configs:**

- **eks-pod-scaling**: `{ clusters: [{ name, x, y, nodes: [{ name, pods, max }] }], steps: [{ step, action, node, to, label }] }`
- **traffic-flow**: `{ services: [{ name, x, y, color }], flows: [{ from, to, label, color, dashed, step }] }`
- **rolling-update**: `{ totalPods: 6 }` — step count = updated pods
- **failover**: `{ primary: { name, x }, standby: { name, x }, failoverStep: 2 }`

### renderCanvasDSL (Runtime DSL Renderer)

```javascript
// For rendering DSL data structure at runtime
const renderer = renderCanvasDSL('canvas-id', dslData, currentStep, { width: 960, height: 400 });
renderer.setStep(3);  // Update visible step
renderer.redraw();    // Force redraw
```

---

## AWS Icon Paths

Icons are at `../common/aws-icons/` relative to the HTML file. Service name mapping:

| Service | Icon File |
|---------|-----------|
| `Lambda` | `Arch_AWS-Lambda_48.svg` |
| `EC2` | `Arch_Amazon-EC2_48.svg` |
| `ECS` | `Arch_Amazon-Elastic-Container-Service_48.svg` |
| `EKS` | `Arch_Amazon-Elastic-Kubernetes-Service_48.svg` |
| `Fargate` | `Arch_AWS-Fargate_48.svg` |
| `API-Gateway` | `Arch_Amazon-API-Gateway_48.svg` |
| `ALB` | `Arch_Elastic-Load-Balancing_48.svg` |
| `DynamoDB` | `Arch_Amazon-DynamoDB_48.svg` |
| `S3` | `Arch_Amazon-Simple-Storage-Service_48.svg` |
| `RDS` | `Arch_Amazon-RDS_48.svg` |
| `Aurora` | `Arch_Amazon-Aurora_48.svg` |
| `CloudFront` | `Arch_Amazon-CloudFront_48.svg` |
| `SQS` | `Arch_Amazon-Simple-Queue-Service_48.svg` |
| `SNS` | `Arch_Amazon-Simple-Notification-Service_48.svg` |
| `EventBridge` | `Arch_Amazon-EventBridge_48.svg` |
| `StepFunctions` | `Arch_AWS-Step-Functions_48.svg` |
| `Bedrock` | `Arch_Amazon-Bedrock_48.svg` |
| `SageMaker` | `Arch_Amazon-SageMaker_48.svg` |
| `CloudWatch` | `Arch_Amazon-CloudWatch_48.svg` |
| `CloudTrail` | `Arch_AWS-CloudTrail_48.svg` |
| `X-Ray` | `Arch_AWS-X-Ray_48.svg` |
| `IAM` | `Arch_AWS-Identity-and-Access-Management_48.svg` |
| `Cognito` | `Arch_Amazon-Cognito_48.svg` |
| `Kinesis` | `Arch_Amazon-Kinesis_48.svg` |
| `Systems-Manager` | `Arch_AWS-Systems-Manager_48.svg` |
| `DevOps-Guru` | `Arch_Amazon-DevOps-Guru_48.svg` |
| `KMS` | `Arch_AWS-Key-Management-Service_48.svg` |
| `VPC` | `Virtual-private-cloud-VPC_32.svg` |

Full mapping (70 services) in `remarp-format-guide.md` → "Supported Service Names".

---

## Required Patterns

### 1. IIFE Wrapper

All generated `:::canvas js` code MUST use an IIFE to avoid polluting global scope:

```javascript
(function() {
  const { canvas, ctx, width: W, height: H } = setupCanvas('CANVAS_ID', 960, 400);
  if (!canvas) return;

  // ... drawing code ...
})();
```

### 2. Proportional Scaling (ResizeObserver)

For responsive rendering, use `setupCanvas()` which handles DPR scaling. The canvas `style.width` is set to `100%` with `maxWidth` constraint, so content scales proportionally.

### 3. Step-Based Keyboard Navigation

For step-reveal animations, register a `slideAction` on the canvas's parent slide:

```javascript
(function() {
  const { canvas, ctx, width: W, height: H } = setupCanvas('CANVAS_ID', 960, 400);
  if (!canvas) return;
  let step = 0;
  const MAX_STEP = 5;

  function draw() {
    ctx.clearRect(0, 0, W, H);
    // Draw elements conditionally based on step
    if (step >= 1) { /* draw step 1 elements */ }
    if (step >= 2) { /* draw step 2 elements */ }
  }

  draw(); // Initial render

  // Register keyboard step control
  const slide = canvas.closest('.slide');
  if (slide) {
    slide.dataset.slideAction = 'canvas-step';
    slide.dataset.canvasMaxStep = MAX_STEP;
    slide.__canvasStep = function(direction) {
      if (direction === 'next' && step < MAX_STEP) step++;
      if (direction === 'prev' && step > 0) step--;
      draw();
      return step; // Return current step for framework tracking
    };
  }
})();
```

### 4. Icon Preloading

When using icons, preload all images before drawing:

```javascript
const icons = {
  lambda: '../common/aws-icons/Arch_AWS-Lambda_48.svg',
  dynamo: '../common/aws-icons/Arch_Amazon-DynamoDB_48.svg',
};
const loaded = {};
let pending = Object.keys(icons).length;

Object.entries(icons).forEach(([key, src]) => {
  const img = new Image();
  img.onload = () => {
    loaded[key] = img;
    if (--pending === 0) draw(); // Redraw when all loaded
  };
  img.src = src;
});
```

---

## Prompt → Code Examples

### Example 1: Simple Traffic Flow (ALB → EKS → RDS)

**Prompt:**
```
ALB → EKS → RDS 트래픽 흐름
Step 1: 서비스 아이콘 표시
Step 2: 화살표 연결
```

**Approach:** DSL is sufficient — convert to `:::canvas` (not `:::canvas js`)

**Output:**
```
:::canvas
icon alb "ALB" at 100,150 size 48 step 1
icon eks "EKS" at 300,150 size 48 step 1
icon rds "RDS" at 500,150 size 48 step 1

arrow alb -> eks "HTTP" step 2
arrow eks -> rds "Query" step 2
:::
```

### Example 2: EKS Scaling with Preset

**Prompt:**
```
EKS 클러스터 오토스케일링 시각화
3개 노드, 각각 2/4 파드
Step 1: 현재 상태
Step 2: 노드1에 파드 추가
Step 3: 노드2에 파드 추가
```

**Approach:** Use `CanvasPresets['eks-pod-scaling']`

**Output:**
```javascript
:::canvas js
(function() {
  const { canvas, ctx, width: W, height: H } = setupCanvas('eks-scaling', 960, 400);
  if (!canvas) return;
  let step = 0;

  const config = {
    clusters: [{
      name: 'Production EKS', x: 40, y: 30,
      nodes: [
        { name: 'node-1', pods: 2, max: 4 },
        { name: 'node-2', pods: 2, max: 4 },
        { name: 'node-3', pods: 2, max: 4 }
      ]
    }],
    steps: [
      { step: 1, action: 'scale-out', node: 0, to: 3, label: 'Scale out node-1' },
      { step: 2, action: 'scale-out', node: 1, to: 3, label: 'Scale out node-2' }
    ]
  };

  function draw() {
    CanvasPresets['eks-pod-scaling'](ctx, config, step, W, H);
  }

  draw();

  const slide = canvas.closest('.slide');
  if (slide) {
    slide.dataset.slideAction = 'canvas-step';
    slide.dataset.canvasMaxStep = '2';
    slide.__canvasStep = function(dir) {
      if (dir === 'next' && step < 2) step++;
      if (dir === 'prev' && step > 0) step--;
      draw();
      return step;
    };
  }
})();
:::
```

### Example 3: Multi-Step Pipeline with Icons

**Prompt:**
```
API Gateway → Lambda → DynamoDB → S3 데이터 파이프라인
각 서비스가 순서대로 나타나고 화살표 연결
마지막에 CloudWatch 모니터링 추가
```

**Approach:** Custom JS with icon preloading + step control

**Output:**
```javascript
:::canvas js
(function() {
  const { canvas, ctx, width: W, height: H } = setupCanvas('data-pipeline', 960, 400);
  if (!canvas) return;
  let step = 0;
  const MAX_STEP = 6;

  const iconSrcs = {
    apigw: '../common/aws-icons/Arch_Amazon-API-Gateway_48.svg',
    lambda: '../common/aws-icons/Arch_AWS-Lambda_48.svg',
    dynamo: '../common/aws-icons/Arch_Amazon-DynamoDB_48.svg',
    s3: '../common/aws-icons/Arch_Amazon-Simple-Storage-Service_48.svg',
    cw: '../common/aws-icons/Arch_Amazon-CloudWatch_48.svg',
  };
  const imgs = {};
  let pending = Object.keys(iconSrcs).length;

  Object.entries(iconSrcs).forEach(([k, src]) => {
    const img = new Image();
    img.onload = () => { imgs[k] = img; if (--pending === 0) draw(); };
    img.src = src;
  });

  const nodes = [
    { key: 'apigw', label: 'API Gateway', x: 100, y: 180, step: 1 },
    { key: 'lambda', label: 'Lambda', x: 280, y: 180, step: 2 },
    { key: 'dynamo', label: 'DynamoDB', x: 460, y: 180, step: 3 },
    { key: 's3', label: 'S3', x: 640, y: 180, step: 4 },
    { key: 'cw', label: 'CloudWatch', x: 370, y: 320, step: 6 },
  ];

  function draw() {
    ctx.clearRect(0, 0, W, H);
    nodes.forEach(n => {
      if (step >= n.step && imgs[n.key]) {
        drawIcon(ctx, imgs[n.key], n.x, n.y, 48);
        drawText(ctx, n.label, n.x, n.y + 38, { size: 11, color: Colors.textSec });
      }
    });
    if (step >= 5) {
      drawArrow(ctx, 124, 180, 256, 180, Colors.accent);
      drawArrow(ctx, 304, 180, 436, 180, Colors.accent);
      drawArrow(ctx, 484, 180, 616, 180, Colors.accent);
    }
    if (step >= 6) {
      drawArrow(ctx, 280, 204, 370, 296, Colors.yellow, true);
      drawText(ctx, 'logs', 315, 245, { size: 10, color: Colors.yellow });
    }
  }

  draw();

  const slide = canvas.closest('.slide');
  if (slide) {
    slide.dataset.slideAction = 'canvas-step';
    slide.dataset.canvasMaxStep = String(MAX_STEP);
    slide.__canvasStep = function(dir) {
      if (dir === 'next' && step < MAX_STEP) step++;
      if (dir === 'prev' && step > 0) step--;
      draw();
      return step;
    };
  }
})();
:::
```

### Example 4: Failover Scenario

**Prompt:**
```
Primary-Standby 장애 조치
Step 1: Primary 활성, Standby 대기
Step 2: Primary 장애 발생
Step 3: Standby로 전환 완료
```

**Approach:** Use `CanvasPresets['failover']`

**Output:**
```javascript
:::canvas js
(function() {
  const { canvas, ctx, width: W, height: H } = setupCanvas('failover-demo', 960, 400);
  if (!canvas) return;
  let step = 0;

  const config = {
    primary: { name: 'Primary (us-east-1)', x: W * 0.25 },
    standby: { name: 'Standby (us-west-2)', x: W * 0.75 },
    failoverStep: 2
  };

  function draw() {
    CanvasPresets['failover'](ctx, config, step, W, H);
  }

  draw();

  const slide = canvas.closest('.slide');
  if (slide) {
    slide.dataset.slideAction = 'canvas-step';
    slide.dataset.canvasMaxStep = '3';
    slide.__canvasStep = function(dir) {
      if (dir === 'next' && step < 3) step++;
      if (dir === 'prev' && step > 0) step--;
      draw();
      return step;
    };
  }
})();
:::
```

### Example 5: Data Streaming with Particles

**Prompt:**
```
실시간 데이터 스트리밍 시각화
Kinesis → Lambda → OpenSearch
파티클 효과로 데이터 흐름 표현
연속 애니메이션
```

**Approach:** Custom JS with `AnimationLoop` + `ParticleSystem`

**Output:**
```javascript
:::canvas js
(function() {
  const { canvas, ctx, width: W, height: H } = setupCanvas('streaming', 960, 400);
  if (!canvas) return;

  const particles = new ParticleSystem(40, { w: W, h: H });

  const services = [
    { label: 'Kinesis', x: 120, y: H / 2, color: Colors.orange },
    { label: 'Lambda', x: W / 2, y: H / 2, color: Colors.accent },
    { label: 'OpenSearch', x: W - 120, y: H / 2, color: Colors.cyan },
  ];
  const boxW = 120, boxH = 50;

  const loop = new AnimationLoop((elapsed) => {
    ctx.clearRect(0, 0, W, H);
    particles.update();
    particles.draw(ctx);

    services.forEach(s => {
      drawBox(ctx, s.x - boxW / 2, s.y - boxH / 2, boxW, boxH, s.label, s.color);
    });

    // Animated flow arrows with pulsing
    const pulse = 0.5 + 0.5 * Math.sin(elapsed * 3);
    ctx.globalAlpha = 0.4 + 0.6 * pulse;
    drawArrow(ctx, services[0].x + boxW / 2, services[0].y,
              services[1].x - boxW / 2, services[1].y, Colors.orange);
    drawArrow(ctx, services[1].x + boxW / 2, services[1].y,
              services[2].x - boxW / 2, services[2].y, Colors.cyan);
    ctx.globalAlpha = 1;
  });

  loop.start();

  // Stop animation when slide is not visible (performance)
  const observer = new IntersectionObserver(entries => {
    entries.forEach(e => e.isIntersecting ? loop.start() : loop.stop());
  });
  observer.observe(canvas);
})();
:::
```

---

## Common Prompt Patterns

| User Keyword / Pattern | Recommended Approach |
|------------------------|----------------------|
| "A → B → C 흐름", "트래픽 흐름" | DSL with `icon` + `arrow` + `step` |
| "아키텍처 다이어그램" (static) | DSL with `box`/`icon`/`arrow`/`group` |
| "오토스케일링", "파드 스케일링" | `CanvasPresets['eks-pod-scaling']` |
| "노드 스케일링", "노드 추가" | `CanvasPresets['eks-node-scaling']` |
| "롤링 업데이트", "배포" | `CanvasPresets['rolling-update']` |
| "장애 조치", "Failover" | `CanvasPresets['failover']` |
| "서비스 간 트래픽" (with config) | `CanvasPresets['traffic-flow']` |
| "타임라인 애니메이션", "단계별 진행" | Custom JS with `TimelineAnimation` |
| "실시간", "스트리밍", "파티클" | Custom JS with `AnimationLoop` + `ParticleSystem` |
| "맥박", "펄스", "깜빡임" | Custom JS with `AnimationLoop` + `Math.sin()` |
| "커스텀 시각화" | Custom JS with `setupCanvas` + primitives |
| "차트", "chart", "그래프", "graph" | Chart.js CDN or CSS/SVG chart |
| "대시보드", "dashboard", "KPI", "메트릭" | HTML/CSS dashboard slide |
| "인포그래픽", "infographic", "시각화" | HTML/CSS infographic slide |
| "게이지", "gauge", "미터", "meter" | Canvas JS drawGauge pattern |
| "도넛", "파이", "pie", "donut" | CSS conic-gradient or Canvas |
| "스파크라인", "sparkline", "미니차트" | SVG polyline mini chart |
| "진행률", "progress", "프로그레스" | SVG/CSS progress ring/bar |
| "비교", "comparison", "vs" | Comparison slide or horizontal bar |

---

## Validation Checklist

Before finalizing generated code, verify **ALL** items. This checklist is **mandatory** — skipping any item will cause runtime failures.

### Structure (must have)
- [ ] **IIFE wrapper**: Code wrapped in `(function() { ... })();`
- [ ] **setupCanvas call**: Uses `setupCanvas('CANVAS_ID', 960, 400)` with correct canvas ID
- [ ] **Null check**: `if (!canvas) return;` after setupCanvas
- [ ] **No global pollution**: All variables inside IIFE scope

### Rendering (must have)
- [ ] **clearRect**: `ctx.clearRect(0, 0, W, H)` at start of each draw call
- [ ] **Colors reference**: Use `Colors.accent`, `Colors.textPri`, etc. — not hardcoded values
- [ ] **Canvas ID matches**: `@canvas-id` directive matches the ID in setupCanvas call
- [ ] **maxWidth**: setupCanvas handles this automatically (no manual CSS needed)

### Step Navigation (must have for step-based animations)
- [ ] **slideAction registration**: `slide.dataset.slideAction = 'canvas-step'` set on parent slide
- [ ] **canvasMaxStep**: `slide.dataset.canvasMaxStep = String(MAX_STEP)` set on parent slide
- [ ] **__canvasStep function**: `slide.__canvasStep = function(dir) { ... }` registered on parent slide
- [ ] **Direction handling**: Function handles both `'next'` and `'prev'` directions
- [ ] **Step bounds**: `step` variable bounded between 0 and MAX_STEP
- [ ] **Return value**: Function returns current step number (for framework tracking)

### Icons (when using AWS icons)
- [ ] **Icon paths**: Use `../common/aws-icons/FILENAME` relative paths
- [ ] **Icon preloading**: All icons loaded before draw, with redraw on load complete

### Agent-authored `:::canvas js` blocks
When the agent writes `:::canvas js` directly (without the converter DSL), the agent MUST follow this exact pattern for step registration:

```javascript
const slide = canvas.closest('.slide');
if (slide) {
  slide.dataset.slideAction = 'canvas-step';
  slide.dataset.canvasMaxStep = String(MAX_STEP);
  slide.__canvasStep = function(dir) {
    if (dir === 'next' && step < MAX_STEP) step++;
    if (dir === 'prev' && step > 0) step--;
    draw();
    return step;
  };
}
```

Without this registration, ↑↓ keyboard step control will NOT work on the slide.

---

## Canvas JS Chart Drawing Patterns

These patterns provide chart drawing functions using the Canvas 2D API and the existing `Colors` object. Each is a self-contained function suitable for data visualization on canvas slides.

### 1. drawBarChart — Vertical Bar Chart

```javascript
function drawBarChart(ctx, x, y, w, h, data, colors) {
  const barCount = data.length;
  const barWidth = (w - (barCount + 1) * 10) / barCount;
  const maxVal = Math.max(...data.map(d => d.value));

  // Draw grid lines
  ctx.strokeStyle = Colors.border;
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const gy = y + h - (h * i / 4);
    ctx.beginPath();
    ctx.moveTo(x, gy);
    ctx.lineTo(x + w, gy);
    ctx.stroke();
    drawText(ctx, String(Math.round(maxVal * i / 4)), x - 8, gy, { size: 10, color: Colors.textSec, align: 'right' });
  }

  // Draw bars
  data.forEach((d, i) => {
    const barH = (d.value / maxVal) * (h - 20);
    const bx = x + 10 + i * (barWidth + 10);
    const by = y + h - barH;
    ctx.fillStyle = colors[i % colors.length];
    ctx.fillRect(bx, by, barWidth, barH);
    drawText(ctx, d.label, bx + barWidth / 2, y + h + 14, { size: 10, color: Colors.textSec, align: 'center' });
  });
}
```

**Complete Example:**

```javascript
:::canvas js
(function() {
  const { canvas, ctx, width: W, height: H } = setupCanvas('bar-chart', 960, 400);
  if (!canvas) return;
  let step = 0;
  const MAX_STEP = 2;

  const data = [
    { label: 'Q1', value: 120 },
    { label: 'Q2', value: 180 },
    { label: 'Q3', value: 150 },
    { label: 'Q4', value: 220 }
  ];
  const colors = [Colors.accent, Colors.green, Colors.cyan, Colors.orange];

  function drawBarChart(ctx, x, y, w, h, data, colors) {
    const barCount = data.length;
    const barWidth = (w - (barCount + 1) * 10) / barCount;
    const maxVal = Math.max(...data.map(d => d.value));
    ctx.strokeStyle = Colors.border;
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const gy = y + h - (h * i / 4);
      ctx.beginPath();
      ctx.moveTo(x, gy);
      ctx.lineTo(x + w, gy);
      ctx.stroke();
      drawText(ctx, String(Math.round(maxVal * i / 4)), x - 8, gy, { size: 10, color: Colors.textSec, align: 'right' });
    }
    data.forEach((d, i) => {
      if (step >= 1) {
        const barH = (d.value / maxVal) * (h - 20);
        const bx = x + 10 + i * (barWidth + 10);
        const by = y + h - barH;
        ctx.fillStyle = colors[i % colors.length];
        ctx.fillRect(bx, by, barWidth, barH);
      }
      if (step >= 2) {
        const bx = x + 10 + i * (barWidth + 10);
        drawText(ctx, d.label, bx + barWidth / 2, y + h + 14, { size: 10, color: Colors.textSec, align: 'center' });
      }
    });
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    drawText(ctx, 'Quarterly Revenue', W / 2, 30, { size: 16, color: Colors.textPri, align: 'center' });
    drawBarChart(ctx, 100, 60, W - 200, H - 120, data, colors);
  }

  draw();

  const slide = canvas.closest('.slide');
  if (slide) {
    slide.dataset.slideAction = 'canvas-step';
    slide.dataset.canvasMaxStep = String(MAX_STEP);
    slide.__canvasStep = function(dir) {
      if (dir === 'next' && step < MAX_STEP) step++;
      if (dir === 'prev' && step > 0) step--;
      draw();
      return step;
    };
  }
})();
:::
```

#### Animated Variant: Bar Growth Animation

Bars grow from bottom to target height with eased timing:

```javascript
:::canvas js
(function() {
  const { canvas, ctx, width: W, height: H } = setupCanvas('bar-chart-animated', 960, 400);
  if (!canvas) return;

  const data = [
    { label: 'Q1', value: 120 },
    { label: 'Q2', value: 180 },
    { label: 'Q3', value: 150 },
    { label: 'Q4', value: 220 }
  ];
  const colors = [Colors.accent, Colors.green, Colors.cyan, Colors.orange];

  let animationProgress = 0;
  let animationId = null;

  function drawAnimatedBarChart(ctx, x, y, w, h, data, colors, progress) {
    const barCount = data.length;
    const barWidth = (w - (barCount + 1) * 10) / barCount;
    const maxVal = Math.max(...data.map(d => d.value));

    // Easing function (ease-out cubic)
    const eased = 1 - Math.pow(1 - progress, 3);

    // Draw grid lines
    ctx.strokeStyle = Colors.border;
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const gy = y + h - (h * i / 4);
      ctx.beginPath();
      ctx.moveTo(x, gy);
      ctx.lineTo(x + w, gy);
      ctx.stroke();
      drawText(ctx, String(Math.round(maxVal * i / 4)), x - 8, gy, { size: 10, color: Colors.textSec, align: 'right' });
    }

    // Draw bars with animated height
    data.forEach((d, i) => {
      const targetBarH = (d.value / maxVal) * (h - 20);
      const barH = targetBarH * eased;
      const bx = x + 10 + i * (barWidth + 10);
      const by = y + h - barH;
      ctx.fillStyle = colors[i % colors.length];
      ctx.fillRect(bx, by, barWidth, barH);
      drawText(ctx, d.label, bx + barWidth / 2, y + h + 14, { size: 10, color: Colors.textSec, align: 'center' });
    });
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    drawText(ctx, 'Quarterly Revenue', W / 2, 30, { size: 16, color: Colors.textPri, align: 'center' });
    drawAnimatedBarChart(ctx, 100, 60, W - 200, H - 120, data, colors, animationProgress);
  }

  function animate() {
    animationProgress = Math.min(animationProgress + 0.02, 1);
    draw();
    if (animationProgress < 1) {
      animationId = requestAnimationFrame(animate);
    }
  }

  // Start animation when slide becomes visible
  const observer = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting && animationProgress === 0) {
        animate();
      }
    });
  });
  observer.observe(canvas);

  draw(); // Initial render (empty bars)
})();
:::
```

### 2. drawHorizontalBar — Horizontal Bar Chart

```javascript
function drawHorizontalBar(ctx, x, y, w, h, data, colors) {
  const barCount = data.length;
  const barHeight = (h - (barCount + 1) * 8) / barCount;
  const maxVal = Math.max(...data.map(d => d.value));

  // Draw grid lines
  ctx.strokeStyle = Colors.border;
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const gx = x + (w * i / 4);
    ctx.beginPath();
    ctx.moveTo(gx, y);
    ctx.lineTo(gx, y + h);
    ctx.stroke();
    drawText(ctx, String(Math.round(maxVal * i / 4)), gx, y + h + 14, { size: 10, color: Colors.textSec, align: 'center' });
  }

  // Draw bars
  data.forEach((d, i) => {
    const barW = (d.value / maxVal) * w;
    const by = y + 8 + i * (barHeight + 8);
    ctx.fillStyle = colors[i % colors.length];
    ctx.fillRect(x, by, barW, barHeight);
    drawText(ctx, d.label, x - 8, by + barHeight / 2, { size: 10, color: Colors.textSec, align: 'right', baseline: 'middle' });
  });
}
```

**Complete Example:**

```javascript
:::canvas js
(function() {
  const { canvas, ctx, width: W, height: H } = setupCanvas('hbar-chart', 960, 400);
  if (!canvas) return;
  let step = 0;
  const MAX_STEP = 2;

  const data = [
    { label: 'Lambda', value: 45 },
    { label: 'EC2', value: 120 },
    { label: 'S3', value: 80 },
    { label: 'RDS', value: 95 }
  ];
  const colors = [Colors.accent, Colors.orange, Colors.green, Colors.cyan];

  function drawHorizontalBar(ctx, x, y, w, h, data, colors) {
    const barCount = data.length;
    const barHeight = (h - (barCount + 1) * 8) / barCount;
    const maxVal = Math.max(...data.map(d => d.value));
    ctx.strokeStyle = Colors.border;
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const gx = x + (w * i / 4);
      ctx.beginPath();
      ctx.moveTo(gx, y);
      ctx.lineTo(gx, y + h);
      ctx.stroke();
      if (step >= 2) {
        drawText(ctx, String(Math.round(maxVal * i / 4)), gx, y + h + 14, { size: 10, color: Colors.textSec, align: 'center' });
      }
    }
    data.forEach((d, i) => {
      if (step >= 1) {
        const barW = (d.value / maxVal) * w;
        const by = y + 8 + i * (barHeight + 8);
        ctx.fillStyle = colors[i % colors.length];
        ctx.fillRect(x, by, barW, barHeight);
        drawText(ctx, d.label, x - 8, by + barHeight / 2, { size: 10, color: Colors.textSec, align: 'right', baseline: 'middle' });
      }
    });
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    drawText(ctx, 'Service Cost Comparison', W / 2, 30, { size: 16, color: Colors.textPri, align: 'center' });
    drawHorizontalBar(ctx, 150, 60, W - 200, H - 120, data, colors);
  }

  draw();

  const slide = canvas.closest('.slide');
  if (slide) {
    slide.dataset.slideAction = 'canvas-step';
    slide.dataset.canvasMaxStep = String(MAX_STEP);
    slide.__canvasStep = function(dir) {
      if (dir === 'next' && step < MAX_STEP) step++;
      if (dir === 'prev' && step > 0) step--;
      draw();
      return step;
    };
  }
})();
:::
```

### 3. drawPieChart — Pie/Donut Chart

```javascript
function drawPieChart(ctx, cx, cy, radius, segments, donut = false) {
  let startAngle = -Math.PI / 2;
  const total = segments.reduce((sum, s) => sum + s.value, 0);
  const innerRadius = donut ? radius * 0.6 : 0;

  segments.forEach(seg => {
    const sliceAngle = (seg.value / total) * Math.PI * 2;
    ctx.beginPath();
    ctx.moveTo(cx + innerRadius * Math.cos(startAngle), cy + innerRadius * Math.sin(startAngle));
    ctx.arc(cx, cy, radius, startAngle, startAngle + sliceAngle);
    ctx.arc(cx, cy, innerRadius, startAngle + sliceAngle, startAngle, true);
    ctx.closePath();
    ctx.fillStyle = seg.color;
    ctx.fill();

    // Draw label
    const midAngle = startAngle + sliceAngle / 2;
    const labelRadius = radius + 20;
    const lx = cx + labelRadius * Math.cos(midAngle);
    const ly = cy + labelRadius * Math.sin(midAngle);
    drawText(ctx, `${seg.label} (${Math.round(seg.value / total * 100)}%)`, lx, ly, {
      size: 11, color: Colors.textSec, align: midAngle > Math.PI / 2 && midAngle < Math.PI * 1.5 ? 'right' : 'left'
    });

    startAngle += sliceAngle;
  });
}
```

**Complete Example:**

```javascript
:::canvas js
(function() {
  const { canvas, ctx, width: W, height: H } = setupCanvas('pie-chart', 960, 400);
  if (!canvas) return;
  let step = 0;
  const MAX_STEP = 2;

  const segments = [
    { label: 'Compute', value: 45, color: Colors.accent },
    { label: 'Storage', value: 25, color: Colors.green },
    { label: 'Network', value: 15, color: Colors.cyan },
    { label: 'Database', value: 15, color: Colors.orange }
  ];

  function drawPieChart(ctx, cx, cy, radius, segments, donut = false) {
    let startAngle = -Math.PI / 2;
    const total = segments.reduce((sum, s) => sum + s.value, 0);
    const innerRadius = donut ? radius * 0.6 : 0;
    segments.forEach((seg, i) => {
      if (step >= 1) {
        const sliceAngle = (seg.value / total) * Math.PI * 2;
        ctx.beginPath();
        ctx.moveTo(cx + innerRadius * Math.cos(startAngle), cy + innerRadius * Math.sin(startAngle));
        ctx.arc(cx, cy, radius, startAngle, startAngle + sliceAngle);
        ctx.arc(cx, cy, innerRadius, startAngle + sliceAngle, startAngle, true);
        ctx.closePath();
        ctx.fillStyle = seg.color;
        ctx.fill();
        if (step >= 2) {
          const midAngle = startAngle + sliceAngle / 2;
          const labelRadius = radius + 20;
          const lx = cx + labelRadius * Math.cos(midAngle);
          const ly = cy + labelRadius * Math.sin(midAngle);
          drawText(ctx, `${seg.label} (${Math.round(seg.value / total * 100)}%)`, lx, ly, {
            size: 11, color: Colors.textSec, align: midAngle > Math.PI / 2 && midAngle < Math.PI * 1.5 ? 'right' : 'left'
          });
        }
        startAngle += sliceAngle;
      }
    });
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    drawText(ctx, 'Cost Distribution', W / 2, 30, { size: 16, color: Colors.textPri, align: 'center' });
    drawPieChart(ctx, W / 2, H / 2 + 20, 120, segments, true);
  }

  draw();

  const slide = canvas.closest('.slide');
  if (slide) {
    slide.dataset.slideAction = 'canvas-step';
    slide.dataset.canvasMaxStep = String(MAX_STEP);
    slide.__canvasStep = function(dir) {
      if (dir === 'next' && step < MAX_STEP) step++;
      if (dir === 'prev' && step > 0) step--;
      draw();
      return step;
    };
  }
})();
:::
```

#### Animated Variant: Pie Sweep Animation

Pie slices animate from 0 to 360 degrees with a sweep effect:

```javascript
:::canvas js
(function() {
  const { canvas, ctx, width: W, height: H } = setupCanvas('pie-chart-animated', 960, 400);
  if (!canvas) return;

  const segments = [
    { label: 'Compute', value: 45, color: Colors.accent },
    { label: 'Storage', value: 25, color: Colors.green },
    { label: 'Network', value: 15, color: Colors.cyan },
    { label: 'Database', value: 15, color: Colors.orange }
  ];

  let animationProgress = 0;

  function drawAnimatedPieChart(ctx, cx, cy, radius, segments, donut, progress) {
    const total = segments.reduce((sum, s) => sum + s.value, 0);
    const innerRadius = donut ? radius * 0.6 : 0;

    // Easing function (ease-out cubic)
    const eased = 1 - Math.pow(1 - progress, 3);
    const maxAngle = Math.PI * 2 * eased;

    let startAngle = -Math.PI / 2;
    let accumulatedAngle = 0;

    segments.forEach(seg => {
      const sliceAngle = (seg.value / total) * Math.PI * 2;
      const visibleAngle = Math.min(sliceAngle, Math.max(0, maxAngle - accumulatedAngle));

      if (visibleAngle > 0) {
        ctx.beginPath();
        ctx.moveTo(cx + innerRadius * Math.cos(startAngle), cy + innerRadius * Math.sin(startAngle));
        ctx.arc(cx, cy, radius, startAngle, startAngle + visibleAngle);
        ctx.arc(cx, cy, innerRadius, startAngle + visibleAngle, startAngle, true);
        ctx.closePath();
        ctx.fillStyle = seg.color;
        ctx.fill();

        // Draw label only when segment is fully visible
        if (accumulatedAngle + sliceAngle <= maxAngle) {
          const midAngle = startAngle + sliceAngle / 2;
          const labelRadius = radius + 20;
          const lx = cx + labelRadius * Math.cos(midAngle);
          const ly = cy + labelRadius * Math.sin(midAngle);
          drawText(ctx, `${seg.label} (${Math.round(seg.value / total * 100)}%)`, lx, ly, {
            size: 11, color: Colors.textSec, align: midAngle > Math.PI / 2 && midAngle < Math.PI * 1.5 ? 'right' : 'left'
          });
        }
      }

      accumulatedAngle += sliceAngle;
      startAngle += sliceAngle;
    });
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    drawText(ctx, 'Cost Distribution', W / 2, 30, { size: 16, color: Colors.textPri, align: 'center' });
    drawAnimatedPieChart(ctx, W / 2, H / 2 + 20, 120, segments, true, animationProgress);
  }

  function animate() {
    animationProgress = Math.min(animationProgress + 0.02, 1);
    draw();
    if (animationProgress < 1) {
      requestAnimationFrame(animate);
    }
  }

  // Start animation when slide becomes visible
  const observer = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting && animationProgress === 0) {
        animate();
      }
    });
  });
  observer.observe(canvas);

  draw();
})();
:::
```

### 4. drawLineChart — Line Chart with Area Fill

```javascript
function drawLineChart(ctx, x, y, w, h, points, color) {
  const maxVal = Math.max(...points.map(p => p.value));
  const minVal = Math.min(...points.map(p => p.value));
  const range = maxVal - minVal || 1;
  const stepX = w / (points.length - 1);

  // Draw grid lines
  ctx.strokeStyle = Colors.border;
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const gy = y + h - (h * i / 4);
    ctx.beginPath();
    ctx.moveTo(x, gy);
    ctx.lineTo(x + w, gy);
    ctx.stroke();
    const val = minVal + (range * i / 4);
    drawText(ctx, val.toFixed(0), x - 8, gy, { size: 10, color: Colors.textSec, align: 'right' });
  }

  // Draw area fill
  ctx.beginPath();
  ctx.moveTo(x, y + h);
  points.forEach((p, i) => {
    const px = x + i * stepX;
    const py = y + h - ((p.value - minVal) / range) * h;
    ctx.lineTo(px, py);
  });
  ctx.lineTo(x + w, y + h);
  ctx.closePath();
  ctx.fillStyle = color + '33'; // 20% opacity
  ctx.fill();

  // Draw line
  ctx.beginPath();
  points.forEach((p, i) => {
    const px = x + i * stepX;
    const py = y + h - ((p.value - minVal) / range) * h;
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  });
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.stroke();

  // Draw points and labels
  points.forEach((p, i) => {
    const px = x + i * stepX;
    const py = y + h - ((p.value - minVal) / range) * h;
    ctx.beginPath();
    ctx.arc(px, py, 4, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
    drawText(ctx, p.label, px, y + h + 14, { size: 10, color: Colors.textSec, align: 'center' });
  });
}
```

**Complete Example:**

```javascript
:::canvas js
(function() {
  const { canvas, ctx, width: W, height: H } = setupCanvas('line-chart', 960, 400);
  if (!canvas) return;
  let step = 0;
  const MAX_STEP = 3;

  const points = [
    { label: 'Jan', value: 100 },
    { label: 'Feb', value: 120 },
    { label: 'Mar', value: 115 },
    { label: 'Apr', value: 140 },
    { label: 'May', value: 160 },
    { label: 'Jun', value: 155 }
  ];

  function drawLineChart(ctx, x, y, w, h, points, color) {
    const maxVal = Math.max(...points.map(p => p.value));
    const minVal = Math.min(...points.map(p => p.value));
    const range = maxVal - minVal || 1;
    const stepX = w / (points.length - 1);
    ctx.strokeStyle = Colors.border;
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const gy = y + h - (h * i / 4);
      ctx.beginPath();
      ctx.moveTo(x, gy);
      ctx.lineTo(x + w, gy);
      ctx.stroke();
      const val = minVal + (range * i / 4);
      drawText(ctx, val.toFixed(0), x - 8, gy, { size: 10, color: Colors.textSec, align: 'right' });
    }
    if (step >= 2) {
      ctx.beginPath();
      ctx.moveTo(x, y + h);
      points.forEach((p, i) => {
        const px = x + i * stepX;
        const py = y + h - ((p.value - minVal) / range) * h;
        ctx.lineTo(px, py);
      });
      ctx.lineTo(x + w, y + h);
      ctx.closePath();
      ctx.fillStyle = color + '33';
      ctx.fill();
    }
    if (step >= 1) {
      ctx.beginPath();
      points.forEach((p, i) => {
        const px = x + i * stepX;
        const py = y + h - ((p.value - minVal) / range) * h;
        if (i === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      });
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.stroke();
    }
    if (step >= 3) {
      points.forEach((p, i) => {
        const px = x + i * stepX;
        const py = y + h - ((p.value - minVal) / range) * h;
        ctx.beginPath();
        ctx.arc(px, py, 4, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        drawText(ctx, p.label, px, y + h + 14, { size: 10, color: Colors.textSec, align: 'center' });
      });
    }
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    drawText(ctx, 'Monthly Requests (millions)', W / 2, 30, { size: 16, color: Colors.textPri, align: 'center' });
    drawLineChart(ctx, 100, 60, W - 200, H - 120, points, Colors.accent);
  }

  draw();

  const slide = canvas.closest('.slide');
  if (slide) {
    slide.dataset.slideAction = 'canvas-step';
    slide.dataset.canvasMaxStep = String(MAX_STEP);
    slide.__canvasStep = function(dir) {
      if (dir === 'next' && step < MAX_STEP) step++;
      if (dir === 'prev' && step > 0) step--;
      draw();
      return step;
    };
  }
})();
:::
```

#### Animated Variant: Left-to-Right Line Drawing

Line reveals from left to right using a clip path:

```javascript
:::canvas js
(function() {
  const { canvas, ctx, width: W, height: H } = setupCanvas('line-chart-animated', 960, 400);
  if (!canvas) return;

  const points = [
    { label: 'Jan', value: 100 },
    { label: 'Feb', value: 120 },
    { label: 'Mar', value: 115 },
    { label: 'Apr', value: 140 },
    { label: 'May', value: 160 },
    { label: 'Jun', value: 155 }
  ];

  const chartArea = { left: 100, top: 60, width: W - 200, height: H - 120 };
  let animationProgress = 0;

  function drawAnimatedLineChart(ctx, x, y, w, h, points, color, progress) {
    const maxVal = Math.max(...points.map(p => p.value));
    const minVal = Math.min(...points.map(p => p.value));
    const range = maxVal - minVal || 1;
    const stepX = w / (points.length - 1);

    // Easing function (ease-out quad)
    const eased = 1 - Math.pow(1 - progress, 2);
    const clipWidth = w * eased;

    // Draw grid lines (always visible)
    ctx.strokeStyle = Colors.border;
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const gy = y + h - (h * i / 4);
      ctx.beginPath();
      ctx.moveTo(x, gy);
      ctx.lineTo(x + w, gy);
      ctx.stroke();
      const val = minVal + (range * i / 4);
      drawText(ctx, val.toFixed(0), x - 8, gy, { size: 10, color: Colors.textSec, align: 'right' });
    }

    // Draw labels
    points.forEach((p, i) => {
      const px = x + i * stepX;
      drawText(ctx, p.label, px, y + h + 14, { size: 10, color: Colors.textSec, align: 'center' });
    });

    // Clip and draw area fill + line
    ctx.save();
    ctx.beginPath();
    ctx.rect(x, y - 10, clipWidth, h + 20);
    ctx.clip();

    // Area fill
    ctx.beginPath();
    ctx.moveTo(x, y + h);
    points.forEach((p, i) => {
      const px = x + i * stepX;
      const py = y + h - ((p.value - minVal) / range) * h;
      ctx.lineTo(px, py);
    });
    ctx.lineTo(x + w, y + h);
    ctx.closePath();
    ctx.fillStyle = color + '33';
    ctx.fill();

    // Line
    ctx.beginPath();
    points.forEach((p, i) => {
      const px = x + i * stepX;
      const py = y + h - ((p.value - minVal) / range) * h;
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    });
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.stroke();

    // Points
    points.forEach((p, i) => {
      const px = x + i * stepX;
      const py = y + h - ((p.value - minVal) / range) * h;
      ctx.beginPath();
      ctx.arc(px, py, 4, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
    });

    ctx.restore();
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    drawText(ctx, 'Monthly Requests (millions)', W / 2, 30, { size: 16, color: Colors.textPri, align: 'center' });
    drawAnimatedLineChart(ctx, chartArea.left, chartArea.top, chartArea.width, chartArea.height, points, Colors.accent, animationProgress);
  }

  function animate() {
    animationProgress = Math.min(animationProgress + 0.015, 1);
    draw();
    if (animationProgress < 1) {
      requestAnimationFrame(animate);
    }
  }

  // Start animation when slide becomes visible
  const observer = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting && animationProgress === 0) {
        animate();
      }
    });
  });
  observer.observe(canvas);

  draw();
})();
:::
```

### 5. drawGauge — Semicircle Gauge

```javascript
function drawGauge(ctx, cx, cy, radius, value, max, color) {
  const startAngle = Math.PI;
  const endAngle = Math.PI * 2;
  const valueAngle = startAngle + (value / max) * Math.PI;

  // Draw background arc
  ctx.beginPath();
  ctx.arc(cx, cy, radius, startAngle, endAngle);
  ctx.strokeStyle = Colors.border;
  ctx.lineWidth = 20;
  ctx.lineCap = 'round';
  ctx.stroke();

  // Draw value arc
  ctx.beginPath();
  ctx.arc(cx, cy, radius, startAngle, valueAngle);
  ctx.strokeStyle = color;
  ctx.lineWidth = 20;
  ctx.lineCap = 'round';
  ctx.stroke();

  // Draw value text
  drawText(ctx, `${value}`, cx, cy - 10, { size: 32, color: Colors.textPri, align: 'center', weight: 'bold' });
  drawText(ctx, `/ ${max}`, cx, cy + 20, { size: 14, color: Colors.textSec, align: 'center' });
}
```

**Complete Example:**

```javascript
:::canvas js
(function() {
  const { canvas, ctx, width: W, height: H } = setupCanvas('gauge-chart', 960, 400);
  if (!canvas) return;
  let step = 0;
  const MAX_STEP = 3;

  const gauges = [
    { label: 'CPU', value: 72, max: 100, color: Colors.green, cx: W * 0.25 },
    { label: 'Memory', value: 85, max: 100, color: Colors.yellow, cx: W * 0.5 },
    { label: 'Disk', value: 45, max: 100, color: Colors.accent, cx: W * 0.75 }
  ];

  function drawGauge(ctx, cx, cy, radius, value, max, color) {
    const startAngle = Math.PI;
    const endAngle = Math.PI * 2;
    const valueAngle = startAngle + (value / max) * Math.PI;
    ctx.beginPath();
    ctx.arc(cx, cy, radius, startAngle, endAngle);
    ctx.strokeStyle = Colors.border;
    ctx.lineWidth = 20;
    ctx.lineCap = 'round';
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(cx, cy, radius, startAngle, valueAngle);
    ctx.strokeStyle = color;
    ctx.lineWidth = 20;
    ctx.lineCap = 'round';
    ctx.stroke();
    drawText(ctx, `${value}`, cx, cy - 10, { size: 32, color: Colors.textPri, align: 'center', weight: 'bold' });
    drawText(ctx, `/ ${max}`, cx, cy + 20, { size: 14, color: Colors.textSec, align: 'center' });
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    drawText(ctx, 'System Metrics', W / 2, 30, { size: 16, color: Colors.textPri, align: 'center' });
    gauges.forEach((g, i) => {
      if (step >= i + 1) {
        drawGauge(ctx, g.cx, H / 2 + 40, 80, g.value, g.max, g.color);
        drawText(ctx, g.label, g.cx, H / 2 + 140, { size: 14, color: Colors.textSec, align: 'center' });
      }
    });
  }

  draw();

  const slide = canvas.closest('.slide');
  if (slide) {
    slide.dataset.slideAction = 'canvas-step';
    slide.dataset.canvasMaxStep = String(MAX_STEP);
    slide.__canvasStep = function(dir) {
      if (dir === 'next' && step < MAX_STEP) step++;
      if (dir === 'prev' && step > 0) step--;
      draw();
      return step;
    };
  }
})();
:::
```

#### Animated Variant: Gauge Needle Sweep

Gauge arc sweeps from 0 to target value with animated number counter:

```javascript
:::canvas js
(function() {
  const { canvas, ctx, width: W, height: H } = setupCanvas('gauge-animated', 960, 400);
  if (!canvas) return;

  const gauges = [
    { label: 'CPU', value: 72, max: 100, color: Colors.green, cx: W * 0.25 },
    { label: 'Memory', value: 85, max: 100, color: Colors.yellow, cx: W * 0.5 },
    { label: 'Disk', value: 45, max: 100, color: Colors.accent, cx: W * 0.75 }
  ];

  let animationProgress = 0;

  function drawAnimatedGauge(ctx, cx, cy, radius, targetValue, max, color, progress) {
    const startAngle = Math.PI;
    const endAngle = Math.PI * 2;

    // Easing function (ease-out quad)
    const eased = 1 - Math.pow(1 - progress, 2);
    const currentValue = targetValue * eased;
    const valueAngle = startAngle + (currentValue / max) * Math.PI;

    // Draw background arc
    ctx.beginPath();
    ctx.arc(cx, cy, radius, startAngle, endAngle);
    ctx.strokeStyle = Colors.border;
    ctx.lineWidth = 20;
    ctx.lineCap = 'round';
    ctx.stroke();

    // Draw animated value arc
    ctx.beginPath();
    ctx.arc(cx, cy, radius, startAngle, valueAngle);
    ctx.strokeStyle = color;
    ctx.lineWidth = 20;
    ctx.lineCap = 'round';
    ctx.stroke();

    // Draw animated value text
    drawText(ctx, `${Math.round(currentValue)}`, cx, cy - 10, { size: 32, color: Colors.textPri, align: 'center', weight: 'bold' });
    drawText(ctx, `/ ${max}`, cx, cy + 20, { size: 14, color: Colors.textSec, align: 'center' });
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    drawText(ctx, 'System Metrics', W / 2, 30, { size: 16, color: Colors.textPri, align: 'center' });
    gauges.forEach(g => {
      drawAnimatedGauge(ctx, g.cx, H / 2 + 40, 80, g.value, g.max, g.color, animationProgress);
      drawText(ctx, g.label, g.cx, H / 2 + 140, { size: 14, color: Colors.textSec, align: 'center' });
    });
  }

  function animate() {
    animationProgress = Math.min(animationProgress + 0.02, 1);
    draw();
    if (animationProgress < 1) {
      requestAnimationFrame(animate);
    }
  }

  // Start animation when slide becomes visible
  const observer = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting && animationProgress === 0) {
        animate();
      }
    });
  });
  observer.observe(canvas);

  draw();
})();
:::
```

### 6. drawSparkline — Mini Line Chart

```javascript
function drawSparkline(ctx, x, y, w, h, data, color) {
  const maxVal = Math.max(...data);
  const minVal = Math.min(...data);
  const range = maxVal - minVal || 1;
  const stepX = w / (data.length - 1);

  ctx.beginPath();
  data.forEach((val, i) => {
    const px = x + i * stepX;
    const py = y + h - ((val - minVal) / range) * h;
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  });
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.stroke();

  // Draw end point
  const lastX = x + w;
  const lastY = y + h - ((data[data.length - 1] - minVal) / range) * h;
  ctx.beginPath();
  ctx.arc(lastX, lastY, 3, 0, Math.PI * 2);
  ctx.fillStyle = color;
  ctx.fill();
}
```

**Complete Example:**

```javascript
:::canvas js
(function() {
  const { canvas, ctx, width: W, height: H } = setupCanvas('sparkline-chart', 960, 400);
  if (!canvas) return;
  let step = 0;
  const MAX_STEP = 3;

  const metrics = [
    { label: 'Requests/sec', data: [120, 135, 128, 142, 155, 148, 160], color: Colors.accent },
    { label: 'Latency (ms)', data: [45, 42, 48, 44, 41, 43, 40], color: Colors.green },
    { label: 'Error Rate (%)', data: [0.5, 0.8, 0.6, 1.2, 0.9, 0.7, 0.4], color: Colors.red }
  ];

  function drawSparkline(ctx, x, y, w, h, data, color) {
    const maxVal = Math.max(...data);
    const minVal = Math.min(...data);
    const range = maxVal - minVal || 1;
    const stepX = w / (data.length - 1);
    ctx.beginPath();
    data.forEach((val, i) => {
      const px = x + i * stepX;
      const py = y + h - ((val - minVal) / range) * h;
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    });
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.stroke();
    const lastX = x + w;
    const lastY = y + h - ((data[data.length - 1] - minVal) / range) * h;
    ctx.beginPath();
    ctx.arc(lastX, lastY, 3, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    drawText(ctx, 'Service Metrics', W / 2, 30, { size: 16, color: Colors.textPri, align: 'center' });
    metrics.forEach((m, i) => {
      if (step >= i + 1) {
        const rowY = 80 + i * 100;
        drawText(ctx, m.label, 100, rowY + 20, { size: 12, color: Colors.textSec, align: 'left' });
        drawText(ctx, String(m.data[m.data.length - 1]), W - 100, rowY + 20, { size: 14, color: m.color, align: 'right', weight: 'bold' });
        drawSparkline(ctx, 250, rowY, 400, 40, m.data, m.color);
      }
    });
  }

  draw();

  const slide = canvas.closest('.slide');
  if (slide) {
    slide.dataset.slideAction = 'canvas-step';
    slide.dataset.canvasMaxStep = String(MAX_STEP);
    slide.__canvasStep = function(dir) {
      if (dir === 'next' && step < MAX_STEP) step++;
      if (dir === 'prev' && step > 0) step--;
      draw();
      return step;
    };
  }
})();
:::
```

### 7. drawProgressRing — Circular Progress

```javascript
function drawProgressRing(ctx, cx, cy, radius, percent, color) {
  const startAngle = -Math.PI / 2;
  const endAngle = startAngle + (percent / 100) * Math.PI * 2;

  // Draw background ring
  ctx.beginPath();
  ctx.arc(cx, cy, radius, 0, Math.PI * 2);
  ctx.strokeStyle = Colors.border;
  ctx.lineWidth = 12;
  ctx.stroke();

  // Draw progress arc
  ctx.beginPath();
  ctx.arc(cx, cy, radius, startAngle, endAngle);
  ctx.strokeStyle = color;
  ctx.lineWidth = 12;
  ctx.lineCap = 'round';
  ctx.stroke();

  // Draw percentage text
  drawText(ctx, `${percent}%`, cx, cy, { size: 20, color: Colors.textPri, align: 'center', baseline: 'middle', weight: 'bold' });
}
```

**Complete Example:**

```javascript
:::canvas js
(function() {
  const { canvas, ctx, width: W, height: H } = setupCanvas('progress-ring', 960, 400);
  if (!canvas) return;
  let step = 0;
  const MAX_STEP = 4;

  const rings = [
    { label: 'Deployment', percent: 100, color: Colors.green, cx: W * 0.2 },
    { label: 'Testing', percent: 75, color: Colors.accent, cx: W * 0.4 },
    { label: 'Review', percent: 50, color: Colors.yellow, cx: W * 0.6 },
    { label: 'Release', percent: 25, color: Colors.cyan, cx: W * 0.8 }
  ];

  function drawProgressRing(ctx, cx, cy, radius, percent, color) {
    const startAngle = -Math.PI / 2;
    const endAngle = startAngle + (percent / 100) * Math.PI * 2;
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.strokeStyle = Colors.border;
    ctx.lineWidth = 12;
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(cx, cy, radius, startAngle, endAngle);
    ctx.strokeStyle = color;
    ctx.lineWidth = 12;
    ctx.lineCap = 'round';
    ctx.stroke();
    drawText(ctx, `${percent}%`, cx, cy, { size: 20, color: Colors.textPri, align: 'center', baseline: 'middle', weight: 'bold' });
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    drawText(ctx, 'Pipeline Progress', W / 2, 30, { size: 16, color: Colors.textPri, align: 'center' });
    rings.forEach((r, i) => {
      if (step >= i + 1) {
        drawProgressRing(ctx, r.cx, H / 2, 60, r.percent, r.color);
        drawText(ctx, r.label, r.cx, H / 2 + 90, { size: 12, color: Colors.textSec, align: 'center' });
      }
    });
  }

  draw();

  const slide = canvas.closest('.slide');
  if (slide) {
    slide.dataset.slideAction = 'canvas-step';
    slide.dataset.canvasMaxStep = String(MAX_STEP);
    slide.__canvasStep = function(dir) {
      if (dir === 'next' && step < MAX_STEP) step++;
      if (dir === 'prev' && step > 0) step--;
      draw();
      return step;
    };
  }
})();
:::
```

#### Animated Variant: Progress Ring Fill Animation

Progress rings animate with stroke fill effect (stroke-dashoffset transition):

```javascript
:::canvas js
(function() {
  const { canvas, ctx, width: W, height: H } = setupCanvas('progress-ring-animated', 960, 400);
  if (!canvas) return;

  const rings = [
    { label: 'Deployment', percent: 100, color: Colors.green, cx: W * 0.2 },
    { label: 'Testing', percent: 75, color: Colors.accent, cx: W * 0.4 },
    { label: 'Review', percent: 50, color: Colors.yellow, cx: W * 0.6 },
    { label: 'Release', percent: 25, color: Colors.cyan, cx: W * 0.8 }
  ];

  let animationProgress = 0;

  function drawAnimatedProgressRing(ctx, cx, cy, radius, targetPercent, color, progress) {
    const startAngle = -Math.PI / 2;

    // Easing function (ease-out cubic)
    const eased = 1 - Math.pow(1 - progress, 3);
    const currentPercent = targetPercent * eased;
    const endAngle = startAngle + (currentPercent / 100) * Math.PI * 2;

    // Draw background ring
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.strokeStyle = Colors.border;
    ctx.lineWidth = 12;
    ctx.stroke();

    // Draw animated progress arc
    ctx.beginPath();
    ctx.arc(cx, cy, radius, startAngle, endAngle);
    ctx.strokeStyle = color;
    ctx.lineWidth = 12;
    ctx.lineCap = 'round';
    ctx.stroke();

    // Draw animated percentage text
    drawText(ctx, `${Math.round(currentPercent)}%`, cx, cy, { size: 20, color: Colors.textPri, align: 'center', baseline: 'middle', weight: 'bold' });
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    drawText(ctx, 'Pipeline Progress', W / 2, 30, { size: 16, color: Colors.textPri, align: 'center' });
    rings.forEach(r => {
      drawAnimatedProgressRing(ctx, r.cx, H / 2, 60, r.percent, r.color, animationProgress);
      drawText(ctx, r.label, r.cx, H / 2 + 90, { size: 12, color: Colors.textSec, align: 'center' });
    });
  }

  function animate() {
    animationProgress = Math.min(animationProgress + 0.02, 1);
    draw();
    if (animationProgress < 1) {
      requestAnimationFrame(animate);
    }
  }

  // Start animation when slide becomes visible
  const observer = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting && animationProgress === 0) {
        animate();
      }
    });
  });
  observer.observe(canvas);

  draw();
})();
:::
```
