# Data Visualization Guide

Comprehensive design patterns for charts, dashboards, KPI cards, and infographic slides in the reactive-presentation framework.

---

## 1. Design System Principles

### Typography Hierarchy

| Element | Size | Weight | Letter-spacing | Additional |
|---------|------|--------|----------------|------------|
| Hero stat | 3.5rem+ | 700 | -0.03em | `text-shadow: 0 0 20px var(--accent-glow)` |
| KPI value | 2.4rem | 700 | -0.02em | — |
| Card title | 1.1rem | 600 | -0.01em | — |
| Body text | 1rem | 400 | 0 | `text-wrap: balance` |
| Label/caption | 0.85rem | 500 | 0.02em | `color: var(--text-secondary)` |
| Muted text | 0.75rem | 400 | 0.01em | `color: var(--text-muted)` |

```css
.stat-hero {
  font-size: 3.5rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: var(--accent-light);
  text-shadow: 0 0 20px var(--accent-glow);
}

.kpi-value {
  font-size: 2.4rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  font-family: var(--font-mono);
}

.card-title {
  font-size: 1.1rem;
  font-weight: 600;
  letter-spacing: -0.01em;
  text-wrap: balance;
}
```

### Semantic Color Rules

Use theme CSS variables consistently for semantic meaning:

| Purpose | Variable | Hex | Usage |
|---------|----------|-----|-------|
| Positive/success | `--green` | #00b894 | Upward trends, completed, healthy |
| Negative/danger | `--red` | #e17055 | Downward trends, errors, critical |
| Warning/caution | `--yellow` | #fdcb6e | Alerts, pending, needs attention |
| Primary accent | `--accent` | #6c5ce7 | Key metrics, primary data series |
| Secondary accent | `--accent-light` | #a29bfe | Secondary data, hover states |
| Information | `--blue` | #74b9ff | Neutral data, links, info callouts |
| Highlight | `--cyan` | #00cec9 | Special emphasis, alternative accent |
| Tertiary | `--orange` | #f39c12 | Third data series, warnings |

**KPI Color Discipline**: For dashboards with 4+ KPI cards, use maximum 2 accent colors. Reserve `--green`/`--red` exclusively for delta indicators.

```css
/* Correct: semantic delta colors */
.delta-positive { color: var(--green); }
.delta-negative { color: var(--red); }

/* Correct: limited accent palette */
.kpi-primary { color: var(--accent-light); }
.kpi-secondary { color: var(--cyan); }

/* Wrong: rainbow KPI values */
.kpi-1 { color: var(--green); }   /* NO */
.kpi-2 { color: var(--blue); }    /* NO */
.kpi-3 { color: var(--orange); }  /* NO */
.kpi-4 { color: var(--cyan); }    /* NO */
```

### Card Hover States

Shadow-only hover transitions. No `transform: translateY()` or `scale()`.

```css
.viz-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px;
  transition: box-shadow 0.2s ease;
}

.viz-card:hover {
  box-shadow: 0 0 0 1px var(--border), 0 8px 16px rgba(0,0,0,0.08);
}

/* FORBIDDEN patterns */
.viz-card:hover {
  transform: translateY(-4px);  /* NO */
  transform: scale(1.02);       /* NO */
}
```

### Anti-Patterns (Forbidden)

**Layout**
| Pattern | Why Forbidden | Alternative |
|---------|--------------|-------------|
| Orphan title | Heading alone on slide wastes space | Combine with content or use as section divider |
| Wall-of-text | >6 bullet items overwhelm viewers | Split across slides or use progressive reveal |
| Cramped grid | >6 cards cause cognitive overload | Max 4-6 cards, paginate if needed |
| Inconsistent padding | Breaks visual rhythm | Use 8px grid system consistently |

**Typography**
| Pattern | Why Forbidden | Alternative |
|---------|--------------|-------------|
| font-size < 0.75rem | Unreadable on projection | Minimum 0.85rem for labels |
| Mixing rem/px/em | Inconsistent scaling | Use rem exclusively |
| >3 font weights per slide | Visual chaos | Limit to 400, 600, 700 |
| Gradient text on data | Reduces readability | Solid `var(--accent-light)` |

**Color**
| Pattern | Why Forbidden | Alternative |
|---------|--------------|-------------|
| Hardcoded hex instead of CSS vars | Theme switching breaks | Always use `var(--color)` |
| Low-contrast text | Fails accessibility | Minimum 4.5:1 ratio |
| >5 accent colors per slide | Rainbow noise | Max 3-4 semantic colors |
| Hex alpha suffix (`#6c5ce780`) | Browser inconsistency | `rgba(108,92,231,0.5)` |
| Random decorative colors | Breaks semantic meaning | Theme palette only |

**Interaction**
| Pattern | Why Forbidden | Alternative |
|---------|--------------|-------------|
| Click target < 44px | Touch/accessibility failure | Minimum 44x44px hit area |
| No hover/focus states | Unclear interactivity | Add `:hover` and `:focus-visible` |
| Broken keyboard nav | Accessibility violation | Test Tab/Enter navigation |
| Scale transform hover | Causes layout shift | Shadow-only hover |

**Charts**
| Pattern | Why Forbidden | Alternative |
|---------|--------------|-------------|
| 3D chart effects | Distorts data perception | Flat 2D charts only |
| Pie chart > 5 slices | Impossible to compare | Use bar chart or group "Other" |
| Unlabeled axes | Data is meaningless | Always label with units |
| Truncated Y-axis | Exaggerates differences | Start Y-axis at 0 |
| Floating orbs/blobs | Distracts from data | Subtle radial gradient OR noise |
| Rainbow borders | Visual noise | Single `var(--border)` or accent |

### 8px Grid Spacing System

All spacing values must be multiples of 8px:

```css
:root {
  --space-1: 8px;
  --space-2: 16px;
  --space-3: 24px;
  --space-4: 32px;
  --space-5: 40px;
  --space-6: 48px;
}

.kpi-row { gap: var(--space-3); }           /* 24px */
.chart-container { padding: var(--space-3); } /* 24px */
.card-stack { gap: var(--space-2); }        /* 16px */
```

### Background Atmosphere (Choose ONE)

Only one atmospheric effect per slide. Never combine.

