---
sidebar_position: 3
title: "Animated Diagram"
---

# Animated Diagram Skill

Create dynamic animated diagrams using SVG with SMIL animations. Produces self-contained HTML files with traffic flow visualizations, pulsing effects, interactive legends, and responsive scaling.

## Trigger Keywords

Activated by the following keywords:
- "animated diagram", "traffic flow"
- "animated architecture", "dynamic diagram"
- "SMIL animation"

## Use Cases

- Traffic flow visualization through AWS services
- Service interaction diagrams with animated connections
- Deployment pipelines with step-by-step animation
- Real-time monitoring dashboards with animated status indicators
- **Interactive scenarios** — Scaling (EKS, ASG), Blue/Green deployment, failover simulation (button-driven state transitions)

## Provided Resources

### references/

| Reference Doc | Description |
|---------------|-------------|
| `smil-animation-guide.md` | SMIL animation syntax and patterns |
| `aws-diagram-patterns.md` | AWS architecture color coding and layout conventions |

### templates/

| Template | Description |
|----------|-------------|
| `traffic-flow.html` | SMIL traffic flow template (with legend toggle) |
| `interactive-scaling.html` | Interactive EKS hybrid node bursting (Scale Out/In buttons, JavaScript + CSS transitions) |

---

## Architecture

Each animated diagram is a self-contained HTML file with three layers:

```
┌─────────────────────────────────────────────┐
│              HTML Wrapper                    │
│  ┌───────────────────────────────────────┐  │
│  │         Background Layer              │  │
│  │   (Draw.io PNG or inline SVG)         │  │
│  ├───────────────────────────────────────┤  │
│  │         Animation Layer               │  │
│  │   (SVG with SMIL animations)          │  │
│  ├───────────────────────────────────────┤  │
│  │         Interactive Legend             │  │
│  │   (JS toggle for animation groups)    │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

---

## Color Standards

| Traffic Type | Color | Hex |
|--------------|-------|-----|
| Outbound | Red | `#DD344C` |
| Inbound | Blue | `#147EBA` |
| AWS Internal | Orange | `#FF9900` |
| Success/Active | Green | `#1B660F` |
| Warning | Yellow | `#F2C94C` |
| Background | Squid Ink | `#232F3E` |

---

## SMIL Animation Patterns

### Traffic Dots (animateMotion)

```xml
<svg viewBox="0 0 1600 900">
  <!-- Path definition -->
  <path id="path-user-to-alb" d="M 100,450 L 300,450 L 300,300 L 500,300"
        fill="none" stroke="none" />

  <!-- Dot moving along path -->
  <circle r="5" fill="#147EBA">
    <animateMotion dur="3s" repeatCount="indefinite">
      <mpath href="#path-user-to-alb" />
    </animateMotion>
  </circle>
</svg>
```

### Pulsing Glow Effect

```xml
<circle cx="500" cy="300" r="30" fill="none" stroke="#FF9900">
  <animate attributeName="r" values="28;35;28" dur="2s" repeatCount="indefinite" />
  <animate attributeName="opacity" values="0.8;0.3;0.8" dur="2s" repeatCount="indefinite" />
</circle>
```

### Sequential Stagger

```xml
<!-- Dot 1: Start immediately -->
<circle r="4" fill="#DD344C">
  <animateMotion dur="4s" begin="0s" repeatCount="indefinite">
    <mpath href="#outbound-path" />
  </animateMotion>
</circle>

<!-- Dot 2: Start after 1.3s -->
<circle r="4" fill="#DD344C">
  <animateMotion dur="4s" begin="1.3s" repeatCount="indefinite">
    <mpath href="#outbound-path" />
  </animateMotion>
</circle>

<!-- Dot 3: Start after 2.6s -->
<circle r="4" fill="#DD344C">
  <animateMotion dur="4s" begin="2.6s" repeatCount="indefinite">
    <mpath href="#outbound-path" />
  </animateMotion>
</circle>
```

