---
sidebar_position: 1
title: "Reactive Presentation"
---

# Reactive Presentation Skill

Build interactive HTML presentation slideshows with Canvas animations, quizzes, dark theme, and keyboard navigation. Deployed to GitHub Pages.

## Trigger Keywords

Activated by the following keywords:
- "create slides", "build a presentation", "make a slideshow"
- "training slides", "interactive presentation"
- "Canvas animation slides", "reactive presentation"

## Provided Resources

### assets/

Framework files (copy to `common/`):

| File | Description |
|------|-------------|
| `theme.css` | Dark theme, Pretendard font, 16:9 layout, all component styles |
| `theme-override-template.css` | Template for PPTX-extracted CSS overrides |
| `slide-framework.js` | SlideFramework class (keyboard, touch, progress bar, presenter view) |
| `slide-renderer.js` | SlideRenderer class: JSON to HTML dynamic rendering |
| `presenter-view.js` | PresenterView class (draggable splitters, BroadcastChannel sync) |
| `animation-utils.js` | Canvas primitives, AnimationLoop, TimelineAnimation, Colors, Ease |
| `quiz-component.js` | QuizManager (auto-grading, feedback) |
| `export-utils.js` | ExportUtils (PDF export, ZIP download) |

### scripts/

| Script | Description |
|--------|-------------|
| `extract_pptx_theme.py` | PPTX theme extraction to CSS overrides + images |
| `remarp_to_slides.py` | Remarp markdown to HTML slide conversion |
| `marp_to_slides.py` | Marp markdown to HTML slide conversion (legacy) |
| `extract_aws_icons.py` | AWS Architecture Icons extraction |

### references/

| Reference Doc | Description |
|---------------|-------------|
| `framework-guide.md` | CSS classes, JS functions, HTML template API reference |
| `slide-patterns.md` | HTML patterns by slide type, Canvas animation patterns |
| `remarp-format-guide.md` | Remarp markdown format specification (recommended) |
| `marp-format-guide.md` | Marp markdown format specification (legacy) |
| `pptx-theme-guide.md` | PPTX theme extraction usage, color mapping, troubleshooting |
| `aws-icons-guide.md` | AWS Architecture Icons usage, naming conventions |
| `canvas-animation-prompt.md` | Canvas prompt to JS code generation guide |
| `interactive-patterns-guide.md` | Interactive slide patterns (simulators, dashboards, etc.) |
| `colors-reference.md` | AWS color palette |
| `data-visualization-guide.md` | Charts, dashboards, KPI cards design patterns |

### icons/

AWS Architecture Icons (4,224 files):

| Directory | Description |
|-----------|-------------|
| `Architecture-Service-Icons_07312025/` | Service-level icons (121 categories) |
| `Architecture-Group-Icons_07312025/` | Group icons (Cloud, VPC, Region, Subnet) |
| `Category-Icons_07312025/` | Category-level icons (4 sizes) |
| `Resource-Icons_07312025/` | Resource-level icons (22 categories) |
| `others/` | Third-party icons (LangChain, Grafana, etc.) |

---

## Key Features

### Remarp Format (Recommended)

Control fragment animations, Canvas DSL, speaker notes, and slide transitions directly in markdown:

```markdown
---
remarp: true
title: My Presentation
theme: aws-dark
---

# Slide Title
@type: content

This is a paragraph {.click}

:::click
This appears on click
:::

:::notes
{timing: 2min}
Speaker notes here
:::
```

### PPTX Theme Extraction

```bash
python3 scripts/extract_pptx_theme.py <pptx_path> -o {repo}/common/pptx-theme/
```

Generated outputs:
- `theme-manifest.json` — Extracted colors, fonts, logos, footer
- `theme-override.css` — CSS variable overrides
- `images/` — Logos, background images

---

## Data Visualization Patterns

The reactive-presentation framework supports multiple data visualization techniques for creating impactful slides.

### Typography Hierarchy

| Element | Size | Weight | Additional |
|---------|------|--------|------------|
| Hero stat | 3.5rem+ | 700 | `text-shadow: 0 0 20px var(--accent-glow)` |
| KPI value | 2.4rem | 700 | Monospace font |
| Card title | 1.1rem | 600 | `text-wrap: balance` |
| Body text | 1rem | 400 | — |
| Label/caption | 0.85rem | 500 | Secondary color |

### CSS-Only Charts

For lightweight visualizations without JavaScript dependencies:

```css
/* Horizontal bar chart */
.bar-chart .bar {
  height: 24px;
  background: linear-gradient(90deg, var(--accent) 0%, var(--accent-light) 100%);
  border-radius: 4px;
  transition: width 0.6s ease-out;
}

/* Progress ring */
.progress-ring {
  --progress: 75;
  background: conic-gradient(
    var(--accent) calc(var(--progress) * 1%),
    var(--surface-2) 0
  );
}
```

### KPI Card Layout

```html
<div class="kpi-grid">
  <div class="kpi-card">
    <div class="kpi-label">Latency</div>
    <div class="kpi-value">42<span class="kpi-unit">ms</span></div>
    <div class="kpi-trend positive">-15% vs last week</div>
  </div>
</div>
```

### Chart.js Integration

For dynamic charts, embed Chart.js in `:::script` blocks:

```markdown
:::html
<canvas id="myChart" width="400" height="200"></canvas>
:::

:::script
new Chart(document.getElementById('myChart'), {
  type: 'bar',
  data: {
    labels: ['Jan', 'Feb', 'Mar'],
    datasets: [{
      data: [12, 19, 3],
      backgroundColor: ['#6c5ce7', '#a29bfe', '#dfe6e9']
    }]
  }
});
:::
```

---

## Canvas vs HTML Decision Guide

### The 4-Box Rule

Before using Canvas, count the total boxes and icons on your slide:

| Element Count | Approach | Why |
|---------------|----------|-----|
| **1-4 boxes** | `:::canvas` DSL allowed | Simple enough for Canvas coordinates |
| **5+ boxes** | `:::html` + `:::css` **required** | Flexbox/Grid handles complex layouts better |

### Decision Matrix

| Content Type | Use Canvas | Use HTML |
|--------------|------------|----------|
| Simple A→B→C flow | Yes | — |
| 3-tier architecture | — | Yes |
| Service ecosystem map | — | Yes |
| Step-by-step animation | Yes | — |
| Multi-layer diagram | — | Yes |
| Interactive dashboard | — | Yes (with `:::script`) |

### HTML Architecture Pattern

For 5+ elements, use this pattern:

```markdown
:::html
<div class="flow-h">
  <div class="flow-group bg-blue" data-fragment-index="1">
    <div class="flow-group-label">Collect</div>
    <div class="icon-item">
      <img src="../common/aws-icons/services/Arch_Amazon-CloudWatch_48.svg">
      <span>CloudWatch</span>
    </div>
  </div>
  <div class="flow-arrow">→</div>
  <div class="flow-group bg-orange" data-fragment-index="2">
    <div class="flow-group-label">Analyze</div>
    <div class="flow-box">DevOps Guru</div>
  </div>
</div>
:::
```

---

## Remarp Workflow Detail

The 9-step workflow for creating presentations:

### Step 1: Theme Setup (Optional)

If PPTX template is provided:

```bash
python3 scripts/extract_pptx_theme.py template.pptx -o common/pptx-theme/
```

### Step 2: Content Planning

Answer these questions during planning:
- **Topic & audience** — technical depth, learning objectives
- **Duration** — determines block count (20-35 min per block)
- **Quiz inclusion** — yes/no for end-of-block quizzes
- **Speaker info** — name, title, company

### Step 3: Create Project Structure

```
{slug}/
├── _presentation.md           # Global settings
├── 01-fundamentals.md         # Block 1
├── 02-deep-dive.md            # Block 2
└── animations/                # Canvas animation modules
```

### Step 4: Write Remarp Content

Use `@type` directives for slide types:

| Type | Usage |
|------|-------|
| `@type: cover` | Session cover slide |
| `@type: title` | Block title slide |
| `@type: content` | Standard content |
| `@type: compare` | A vs B comparison |
| `@type: tabs` | Tabbed content |
| `@type: canvas` | Canvas animation |
| `@type: quiz` | Quiz slide |
| `@type: agenda` | Session agenda |

### Step 5: Build HTML

```bash
# Full build
python3 scripts/remarp_to_slides.py build {repo}/{slug}/

# Incremental build (changed blocks only)
python3 scripts/remarp_to_slides.py sync {repo}/{slug}/

# Single block
python3 scripts/remarp_to_slides.py build {repo}/{slug}/ --block 01-fundamentals
```

### Step 6: Review & Iterate

Edit Remarp source or request changes via prompt, then rebuild.

### Step 7: Enhancement

Add Canvas animations, interactive elements, AWS icons.

### Step 8: Quality Review

**Mandatory**: Run `content-review-agent` and achieve PASS (85+ score).

### Step 9: Deploy