```css
/* Option 1: Radial gradient */
.slide-atmosphere-gradient {
  background:
    radial-gradient(ellipse at 20% 30%, rgba(108,92,231,0.08) 0%, transparent 50%),
    var(--bg-primary);
}

/* Option 2: Noise texture */
.slide-atmosphere-noise {
  background: var(--bg-primary);
}
.slide-atmosphere-noise::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
  opacity: 0.03;
  pointer-events: none;
}

/* Option 3: Dot grid */
.slide-atmosphere-dots {
  background:
    radial-gradient(circle at center, var(--border) 1px, transparent 1px),
    var(--bg-primary);
  background-size: 24px 24px;
}
```

### Accessibility

Ensure data visualizations are accessible to all users:

- All chart containers: `role="img"` + `aria-label="[description]"`
- Interactive controls: `:focus-visible` outlines, keyboard-operable
- Color contrast: minimum 4.5:1 for text, 3:1 for large text
- Live regions: `aria-live="polite"` for dynamic value updates
- Color-blind safe palette: avoid red/green-only distinctions, use patterns/shapes as secondary encoding

```html
<!-- Accessible chart container -->
<div class="chart-container" role="img" aria-label="Bar chart showing monthly revenue: Jan $45K, Feb $52K, Mar $61K">
  <canvas id="revenue-chart"></canvas>
</div>

<!-- Accessible KPI with live region -->
<div class="kpi-value" data-count="99.97" aria-live="polite" aria-atomic="true">0</div>

<!-- Focus-visible for interactive elements -->
<style>
.chart-legend-item:focus-visible,
.kpi-card:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
</style>
```

---

## 2. Chart.js Integration (Slide Context)

### CDN Setup

Load Chart.js via CDN in the HTML `<head>`:

```html
<head>
  <link rel="stylesheet" href="../common/theme.css">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
```

### Critical Configuration

**MUST disable animation** to prevent screenshot/initial render breakage:

```javascript
// Global config — set BEFORE creating any charts
Chart.defaults.animation = false;
Chart.defaults.font.family = 'Pretendard, system-ui, sans-serif';
Chart.defaults.color = '#9ba1b8'; // --text-secondary
```

### Theme Integration Pattern

CSS variable changes require destroy + recreate (CSS variable swap is insufficient for canvas):

```javascript
// ChartManager singleton — prevents canvas reuse errors on slide transitions
const ChartManager = {
  instances: {},
  create(id, ctx, config) {
    if (this.instances[id]) this.instances[id].destroy();
    this.instances[id] = new Chart(ctx, config);
    return this.instances[id];
  },
  destroyAll() {
    Object.values(this.instances).forEach(c => c.destroy());
    this.instances = {};
  }
};

// Read theme colors from CSS variables (useful for dynamic theming)
function getThemeColors() {
  const s = getComputedStyle(document.documentElement);
  return {
    accent: s.getPropertyValue('--accent').trim(),
    green: s.getPropertyValue('--green').trim(),
    red: s.getPropertyValue('--red').trim(),
    yellow: s.getPropertyValue('--yellow').trim(),
    text: s.getPropertyValue('--text-primary').trim(),
    textMuted: s.getPropertyValue('--text-muted').trim(),
    border: s.getPropertyValue('--border').trim(),
    bgCard: s.getPropertyValue('--bg-card').trim(),
  };
}

function createChart(canvasId, config) {
  const canvas = document.getElementById(canvasId);
  const existingChart = Chart.getChart(canvas);
  if (existingChart) existingChart.destroy();
  return new Chart(canvas, config);
}

// Theme colors as explicit rgba (no hex alpha suffix)
const chartColors = {
  accent: 'rgba(108, 92, 231, 1)',      // --accent
  accentLight: 'rgba(162, 155, 254, 1)', // --accent-light
  green: 'rgba(0, 184, 148, 1)',         // --green
  red: 'rgba(225, 112, 85, 1)',          // --red
  yellow: 'rgba(253, 203, 110, 1)',      // --yellow
  blue: 'rgba(116, 185, 255, 1)',        // --blue
  cyan: 'rgba(0, 206, 201, 1)',          // --cyan
  orange: 'rgba(243, 156, 18, 1)',       // --orange
  textPrimary: 'rgba(232, 234, 240, 1)', // --text-primary
  textSecondary: 'rgba(155, 161, 184, 1)', // --text-secondary
  border: 'rgba(45, 50, 80, 1)',         // --border
  bgCard: 'rgba(30, 34, 53, 1)',         // --bg-card
};
```

### Chart Container Styling

```css
.chart-container {
  min-height: 300px;
  padding: 24px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
}

.chart-grid {
  display: grid;
  grid-template-columns: 3fr 2fr;
  gap: 24px;
}

.chart-grid-equal {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}
```

### Bar Chart Example

```html
<div class="slide">
  <div class="slide-header"><h2>Monthly Revenue by Region</h2></div>
  <div class="slide-body">
    <div class="chart-container" style="height: 400px;">
      <canvas id="barChart"></canvas>
    </div>
  </div>
</div>

<script>
Chart.defaults.animation = false;

const barChart = new Chart(document.getElementById('barChart'), {
  type: 'bar',
  data: {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [
      {
        label: 'APAC',
        data: [12, 19, 15, 25, 22, 30],
        backgroundColor: 'rgba(108, 92, 231, 0.8)',
        borderColor: 'rgba(108, 92, 231, 1)',
        borderWidth: 1,
        borderRadius: 4,
      },
      {
        label: 'EMEA',
        data: [8, 12, 10, 18, 15, 22],
        backgroundColor: 'rgba(0, 206, 201, 0.8)',
        borderColor: 'rgba(0, 206, 201, 1)',
        borderWidth: 1,
        borderRadius: 4,
      }
    ]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: 'rgba(155, 161, 184, 1)',
          font: { family: 'Pretendard' }
        }
      }
    },
    scales: {
      x: {
        grid: { color: 'rgba(45, 50, 80, 0.5)' },
        ticks: { color: 'rgba(155, 161, 184, 1)' }
      },
      y: {
        grid: { color: 'rgba(45, 50, 80, 0.5)' },
        ticks: { color: 'rgba(155, 161, 184, 1)' }
      }
    }
  }
});
</script>
```

### Line Chart Example