**Formula:** `begin_offset = (dur / dot_count) * index`

### Dashed Line Flow Animation

```xml
<line x1="200" y1="300" x2="600" y2="300"
      stroke="#147EBA" stroke-width="2" stroke-dasharray="8 4">
  <animate attributeName="stroke-dashoffset"
           values="0;-24" dur="1s" repeatCount="indefinite" />
</line>
```

### Sequential Highlight (Step-by-Step)

```xml
<!-- Step 1: ALB highlight at 0s -->
<rect x="200" y="280" width="100" height="40"
      fill="none" stroke="#FF9900" stroke-width="3" opacity="0">
  <animate attributeName="opacity"
           values="0;1;1;0" keyTimes="0;0.1;0.4;0.5"
           dur="6s" repeatCount="indefinite" />
</rect>

<!-- Step 2: Lambda highlight at 2s -->
<rect x="400" y="280" width="100" height="40"
      fill="none" stroke="#FF9900" stroke-width="3" opacity="0">
  <animate attributeName="opacity"
           values="0;0;1;1;0;0" keyTimes="0;0.33;0.36;0.6;0.66;1"
           dur="6s" repeatCount="indefinite" />
</rect>
```

---

## Interactive Scenario Patterns

For user-driven state changes, use JavaScript + CSS instead of SMIL.

### Scaling Scenario (EKS/ASG)

```html
<div class="controls">
  <button id="scaleOut" onclick="handleScaleOut()">Scale Out</button>
  <button id="scaleIn" onclick="handleScaleIn()" disabled>Scale In</button>
</div>

<div class="status">
  Pods: <span id="podCount">3</span> |
  Nodes: <span id="nodeCount">2</span>
</div>

<svg id="diagram" viewBox="0 0 800 400">
  <g id="nodes"></g>
  <g id="pods"></g>
</svg>

<script>
const state = { pods: 3, nodes: 2, animating: false };

function handleScaleOut() {
  if (state.animating) return;
  state.animating = true;

  // Animate new pods appearing
  for (let i = 0; i < 3; i++) {
    setTimeout(() => {
      state.pods++;
      renderPod(state.pods);
      updateDisplay();
    }, i * 300);
  }

  // Add new node after pods
  setTimeout(() => {
    state.nodes++;
    renderNode(state.nodes);
    state.animating = false;
    updateButtons();
  }, 1000);
}

function handleScaleIn() {
  if (state.animating || state.pods <= 3) return;
  state.animating = true;

  // Animate pods disappearing
  removePods(3);

  setTimeout(() => {
    state.nodes--;
    removeNode(state.nodes + 1);
    state.animating = false;
    updateButtons();
  }, 1000);
}
</script>

<style>
.pod {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.pod.removing {
  opacity: 0;
  transform: scale(0);
}
.node {
  transition: all 0.5s ease;
}
</style>
```

### Blue/Green Deployment Scenario

```javascript
const deploymentState = {
  current: 'blue',  // 'blue' | 'green' | 'switching'
  blueTraffic: 100,
  greenTraffic: 0
};

function startDeployment() {
  deploymentState.current = 'switching';

  // Gradual traffic shift
  const interval = setInterval(() => {
    if (deploymentState.blueTraffic > 0) {
      deploymentState.blueTraffic -= 10;
      deploymentState.greenTraffic += 10;
      updateTrafficDisplay();
      updateArrowWeights();
    } else {
      clearInterval(interval);
      deploymentState.current = 'green';
      updateStatus('Deployment Complete');
    }
  }, 500);
}
```

### Failover Simulation Scenario

