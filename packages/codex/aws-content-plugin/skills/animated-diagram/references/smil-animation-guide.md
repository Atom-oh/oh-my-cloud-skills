# SMIL Animation Guide

Reference for SVG SMIL animations used in animated architecture diagrams.

---

## Core Animation Elements

### animateMotion — Move Along Path

Moves an element along a defined SVG path. Primary technique for traffic flow dots.

```xml
<circle r="5" fill="#147EBA">
  <animateMotion dur="3s" repeatCount="indefinite" rotate="auto">
    <mpath href="#my-path" />
  </animateMotion>
</circle>
```

| Attribute | Values | Description |
|-----------|--------|-------------|
| `dur` | `2s`, `4s` | Animation duration |
| `repeatCount` | `indefinite`, `3` | Repeat behavior |
| `begin` | `0s`, `1.5s` | Start delay (for staggering) |
| `rotate` | `auto`, `0` | Rotate element along path |
| `fill` | `freeze`, `remove` | End state behavior |

### animate — Attribute Animation

Animates any SVG attribute over time. Used for pulsing, fading, color changes.

```xml
<!-- Pulsing radius -->
<circle cx="500" cy="300" r="30" fill="none" stroke="#FF9900" stroke-width="2">
  <animate attributeName="r" values="28;35;28" dur="2s" repeatCount="indefinite" />
  <animate attributeName="opacity" values="0.8;0.3;0.8" dur="2s" repeatCount="indefinite" />
</circle>

<!-- Color pulse -->
<rect width="100" height="60" fill="#232F3E">
  <animate attributeName="fill" values="#232F3E;#FF9900;#232F3E" dur="3s" repeatCount="indefinite" />
</rect>
```

| Attribute | Values | Description |
|-----------|--------|-------------|
| `attributeName` | `r`, `opacity`, `fill`, `stroke-width` | Target attribute |
| `values` | semicolon-separated | Keyframe values |
| `dur` | duration | Animation cycle time |
| `keyTimes` | `0;0.5;1` | Timing for each value |

---

## Path Definition

### Orthogonal Paths (Architecture Style)

Architecture diagrams use right-angle connections. Define paths with `M` (moveTo) and `L` (lineTo) only:

```xml
<!-- Horizontal → Vertical -->
<path id="path-h-v" d="M 100,450 L 300,450 L 300,200" fill="none" stroke="none" />

<!-- L-shape -->
<path id="path-l" d="M 100,200 L 400,200 L 400,500 L 700,500" fill="none" stroke="none" />

<!-- Z-shape (3 segments) -->
<path id="path-z" d="M 100,200 L 300,200 L 300,400 L 500,400" fill="none" stroke="none" />
```

**Rules:**
- Always use `L` (lineTo), never curves (`C`, `Q`, `A`)
- Paths should be invisible (`stroke="none"`) — they are motion guides
- Path coordinates must match the SVG viewBox coordinate system

---

## Animation Patterns

### Staggered Traffic Dots

Multiple dots following the same path with offset start times:

```xml
<!-- 3 dots, evenly staggered across the duration -->
<circle r="4" fill="#DD344C" data-group="outbound">
  <animateMotion dur="4s" begin="0s" repeatCount="indefinite">
    <mpath href="#outbound-path" />
  </animateMotion>
</circle>
<circle r="4" fill="#DD344C" data-group="outbound">
  <animateMotion dur="4s" begin="1.33s" repeatCount="indefinite">
    <mpath href="#outbound-path" />
  </animateMotion>
</circle>
<circle r="4" fill="#DD344C" data-group="outbound">
  <animateMotion dur="4s" begin="2.66s" repeatCount="indefinite">
    <mpath href="#outbound-path" />
  </animateMotion>
</circle>
```

**Formula:** `begin_offset = (dur / dot_count) * index`

### Pulsing Node Highlight

Draw attention to a specific service node:

```xml
<g transform="translate(500,300)">
  <!-- Outer glow ring -->
  <circle r="30" fill="none" stroke="#FF9900" stroke-width="2">
    <animate attributeName="r" values="28;38;28" dur="2s" repeatCount="indefinite" />
    <animate attributeName="opacity" values="0.6;0.1;0.6" dur="2s" repeatCount="indefinite" />
  </circle>
  <!-- Inner glow ring -->
  <circle r="20" fill="none" stroke="#FF9900" stroke-width="1.5">
    <animate attributeName="r" values="20;28;20" dur="2s" repeatCount="indefinite" />
    <animate attributeName="opacity" values="0.8;0.2;0.8" dur="2s" repeatCount="indefinite" />
  </circle>
</g>
```

### Connection Line Dash Animation

Animated dashed line showing data flow direction:

```xml
<line x1="200" y1="300" x2="600" y2="300"
      stroke="#147EBA" stroke-width="2" stroke-dasharray="8 4">
  <animate attributeName="stroke-dashoffset" values="0;-24" dur="1s" repeatCount="indefinite" />
</line>
```

### Sequential Highlight (Step-by-Step)

Highlight services in sequence to show request flow:

```xml
<!-- Step 1: ALB highlight at 0s -->
<rect x="200" y="280" width="100" height="40" fill="none" stroke="#FF9900" stroke-width="3" opacity="0">
  <animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.1;0.4;0.5" dur="6s" repeatCount="indefinite" />
</rect>

<!-- Step 2: Lambda highlight at 2s -->
<rect x="400" y="280" width="100" height="40" fill="none" stroke="#FF9900" stroke-width="3" opacity="0">
  <animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.33;0.36;0.6;0.66;1" dur="6s" repeatCount="indefinite" />
</rect>

<!-- Step 3: DynamoDB highlight at 4s -->
<rect x="600" y="280" width="100" height="40" fill="none" stroke="#FF9900" stroke-width="3" opacity="0">
  <animate attributeName="opacity" values="0;0;0;1;1;0" keyTimes="0;0.6;0.66;0.7;0.9;1" dur="6s" repeatCount="indefinite" />
</rect>
```

---

## Timing Guidelines

| Animation | Duration | Stagger | Notes |
|-----------|----------|---------|-------|
| Short path dot | 2-3s | dur/3 | 3-5 service hops |
| Long path dot | 4-6s | dur/3 | Cross-VPC or IDC→AWS |
| Pulsing glow | 2s | — | Continuous |
| Dash flow | 1s | — | Direction indicator |
| Sequential highlight | 6-8s | 2s per step | Step-through |

---

## Browser Compatibility

SMIL animations are supported in all modern browsers:
- Chrome, Edge, Firefox, Safari: Full support
- IE11: Not supported (use CSS animations as fallback if needed)

For maximum compatibility, use these SMIL elements:
- `<animate>` — attribute animation
- `<animateMotion>` — path-based motion
- `<set>` — discrete attribute change

Avoid:
- `<animateTransform>` — inconsistent across browsers
- `<animateColor>` — deprecated

---

## See Also: Interactive Animations

SMIL animations are ideal for continuous, declarative effects (traffic flow dots, pulsing glows, dash animations). However, when your diagram requires **user-driven state changes** — such as button-triggered scaling, deployment rollouts, or failover simulations — consider using the **Interactive Animation** pattern instead.

Interactive animations use JavaScript + CSS transitions to provide:
- **Button-triggered state machines** — Scale Out/In, Deploy, Failover buttons
- **Dynamic element creation/deletion** — Pods, nodes, instances that appear/disappear
- **Sequential animations** — Step-by-step transitions with `requestAnimationFrame`
- **State display** — Real-time counters showing current resource counts

**When to use which:**

| Scenario | Use SMIL | Use Interactive |
|----------|----------|----------------|
| Continuous traffic flow | Yes | — |
| Pulsing/glow effects | Yes | — |
| Button-triggered state changes | — | Yes |
| Dynamic element count changes | — | Yes |
| Step-by-step deployment | — | Yes |
| Monitoring dashboard | Yes | — |

**Reference:** See `templates/interactive-scaling.html` for a complete EKS hybrid bursting example using the interactive pattern.