```html
<div class="slide">
  <div class="slide-header"><h2>Request Latency Trend</h2></div>
  <div class="slide-body">
    <div class="chart-container" style="height: 400px;">
      <canvas id="lineChart"></canvas>
    </div>
  </div>
</div>

<script>
Chart.defaults.animation = false;

const lineChart = new Chart(document.getElementById('lineChart'), {
  type: 'line',
  data: {
    labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
    datasets: [
      {
        label: 'p50',
        data: [45, 42, 58, 62, 55, 48],
        borderColor: 'rgba(0, 184, 148, 1)',
        backgroundColor: 'rgba(0, 184, 148, 0.1)',
        fill: true,
        tension: 0.3,
        pointRadius: 0,
        pointHoverRadius: 6,
      },
      {
        label: 'p99',
        data: [120, 115, 180, 195, 160, 130],
        borderColor: 'rgba(225, 112, 85, 1)',
        backgroundColor: 'rgba(225, 112, 85, 0.1)',
        fill: true,
        tension: 0.3,
        pointRadius: 0,
        pointHoverRadius: 6,
      }
    ]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { intersect: false, mode: 'index' },
    plugins: {
      legend: {
        position: 'top',
        labels: { color: 'rgba(155, 161, 184, 1)' }
      },
      tooltip: {
        backgroundColor: 'rgba(30, 34, 53, 0.95)',
        titleColor: 'rgba(232, 234, 240, 1)',
        bodyColor: 'rgba(155, 161, 184, 1)',
        borderColor: 'rgba(45, 50, 80, 1)',
        borderWidth: 1,
        padding: 12,
        cornerRadius: 8,
      }
    },
    scales: {
      x: {
        grid: { color: 'rgba(45, 50, 80, 0.5)' },
        ticks: { color: 'rgba(155, 161, 184, 1)' }
      },
      y: {
        grid: { color: 'rgba(45, 50, 80, 0.5)' },
        ticks: {
          color: 'rgba(155, 161, 184, 1)',
          callback: v => v + 'ms'
        }
      }
    }
  }
});
</script>
```

### Doughnut Chart Example

```html
<div class="slide">
  <div class="slide-header"><h2>Resource Allocation</h2></div>
  <div class="slide-body">
    <div class="chart-grid">
      <div class="chart-container">
        <canvas id="doughnutChart"></canvas>
      </div>
      <div style="display: flex; flex-direction: column; justify-content: center; gap: 16px;">
        <div class="legend-item"><span class="legend-dot" style="background: rgba(108, 92, 231, 1);"></span> Compute (45%)</div>
        <div class="legend-item"><span class="legend-dot" style="background: rgba(0, 206, 201, 1);"></span> Storage (25%)</div>
        <div class="legend-item"><span class="legend-dot" style="background: rgba(116, 185, 255, 1);"></span> Network (20%)</div>
        <div class="legend-item"><span class="legend-dot" style="background: rgba(155, 161, 184, 1);"></span> Other (10%)</div>
      </div>
    </div>
  </div>
</div>

<style>
.legend-item {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--text-secondary);
  font-size: 1rem;
}
.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}
</style>

<script>
Chart.defaults.animation = false;

const doughnutChart = new Chart(document.getElementById('doughnutChart'), {
  type: 'doughnut',
  data: {
    labels: ['Compute', 'Storage', 'Network', 'Other'],
    datasets: [{
      data: [45, 25, 20, 10],
      backgroundColor: [
        'rgba(108, 92, 231, 0.9)',
        'rgba(0, 206, 201, 0.9)',
        'rgba(116, 185, 255, 0.9)',
        'rgba(155, 161, 184, 0.5)',
      ],
      borderColor: 'rgba(30, 34, 53, 1)',
      borderWidth: 3,
      hoverOffset: 8,
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: true,
    cutout: '65%',
    plugins: {
      legend: { display: false }
    }
  }
});
</script>
```

### Radar Chart Example

```html
<div class="slide">
  <div class="slide-header"><h2>Service Health Score</h2></div>
  <div class="slide-body">
    <div class="chart-container" style="max-width: 500px; margin: 0 auto;">
      <canvas id="radarChart"></canvas>
    </div>
  </div>
</div>

<script>
Chart.defaults.animation = false;

const radarChart = new Chart(document.getElementById('radarChart'), {
  type: 'radar',
  data: {
    labels: ['Availability', 'Latency', 'Throughput', 'Error Rate', 'Saturation'],
    datasets: [
      {
        label: 'Current',
        data: [95, 88, 72, 90, 65],
        backgroundColor: 'rgba(108, 92, 231, 0.2)',
        borderColor: 'rgba(108, 92, 231, 1)',
        borderWidth: 2,
        pointBackgroundColor: 'rgba(108, 92, 231, 1)',
        pointRadius: 4,
      },
      {
        label: 'Target',
        data: [99, 95, 85, 95, 80],
        backgroundColor: 'rgba(0, 184, 148, 0.1)',
        borderColor: 'rgba(0, 184, 148, 0.6)',
        borderWidth: 2,
        borderDash: [5, 5],
        pointRadius: 0,
      }
    ]
  },
  options: {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        position: 'bottom',
        labels: { color: 'rgba(155, 161, 184, 1)' }
      }
    },
    scales: {
      r: {
        angleLines: { color: 'rgba(45, 50, 80, 0.5)' },
        grid: { color: 'rgba(45, 50, 80, 0.5)' },
        pointLabels: {
          color: 'rgba(155, 161, 184, 1)',
          font: { size: 12 }
        },
        ticks: {
          color: 'rgba(107, 113, 148, 1)',
          backdropColor: 'transparent'
        },
        suggestedMin: 0,
        suggestedMax: 100,
      }
    }
  }
});
</script>
```

---

## 3. CSS-Only Chart Patterns (No CDN)

### Conic-Gradient Donut