```javascript
const failoverState = {
  primaryActive: true,
  failoverInProgress: false
};

function triggerFailover() {
  failoverState.failoverInProgress = true;

  // Step 1: Primary shows error
  showError('primary-db');

  // Step 2: Health check fails
  setTimeout(() => {
    updateHealthIndicator('primary', 'unhealthy');
  }, 1000);

  // Step 3: Traffic redirects
  setTimeout(() => {
    redirectTraffic('primary', 'standby');
    updateHealthIndicator('standby', 'active');
  }, 2000);

  // Step 4: Complete
  setTimeout(() => {
    failoverState.primaryActive = false;
    failoverState.failoverInProgress = false;
    updateStatus('Failover Complete');
  }, 3000);
}
```

---

## SMIL vs CSS Animation Comparison

### When to Use SMIL

| Scenario | Recommended |
|----------|-------------|
| Continuous traffic flow loops | SMIL |
| Pulsing/glow status indicators | SMIL |
| Path-based motion (dots along lines) | SMIL |
| No user interaction needed | SMIL |
| Legend toggle is the only interaction | SMIL |

### When to Use JavaScript + CSS

| Scenario | Recommended |
|----------|-------------|
| Button-triggered state changes | JavaScript |
| Dynamic element creation/deletion | JavaScript |
| Multi-step storytelling with user control | JavaScript |
| Before/after state comparison | JavaScript |
| Counters that update in real-time | JavaScript |
| Complex state machines | JavaScript |

### Decision Guide

```
Does the animation need user-triggered state changes?
├─ No → Use SMIL
│       ├─ Continuous loop? → animateMotion
│       └─ Pulsing effect? → animate
└─ Yes → Use JavaScript + CSS
         ├─ Simple toggle? → CSS classes
         └─ Complex state? → State machine
```

---

## Animation Timing Guidelines

| Animation Type | Duration | Repeat |
|----------------|----------|--------|
| Traffic dot (short path) | 2-3s | indefinite |
| Traffic dot (long path) | 4-6s | indefinite |
| Pulsing glow | 2s | indefinite |
| Highlight flash | 1s | 3 times |
| State transition | 0.3-0.5s | once |

---

## Interactive Legend

```html
<div class="legend">
  <label>
    <input type="checkbox" checked onchange="toggleGroup('inbound')">
    <span style="color:#147EBA">● Inbound Traffic</span>
  </label>
  <label>
    <input type="checkbox" checked onchange="toggleGroup('outbound')">
    <span style="color:#DD344C">● Outbound Traffic</span>
  </label>
</div>

<script>
function toggleGroup(group) {
  document.querySelectorAll(`[data-group="${group}"]`).forEach(el => {
    el.style.display = el.style.display === 'none' ? '' : 'none';
  });
}
</script>
```

---

## Usage Example

```
User: "Create VPC traffic flow animation"

1. animated-diagram-agent called
2. Static background created (Draw.io or inline SVG)
3. SMIL animations added
4. Interactive legend added
5. content-review-agent review
```

---

## Output Usage

Generated HTML files can be embedded in various places:

- **Presentations**: Insert as `<iframe>` in HTML slides
- **GitBook**: Embed `<iframe>` in document pages
- **Standalone**: Open directly in browser

---

## Quality Review (Required)

After content completion:
1. Call `content-review-agent`
2. Achieve PASS (85+ score) before completion

---

## Validation Checklist

### SMIL Animation
- [ ] All `<animateMotion>` paths are valid and visible
- [ ] Color coding matches standard (Red/Blue/Orange)
- [ ] Legend toggle works for each animation group
- [ ] Responsive scaling works at various viewport sizes
- [ ] Background image/SVG aligns with animation overlay
- [ ] Animation elements don't exceed viewBox
- [ ] `data-group` attributes match legend toggle functions

### Interactive Animation
- [ ] All buttons trigger correct state transitions
- [ ] Dynamic elements appear/disappear with smooth transitions
- [ ] State machine prevents invalid transitions (buttons disabled during animation)
- [ ] No orphaned SVG elements after repeated Scale Out/In cycles
- [ ] Works correctly in both standalone and iframe-embedded contexts
