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
└── Complex custom visualization?
    └── Custom JS with setupCanvas + drawing primitives
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