```html
<div class="slide">
  <div class="slide-header"><h2>Budget Allocation</h2></div>
  <div class="slide-body" style="display: flex; justify-content: center; align-items: center; gap: 48px;">
    <div class="css-donut" style="--v1: 45; --v2: 25; --v3: 20; --v4: 10;">
      <span class="donut-center">$2.4M</span>
    </div>
    <div class="donut-legend">
      <div><span style="--c: var(--accent);"></span> Infrastructure (45%)</div>
      <div><span style="--c: var(--cyan);"></span> Personnel (25%)</div>
      <div><span style="--c: var(--blue);"></span> Licensing (20%)</div>
      <div><span style="--c: var(--text-muted);"></span> Other (10%)</div>
    </div>
  </div>
</div>

<style>
.css-donut {
  --size: 200px;
  --thickness: 32px;
  width: var(--size);
  height: var(--size);
  border-radius: 50%;
  background: conic-gradient(
    var(--accent) 0% calc(var(--v1) * 1%),
    var(--cyan) calc(var(--v1) * 1%) calc((var(--v1) + var(--v2)) * 1%),
    var(--blue) calc((var(--v1) + var(--v2)) * 1%) calc((var(--v1) + var(--v2) + var(--v3)) * 1%),
    var(--text-muted) calc((var(--v1) + var(--v2) + var(--v3)) * 1%) 100%
  );
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.css-donut::after {
  content: '';
  position: absolute;
  width: calc(var(--size) - var(--thickness) * 2);
  height: calc(var(--size) - var(--thickness) * 2);
  background: var(--bg-card);
  border-radius: 50%;
}

.donut-center {
  position: relative;
  z-index: 1;
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--text-primary);
  font-family: var(--font-mono);
}

.donut-legend {
  display: flex;
  flex-direction: column;
  gap: 12px;
  color: var(--text-secondary);
}

.donut-legend span {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--c);
  margin-right: 8px;
}
</style>
```

### CSS Bar Chart

```html
<div class="slide">
  <div class="slide-header"><h2>Weekly Deployments</h2></div>
  <div class="slide-body">
    <div class="css-bar-chart">
      <div class="bar-row">
        <span class="bar-label">Mon</span>
        <div class="bar-track"><div class="bar-fill" style="--pct: 85%;"></div></div>
        <span class="bar-value">17</span>
      </div>
      <div class="bar-row">
        <span class="bar-label">Tue</span>
        <div class="bar-track"><div class="bar-fill" style="--pct: 60%;"></div></div>
        <span class="bar-value">12</span>
      </div>
      <div class="bar-row">
        <span class="bar-label">Wed</span>
        <div class="bar-track"><div class="bar-fill" style="--pct: 95%;"></div></div>
        <span class="bar-value">19</span>
      </div>
      <div class="bar-row">
        <span class="bar-label">Thu</span>
        <div class="bar-track"><div class="bar-fill" style="--pct: 70%;"></div></div>
        <span class="bar-value">14</span>
      </div>
      <div class="bar-row">
        <span class="bar-label">Fri</span>
        <div class="bar-track"><div class="bar-fill bar-fill-warning" style="--pct: 25%;"></div></div>
        <span class="bar-value">5</span>
      </div>
    </div>
  </div>
</div>

<style>
.css-bar-chart {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 600px;
  margin: 0 auto;
}

.bar-row {
  display: grid;
  grid-template-columns: 60px 1fr 50px;
  align-items: center;
  gap: 16px;
}

.bar-label {
  color: var(--text-secondary);
  font-size: 0.9rem;
  text-align: right;
}

.bar-track {
  height: 24px;
  background: var(--surface);
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  width: var(--pct);
  background: linear-gradient(90deg, var(--accent), var(--accent-light));
  border-radius: 4px;
  transition: width 0.6s ease;
}

.bar-fill-warning {
  background: linear-gradient(90deg, var(--yellow), var(--orange));
}

.bar-value {
  color: var(--text-primary);
  font-weight: 600;
  font-family: var(--font-mono);
}
</style>
```

### SVG Inline Line Chart

```html
<div class="slide">
  <div class="slide-header"><h2>Traffic Pattern</h2></div>
  <div class="slide-body" style="display: flex; justify-content: center;">
    <svg class="svg-line-chart" viewBox="0 0 400 200" width="600">
      <!-- Grid lines -->
      <line x1="50" y1="20" x2="50" y2="170" stroke="var(--border)" stroke-width="1"/>
      <line x1="50" y1="170" x2="380" y2="170" stroke="var(--border)" stroke-width="1"/>
      <line x1="50" y1="95" x2="380" y2="95" stroke="var(--border)" stroke-width="1" stroke-dasharray="4"/>
      <line x1="50" y1="20" x2="380" y2="20" stroke="var(--border)" stroke-width="1" stroke-dasharray="4"/>

      <!-- Y-axis labels -->
      <text x="45" y="175" fill="var(--text-muted)" font-size="10" text-anchor="end">0</text>
      <text x="45" y="100" fill="var(--text-muted)" font-size="10" text-anchor="end">50</text>
      <text x="45" y="25" fill="var(--text-muted)" font-size="10" text-anchor="end">100</text>

      <!-- X-axis labels -->
      <text x="50" y="185" fill="var(--text-muted)" font-size="10" text-anchor="middle">0h</text>
      <text x="160" y="185" fill="var(--text-muted)" font-size="10" text-anchor="middle">8h</text>
      <text x="270" y="185" fill="var(--text-muted)" font-size="10" text-anchor="middle">16h</text>
      <text x="380" y="185" fill="var(--text-muted)" font-size="10" text-anchor="middle">24h</text>

      <!-- Area fill -->
      <polygon
        points="50,170 80,140 130,120 180,90 230,60 280,80 330,50 380,70 380,170"
        fill="url(#areaGradient)"
      />

      <!-- Line -->
      <polyline
        points="50,170 80,140 130,120 180,90 230,60 280,80 330,50 380,70"
        fill="none"
        stroke="var(--accent)"
        stroke-width="3"
        stroke-linecap="round"
        stroke-linejoin="round"
      />

      <!-- Data points -->
      <circle cx="230" cy="60" r="6" fill="var(--accent)" stroke="var(--bg-card)" stroke-width="2"/>
      <circle cx="330" cy="50" r="6" fill="var(--accent)" stroke="var(--bg-card)" stroke-width="2"/>

      <defs>
        <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="var(--accent)" stop-opacity="0.3"/>
          <stop offset="100%" stop-color="var(--accent)" stop-opacity="0"/>
        </linearGradient>
      </defs>
    </svg>
  </div>
</div>

<style>
.svg-line-chart {
  max-width: 100%;
  height: auto;
}
</style>
```

### SVG Bar Chart