```bash
git add common/ {slug}/ index.html
git commit -m "feat: add {name} presentation"
git push origin main
```

---

## Interactive Pattern Guide

### Simulator Pattern

For parameter exploration (VPA, cost calculators):

```markdown
:::html
<div class="simulator-layout">
  <div class="slider-group">
    <label>CPU Request</label>
    <input type="range" id="cpu" min="50" max="2000" value="250">
    <span id="cpu-val">250m</span>
  </div>
  <div class="yaml-output" id="output"></div>
</div>
:::

:::script
document.getElementById('cpu').oninput = function() {
  document.getElementById('cpu-val').textContent = this.value + 'm';
  updateYAML();
};
:::
```

### Calculator Pattern

For cost/metric calculations:

```markdown
:::html
<div class="calculator">
  <div class="input-group">
    <label>Instances</label>
    <input type="number" id="instances" value="3">
  </div>
  <div class="result">
    <span class="label">Monthly Cost</span>
    <span class="value" id="cost">$0</span>
  </div>
</div>
:::
```

### Dashboard Pattern

For monitoring/metrics displays:

```markdown
:::html
<div class="dashboard-grid">
  <div class="stat-panel">
    <div class="stat-label">Active Pods</div>
    <div class="stat-value" id="pods">12</div>
  </div>
  <div class="node-grid" id="nodes"></div>
  <div class="controls">
    <button onclick="scaleOut()">Scale Out</button>
    <button onclick="scaleIn()">Scale In</button>
  </div>
</div>
:::
```

---

## Speaker Notes Writing Guide

All slides **must** include `:::notes` blocks meeting these requirements:

### Requirements

| Criterion | Requirement |
|-----------|-------------|
| **Minimum length** | 150 characters per slide |
| **Recommended length** | 300-500 characters (1-3 minutes speaking) |
| **Structure** | Timing marker → Intro → Key points → Cues → Transition |

### Structure Template

```markdown
:::notes
{timing: 2min}
[Opening hook that connects to previous slide]

Key points to cover:
- Point 1 with real-world example or analogy
- Point 2 with practical tip
- Point 3 addressing common misconception

{cue: question}
Ask audience: "Has anyone experienced...?"

{cue: transition}
Now that we understand X, let's see how Y builds on this...
:::
```

### Good Example

```markdown
:::notes
{timing: 3min}
Before diving into the code, let's understand why VPA matters.

Traditional resource allocation is like buying clothes for a growing child —
you either waste money on oversized clothes or constantly buy new ones. VPA
solves this by automatically adjusting container resources based on actual usage.

Key insight: VPA doesn't just save costs — it improves application stability
by preventing OOM kills and CPU throttling.

{cue: pause}
Take a moment to think about your current resource allocation strategy.

{cue: transition}
With this mental model in place, let's look at the configuration options...
:::
```

### Bad Example (What NOT to do)

```markdown
:::notes
This slide shows VPA configuration.
:::
```

Problems: Too short, no timing, repeats slide content, no engagement cues.

---

## Slide Types

| Content Type | Pattern | Interactive Element |
|--------------|---------|---------------------|
| Simple flow (boxes ≤4) | Canvas Animation | `:::canvas` DSL, step navigation |
| Complex architecture (boxes 5+) | HTML Architecture | `:::html` + `:::css` (flexbox/grid) |
| A vs B comparison | Compare Toggle | `.compare-toggle` buttons |
| Config variants | Tab Content | `.tab-bar` + YAML code blocks |
| Step-by-step process | Timeline | `.timeline` animation |
| Monitoring/dashboard (boxes 5+) | HTML Dashboard | `:::html` + `:::script` |
| Best practices | Checklist | `.checklist` toggle |
| Block summary | Quiz | `data-quiz` + 3-4 questions |

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| ← → | Previous/Next slide |
| ↑ ↓ | Cycle tabs/compare options |
| F | Fullscreen |
| P | Presenter view |
| N | Speaker notes panel |
| O | Overview mode |

---

## Usage Example

```
User: "Create an EKS introduction presentation"

1. presentation-agent called
2. Remarp content written
3. HTML build: python3 scripts/remarp_to_slides.py build {slug}/
4. content-review-agent review
5. GitHub Pages deployment
```

---

## Quality Review (Required)

After content completion, before deployment:
1. Call `content-review-agent`
2. Achieve PASS (85+ score) before deployment
3. Re-review after fixes if FAIL/REVIEW verdict

:::warning Required
Skipping this step and deploying is prohibited.
:::