```html
<div class="slide">
  <div class="slide-header"><h2>Error Distribution</h2></div>
  <div class="slide-body" style="display: flex; justify-content: center;">
    <svg viewBox="0 0 400 220" width="600">
      <!-- Bars -->
      <rect x="60" y="40" width="50" height="140" rx="4" fill="var(--accent)" opacity="0.9"/>
      <rect x="130" y="80" width="50" height="100" rx="4" fill="var(--accent)" opacity="0.9"/>
      <rect x="200" y="120" width="50" height="60" rx="4" fill="var(--accent)" opacity="0.9"/>
      <rect x="270" y="60" width="50" height="120" rx="4" fill="var(--red)" opacity="0.9"/>
      <rect x="340" y="140" width="50" height="40" rx="4" fill="var(--accent)" opacity="0.9"/>

      <!-- Labels -->
      <text x="85" y="200" fill="var(--text-secondary)" font-size="12" text-anchor="middle">4xx</text>
      <text x="155" y="200" fill="var(--text-secondary)" font-size="12" text-anchor="middle">5xx</text>
      <text x="225" y="200" fill="var(--text-secondary)" font-size="12" text-anchor="middle">Timeout</text>
      <text x="295" y="200" fill="var(--text-secondary)" font-size="12" text-anchor="middle">Auth</text>
      <text x="365" y="200" fill="var(--text-secondary)" font-size="12" text-anchor="middle">Other</text>

      <!-- Values -->
      <text x="85" y="32" fill="var(--text-primary)" font-size="14" font-weight="600" text-anchor="middle">234</text>
      <text x="155" y="72" fill="var(--text-primary)" font-size="14" font-weight="600" text-anchor="middle">167</text>
      <text x="225" y="112" fill="var(--text-primary)" font-size="14" font-weight="600" text-anchor="middle">89</text>
      <text x="295" y="52" fill="var(--red)" font-size="14" font-weight="600" text-anchor="middle">201</text>
      <text x="365" y="132" fill="var(--text-primary)" font-size="14" font-weight="600" text-anchor="middle">45</text>
    </svg>
  </div>
</div>
```

### SVG Donut (stroke-dasharray)

```html
<div class="slide">
  <div class="slide-header"><h2>Cluster Utilization</h2></div>
  <div class="slide-body" style="display: flex; justify-content: center; align-items: center; gap: 48px;">
    <svg viewBox="0 0 120 120" width="200" height="200" class="svg-donut">
      <!-- Background ring -->
      <circle cx="60" cy="60" r="50" fill="none" stroke="var(--surface)" stroke-width="12"/>
      <!-- Progress ring (72% = 0.72 * 314.159 = 226.19) -->
      <circle cx="60" cy="60" r="50" fill="none"
        stroke="var(--accent)"
        stroke-width="12"
        stroke-dasharray="226.19 314.159"
        stroke-linecap="round"
        transform="rotate(-90 60 60)"
        class="donut-progress"
      />
      <!-- Center text -->
      <text x="60" y="55" fill="var(--text-primary)" font-size="24" font-weight="700" text-anchor="middle" font-family="var(--font-mono)">72%</text>
      <text x="60" y="72" fill="var(--text-secondary)" font-size="10" text-anchor="middle">CPU Used</text>
    </svg>

    <div style="display: flex; flex-direction: column; gap: 16px;">
      <div class="util-stat"><span class="util-label">vCPUs</span><span class="util-value">576 / 800</span></div>
      <div class="util-stat"><span class="util-label">Memory</span><span class="util-value">1.8 TiB / 2.4 TiB</span></div>
      <div class="util-stat"><span class="util-label">Pods</span><span class="util-value">892 / 1,200</span></div>
    </div>
  </div>
</div>

<style>
.svg-donut .donut-progress {
  transition: stroke-dasharray 0.8s ease;
}

.util-stat {
  display: flex;
  justify-content: space-between;
  gap: 32px;
}
.util-label { color: var(--text-secondary); }
.util-value { color: var(--text-primary); font-family: var(--font-mono); font-weight: 600; }
</style>
```

### SVG Line Chart Drawing Animation

```html
<style>
@keyframes draw-line {
  from { stroke-dashoffset: 1000; }
  to { stroke-dashoffset: 0; }
}

.animated-line {
  stroke-dasharray: 1000;
  stroke-dashoffset: 1000;
  animation: draw-line 2s ease forwards;
}

/* Trigger animation when slide becomes active */
.slide.active .animated-line {
  animation: draw-line 2s ease forwards;
}
</style>

<svg viewBox="0 0 400 150" width="600">
  <polyline
    class="animated-line"
    points="20,120 80,100 140,110 200,60 260,70 320,30 380,50"
    fill="none"
    stroke="var(--cyan)"
    stroke-width="3"
    stroke-linecap="round"
    stroke-linejoin="round"
  />
</svg>
```

### Sparkline in KPI Card

```html
<div class="kpi-card">
  <div class="kpi-label">Requests/sec</div>
  <div class="kpi-value">2,847</div>
  <svg class="sparkline" viewBox="0 0 80 24" preserveAspectRatio="none">
    <polyline
      points="0,20 10,18 20,15 30,16 40,12 50,8 60,10 70,6 80,4"
      fill="none"
      stroke="var(--green)"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
  </svg>
  <div class="kpi-delta delta-positive">+12.3%</div>
</div>

<style>
.sparkline {
  width: 100%;
  height: 24px;
  margin: 8px 0;
}
</style>
```

---

## 4. KPI Dashboard Slide Pattern

### Basic KPI Row (3-5 Cards)

```html
<div class="slide">
  <div class="slide-header"><h2>System Overview</h2></div>
  <div class="slide-body">
    <div class="kpi-row">
      <div class="kpi-card">
        <div class="kpi-label">Uptime</div>
        <div class="kpi-value" data-count="99.97">0</div>
        <div class="kpi-unit">%</div>
        <div class="kpi-delta delta-positive">+0.02%</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Avg Latency</div>
        <div class="kpi-value" data-count="42">0</div>
        <div class="kpi-unit">ms</div>
        <div class="kpi-delta delta-positive">-8ms</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Error Rate</div>
        <div class="kpi-value" data-count="0.12">0</div>
        <div class="kpi-unit">%</div>
        <div class="kpi-delta delta-negative">+0.04%</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Throughput</div>
        <div class="kpi-value" data-count="12847">0</div>
        <div class="kpi-unit">req/s</div>
        <div class="kpi-delta delta-positive">+2.1k</div>
      </div>
    </div>
  </div>
</div>

<style>
.kpi-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 24px;
  padding: 16px 0;
}

.kpi-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  transition: box-shadow 0.2s ease;
}

.kpi-card:hover {
  box-shadow: 0 0 0 1px var(--border), 0 8px 16px rgba(0,0,0,0.08);
}

.kpi-label {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-secondary);
  letter-spacing: 0.02em;
  margin-bottom: 8px;
}

.kpi-value {
  font-size: 2.4rem;
  font-weight: 700;
  color: var(--accent-light);
  font-family: var(--font-mono);
  letter-spacing: -0.02em;
  line-height: 1.1;
}

.kpi-unit {
  font-size: 1rem;
  color: var(--text-muted);
  margin-top: 4px;
}

.kpi-delta {
  font-size: 0.85rem;
  font-weight: 600;
  margin-top: 12px;
}

.delta-positive { color: var(--green); }
.delta-negative { color: var(--red); }
</style>

<script>
// Standalone counter animation — works without SlideFramework dependency
function animateCounters(container = document) {
  container.querySelectorAll('[data-count]').forEach(el => {
    const target = parseFloat(el.dataset.count);
    const format = el.dataset.format || '';
    const duration = 1200;
    const start = performance.now();
    function step(now) {
      const t = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - t, 3);
      const val = eased * target;
      el.textContent = format === 'percent' ? val.toFixed(1) + '%'
        : format === 'currency' ? '$' + val.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
        : val.toFixed(0);
      if (t < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  });
}

// Trigger on slide activation (if using SlideFramework)
if (typeof SlideFramework !== 'undefined') {
  const deck = new SlideFramework({
    onSlideChange: (index, slide) => {
      if (slide.querySelector('[data-count]')) {
        animateCounters(slide);
      }
    }
  });
} else {
  // Standalone: animate on DOMContentLoaded
  document.addEventListener('DOMContentLoaded', () => animateCounters());
}
</script>
```

### KPI with Sparkline

```html
<div class="kpi-row">
  <div class="kpi-card kpi-card-spark">
    <div class="kpi-header">
      <div class="kpi-label">CPU Utilization</div>
      <div class="kpi-delta delta-positive">+5.2%</div>
    </div>
    <div class="kpi-value">72%</div>
    <svg class="kpi-sparkline" viewBox="0 0 100 30" preserveAspectRatio="none">
      <polyline
        points="0,25 15,22 30,24 45,18 60,20 75,12 90,15 100,8"
        fill="none"
        stroke="var(--accent)"
        stroke-width="2"
      />
    </svg>
  </div>
  <!-- More cards... -->
</div>

<style>
.kpi-card-spark {
  text-align: left;
}

.kpi-card-spark .kpi-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.kpi-card-spark .kpi-value {
  font-size: 2rem;
}

.kpi-sparkline {
  width: 100%;
  height: 30px;
  margin-top: 12px;
}
</style>
```

---

## 5. Infographic Slide Pattern

### Hero Stats with Icon Pairs

```html
<div class="slide">
  <div class="slide-header"><h2>EKS Auto Mode Impact</h2></div>
  <div class="slide-body">
    <div class="hero-stats">
      <div class="hero-stat">
        <div class="hero-number">73%</div>
        <div class="hero-desc">Reduction in operational overhead</div>
      </div>
      <div class="hero-stat">
        <div class="hero-number">&lt;2s</div>
        <div class="hero-desc">Node provisioning time</div>
      </div>
      <div class="hero-stat">
        <div class="hero-number">$1.2M</div>
        <div class="hero-desc">Annual cost savings (avg)</div>
      </div>
    </div>

    <div class="icon-facts">
      <div class="icon-fact">
        <svg class="fact-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
        </svg>
        <div>
          <strong>Managed Karpenter</strong>
          <p>AWS handles controller upgrades</p>
        </div>
      </div>
      <div class="icon-fact">
        <svg class="fact-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="3" width="18" height="18" rx="2"/>
          <path d="M9 9h6v6H9z"/>
        </svg>
        <div>
          <strong>Optimized AMIs</strong>
          <p>Bottlerocket pre-configured</p>
        </div>
      </div>
      <div class="icon-fact">
        <svg class="fact-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M12 6v6l4 2"/>
        </svg>
        <div>
          <strong>Zero-downtime updates</strong>
          <p>Rolling node replacements</p>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
.hero-stats {
  display: flex;
  justify-content: center;
  gap: 64px;
  margin-bottom: 48px;
}

.hero-stat {
  text-align: center;
}

.hero-number {
  font-size: 3.5rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: var(--accent-light);
  text-shadow: 0 0 20px rgba(108, 92, 231, 0.3);
  font-family: var(--font-mono);
}

.hero-desc {
  font-size: 1rem;
  color: var(--text-secondary);
  margin-top: 8px;
  text-wrap: balance;
  max-width: 180px;
}

.icon-facts {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 32px;
  max-width: 900px;
  margin: 0 auto;
}

.icon-fact {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.fact-icon {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
  color: var(--cyan);
}

.icon-fact strong {
  display: block;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.icon-fact p {
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin: 0;
}
</style>
```

### Comparison Horizontal Bar

```html
<div class="slide">
  <div class="slide-header"><h2>Before vs After</h2></div>
  <div class="slide-body">
    <div class="compare-bars">
      <div class="compare-item">
        <div class="compare-label">Deployment Time</div>
        <div class="compare-bar-pair">
          <div class="compare-bar before">
            <div class="compare-fill" style="--pct: 100%;"></div>
            <span class="compare-value">45 min</span>
          </div>
          <div class="compare-bar after">
            <div class="compare-fill" style="--pct: 22%;"></div>
            <span class="compare-value">10 min</span>
          </div>
        </div>
      </div>
      <div class="compare-item">
        <div class="compare-label">Scaling Response</div>
        <div class="compare-bar-pair">
          <div class="compare-bar before">
            <div class="compare-fill" style="--pct: 100%;"></div>
            <span class="compare-value">5-10 min</span>
          </div>
          <div class="compare-bar after">
            <div class="compare-fill" style="--pct: 6%;"></div>
            <span class="compare-value">&lt;30s</span>
          </div>
        </div>
      </div>
      <div class="compare-item">
        <div class="compare-label">Config Lines</div>
        <div class="compare-bar-pair">
          <div class="compare-bar before">
            <div class="compare-fill" style="--pct: 100%;"></div>
            <span class="compare-value">500+</span>
          </div>
          <div class="compare-bar after">
            <div class="compare-fill" style="--pct: 10%;"></div>
            <span class="compare-value">~50</span>
          </div>
        </div>
      </div>
    </div>

    <div class="compare-legend">
      <span class="legend-before">Before (MNG)</span>
      <span class="legend-after">After (Auto Mode)</span>
    </div>
  </div>
</div>

<style>
.compare-bars {
  display: flex;
  flex-direction: column;
  gap: 32px;
  max-width: 700px;
  margin: 0 auto 32px;
}

.compare-item {
  display: grid;
  grid-template-columns: 140px 1fr;
  gap: 16px;
  align-items: center;
}

.compare-label {
  color: var(--text-secondary);
  font-size: 0.95rem;
  text-align: right;
}

.compare-bar-pair {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.compare-bar {
  height: 20px;
  background: var(--surface);
  border-radius: 4px;
  position: relative;
  overflow: hidden;
}

.compare-fill {
  height: 100%;
  width: var(--pct);
  border-radius: 4px;
  transition: width 0.8s ease;
}

.compare-bar.before .compare-fill {
  background: var(--text-muted);
}

.compare-bar.after .compare-fill {
  background: linear-gradient(90deg, var(--green), var(--cyan));
}

.compare-value {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-primary);
  font-family: var(--font-mono);
}

.compare-legend {
  display: flex;
  justify-content: center;
  gap: 32px;
  font-size: 0.85rem;
}

.legend-before::before,
.legend-after::before {
  content: '';
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 2px;
  margin-right: 8px;
  vertical-align: middle;
}

.legend-before::before { background: var(--text-muted); }
.legend-after::before { background: var(--green); }

.legend-before { color: var(--text-muted); }
.legend-after { color: var(--green); }
</style>
```

### Progress Ring

```html
<div class="progress-ring-container">
  <svg class="progress-ring" viewBox="0 0 100 100">
    <circle class="progress-bg" cx="50" cy="50" r="42"/>
    <circle class="progress-fill" cx="50" cy="50" r="42"
      style="--progress: 0.78;"
      stroke-dasharray="calc(2 * 3.14159 * 42 * var(--progress)) calc(2 * 3.14159 * 42)"
    />
    <text x="50" y="50" class="progress-text">78%</text>
    <text x="50" y="62" class="progress-label">Complete</text>
  </svg>
</div>

<style>
.progress-ring-container {
  width: 150px;
  height: 150px;
}

.progress-ring {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.progress-bg {
  fill: none;
  stroke: var(--surface);
  stroke-width: 8;
}

.progress-fill {
  fill: none;
  stroke: var(--accent);
  stroke-width: 8;
  stroke-linecap: round;
  transition: stroke-dasharray 1s ease;
}

.progress-text {
  fill: var(--text-primary);
  font-size: 18px;
  font-weight: 700;
  text-anchor: middle;
  dominant-baseline: middle;
  transform: rotate(90deg);
  transform-origin: 50% 50%;
  font-family: var(--font-mono);
}

.progress-label {
  fill: var(--text-secondary);
  font-size: 8px;
  text-anchor: middle;
  transform: rotate(90deg);
  transform-origin: 50% 50%;
}
</style>
```

### Section Divider

```html
<div class="section-divider">
  <span class="section-number">02</span>
  <div class="section-line"></div>
  <span class="section-title">Architecture Deep Dive</span>
</div>

<style>
.section-divider {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 32px 0;
}

.section-number {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--accent);
  font-family: var(--font-mono);
  letter-spacing: 0.1em;
}

.section-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, var(--border), transparent);
}

.section-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-secondary);
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
</style>
```

---

## 6. Advanced CSS Techniques

### Dynamic Background Tint with color-mix()

```css
/* Create semi-transparent tints from any theme color */
.card-accent-tint {
  background: color-mix(in srgb, var(--accent), transparent 85%);
}

.card-success-tint {
  background: color-mix(in srgb, var(--green), transparent 90%);
}

.card-danger-tint {
  background: color-mix(in srgb, var(--red), transparent 90%);
}

/* Hover state with slightly less transparency */
.card-accent-tint:hover {
  background: color-mix(in srgb, var(--accent), transparent 80%);
}
```

### Container Queries for Chart Responsiveness

```css
.chart-wrapper {
  container-type: inline-size;
  container-name: chart;
}

@container chart (max-width: 400px) {
  .chart-legend {
    flex-direction: column;
    gap: 8px;
  }

  .chart-title {
    font-size: 1rem;
  }
}

@container chart (min-width: 600px) {
  .chart-legend {
    flex-direction: row;
    gap: 24px;
  }
}
```

### :has() Parent Selector

```css
/* Highlight KPI card if it contains a negative delta */
.kpi-card:has(.delta-negative) {
  border-color: color-mix(in srgb, var(--red), transparent 70%);
}

/* Add separator line to chart grid if it has multiple charts */
.chart-grid:has(.chart-container + .chart-container) {
  position: relative;
}

.chart-grid:has(.chart-container + .chart-container)::before {
  content: '';
  position: absolute;
  left: 50%;
  top: 10%;
  height: 80%;
  width: 1px;
  background: var(--border);
}
```

### CSS Counters for Automatic Numbering

```css
.numbered-list {
  counter-reset: item;
  list-style: none;
  padding: 0;
}

.numbered-list li {
  counter-increment: item;
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.numbered-list li::before {
  content: counter(item, decimal-leading-zero);
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--accent);
  font-family: var(--font-mono);
  min-width: 28px;
}
```

### @starting-style Entry Animations

```css
/* Card entry animation on slide activation */
.slide.active .kpi-card {
  opacity: 1;
  transform: translateY(0);

  @starting-style {
    opacity: 0;
    transform: translateY(16px);
  }

  transition: opacity 0.4s ease, transform 0.4s ease;
}

/* Stagger animation delay */
.kpi-card:nth-child(1) { transition-delay: 0s; }
.kpi-card:nth-child(2) { transition-delay: 0.1s; }
.kpi-card:nth-child(3) { transition-delay: 0.2s; }
.kpi-card:nth-child(4) { transition-delay: 0.3s; }
```

### Popover API (Zero-JS Tooltip)

```html
<button popovertarget="info-tip" class="info-btn">?</button>
<div id="info-tip" popover class="tooltip-popover">
  <strong>Calculation Method</strong>
  <p>p99 latency measured over 5-minute rolling windows, excluding health checks.</p>
</div>

<style>
.info-btn {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text-muted);
  font-size: 0.7rem;
  cursor: pointer;
}

.tooltip-popover {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  max-width: 280px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.2);
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.tooltip-popover strong {
  display: block;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.tooltip-popover p {
  margin: 0;
  line-height: 1.5;
}

/* Anchor positioning (progressive enhancement) */
@supports (anchor-name: --trigger) {
  .info-btn { anchor-name: --trigger; }
  .tooltip-popover {
    position-anchor: --trigger;
    top: anchor(bottom);
    left: anchor(center);
    translate: -50% 8px;
  }
}
</style>
```

---

## 7. Quality Evaluation Criteria

Adapted from data visualization eval dimensions for presentation context.

### D1. First Impression (15%)

**2-second gut reaction**: Does the slide immediately communicate professionalism and clarity?

| Score | Criteria |
|-------|----------|
| 15 | Instantly compelling, clear hierarchy, memorable visual |
| 12 | Professional, clean, purpose is obvious |
| 9 | Acceptable, but forgettable |
| 6 | Cluttered or unclear focus |
| 0-3 | Amateurish, confusing, or broken |

### D2. Typography (15%)

| Score | Criteria |
|-------|----------|
| 15 | Perfect hierarchy, optimal sizes, consistent line-height, letter-spacing tuned |
| 12 | Good hierarchy, minor spacing issues |
| 9 | Readable but lacks polish |
| 6 | Inconsistent sizes, poor line-height |
| 0-3 | Unreadable or chaotic |

**Checklist**:
- [ ] Hero stats use `-0.03em` letter-spacing
- [ ] Labels use `text-secondary` color
- [ ] `font-family: var(--font-mono)` for numeric values
- [ ] `text-wrap: balance` on multi-line headings

### D3. Color (10%)

| Score | Criteria |
|-------|----------|
| 10 | Semantic color usage, harmonious palette, max 3-4 colors |
| 7 | Good palette, minor semantic violations |
| 4 | Random color choices, palette clash |
| 0-2 | Rainbow chaos, accessibility failure |

**Checklist**:
- [ ] Green/red reserved for positive/negative semantics
- [ ] Max 2 accent colors for KPI values
- [ ] Consistent use of theme variables
- [ ] No hex alpha suffix (`#fff8`) — use `rgba()`

### D4. Layout (15%)

| Score | Criteria |
|-------|----------|
| 15 | Perfect 8px grid alignment, balanced whitespace, clear visual groups |
| 12 | Good spacing, minor alignment issues |
| 9 | Acceptable but cramped or too sparse |
| 6 | Misaligned elements, inconsistent gaps |
| 0-3 | Chaotic layout |

**Checklist**:
- [ ] All gaps are multiples of 8px
- [ ] Charts have min-height 300px
- [ ] KPI cards use auto-fit grid
- [ ] Consistent padding across cards

### D5. Content Clarity (15%)

**5-second test**: Can the viewer understand the core message within 5 seconds?

| Score | Criteria |
|-------|----------|
| 15 | Message crystal clear, supporting data reinforces narrative |
| 12 | Clear message, some cognitive load to parse data |
| 9 | Message present but buried |
| 6 | Unclear what the slide is communicating |
| 0-3 | No discernible message |

### D6. Interactivity (10%)

| Score | Criteria |
|-------|----------|
| 10 | Hover states, tooltips, counter animations all functional and subtle |
| 7 | Some interactivity, minor UX issues |
| 4 | Interactive elements feel broken or jarring |
| 0-2 | No interactivity where expected, or broken interactions |

**Checklist**:
- [ ] Card hover uses shadow-only (no transform)
- [ ] Counter animation triggers on slide entry
- [ ] Tooltips use Popover API where appropriate
- [ ] Chart.js animation disabled (`animation: false`)

### D7. Technical Quality (10%)

Page load time < 3s, zero console errors, responsive from 1024px to 4K, WCAG 2.1 AA color contrast (4.5:1).

| Score | Criteria |
|-------|----------|
| 10 | Zero console errors, loads < 2s, fully responsive, passes WCAG AA |
| 7 | Minor warnings, loads < 3s, responsive with minor issues |
| 4 | Some errors, slow load, breaks at certain viewports |
| 0-2 | Console errors, broken functionality, inaccessible |

**Checklist**:
- [ ] Zero console errors/warnings
- [ ] Page load < 3s (including Chart.js CDN)
- [ ] Works from 1024px to 4K displays
- [ ] All text passes 4.5:1 contrast ratio
- [ ] All interactive elements keyboard accessible

### D8. Shareability (10%)

**"How did you make this?"**: Would viewers want to share or recreate this slide?

| Score | Criteria |
|-------|----------|
| 10 | Screenshot-worthy, would generate questions |
| 7 | Professional, but standard corporate fare |
| 4 | Functional but forgettable |
| 0-2 | Embarrassing to share |

### Scoring Summary

| Grade | Score | Verdict |
|-------|-------|---------|
| A | 85-100 | Production-ready |
| B | 70-84 | Minor refinements needed |
| C | 50-69 | Significant rework required |
| F | <50 | Start over |

---

## Quick Reference: Theme CSS Variables

```css
/* Backgrounds */
--bg-primary: #0f1117;
--bg-secondary: #1a1d2e;
--bg-tertiary: #232740;
--bg-card: #1e2235;
--surface: #282d45;
--border: #2d3250;

/* Accent colors */
--accent: #6c5ce7;
--accent-light: #a29bfe;
--accent-glow: rgba(108,92,231,0.3);

/* Semantic colors */
--green: #00b894;
--red: #e17055;
--yellow: #fdcb6e;
--blue: #74b9ff;
--cyan: #00cec9;
--orange: #f39c12;

/* Text */
--text-primary: #e8eaf0;
--text-secondary: #9ba1b8;
--text-muted: #6b7194;

/* Typography */
--font-main: Pretendard;
--font-mono: JetBrains Mono;
```
