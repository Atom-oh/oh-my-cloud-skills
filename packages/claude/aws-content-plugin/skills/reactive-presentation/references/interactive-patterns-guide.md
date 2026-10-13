<!-- SECTION INDEX (auto) — Large file. Don't read the whole thing; offset-read only the ## section you need.
     Line numbers are exact (as of 10 sec ago). Example: Read(file, offset=L, limit=nextSectionL−L). If a section references another §/##, read that one too. -->
<!--
  L22    When-to-Use Decision Tree
  L54    §0 :::html Block Layout Rules (MANDATORY)
  L176   §1 Range Slider Patterns
  L628   §2 Mode Selector / Toggle Patterns
  L1083  §3 Dynamic YAML Generation
  L1407  §4 Canvas Animation with Controls
  L1877  §5 Live Input Patterns
  L2343  §6 Expandable Content Patterns
  L2644  §7 DOM Animation Patterns
  L3233  Quick Reference
-->

# Interactive Patterns Guide

A copy-paste template library implementing the v1.0.0 interactive patterns as Remarp `:::html` / `:::script` / `:::css` blocks.

---

## When-to-Use Decision Tree

```
Static content? (1-2 sentences, an image)
├─ Yes → Use Remarp markdown as-is
└─ No → Slide has data/information
         │
         ├─ 3+ sub-items/categories → ★ Self-contained Tab pattern (see SKILL.md "Interactive Design Principles")
         │     └─ inline onclick + .tc toggle — no external JS needed
         ├─ 4+ listed items → ★ Grid card pattern (instead of a bullet list)
         │     └─ display:grid + color-bordered cards
         ├─ A vs B comparison → Remarp `@type: compare` or a self-contained Tab
         ├─ Step-by-step flow (≤4 boxes) → `:::canvas` DSL or fragment
         ├─ Multi-tier/5+ boxes → `:::html` + `:::css` (canvas forbidden)
         │
         └─ Needs dynamic interaction → `:::html` + `:::script` (this guide)
              │
              ├─ Adjust a value via slider → §1 Range Slider Patterns
              ├─ Select a mode/option → §2 Mode Selector Patterns
              ├─ Generate YAML dynamically → §3 Dynamic YAML Patterns
              ├─ Canvas animation + controls → §4 Canvas Animation Patterns
              ├─ Live input/calculation → §5 Live Input Patterns
              ├─ Expand/collapse detail → §6 Expandable Content Patterns
              └─ DOM animation → §7 DOM Animation Patterns
```

> **★ Interactive-First**: The patterns marked ★ in the tree above are the most frequently used.
> Most technical slides become sufficiently interactive with a "tabs + cards" combination.
> Reserve advanced patterns like sliders/simulators for cases that genuinely need calculation or input.

---

## §0 :::html Block Layout Rules (MANDATORY)

`:::html` blocks render inside `.slide-body` (flex: 1), where the slide padding is already applied. You must follow the rules below so content never overflows the slide area.

### Safe Content Area

| Item | Value |
|------|-----|
| Default slide size | 1280 × 720 px |
| Slide padding | `2rem 2.7rem` (2rem top/bottom, 2.7rem left/right) |
| Effective content area | **~1194 × 620 px** (~540px height once the title area is excluded) |

> **Rule**: Content inside `:::html` must never exceed the effective area. If a scrollbar appears on the slide, the layout has failed.

### max-height Rule

Always set a height limit on the top-level container of a `:::html` block:

```css
/* Absolute-value approach — slide with a title */
.container { max-height: 500px; overflow: hidden; }

/* Relative-value approach — slide without a title */
.container { max-height: calc(100% - 2rem); overflow: hidden; }
```

### Preventing Padding Accumulation

Padding stacks up across slide → html block → card component. **Keep the total at or below 60px**:

| Layer | Recommended padding | Notes |
|--------|----------|------|
| Slide (automatic) | 2rem (~32px) | Applied by the theme, not modifiable |
| `:::html` outer wrapper | 0 ~ 0.5rem | Minimize |
| Inner card/box | 0.75rem ~ 1rem max | Keep the total at or below 60px |

```css
/* BAD — padding accumulates to 100px+ */
.wrapper { padding: 2rem; }
.wrapper .card { padding: 1.5rem; }

/* GOOD — padding accumulates to ~44px */
.wrapper { padding: 0.25rem; }
.wrapper .card { padding: 0.75rem; }
```

### Responsive Sizing Rules

Hardcoded `px` values break FHD/4K compatibility. Choose units according to the table below:

| Target | Unit to use | Example | Forbidden |
|------|-----------|------|------|
| Typography | `rem` or `clamp()` | `font-size: clamp(0.8rem, 1.2vw, 1.1rem)` | `font-size: 14px` |
| Width | `%`, `fr` | `width: 48%`, `grid-template-columns: 1fr 1fr` | `width: 400px` |
| Height | `auto`, `max-height` | `max-height: 500px`, `height: auto` | `height: 600px` |
| Spacing | `rem`, `gap` | `gap: 1rem`, `margin-bottom: 0.5rem` | `margin: 20px` |
| Icons | `2~3rem` | `width: 2.5rem; height: 2.5rem` | `width: 48px` |
| Borders/shadows | `px` allowed | `border: 1px solid`, `box-shadow: 0 2px 8px` | — |

### CSS Variables Are Mandatory

For theme consistency, use CSS variables instead of hardcoded colors/sizes:

```css
/* GOOD — uses theme variables */
.card {
  background: var(--bg-card);
  color: var(--text);
  border: 1px solid var(--border);
}
.highlight { color: var(--accent); }

/* BAD — hardcoded colors */
.card {
  background: #1a1a2e;
  color: #e0e0e0;
  border: 1px solid #333;
}
```

Key CSS variables:

| Variable | Purpose |
|------|------|
| `var(--bg)` | Slide background |
| `var(--bg-card)` | Card/box background |
| `var(--text)` | Base text |
| `var(--text-muted)` | Secondary text |
| `var(--accent)` | Accent color (primary) |
| `var(--border)` | Border |
| `var(--success)` | Success/positive |
| `var(--warning)` | Warning |
| `var(--danger)` | Danger/error |

### Korean Text Rules

Always apply the following CSS to Korean content:

```css
/* Korean line-wrapping — keep word units intact */
.container {
  word-break: keep-all;
  overflow-wrap: break-word;
}
```

Without `word-break: keep-all`, Korean text wraps character-by-character, which severely hurts readability.

### Verification Checklist

After writing a `:::html` block, always confirm the following:

- [ ] No scrollbar at FHD (1920×1080)
- [ ] Layout holds at 4K (3840×2160)
- [ ] Total padding ≤ 60px (slide + wrapper + card)
- [ ] No hardcoded colors (all use `var(--*)`)
- [ ] No hardcoded px (except border/shadow)
- [ ] `max-height` is set
- [ ] `word-break: keep-all` applied to Korean text

---

## §1 Range Slider Patterns

### §1.1 Single Slider with Value Display

Adjust a value with a single slider and display it in real time. The most basic interactive pattern.

**When to use**: Adjusting a single parameter (replicas, timeout, threshold, etc.)

:::html
```html
<div class="slider-group">
  <div class="slider-row">
    <label>Pod Replicas</label>
    <input type="range" id="replicas-slider" min="1" max="20" value="3">
    <span class="slider-value" id="replicas-value">3</span>
  </div>
  <div class="result-display">
    <span class="result-label">Estimated Monthly Cost:</span>
    <span class="result-value" id="cost-result">$45.00</span>
  </div>
</div>
```

:::script
```javascript
(function() {
  const slider = document.getElementById('replicas-slider');
  const valueDisplay = document.getElementById('replicas-value');
  const costResult = document.getElementById('cost-result');
  const COST_PER_POD = 15;

  function update() {
    const val = parseInt(slider.value);
    valueDisplay.textContent = val;
    costResult.textContent = '$' + (val * COST_PER_POD).toFixed(2);
  }

  slider.addEventListener('input', update);
  update();
})();
```

:::css
```css
.slider-group {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 1.5rem;
}
.slider-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}
.slider-row label {
  min-width: 120px;
  color: var(--text-secondary);
  font-size: 0.9rem;
}
.slider-row input[type="range"] {
  flex: 1;
}
.slider-value {
  min-width: 60px;
  text-align: right;
  font-family: var(--font-mono);
  color: var(--accent-light);
  font-weight: 600;
}
.result-display {
  display: flex;
  justify-content: space-between;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
}
.result-label {
  color: var(--text-muted);
}
.result-value {
  font-family: var(--font-mono);
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--green);
}
```

:::notes
```
- Presentation time: 30 seconds
- Demo the cost change by moving the slider
- "Increasing replicas raises availability but also increases cost"
```

---

### §1.2 Multi-Slider Calculator (VPA Simulator)

Adjust CPU/Memory request/limit with four sliders and generate the savings rate and YAML in real time.

**When to use**: VPA, HPA, resource-optimization simulations

:::html
```html
<div class="simulator-layout">
  <div class="simulator-controls">
    <h3>Resource Configuration</h3>
    <div class="slider-group">
      <div class="slider-row">
        <label>CPU Request</label>
        <input type="range" id="cpu-req" min="100" max="2000" step="100" value="500">
        <span class="slider-value" id="cpu-req-val">500m</span>
      </div>
      <div class="slider-row">
        <label>CPU Limit</label>
        <input type="range" id="cpu-lim" min="100" max="4000" step="100" value="1000">
        <span class="slider-value" id="cpu-lim-val">1000m</span>
      </div>
      <div class="slider-row">
        <label>Memory Request</label>
        <input type="range" id="mem-req" min="128" max="4096" step="128" value="512">
        <span class="slider-value" id="mem-req-val">512Mi</span>
      </div>
      <div class="slider-row">
        <label>Memory Limit</label>
        <input type="range" id="mem-lim" min="128" max="8192" step="128" value="1024">
        <span class="slider-value" id="mem-lim-val">1024Mi</span>
      </div>
    </div>
    <div class="savings-gauge">
      <div class="gauge-label">Estimated Savings</div>
      <div class="gauge-bar">
        <div class="gauge-fill" id="savings-fill"></div>
      </div>
      <div class="gauge-value" id="savings-pct">0%</div>
    </div>
  </div>
  <div class="simulator-output">
    <h3>Generated VPA Spec</h3>
    <pre class="yaml-output" id="vpa-yaml"></pre>
  </div>
</div>
```

:::script
```javascript
(function() {
  const cpuReq = document.getElementById('cpu-req');
  const cpuLim = document.getElementById('cpu-lim');
  const memReq = document.getElementById('mem-req');
  const memLim = document.getElementById('mem-lim');
  const cpuReqVal = document.getElementById('cpu-req-val');
  const cpuLimVal = document.getElementById('cpu-lim-val');
  const memReqVal = document.getElementById('mem-req-val');
  const memLimVal = document.getElementById('mem-lim-val');
  const savingsFill = document.getElementById('savings-fill');
  const savingsPct = document.getElementById('savings-pct');
  const yamlOutput = document.getElementById('vpa-yaml');

  const BASELINE = { cpu: 1000, mem: 2048 };

  function update() {
    const cr = parseInt(cpuReq.value);
    const cl = parseInt(cpuLim.value);
    const mr = parseInt(memReq.value);
    const ml = parseInt(memLim.value);

    cpuReqVal.textContent = cr + 'm';
    cpuLimVal.textContent = cl + 'm';
    memReqVal.textContent = mr + 'Mi';
    memLimVal.textContent = ml + 'Mi';

    // Calculate savings
    const cpuSavings = Math.max(0, (BASELINE.cpu - cr) / BASELINE.cpu * 100);
    const memSavings = Math.max(0, (BASELINE.mem - mr) / BASELINE.mem * 100);
    const totalSavings = Math.round((cpuSavings + memSavings) / 2);

    savingsFill.style.width = totalSavings + '%';
    savingsPct.textContent = totalSavings + '%';
    savingsFill.style.background = totalSavings > 30 ? 'var(--green)' : 'var(--accent)';

    // Generate YAML
    yamlOutput.textContent = `apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: my-app-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  resourcePolicy:
    containerPolicies:
      - containerName: "*"
        minAllowed:
          cpu: "${cr}m"
          memory: "${mr}Mi"
        maxAllowed:
          cpu: "${cl}m"
          memory: "${ml}Mi"
  updatePolicy:
    updateMode: "Auto"`;
  }

  [cpuReq, cpuLim, memReq, memLim].forEach(s => s.addEventListener('input', update));
  update();
})();
```

:::css
```css
.simulator-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}
.simulator-controls, .simulator-output {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 1.2rem;
}
.simulator-controls h3, .simulator-output h3 {
  font-size: 1rem;
  color: var(--text-accent);
  margin-bottom: 1rem;
}
.savings-gauge {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
}
.gauge-label {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}
.gauge-bar {
  height: 8px;
  background: var(--bg-tertiary);
  border-radius: 4px;
  overflow: hidden;
}
.gauge-fill {
  height: 100%;
  width: 0%;
  background: var(--accent);
  transition: width 0.3s ease, background 0.3s ease;
}
.gauge-value {
  font-family: var(--font-mono);
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--green);
  margin-top: 0.5rem;
}
.yaml-output {
  background: #0d1117;
  border: 1px solid var(--border);
  border-radius: 0.33rem;
  padding: 1rem;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  line-height: 1.5;
  color: #7ee787;
  overflow-x: auto;
  white-space: pre;
  max-height: 300px;
}
```

:::notes
```
- Presentation time: 2 minutes
- Explain the principle behind VPA's automatic resource adjustment
- Demonstrate a before/after comparison with the slider
- "VPA recommends optimal values based on actual usage"
```

---

### §1.3 Slider with Tradeoff Bars (TTL Controller)

The tradeoff bars change visually according to the slider value, and the recommendation text updates dynamically too.

**When to use**: Settings with a tradeoff, such as expireAfter, TTL, or retention

:::html
```html
<div class="tradeoff-card">
  <div class="slider-section">
    <label>Node TTL (expireAfter)</label>
    <div class="slider-row">
      <span class="slider-min">1h</span>
      <input type="range" id="ttl-slider" min="1" max="168" value="24">
      <span class="slider-max">168h</span>
    </div>
    <div class="slider-value-large" id="ttl-display">24 hours</div>
  </div>
  <div class="tradeoff-section">
    <div class="tradeoff-row">
      <span class="tradeoff-label">Cost Efficiency</span>
      <div class="tradeoff-bar">
        <div class="tradeoff-fill cost-fill" id="cost-bar"></div>
      </div>
    </div>
    <div class="tradeoff-row">
      <span class="tradeoff-label">Stability</span>
      <div class="tradeoff-bar">
        <div class="tradeoff-fill stability-fill" id="stability-bar"></div>
      </div>
    </div>
    <div class="tradeoff-row">
      <span class="tradeoff-label">Churn Rate</span>
      <div class="tradeoff-bar">
        <div class="tradeoff-fill churn-fill" id="churn-bar"></div>
      </div>
    </div>
  </div>
  <div class="recommendation" id="ttl-recommendation"></div>
</div>
```

:::script
```javascript
(function() {
  const slider = document.getElementById('ttl-slider');
  const display = document.getElementById('ttl-display');
  const costBar = document.getElementById('cost-bar');
  const stabilityBar = document.getElementById('stability-bar');
  const churnBar = document.getElementById('churn-bar');
  const recommendation = document.getElementById('ttl-recommendation');

  const recommendations = {
    short: { text: 'Aggressive: Best for dev/test with frequent spot interruptions', class: 'rec-yellow' },
    medium: { text: 'Balanced: Good for production batch workloads', class: 'rec-green' },
    long: { text: 'Conservative: Best for stateful workloads requiring stability', class: 'rec-blue' }
  };

  function update() {
    const hours = parseInt(slider.value);
    display.textContent = hours + (hours === 1 ? ' hour' : ' hours');

    // Calculate tradeoffs (inverse relationships)
    const costPct = Math.min(100, Math.round((168 - hours) / 168 * 100));
    const stabilityPct = Math.min(100, Math.round(hours / 168 * 100));
    const churnPct = Math.min(100, Math.round((168 - hours) / 168 * 100));

    costBar.style.width = costPct + '%';
    stabilityBar.style.width = stabilityPct + '%';
    churnBar.style.width = churnPct + '%';

    // Set recommendation
    let rec;
    if (hours <= 12) rec = recommendations.short;
    else if (hours <= 72) rec = recommendations.medium;
    else rec = recommendations.long;

    recommendation.textContent = rec.text;
    recommendation.className = 'recommendation ' + rec.class;
  }

  slider.addEventListener('input', update);
  update();
})();
```

:::css
```css
.tradeoff-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 1.5rem;
}
.slider-section {
  margin-bottom: 1.5rem;
}
.slider-section label {
  display: block;
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin-bottom: 0.75rem;
}
.slider-section .slider-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.slider-min, .slider-max {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-family: var(--font-mono);
}
.slider-value-large {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--accent-light);
  text-align: center;
  margin-top: 0.75rem;
}
.tradeoff-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}
.tradeoff-row {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.tradeoff-label {
  min-width: 120px;
  font-size: 0.85rem;
  color: var(--text-secondary);
}
.tradeoff-bar {
  flex: 1;
  height: 8px;
  background: var(--bg-tertiary);
  border-radius: 4px;
  overflow: hidden;
}
.tradeoff-fill {
  height: 100%;
  transition: width 0.3s ease;
}
.cost-fill { background: var(--green); }
.stability-fill { background: var(--blue); }
.churn-fill { background: var(--yellow); }
.recommendation {
  padding: 0.75rem 1rem;
  border-radius: 0.33rem;
  font-size: 0.9rem;
}
.rec-yellow { background: var(--yellow-bg); color: var(--yellow); }
.rec-green { background: var(--green-bg); color: var(--green); }
.rec-blue { background: var(--blue-bg); color: var(--blue); }
```

:::notes
```
- Presentation time: 1 minute 30 seconds
- Visualize the tradeoff across TTL values
- "Short TTL = cost savings but higher churn"
- "Long TTL = stability but higher cost"
```

---

## §2 Mode Selector / Toggle Patterns

### §2.1 Button Group Mode Selector (VPA Mode)

Selecting a mode via a button group displays the corresponding description.

**When to use**: VPA updateMode, HPA behavior, policy selection, etc.

:::html
```html
<div class="mode-selector-card">
  <h3>VPA Update Mode</h3>
  <div class="mode-selector">
    <button class="mode-btn active" data-mode="off">Off</button>
    <button class="mode-btn" data-mode="initial">Initial</button>
    <button class="mode-btn" data-mode="recreate">Recreate</button>
    <button class="mode-btn" data-mode="auto">Auto</button>
  </div>
  <div class="mode-content active" id="mode-off">
    <div class="mode-icon">&#128683;</div>
    <h4>Off Mode</h4>
    <p>VPA only provides recommendations. No automatic updates.</p>
    <ul>
      <li>Safe for initial analysis</li>
      <li>Manually apply recommendations</li>
      <li>Zero disruption risk</li>
    </ul>
  </div>
  <div class="mode-content" id="mode-initial">
    <div class="mode-icon">&#127793;</div>
    <h4>Initial Mode</h4>
    <p>Resources set only at pod creation time.</p>
    <ul>
      <li>New pods get optimized resources</li>
      <li>Existing pods unchanged</li>
      <li>Gradual rollout via deployments</li>
    </ul>
  </div>
  <div class="mode-content" id="mode-recreate">
    <div class="mode-icon">&#128260;</div>
    <h4>Recreate Mode</h4>
    <p>VPA evicts pods when recommendations change significantly.</p>
    <ul>
      <li>Pods recreated with new resources</li>
      <li>Some downtime per pod</li>
      <li>Faster convergence than Initial</li>
    </ul>
  </div>
  <div class="mode-content" id="mode-auto">
    <div class="mode-icon">&#9889;</div>
    <h4>Auto Mode</h4>
    <p>Full automation - VPA manages everything.</p>
    <ul>
      <li>Automatic pod updates</li>
      <li>Best for stateless workloads</li>
      <li>Requires PDB for safety</li>
    </ul>
  </div>
</div>
```

:::script
```javascript
(function() {
  const buttons = document.querySelectorAll('.mode-btn');
  const contents = document.querySelectorAll('.mode-content');

  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      const mode = btn.dataset.mode;

      buttons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      contents.forEach(c => c.classList.remove('active'));
      document.getElementById('mode-' + mode).classList.add('active');
    });
  });
})();
```

:::css
```css
.mode-selector-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 1.5rem;
}
.mode-selector-card h3 {
  font-size: 1rem;
  color: var(--text-accent);
  margin-bottom: 1rem;
}
.mode-selector {
  display: flex;
  gap: 0.25rem;
  background: var(--bg-secondary);
  border-radius: 0.5rem;
  padding: 0.25rem;
  margin-bottom: 1.5rem;
}
.mode-btn {
  flex: 1;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.33rem;
  background: transparent;
  color: var(--text-muted);
  font-family: var(--font-main);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.mode-btn:hover {
  color: var(--text-secondary);
  background: var(--bg-tertiary);
}
.mode-btn.active {
  background: var(--accent);
  color: #fff;
}
.mode-content {
  display: none;
  animation: fadeIn 0.3s ease;
}
.mode-content.active {
  display: block;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
.mode-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}
.mode-content h4 {
  font-size: 1.1rem;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}
.mode-content p {
  color: var(--text-secondary);
  margin-bottom: 0.75rem;
}
.mode-content ul {
  padding-left: 1.25rem;
}
.mode-content li {
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin-bottom: 0.25rem;
}
```

:::notes
```
- Presentation time: 1 minute 30 seconds
- Click through each mode to explain the differences
- "For production, the Auto + PDB combination is recommended"
```

---

### §2.2 Compare Toggle (Auto/MNG/Fargate)

An A vs B vs C comparison toggle, reusing the existing compare-toggle style.

**When to use**: Comparing EKS compute options, deployment strategies, storage types

:::html
```html
<div class="compare-card">
  <div class="compare-toggle">
    <button class="compare-btn active" data-target="auto">Karpenter</button>
    <button class="compare-btn" data-target="mng">Managed Node Group</button>
    <button class="compare-btn" data-target="fargate">Fargate</button>
  </div>
  <div class="compare-content active" id="compare-auto">
    <div class="compare-header">
      <span class="compare-badge badge-green">Recommended</span>
      <h4>Karpenter (Auto Mode)</h4>
    </div>
    <table class="compare-table">
      <tr><td>Scaling Speed</td><td><strong>~30 seconds</strong></td></tr>
      <tr><td>Instance Flexibility</td><td>Any EC2 type</td></tr>
      <tr><td>Cost Optimization</td><td>Spot + Consolidation</td></tr>
      <tr><td>Management</td><td>Fully automated</td></tr>
    </table>
  </div>
  <div class="compare-content" id="compare-mng">
    <div class="compare-header">
      <span class="compare-badge badge-blue">Traditional</span>
      <h4>Managed Node Group</h4>
    </div>
    <table class="compare-table">
      <tr><td>Scaling Speed</td><td>~2-5 minutes</td></tr>
      <tr><td>Instance Flexibility</td><td>Pre-defined types</td></tr>
      <tr><td>Cost Optimization</td><td>Limited Spot support</td></tr>
      <tr><td>Management</td><td>AWS managed AMI updates</td></tr>
    </table>
  </div>
  <div class="compare-content" id="compare-fargate">
    <div class="compare-header">
      <span class="compare-badge badge-yellow">Serverless</span>
      <h4>Fargate</h4>
    </div>
    <table class="compare-table">
      <tr><td>Scaling Speed</td><td>~1-2 minutes</td></tr>
      <tr><td>Instance Flexibility</td><td>vCPU/Memory combos</td></tr>
      <tr><td>Cost Optimization</td><td>Pay per pod</td></tr>
      <tr><td>Management</td><td>Zero node management</td></tr>
    </table>
  </div>
</div>
```

:::script
```javascript
(function() {
  const buttons = document.querySelectorAll('.compare-btn');
  const contents = document.querySelectorAll('.compare-content');

  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.target;

      buttons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      contents.forEach(c => c.classList.remove('active'));
      document.getElementById('compare-' + target).classList.add('active');
    });
  });
})();
```

:::css
```css
.compare-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 1.5rem;
}
.compare-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}
.compare-header h4 {
  font-size: 1.1rem;
  color: var(--text-primary);
}
.compare-badge {
  font-size: 0.7rem;
  padding: 0.2rem 0.5rem;
}
.compare-table {
  width: 100%;
  border-collapse: collapse;
}
.compare-table td {
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--border);
  font-size: 0.9rem;
}
.compare-table td:first-child {
  color: var(--text-muted);
  width: 40%;
}
.compare-table td:last-child {
  color: var(--text-primary);
}
```

:::notes
```
- Presentation time: 1 minute
- Quickly compare the three options
- "Karpenter is recommended in most cases; Fargate is for special cases"
```

---

### §2.3 Alert Toggle Builder (Checkbox to YAML)

A PrometheusRule YAML is generated dynamically based on the checkboxes selected.

**When to use**: Alert configuration, policy setup, feature toggles, etc.

:::html
```html
<div class="alert-builder-card">
  <h3>Build Your Alert Rules</h3>
  <div class="alert-toggles">
    <label class="alert-toggle">
      <input type="checkbox" id="alert-cpu" checked>
      <span class="toggle-label">High CPU Usage (&gt;80%)</span>
    </label>
    <label class="alert-toggle">
      <input type="checkbox" id="alert-memory" checked>
      <span class="toggle-label">High Memory Usage (&gt;85%)</span>
    </label>
    <label class="alert-toggle">
      <input type="checkbox" id="alert-restart">
      <span class="toggle-label">Pod Restart Loop (&gt;5/hour)</span>
    </label>
    <label class="alert-toggle">
      <input type="checkbox" id="alert-pending">
      <span class="toggle-label">Pods Pending (&gt;5min)</span>
    </label>
    <label class="alert-toggle">
      <input type="checkbox" id="alert-oom">
      <span class="toggle-label">OOM Killed Events</span>
    </label>
  </div>
  <div class="alert-output">
    <h4>Generated PrometheusRule</h4>
    <pre class="yaml-output" id="alert-yaml"></pre>
  </div>
</div>
```

:::script
```javascript
(function() {
  const checkboxes = document.querySelectorAll('.alert-toggle input');
  const yamlOutput = document.getElementById('alert-yaml');

  const rules = {
    'alert-cpu': `  - alert: HighCPUUsage
    expr: avg(rate(container_cpu_usage_seconds_total[5m])) by (pod) > 0.8
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High CPU usage detected"`,
    'alert-memory': `  - alert: HighMemoryUsage
    expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.85
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage detected"`,
    'alert-restart': `  - alert: PodRestartLoop
    expr: increase(kube_pod_container_status_restarts_total[1h]) > 5
    for: 10m
    labels:
      severity: critical
    annotations:
      summary: "Pod restart loop detected"`,
    'alert-pending': `  - alert: PodsPending
    expr: kube_pod_status_phase{phase="Pending"} == 1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Pod stuck in Pending state"`,
    'alert-oom': `  - alert: OOMKilled
    expr: kube_pod_container_status_last_terminated_reason{reason="OOMKilled"} == 1
    for: 0m
    labels:
      severity: critical
    annotations:
      summary: "Container OOM killed"`
  };

  function updateYAML() {
    const selected = Array.from(checkboxes)
      .filter(cb => cb.checked)
      .map(cb => rules[cb.id]);

    if (selected.length === 0) {
      yamlOutput.textContent = '# No alerts selected';
      return;
    }

    yamlOutput.textContent = `apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: eks-alerts
  namespace: monitoring
spec:
  groups:
  - name: eks.rules
    rules:
${selected.join('\n')}`;
  }

  checkboxes.forEach(cb => cb.addEventListener('change', updateYAML));
  updateYAML();
})();
```

:::css
```css
.alert-builder-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 1.5rem;
}
.alert-builder-card h3 {
  font-size: 1rem;
  color: var(--text-accent);
  margin-bottom: 1rem;
}
.alert-toggles {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}
.alert-toggle {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  background: var(--bg-secondary);
  border-radius: 0.33rem;
  cursor: pointer;
  transition: background var(--transition-fast);
}
.alert-toggle:hover {
  background: var(--bg-tertiary);
}
.alert-toggle input {
  width: 18px;
  height: 18px;
  accent-color: var(--accent);
}
.toggle-label {
  font-size: 0.9rem;
  color: var(--text-secondary);
}
.alert-output h4 {
  font-size: 0.9rem;
  color: var(--text-muted);
  margin-bottom: 0.75rem;
}
```

:::notes
```
- Presentation time: 1 minute 30 seconds
- Toggle the checkboxes to demonstrate the YAML changing
- "Select only the alerts you need and apply them immediately"
```

---

## §3 Dynamic YAML Generation

### §3.1 Radio/Checkbox to YAML (NodeClass Builder)

Generate EC2NodeClass YAML from a combination of radio buttons and checkboxes.

**When to use**: Karpenter NodeClass, NodePool, complex K8s resource configuration

:::html
```html
<div class="nodeclass-builder">
  <div class="builder-section">
    <h4>Instance Category</h4>
    <div class="radio-group">
      <label class="radio-option">
        <input type="radio" name="category" value="general" checked>
        <span>General Purpose (m5, m6i)</span>
      </label>
      <label class="radio-option">
        <input type="radio" name="category" value="compute">
        <span>Compute Optimized (c5, c6i)</span>
      </label>
      <label class="radio-option">
        <input type="radio" name="category" value="memory">
        <span>Memory Optimized (r5, r6i)</span>
      </label>
    </div>
  </div>
  <div class="builder-section">
    <h4>Features</h4>
    <div class="checkbox-group">
      <label class="checkbox-option">
        <input type="checkbox" id="feat-spot" checked>
        <span>Enable Spot Instances</span>
      </label>
      <label class="checkbox-option">
        <input type="checkbox" id="feat-arm">
        <span>Include ARM64 (Graviton)</span>
      </label>
      <label class="checkbox-option">
        <input type="checkbox" id="feat-gpu">
        <span>GPU Instances</span>
      </label>
    </div>
  </div>
  <div class="builder-output">
    <h4>Generated EC2NodeClass</h4>
    <pre class="yaml-output" id="nodeclass-yaml"></pre>
  </div>
</div>
```

:::script
```javascript
(function() {
  const radios = document.querySelectorAll('input[name="category"]');
  const spotCheck = document.getElementById('feat-spot');
  const armCheck = document.getElementById('feat-arm');
  const gpuCheck = document.getElementById('feat-gpu');
  const yamlOutput = document.getElementById('nodeclass-yaml');

  const instanceMap = {
    general: ['m5', 'm6i', 'm6a', 'm7i'],
    compute: ['c5', 'c6i', 'c6a', 'c7i'],
    memory: ['r5', 'r6i', 'r6a', 'r7i']
  };

  function updatePreview() {
    const category = document.querySelector('input[name="category"]:checked').value;
    let families = [...instanceMap[category]];

    if (armCheck.checked) {
      families = families.concat(families.map(f => f + 'g'));
    }
    if (gpuCheck.checked) {
      families.push('g4dn', 'g5', 'p4d');
    }

    const capacityTypes = spotCheck.checked
      ? '["spot", "on-demand"]'
      : '["on-demand"]';

    yamlOutput.textContent = `apiVersion: karpenter.k8s.aws/v1
kind: EC2NodeClass
metadata:
  name: ${category}-nodes
spec:
  amiSelectorTerms:
    - alias: al2023@latest
  subnetSelectorTerms:
    - tags:
        karpenter.sh/discovery: "my-cluster"
  securityGroupSelectorTerms:
    - tags:
        karpenter.sh/discovery: "my-cluster"
  instanceStorePolicy: RAID0
---
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: ${category}-pool
spec:
  template:
    spec:
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: ${category}-nodes
      requirements:
        - key: karpenter.k8s.aws/instance-family
          operator: In
          values: ${JSON.stringify(families)}
        - key: karpenter.sh/capacity-type
          operator: In
          values: ${capacityTypes}
        - key: kubernetes.io/arch
          operator: In
          values: ${armCheck.checked ? '["amd64", "arm64"]' : '["amd64"]'}
  limits:
    cpu: 1000
    memory: 1000Gi`;
  }

  radios.forEach(r => r.addEventListener('change', updatePreview));
  [spotCheck, armCheck, gpuCheck].forEach(cb => cb.addEventListener('change', updatePreview));
  updatePreview();
})();
```

:::css
```css
.nodeclass-builder {
  display: grid;
  grid-template-columns: 1fr 1.5fr;
  gap: 1.5rem;
}
.builder-section {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 1.2rem;
}
.builder-section h4 {
  font-size: 0.9rem;
  color: var(--text-accent);
  margin-bottom: 1rem;
}
.radio-group, .checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.radio-option, .checkbox-option {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  background: var(--bg-secondary);
  border-radius: 0.33rem;
  cursor: pointer;
  transition: background var(--transition-fast);
}
.radio-option:hover, .checkbox-option:hover {
  background: var(--bg-tertiary);
}
.radio-option input, .checkbox-option input {
  width: 16px;
  height: 16px;
  accent-color: var(--accent);
}
.radio-option span, .checkbox-option span {
  font-size: 0.85rem;
  color: var(--text-secondary);
}
.builder-output {
  grid-column: 1 / -1;
}
.builder-output h4 {
  font-size: 0.9rem;
  color: var(--text-muted);
  margin-bottom: 0.75rem;
}
```

:::notes
```
- Presentation time: 2 minutes
- The YAML changes based on the instance type/feature combination
- "The Graviton + Spot combination can save up to 75%"
```

---

### §3.2 Slider Values to YAML (Resource Recommendation)

Compute the slider values to generate a YAML in the VPA recommendation format.

**When to use**: Resource recommendations, capacity calculations, cost estimates

:::html
```html
<div class="recommendation-builder">
  <div class="rec-inputs">
    <h4>Current Resource Usage</h4>
    <div class="slider-group">
      <div class="slider-row">
        <label>Avg CPU</label>
        <input type="range" id="rec-cpu-avg" min="50" max="1000" value="250">
        <span class="slider-value" id="rec-cpu-avg-val">250m</span>
      </div>
      <div class="slider-row">
        <label>Peak CPU</label>
        <input type="range" id="rec-cpu-peak" min="100" max="2000" value="800">
        <span class="slider-value" id="rec-cpu-peak-val">800m</span>
      </div>
      <div class="slider-row">
        <label>Avg Memory</label>
        <input type="range" id="rec-mem-avg" min="64" max="2048" step="64" value="384">
        <span class="slider-value" id="rec-mem-avg-val">384Mi</span>
      </div>
      <div class="slider-row">
        <label>Peak Memory</label>
        <input type="range" id="rec-mem-peak" min="128" max="4096" step="64" value="768">
        <span class="slider-value" id="rec-mem-peak-val">768Mi</span>
      </div>
    </div>
  </div>
  <div class="rec-output">
    <h4>VPA Recommendation</h4>
    <pre class="yaml-output" id="rec-yaml"></pre>
  </div>
</div>
```

:::script
```javascript
(function() {
  const cpuAvg = document.getElementById('rec-cpu-avg');
  const cpuPeak = document.getElementById('rec-cpu-peak');
  const memAvg = document.getElementById('rec-mem-avg');
  const memPeak = document.getElementById('rec-mem-peak');
  const yamlOutput = document.getElementById('rec-yaml');

  function update() {
    const ca = parseInt(cpuAvg.value);
    const cp = parseInt(cpuPeak.value);
    const ma = parseInt(memAvg.value);
    const mp = parseInt(memPeak.value);

    document.getElementById('rec-cpu-avg-val').textContent = ca + 'm';
    document.getElementById('rec-cpu-peak-val').textContent = cp + 'm';
    document.getElementById('rec-mem-avg-val').textContent = ma + 'Mi';
    document.getElementById('rec-mem-peak-val').textContent = mp + 'Mi';

    // Calculate recommendations with headroom
    const lowerCpu = Math.round(ca * 0.9);
    const targetCpu = Math.round(ca * 1.15);
    const upperCpu = Math.round(cp * 1.2);
    const lowerMem = Math.round(ma * 0.95);
    const targetMem = Math.round(ma * 1.1);
    const upperMem = Math.round(mp * 1.25);

    yamlOutput.textContent = `# VPA Recommendation Status
status:
  recommendation:
    containerRecommendations:
      - containerName: app
        lowerBound:
          cpu: "${lowerCpu}m"
          memory: "${lowerMem}Mi"
        target:
          cpu: "${targetCpu}m"
          memory: "${targetMem}Mi"
        uncappedTarget:
          cpu: "${targetCpu}m"
          memory: "${targetMem}Mi"
        upperBound:
          cpu: "${upperCpu}m"
          memory: "${upperMem}Mi"

# Suggested Resource Spec
resources:
  requests:
    cpu: "${targetCpu}m"
    memory: "${targetMem}Mi"
  limits:
    cpu: "${upperCpu}m"
    memory: "${upperMem}Mi"`;
  }

  [cpuAvg, cpuPeak, memAvg, memPeak].forEach(s => s.addEventListener('input', update));
  update();
})();
```

:::css
```css
.recommendation-builder {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}
.rec-inputs, .rec-output {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 1.2rem;
}
.rec-inputs h4, .rec-output h4 {
  font-size: 0.9rem;
  color: var(--text-accent);
  margin-bottom: 1rem;
}
```

:::notes
```
- Presentation time: 1 minute
- Entering the actual usage values auto-calculates the VPA recommended values
- "target uses 15% headroom over the average, upper uses 20% headroom over the peak"
```

---

## §4 Canvas Animation with Controls

### §4.1 Phase Animation with Buttons (Signal Correlation)

Control a multi-stage canvas animation with Play/Next/Reset buttons.

**When to use**: Signal correlation, data flow, visualizing process stages

:::html
```html
<div class="phase-animation-card">
  <div class="canvas-container">
    <canvas id="signal-canvas"></canvas>
    <div class="canvas-controls">
      <button class="btn btn-sm" id="sig-prev">&#9664; Prev</button>
      <button class="btn btn-sm btn-primary" id="sig-play">&#9654; Play</button>
      <button class="btn btn-sm" id="sig-next">Next &#9654;</button>
      <button class="btn btn-sm" id="sig-reset">Reset</button>
    </div>
  </div>
  <div class="phase-indicator">
    <span class="phase-dot active" data-phase="0">1</span>
    <span class="phase-connector"></span>
    <span class="phase-dot" data-phase="1">2</span>
    <span class="phase-connector"></span>
    <span class="phase-dot" data-phase="2">3</span>
  </div>
  <div class="phase-label" id="phase-label">Phase 1: Metrics Collection</div>
</div>
```

:::script
```javascript
(function() {
  const canvas = document.getElementById('signal-canvas');
  const ctx = canvas.getContext('2d');
  const playBtn = document.getElementById('sig-play');
  const prevBtn = document.getElementById('sig-prev');
  const nextBtn = document.getElementById('sig-next');
  const resetBtn = document.getElementById('sig-reset');
  const phaseLabel = document.getElementById('phase-label');
  const phaseDots = document.querySelectorAll('.phase-dot');

  const W = 800, H = 300;
  canvas.width = W * 2;
  canvas.height = H * 2;
  canvas.style.width = W + 'px';
  canvas.style.height = H + 'px';
  ctx.scale(2, 2);

  const phases = [
    { label: 'Phase 1: Metrics Collection', color: '#74b9ff' },
    { label: 'Phase 2: Log Correlation', color: '#00b894' },
    { label: 'Phase 3: Trace Analysis', color: '#6c5ce7' }
  ];

  let currentPhase = 0;
  let animating = false;
  let animFrame = 0;

  function drawPhase(phase, progress) {
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = '#1a1d2e';
    ctx.fillRect(0, 0, W, H);

    // Draw signal boxes
    const boxes = [
      { x: 50, y: 120, label: 'Metrics', active: phase >= 0 },
      { x: 300, y: 120, label: 'Logs', active: phase >= 1 },
      { x: 550, y: 120, label: 'Traces', active: phase >= 2 }
    ];

    boxes.forEach((box, i) => {
      ctx.fillStyle = box.active ? phases[i].color : '#2d3250';
      ctx.strokeStyle = box.active ? phases[i].color : '#2d3250';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.roundRect(box.x, box.y, 180, 60, 8);
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = box.active ? '#fff' : '#6b7194';
      ctx.font = '600 16px Pretendard';
      ctx.textAlign = 'center';
      ctx.fillText(box.label, box.x + 90, box.y + 36);
    });

    // Draw arrows between active boxes
    if (phase >= 1) {
      drawArrow(ctx, 230, 150, 300, 150, phases[1].color, progress);
    }
    if (phase >= 2) {
      drawArrow(ctx, 480, 150, 550, 150, phases[2].color, progress);
    }
  }

  function drawArrow(ctx, x1, y1, x2, y2, color, progress) {
    const dx = (x2 - x1) * progress;
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x1 + dx, y1);
    ctx.stroke();

    if (progress >= 1) {
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.moveTo(x2, y1);
      ctx.lineTo(x2 - 10, y1 - 6);
      ctx.lineTo(x2 - 10, y1 + 6);
      ctx.fill();
    }
  }

  function updateUI() {
    phaseLabel.textContent = phases[currentPhase].label;
    phaseDots.forEach((dot, i) => {
      dot.classList.toggle('active', i <= currentPhase);
    });
  }

  function goToPhase(phase) {
    currentPhase = Math.max(0, Math.min(phases.length - 1, phase));
    drawPhase(currentPhase, 1);
    updateUI();
  }

  function animateToPhase(targetPhase) {
    if (animating) return;
    animating = true;
    animFrame = 0;
    const duration = 30;

    function step() {
      animFrame++;
      const progress = Math.min(1, animFrame / duration);
      drawPhase(targetPhase, progress);

      if (progress < 1) {
        requestAnimationFrame(step);
      } else {
        currentPhase = targetPhase;
        updateUI();
        animating = false;
      }
    }
    step();
  }

  prevBtn.addEventListener('click', () => goToPhase(currentPhase - 1));
  nextBtn.addEventListener('click', () => animateToPhase(currentPhase + 1));
  resetBtn.addEventListener('click', () => goToPhase(0));
  playBtn.addEventListener('click', () => {
    if (currentPhase < phases.length - 1) {
      animateToPhase(currentPhase + 1);
    } else {
      goToPhase(0);
    }
  });

  drawPhase(0, 1);
  updateUI();
})();
```

:::css
```css
.phase-animation-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 1.5rem;
}
.phase-animation-card .canvas-container {
  margin-bottom: 1rem;
}
.phase-animation-card canvas {
  display: block;
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
  border-radius: 0.33rem;
}
.phase-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  margin-bottom: 1rem;
}
.phase-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--bg-tertiary);
  border: 2px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-muted);
  transition: all var(--transition-normal);
}
.phase-dot.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}
.phase-connector {
  width: 40px;
  height: 2px;
  background: var(--border);
}
.phase-label {
  text-align: center;
  font-size: 1rem;
  color: var(--text-secondary);
}
```

:::notes
```
- Presentation time: 2 minutes
- Play advances automatically; Next/Prev give manual control
- "Explain the correlation among the three signals step by step"
```

---

### §4.2 Timeline Animation with Speed Control

A timeline animation driven by Start/Reset/Speed buttons plus requestAnimationFrame.

**When to use**: Rolling updates, scaling processes, visualizing the passage of time

:::html
```html
<div class="timeline-anim-card">
  <div class="canvas-container">
    <canvas id="timeline-canvas"></canvas>
    <div class="canvas-controls">
      <button class="btn btn-sm btn-primary" id="tl-start">&#9654; Start</button>
      <button class="btn btn-sm" id="tl-reset">Reset</button>
      <div class="speed-control">
        <label>Speed:</label>
        <select id="tl-speed">
          <option value="0.5">0.5x</option>
          <option value="1" selected>1x</option>
          <option value="2">2x</option>
          <option value="4">4x</option>
        </select>
      </div>
    </div>
  </div>
  <div class="stage-info">
    <span class="stage-badge" id="stage-badge">Waiting</span>
    <span class="stage-time" id="stage-time">0:00</span>
  </div>
</div>
```

:::script
```javascript
(function() {
  const canvas = document.getElementById('timeline-canvas');
  const ctx = canvas.getContext('2d');
  const startBtn = document.getElementById('tl-start');
  const resetBtn = document.getElementById('tl-reset');
  const speedSelect = document.getElementById('tl-speed');
  const stageBadge = document.getElementById('stage-badge');
  const stageTime = document.getElementById('stage-time');

  const W = 800, H = 200;
  canvas.width = W * 2;
  canvas.height = H * 2;
  canvas.style.width = W + 'px';
  canvas.style.height = H + 'px';
  ctx.scale(2, 2);

  const stages = [
    { name: 'Deploy v2', color: '#6c5ce7', duration: 2 },
    { name: 'Health Check', color: '#74b9ff', duration: 1.5 },
    { name: 'Scale Up', color: '#00b894', duration: 2 },
    { name: 'Drain v1', color: '#fdcb6e', duration: 1.5 },
    { name: 'Complete', color: '#00b894', duration: 0.5 }
  ];

  let running = false;
  let elapsed = 0;
  let lastTime = 0;
  let animId = null;

  function getTotalDuration() {
    return stages.reduce((sum, s) => sum + s.duration, 0);
  }

  function getCurrentStage(t) {
    let acc = 0;
    for (let i = 0; i < stages.length; i++) {
      if (t < acc + stages[i].duration) {
        return { index: i, progress: (t - acc) / stages[i].duration };
      }
      acc += stages[i].duration;
    }
    return { index: stages.length - 1, progress: 1 };
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = '#1a1d2e';
    ctx.fillRect(0, 0, W, H);

    const totalDuration = getTotalDuration();
    const { index: currentIndex, progress: stageProgress } = getCurrentStage(elapsed);

    // Draw timeline track
    ctx.fillStyle = '#2d3250';
    ctx.fillRect(50, 90, 700, 20);

    // Draw completed portion
    const completedWidth = (elapsed / totalDuration) * 700;
    ctx.fillStyle = stages[currentIndex].color;
    ctx.fillRect(50, 90, completedWidth, 20);

    // Draw stage markers
    let xPos = 50;
    stages.forEach((stage, i) => {
      const stageWidth = (stage.duration / totalDuration) * 700;

      // Stage label
      ctx.fillStyle = i <= currentIndex ? '#fff' : '#6b7194';
      ctx.font = '500 12px Pretendard';
      ctx.textAlign = 'center';
      ctx.fillText(stage.name, xPos + stageWidth / 2, 80);

      // Marker dot
      ctx.beginPath();
      ctx.arc(xPos, 100, 6, 0, Math.PI * 2);
      ctx.fillStyle = i <= currentIndex ? stage.color : '#2d3250';
      ctx.fill();

      xPos += stageWidth;
    });

    // End marker
    ctx.beginPath();
    ctx.arc(750, 100, 6, 0, Math.PI * 2);
    ctx.fillStyle = elapsed >= totalDuration ? '#00b894' : '#2d3250';
    ctx.fill();

    // Update UI
    stageBadge.textContent = stages[currentIndex].name;
    stageBadge.style.background = stages[currentIndex].color;
    const mins = Math.floor(elapsed / 60);
    const secs = Math.floor(elapsed % 60);
    stageTime.textContent = `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  function animate(timestamp) {
    if (!running) return;

    if (lastTime === 0) lastTime = timestamp;
    const delta = (timestamp - lastTime) / 1000;
    lastTime = timestamp;

    const speed = parseFloat(speedSelect.value);
    elapsed += delta * speed;

    if (elapsed >= getTotalDuration()) {
      elapsed = getTotalDuration();
      running = false;
      startBtn.textContent = '⟳ Replay';
    }

    draw();

    if (running) {
      animId = requestAnimationFrame(animate);
    }
  }

  startBtn.addEventListener('click', () => {
    if (elapsed >= getTotalDuration()) {
      elapsed = 0;
    }
    running = true;
    lastTime = 0;
    startBtn.textContent = '⏸ Pause';
    animId = requestAnimationFrame(animate);
  });

  resetBtn.addEventListener('click', () => {
    running = false;
    elapsed = 0;
    lastTime = 0;
    if (animId) cancelAnimationFrame(animId);
    startBtn.textContent = '▶ Start';
    draw();
  });

  draw();
})();
```

:::css
```css
.timeline-anim-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 1.5rem;
}
.timeline-anim-card canvas {
  display: block;
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
  border-radius: 0.33rem;
}
.speed-control {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-left: 1rem;
}
.speed-control label {
  font-size: 0.85rem;
  color: var(--text-muted);
}
.speed-control select {
  padding: 0.25rem 0.5rem;
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: 0.25rem;
  color: var(--text-primary);
  font-family: var(--font-main);
}
.stage-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-top: 1rem;
}
.stage-badge {
  padding: 0.33rem 0.75rem;
  border-radius: 0.33rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: #fff;
  background: var(--accent);
}
.stage-time {
  font-family: var(--font-mono);
  font-size: 1.2rem;
  color: var(--text-secondary);
}
```

:::notes
```
- Presentation time: 2 minutes
- Visualize the rolling-update process as a timeline
- Adjusting the speed lets you demo the whole process quickly
```

---

## §5 Live Input Patterns

### §5.1 Regex Tester with Highlighting

Highlights regex matches in a log sample against a text input.

**When to use**: Log parsing, filter rules, explaining pattern matching

:::html
```html
<div class="regex-tester-card">
  <div class="regex-input">
    <label>Regex Pattern</label>
    <input type="text" id="regex-pattern" value="ERROR|WARN" placeholder="Enter regex...">
  </div>
  <div class="log-sample">
    <label>Log Sample</label>
    <div class="log-content" id="log-content">
      <div class="log-line">[2025-01-15 10:23:45] INFO Starting application...</div>
      <div class="log-line">[2025-01-15 10:23:46] INFO Connected to database</div>
      <div class="log-line">[2025-01-15 10:23:47] WARN High memory usage detected</div>
      <div class="log-line">[2025-01-15 10:23:48] ERROR Failed to connect to Redis</div>
      <div class="log-line">[2025-01-15 10:23:49] INFO Retrying connection...</div>
      <div class="log-line">[2025-01-15 10:23:50] ERROR Connection timeout after 30s</div>
      <div class="log-line">[2025-01-15 10:23:51] WARN Falling back to local cache</div>
    </div>
  </div>
  <div class="match-count">
    Matches: <span id="match-count">0</span>
  </div>
</div>
```

:::script
```javascript
(function() {
  const patternInput = document.getElementById('regex-pattern');
  const logContent = document.getElementById('log-content');
  const matchCount = document.getElementById('match-count');
  const originalLines = Array.from(logContent.querySelectorAll('.log-line'))
    .map(el => el.textContent);

  function highlightMatches() {
    const pattern = patternInput.value;
    let regex;
    let count = 0;

    try {
      regex = new RegExp('(' + pattern + ')', 'gi');
    } catch (e) {
      regex = null;
    }

    const lines = logContent.querySelectorAll('.log-line');
    lines.forEach((line, i) => {
      const text = originalLines[i];
      if (regex && pattern) {
        const matches = text.match(regex);
        if (matches) count += matches.length;
        line.innerHTML = text.replace(regex, '<mark class="highlight">$1</mark>');
      } else {
        line.textContent = text;
      }
    });

    matchCount.textContent = count;
  }

  patternInput.addEventListener('input', highlightMatches);
  highlightMatches();
})();
```

:::css
```css
.regex-tester-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 1.5rem;
}
.regex-input {
  margin-bottom: 1rem;
}
.regex-input label {
  display: block;
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}
.regex-input input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 0.33rem;
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: 0.9rem;
}
.regex-input input:focus {
  outline: none;
  border-color: var(--accent);
}
.log-sample label {
  display: block;
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}
.log-content {
  background: #0d1117;
  border: 1px solid var(--border);
  border-radius: 0.33rem;
  padding: 0.75rem;
  font-family: var(--font-mono);
  font-size: 0.8rem;
  max-height: 200px;
  overflow-y: auto;
}
.log-line {
  padding: 0.25rem 0;
  color: var(--text-secondary);
  white-space: nowrap;
}
.log-line .highlight {
  background: rgba(253, 203, 110, 0.3);
  color: var(--yellow);
  padding: 0 2px;
  border-radius: 2px;
}
.match-count {
  margin-top: 1rem;
  font-size: 0.9rem;
  color: var(--text-muted);
}
.match-count span {
  font-weight: 600;
  color: var(--accent-light);
}
```

:::notes
```
- Presentation time: 1 minute
- Demo the real-time highlighting as the regex is typed
- "Filter down to just the problem logs with ERROR|WARN"
```

---

### §5.2 Sampling Rate Calculator

Adjusting the sampling rate with a slider computes the cost/trace count/error-capture rate.

**When to use**: X-Ray/ADOT sampling, logging cost optimization

:::html
```html
<div class="sampling-card">
  <div class="sampling-control">
    <label>Sampling Rate</label>
    <div class="slider-row">
      <span class="slider-min">1%</span>
      <input type="range" id="sampling-rate" min="1" max="100" value="10">
      <span class="slider-max">100%</span>
    </div>
    <div class="sampling-value" id="sampling-display">10%</div>
  </div>
  <div class="sampling-metrics">
    <div class="sampling-metric">
      <div class="metric-icon">&#128176;</div>
      <div class="metric-value" id="cost-value">$150</div>
      <div class="metric-label">Est. Monthly Cost</div>
    </div>
    <div class="sampling-metric">
      <div class="metric-icon">&#128202;</div>
      <div class="metric-value" id="traces-value">100K</div>
      <div class="metric-label">Traces/Month</div>
    </div>
    <div class="sampling-metric highlight">
      <div class="metric-icon">&#9888;</div>
      <div class="metric-value" id="errors-value">95%</div>
      <div class="metric-label">Error Capture</div>
    </div>
  </div>
  <div class="sampling-note" id="sampling-note"></div>
</div>
```

:::script
```javascript
(function() {
  const slider = document.getElementById('sampling-rate');
  const display = document.getElementById('sampling-display');
  const costValue = document.getElementById('cost-value');
  const tracesValue = document.getElementById('traces-value');
  const errorsValue = document.getElementById('errors-value');
  const note = document.getElementById('sampling-note');

  const BASE_TRACES = 1000000; // 1M requests/month
  const COST_PER_TRACE = 0.0015;

  function update() {
    const rate = parseInt(slider.value);
    display.textContent = rate + '%';

    const traces = Math.round(BASE_TRACES * rate / 100);
    const cost = traces * COST_PER_TRACE;
    // Error capture is always higher due to error-based sampling
    const errorCapture = Math.min(100, rate + Math.round((100 - rate) * 0.8));

    costValue.textContent = '$' + cost.toFixed(0);
    tracesValue.textContent = (traces / 1000).toFixed(0) + 'K';
    errorsValue.textContent = errorCapture + '%';

    if (rate <= 5) {
      note.textContent = '⚠️ Very low sampling - may miss important patterns';
      note.className = 'sampling-note note-warning';
    } else if (rate <= 20) {
      note.textContent = '✓ Good balance of cost and visibility';
      note.className = 'sampling-note note-success';
    } else if (rate <= 50) {
      note.textContent = 'ℹ️ Higher visibility, moderate cost';
      note.className = 'sampling-note note-info';
    } else {
      note.textContent = '💰 Full visibility but high cost - consider for debugging only';
      note.className = 'sampling-note note-warning';
    }
  }

  slider.addEventListener('input', update);
  update();
})();
```

:::css
```css
.sampling-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 1.5rem;
}
.sampling-control {
  margin-bottom: 1.5rem;
}
.sampling-control label {
  display: block;
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin-bottom: 0.75rem;
}
.sampling-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--accent-light);
  text-align: center;
  margin-top: 0.5rem;
}
.sampling-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-bottom: 1rem;
}
.sampling-metric {
  text-align: center;
  padding: 1rem;
  background: var(--bg-secondary);
  border-radius: 0.5rem;
}
.sampling-metric.highlight {
  background: var(--accent-glow);
  border: 1px solid var(--accent);
}
.metric-icon {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}
.sampling-note {
  padding: 0.75rem 1rem;
  border-radius: 0.33rem;
  font-size: 0.9rem;
  text-align: center;
}
.note-success { background: var(--green-bg); color: var(--green); }
.note-warning { background: var(--yellow-bg); color: var(--yellow); }
.note-info { background: var(--blue-bg); color: var(--blue); }
```

:::notes
```
- Presentation time: 1 minute
- The cost/visibility tradeoff across sampling rates
- "10-20% is suitable for most workloads"
```

---

### §5.3 QoS Class Calculator

Setting requests/limits with four sliders automatically determines the QoS class.

**When to use**: Pod QoS classes, resource-configuration training

:::html
```html
<div class="qos-calculator-card">
  <div class="qos-inputs">
    <div class="slider-group">
      <div class="slider-row">
        <label>CPU Request</label>
        <input type="range" id="qos-cpu-req" min="0" max="1000" step="100" value="500">
        <span class="slider-value" id="qos-cpu-req-val">500m</span>
      </div>
      <div class="slider-row">
        <label>CPU Limit</label>
        <input type="range" id="qos-cpu-lim" min="0" max="2000" step="100" value="1000">
        <span class="slider-value" id="qos-cpu-lim-val">1000m</span>
      </div>
      <div class="slider-row">
        <label>Memory Request</label>
        <input type="range" id="qos-mem-req" min="0" max="2048" step="128" value="512">
        <span class="slider-value" id="qos-mem-req-val">512Mi</span>
      </div>
      <div class="slider-row">
        <label>Memory Limit</label>
        <input type="range" id="qos-mem-lim" min="0" max="4096" step="128" value="1024">
        <span class="slider-value" id="qos-mem-lim-val">1024Mi</span>
      </div>
    </div>
  </div>
  <div class="qos-result">
    <div class="qos-cards">
      <div class="qos-card" id="qos-guaranteed">
        <h4>Guaranteed</h4>
        <p>requests = limits (all resources)</p>
      </div>
      <div class="qos-card" id="qos-burstable">
        <h4>Burstable</h4>
        <p>requests &lt; limits</p>
      </div>
      <div class="qos-card" id="qos-besteffort">
        <h4>BestEffort</h4>
        <p>No requests or limits</p>
      </div>
    </div>
    <div class="qos-explanation" id="qos-explanation"></div>
  </div>
</div>
```

:::script
```javascript
(function() {
  const cpuReq = document.getElementById('qos-cpu-req');
  const cpuLim = document.getElementById('qos-cpu-lim');
  const memReq = document.getElementById('qos-mem-req');
  const memLim = document.getElementById('qos-mem-lim');
  const explanation = document.getElementById('qos-explanation');

  function update() {
    const cr = parseInt(cpuReq.value);
    const cl = parseInt(cpuLim.value);
    const mr = parseInt(memReq.value);
    const ml = parseInt(memLim.value);

    document.getElementById('qos-cpu-req-val').textContent = cr ? cr + 'm' : '-';
    document.getElementById('qos-cpu-lim-val').textContent = cl ? cl + 'm' : '-';
    document.getElementById('qos-mem-req-val').textContent = mr ? mr + 'Mi' : '-';
    document.getElementById('qos-mem-lim-val').textContent = ml ? ml + 'Mi' : '-';

    // Reset all cards
    document.querySelectorAll('.qos-card').forEach(c => c.classList.remove('active'));

    let qosClass, desc;

    if (cr === 0 && cl === 0 && mr === 0 && ml === 0) {
      qosClass = 'qos-besteffort';
      desc = 'No resources defined. Pod will be first to be evicted under pressure.';
    } else if (cr === cl && mr === ml && cr > 0 && mr > 0) {
      qosClass = 'qos-guaranteed';
      desc = 'Requests equal limits for all resources. Pod has highest priority and predictable resources.';
    } else {
      qosClass = 'qos-burstable';
      desc = 'Requests differ from limits. Pod can burst but may be evicted if node is under pressure.';
    }

    document.getElementById(qosClass).classList.add('active');
    explanation.textContent = desc;
  }

  [cpuReq, cpuLim, memReq, memLim].forEach(s => s.addEventListener('input', update));
  update();
})();
```

:::css
```css
.qos-calculator-card {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 1.5rem;
}
.qos-inputs, .qos-result {
  display: flex;
  flex-direction: column;
}
.qos-cards {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.qos-card {
  padding: 0.75rem 1rem;
  background: var(--bg-secondary);
  border: 2px solid transparent;
  border-radius: 0.5rem;
  transition: all var(--transition-fast);
}
.qos-card h4 {
  font-size: 0.95rem;
  color: var(--text-muted);
  margin-bottom: 0.25rem;
}
.qos-card p {
  font-size: 0.8rem;
  color: var(--text-muted);
}
.qos-card.active {
  border-color: var(--accent);
  background: var(--accent-glow);
}
.qos-card.active h4 {
  color: var(--accent-light);
}
#qos-guaranteed.active { border-color: var(--green); background: var(--green-bg); }
#qos-guaranteed.active h4 { color: var(--green); }
#qos-burstable.active { border-color: var(--yellow); background: var(--yellow-bg); }
#qos-burstable.active h4 { color: var(--yellow); }
#qos-besteffort.active { border-color: var(--red); background: var(--red-bg); }
#qos-besteffort.active h4 { color: var(--red); }
.qos-explanation {
  font-size: 0.9rem;
  color: var(--text-secondary);
  padding: 0.75rem;
  background: var(--bg-tertiary);
  border-radius: 0.33rem;
}
```

:::notes
```
- Presentation time: 1 minute 30 seconds
- Change the resource combination via the sliders → QoS class is determined automatically
- "Guaranteed is the most stable; BestEffort is first in line for eviction"
```

---

## §6 Expandable Content Patterns

### §6.1 Command Card with Output Toggle

A card pattern where clicking expands the command's output.

**When to use**: kubectl commands, troubleshooting guides, step-by-step instructions

:::html
```html
<div class="command-cards">
  <div class="command-card" data-expanded="false">
    <div class="command-header">
      <code class="command-text">kubectl get pods -o wide</code>
      <span class="expand-hint">Click to see output</span>
    </div>
    <div class="command-output">
      <pre>NAME                     READY   STATUS    RESTARTS   AGE   IP           NODE
nginx-6799fc88d8-4xkpv   1/1     Running   0          2d    10.0.1.45    ip-10-0-1-100
nginx-6799fc88d8-8rwtj   1/1     Running   0          2d    10.0.2.67    ip-10-0-2-200
redis-7b48c6f9c4-mz5px   1/1     Running   0          5d    10.0.1.89    ip-10-0-1-100</pre>
    </div>
  </div>
  <div class="command-card" data-expanded="false">
    <div class="command-header">
      <code class="command-text">kubectl describe node ip-10-0-1-100 | grep -A5 Conditions</code>
      <span class="expand-hint">Click to see output</span>
    </div>
    <div class="command-output">
      <pre>Conditions:
  Type             Status  LastHeartbeatTime                 Reason
  ----             ------  -----------------                 ------
  MemoryPressure   False   Mon, 15 Jan 2025 10:30:00 +0000   KubeletHasSufficientMemory
  DiskPressure     False   Mon, 15 Jan 2025 10:30:00 +0000   KubeletHasNoDiskPressure
  Ready            True    Mon, 15 Jan 2025 10:30:00 +0000   KubeletReady</pre>
    </div>
  </div>
  <div class="command-card" data-expanded="false">
    <div class="command-header">
      <code class="command-text">kubectl top pods --sort-by=memory</code>
      <span class="expand-hint">Click to see output</span>
    </div>
    <div class="command-output">
      <pre>NAME                     CPU(cores)   MEMORY(bytes)
redis-7b48c6f9c4-mz5px   45m          256Mi
nginx-6799fc88d8-4xkpv   12m          128Mi
nginx-6799fc88d8-8rwtj   10m          124Mi</pre>
    </div>
  </div>
</div>
```

:::script
```javascript
(function() {
  const cards = document.querySelectorAll('.command-card');

  cards.forEach(card => {
    card.addEventListener('click', () => {
      const isExpanded = card.dataset.expanded === 'true';
      card.dataset.expanded = !isExpanded;
      card.classList.toggle('expanded', !isExpanded);
    });
  });
})();
```

:::css
```css
.command-cards {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.command-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  overflow: hidden;
  cursor: pointer;
  transition: border-color var(--transition-fast);
}
.command-card:hover {
  border-color: var(--accent);
}
.command-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: var(--bg-secondary);
}
.command-text {
  font-family: var(--font-mono);
  font-size: 0.85rem;
  color: var(--accent-light);
}
.expand-hint {
  font-size: 0.75rem;
  color: var(--text-muted);
  transition: opacity var(--transition-fast);
}
.command-card.expanded .expand-hint {
  opacity: 0;
}
.command-output {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.3s ease;
}
.command-card.expanded .command-output {
  max-height: 200px;
}
.command-output pre {
  margin: 0;
  padding: 1rem;
  background: #0d1117;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  line-height: 1.5;
  color: #c9d1d9;
  overflow-x: auto;
}
```

:::notes
```
- Presentation time: 1 minute
- Click each command to see its output
- "This is the order to follow during actual troubleshooting"
```

---

### §6.2 Pipeline Component Selector

A pattern where clicking a pipeline stage displays a detail panel.

**When to use**: CI/CD pipelines, data flow, architecture components

:::html
```html
<div class="pipeline-selector">
  <div class="pipeline-stages">
    <div class="pipeline-stage active" data-stage="source">
      <div class="stage-icon">&#128230;</div>
      <div class="stage-name">Source</div>
    </div>
    <div class="stage-arrow">&#8594;</div>
    <div class="pipeline-stage" data-stage="build">
      <div class="stage-icon">&#128736;</div>
      <div class="stage-name">Build</div>
    </div>
    <div class="stage-arrow">&#8594;</div>
    <div class="pipeline-stage" data-stage="test">
      <div class="stage-icon">&#9989;</div>
      <div class="stage-name">Test</div>
    </div>
    <div class="stage-arrow">&#8594;</div>
    <div class="pipeline-stage" data-stage="deploy">
      <div class="stage-icon">&#128640;</div>
      <div class="stage-name">Deploy</div>
    </div>
  </div>
  <div class="pipeline-details">
    <div class="detail-panel active" id="detail-source">
      <h4>Source Stage</h4>
      <ul>
        <li>Trigger: Push to main branch</li>
        <li>Provider: GitHub / CodeCommit</li>
        <li>Branch: main, feature/*</li>
      </ul>
    </div>
    <div class="detail-panel" id="detail-build">
      <h4>Build Stage</h4>
      <ul>
        <li>Runtime: CodeBuild</li>
        <li>Image: aws/codebuild/amazonlinux2-x86_64-standard:4.0</li>
        <li>Artifacts: Docker image → ECR</li>
      </ul>
    </div>
    <div class="detail-panel" id="detail-test">
      <h4>Test Stage</h4>
      <ul>
        <li>Unit Tests: Jest / pytest</li>
        <li>Integration: TestContainers</li>
        <li>Coverage threshold: 80%</li>
      </ul>
    </div>
    <div class="detail-panel" id="detail-deploy">
      <h4>Deploy Stage</h4>
      <ul>
        <li>Target: EKS Cluster</li>
        <li>Strategy: Rolling Update</li>
        <li>Approval: Manual for prod</li>
      </ul>
    </div>
  </div>
</div>
```

:::script
```javascript
(function() {
  const stages = document.querySelectorAll('.pipeline-stage');
  const panels = document.querySelectorAll('.detail-panel');

  stages.forEach(stage => {
    stage.addEventListener('click', () => {
      const target = stage.dataset.stage;

      stages.forEach(s => s.classList.remove('active'));
      stage.classList.add('active');

      panels.forEach(p => p.classList.remove('active'));
      document.getElementById('detail-' + target).classList.add('active');
    });
  });
})();
```

:::css
```css
.pipeline-selector {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 1.5rem;
}
.pipeline-stages {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}
.pipeline-stage {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem 1.5rem;
  background: var(--bg-secondary);
  border: 2px solid transparent;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.pipeline-stage:hover {
  background: var(--bg-tertiary);
}
.pipeline-stage.active {
  border-color: var(--accent);
  background: var(--accent-glow);
}
.stage-icon {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}
.stage-name {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-secondary);
}
.pipeline-stage.active .stage-name {
  color: var(--accent-light);
}
.stage-arrow {
  font-size: 1.2rem;
  color: var(--text-muted);
}
.detail-panel {
  display: none;
  animation: fadeIn 0.3s ease;
}
.detail-panel.active {
  display: block;
}
.detail-panel h4 {
  font-size: 1.1rem;
  color: var(--text-accent);
  margin-bottom: 0.75rem;
}
.detail-panel ul {
  padding-left: 1.25rem;
}
.detail-panel li {
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}
```

:::notes
```
- Presentation time: 1 minute
- Click each stage to give a detailed explanation
- "CodePipeline's basic 4-stage configuration"
```

---

## §7 DOM Animation Patterns

### §7.1 Staggered Card Reveal

An animation where cards appear one after another; runs automatically when the slide enters.

**When to use**: Feature introductions, comparison items, step-by-step explanations

:::html
```html
<div class="staggered-cards">
  <div class="reveal-card animate-in">
    <div class="card-number">01</div>
    <h4>Provision</h4>
    <p>Karpenter provisions right-sized nodes in seconds</p>
  </div>
  <div class="reveal-card animate-in">
    <div class="card-number">02</div>
    <h4>Schedule</h4>
    <p>Kubernetes scheduler places pods on optimal nodes</p>
  </div>
  <div class="reveal-card animate-in">
    <div class="card-number">03</div>
    <h4>Consolidate</h4>
    <p>Karpenter consolidates underutilized nodes</p>
  </div>
  <div class="reveal-card animate-in">
    <div class="card-number">04</div>
    <h4>Optimize</h4>
    <p>Continuous right-sizing based on actual usage</p>
  </div>
</div>
```

:::script
```javascript
(function() {
  const cards = document.querySelectorAll('.reveal-card.animate-in');

  // Reset all cards
  cards.forEach(card => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(20px)';
  });

  // Staggered reveal
  cards.forEach((card, i) => {
    setTimeout(() => {
      card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      card.style.opacity = '1';
      card.style.transform = 'translateY(0)';
    }, i * 150);
  });
})();
```

:::css
```css
.staggered-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
}
.reveal-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 1.5rem;
  text-align: center;
}
.card-number {
  font-size: 2rem;
  font-weight: 700;
  color: var(--accent);
  opacity: 0.3;
  margin-bottom: 0.5rem;
}
.reveal-card h4 {
  font-size: 1.1rem;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}
.reveal-card p {
  font-size: 0.85rem;
  color: var(--text-secondary);
}
```

:::notes
```
- Presentation time: 30 seconds
- Cards appear one after another as the slide enters
- "Visualizes the 4-stage automation cycle"
```

---

### §7.2 Node/Pod Grid with State Transitions

Represents state changes in a node grid as an animation.

**When to use**: Cluster status, node lifecycle, visualizing scaling

:::html
```html
<div class="node-grid-card">
  <div class="grid-controls">
    <button class="btn btn-sm" id="grid-scale-up">Scale Up</button>
    <button class="btn btn-sm" id="grid-cordon">Cordon Node</button>
    <button class="btn btn-sm" id="grid-drain">Drain & Terminate</button>
    <button class="btn btn-sm" id="grid-reset">Reset</button>
  </div>
  <div class="node-grid-container">
    <div class="node-grid" id="node-grid"></div>
  </div>
  <div class="grid-legend">
    <span class="legend-item"><span class="legend-dot ready"></span> Ready</span>
    <span class="legend-item"><span class="legend-dot cordoned"></span> Cordoned</span>
    <span class="legend-item"><span class="legend-dot terminating"></span> Terminating</span>
    <span class="legend-item"><span class="legend-dot empty"></span> Empty</span>
  </div>
</div>
```

:::script
```javascript
(function() {
  const grid = document.getElementById('node-grid');
  const scaleUpBtn = document.getElementById('grid-scale-up');
  const cordonBtn = document.getElementById('grid-cordon');
  const drainBtn = document.getElementById('grid-drain');
  const resetBtn = document.getElementById('grid-reset');

  const COLS = 8;
  const ROWS = 4;
  let nodes = [];

  function initGrid() {
    grid.innerHTML = '';
    nodes = [];
    for (let i = 0; i < COLS * ROWS; i++) {
      const cell = document.createElement('div');
      cell.className = 'node-cell';
      if (i < 20) {
        cell.classList.add('node-ready');
        cell.textContent = 'N' + (i + 1);
        nodes.push({ el: cell, state: 'ready', index: i });
      } else {
        cell.classList.add('node-empty');
        nodes.push({ el: cell, state: 'empty', index: i });
      }
      grid.appendChild(cell);
    }
  }

  function scaleUp() {
    const emptyNodes = nodes.filter(n => n.state === 'empty');
    if (emptyNodes.length === 0) return;

    const toAdd = emptyNodes.slice(0, 4);
    toAdd.forEach((node, i) => {
      setTimeout(() => {
        node.el.classList.remove('node-empty');
        node.el.classList.add('node-ready');
        node.el.textContent = 'N' + (node.index + 1);
        node.state = 'ready';
      }, i * 200);
    });
  }

  function cordonNode() {
    const readyNodes = nodes.filter(n => n.state === 'ready');
    if (readyNodes.length === 0) return;

    const node = readyNodes[readyNodes.length - 1];
    node.el.classList.remove('node-ready');
    node.el.classList.add('node-cordoned');
    node.state = 'cordoned';
  }

  function drainAndTerminate() {
    const cordonedNodes = nodes.filter(n => n.state === 'cordoned');
    if (cordonedNodes.length === 0) return;

    const node = cordonedNodes[0];
    node.el.classList.remove('node-cordoned');
    node.el.classList.add('node-terminating');
    node.state = 'terminating';

    setTimeout(() => {
      node.el.classList.remove('node-terminating');
      node.el.classList.add('node-empty');
      node.el.textContent = '';
      node.state = 'empty';
    }, 1500);
  }

  scaleUpBtn.addEventListener('click', scaleUp);
  cordonBtn.addEventListener('click', cordonNode);
  drainBtn.addEventListener('click', drainAndTerminate);
  resetBtn.addEventListener('click', initGrid);

  initGrid();
})();
```

:::css
```css
.node-grid-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 1.5rem;
}
.grid-controls {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  justify-content: center;
}
.node-grid-container {
  background: var(--bg-secondary);
  border-radius: 0.5rem;
  padding: 1rem;
  margin-bottom: 1rem;
}
.node-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 0.5rem;
}
.grid-legend {
  display: flex;
  justify-content: center;
  gap: 1.5rem;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: var(--text-muted);
}
.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 3px;
}
.legend-dot.ready { background: var(--green); }
.legend-dot.cordoned { background: var(--yellow); }
.legend-dot.terminating { background: var(--red); }
.legend-dot.empty { background: var(--bg-tertiary); border: 1px solid var(--border); }
```

:::notes
```
- Presentation time: 2 minutes
- Demo in the order Scale Up → Cordon → Drain
- "Karpenter automatically manages the node lifecycle"
```

---

### §7.3 Step Flow Animation

A process-flow animation where steps activate one after another.

**When to use**: Process flows, workflows, sequential steps

:::html
```html
<div class="step-flow-card">
  <div class="flow-steps">
    <div class="flow-step" data-step="1">
      <div class="step-circle">1</div>
      <div class="step-label">Request</div>
    </div>
    <div class="flow-connector"></div>
    <div class="flow-step" data-step="2">
      <div class="step-circle">2</div>
      <div class="step-label">Authenticate</div>
    </div>
    <div class="flow-connector"></div>
    <div class="flow-step" data-step="3">
      <div class="step-circle">3</div>
      <div class="step-label">Authorize</div>
    </div>
    <div class="flow-connector"></div>
    <div class="flow-step" data-step="4">
      <div class="step-circle">4</div>
      <div class="step-label">Execute</div>
    </div>
    <div class="flow-connector"></div>
    <div class="flow-step" data-step="5">
      <div class="step-circle">5</div>
      <div class="step-label">Response</div>
    </div>
  </div>
  <div class="flow-controls">
    <button class="btn btn-sm btn-primary" id="flow-start">&#9654; Start Flow</button>
    <button class="btn btn-sm" id="flow-reset">Reset</button>
  </div>
</div>
```

:::script
```javascript
(function() {
  const steps = document.querySelectorAll('.flow-step');
  const connectors = document.querySelectorAll('.flow-connector');
  const startBtn = document.getElementById('flow-start');
  const resetBtn = document.getElementById('flow-reset');

  let currentStep = 0;
  let interval = null;

  function resetFlow() {
    currentStep = 0;
    if (interval) clearInterval(interval);
    steps.forEach(s => s.classList.remove('active', 'done'));
    connectors.forEach(c => c.classList.remove('active'));
    startBtn.textContent = '▶ Start Flow';
  }

  function advanceStep() {
    if (currentStep > 0 && currentStep <= steps.length) {
      steps[currentStep - 1].classList.remove('active');
      steps[currentStep - 1].classList.add('done');
      if (currentStep <= connectors.length) {
        connectors[currentStep - 1].classList.add('active');
      }
    }

    currentStep++;

    if (currentStep <= steps.length) {
      steps[currentStep - 1].classList.add('active');
    } else {
      clearInterval(interval);
      startBtn.textContent = '⟳ Replay';
    }
  }

  function startFlow() {
    if (currentStep >= steps.length) {
      resetFlow();
    }
    interval = setInterval(advanceStep, 800);
    startBtn.textContent = '⏸ Running...';
  }

  startBtn.addEventListener('click', startFlow);
  resetBtn.addEventListener('click', resetFlow);
})();
```

:::css
```css
.step-flow-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 1.5rem;
}
.flow-steps {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  margin-bottom: 1.5rem;
}
.flow-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: all var(--transition-normal);
}
.step-circle {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--bg-tertiary);
  border: 2px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: var(--text-muted);
  transition: all var(--transition-normal);
}
.flow-step.active .step-circle {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
  box-shadow: 0 0 20px var(--accent-glow);
  transform: scale(1.1);
}
.flow-step.done .step-circle {
  background: var(--green);
  border-color: var(--green);
  color: #fff;
}
.step-label {
  margin-top: 0.5rem;
  font-size: 0.8rem;
  color: var(--text-muted);
  transition: color var(--transition-normal);
}
.flow-step.active .step-label,
.flow-step.done .step-label {
  color: var(--text-primary);
}
.flow-connector {
  width: 60px;
  height: 2px;
  background: var(--border);
  margin-bottom: 1.5rem;
  transition: background var(--transition-normal);
}
.flow-connector.active {
  background: var(--green);
}
.flow-controls {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
}
```

:::notes
```
- Presentation time: 1 minute
- Start advances automatically, highlighting each step
- "The 5-stage processing flow of an API request"
```

---

### §7.4 Cost Counter Animation

An animation where numbers smoothly count up/down.

**When to use**: Cost savings, performance improvements, emphasizing a numeric change

:::html
```html
<div class="cost-counter-card">
  <div class="counter-display">
    <div class="counter-item">
      <div class="counter-label">Before Optimization</div>
      <div class="counter-value" id="cost-before">$0</div>
    </div>
    <div class="counter-arrow">&#8594;</div>
    <div class="counter-item highlight">
      <div class="counter-label">After Optimization</div>
      <div class="counter-value" id="cost-after">$0</div>
    </div>
    <div class="counter-item savings">
      <div class="counter-label">Monthly Savings</div>
      <div class="counter-value" id="cost-savings">$0</div>
    </div>
  </div>
  <div class="counter-controls">
    <button class="btn btn-sm btn-primary" id="counter-animate">&#9654; Animate</button>
    <button class="btn btn-sm" id="counter-reset">Reset</button>
  </div>
</div>
```

:::script
```javascript
(function() {
  const beforeEl = document.getElementById('cost-before');
  const afterEl = document.getElementById('cost-after');
  const savingsEl = document.getElementById('cost-savings');
  const animateBtn = document.getElementById('counter-animate');
  const resetBtn = document.getElementById('counter-reset');

  const TARGET_BEFORE = 12500;
  const TARGET_AFTER = 4800;
  const TARGET_SAVINGS = TARGET_BEFORE - TARGET_AFTER;

  function animateValue(el, start, end, duration, prefix = '$') {
    const startTime = performance.now();
    const diff = end - start;

    function update(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      const current = Math.round(start + diff * eased);
      el.textContent = prefix + current.toLocaleString();

      if (progress < 1) {
        requestAnimationFrame(update);
      }
    }

    requestAnimationFrame(update);
  }

  function runAnimation() {
    animateValue(beforeEl, 0, TARGET_BEFORE, 1500);
    setTimeout(() => {
      animateValue(afterEl, TARGET_BEFORE, TARGET_AFTER, 1200);
    }, 800);
    setTimeout(() => {
      animateValue(savingsEl, 0, TARGET_SAVINGS, 1000);
    }, 1500);
  }

  function resetCounter() {
    beforeEl.textContent = '$0';
    afterEl.textContent = '$0';
    savingsEl.textContent = '$0';
  }

  animateBtn.addEventListener('click', runAnimation);
  resetBtn.addEventListener('click', resetCounter);
})();
```

:::css
```css
.cost-counter-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 2rem;
}
.counter-display {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2rem;
  margin-bottom: 1.5rem;
}
.counter-item {
  text-align: center;
  padding: 1.5rem;
  background: var(--bg-secondary);
  border-radius: 0.5rem;
  min-width: 150px;
}
.counter-item.highlight {
  background: var(--green-bg);
  border: 1px solid var(--green);
}
.counter-item.savings {
  background: var(--accent-glow);
  border: 1px solid var(--accent);
}
.counter-label {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}
.counter-value {
  font-size: 2rem;
  font-weight: 700;
  font-family: var(--font-mono);
  color: var(--text-primary);
}
.counter-item.highlight .counter-value {
  color: var(--green);
}
.counter-item.savings .counter-value {
  color: var(--accent-light);
}
.counter-arrow {
  font-size: 2rem;
  color: var(--text-muted);
}
.counter-controls {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
}
```

:::notes
```
- Presentation time: 30 seconds
- Clicking Animate triggers the count-up effect
- "The optimization saves $7,700/month — a 62% reduction"
```

---

## Quick Reference

### CSS Variables (from theme.css)

```css
/* Colors */
--bg-card: #1e2235
--bg-secondary: #1a1d2e
--bg-tertiary: #232740
--border: #2d3250
--accent: #6c5ce7
--accent-light: #a29bfe
--accent-glow: rgba(108,92,231,.3)
--green: #00b894
--green-bg: rgba(0,184,148,.15)
--yellow: #fdcb6e
--yellow-bg: rgba(253,203,110,.15)
--red: #e17055
--red-bg: rgba(225,112,85,.15)
--blue: #74b9ff
--blue-bg: rgba(116,185,255,.15)
--text-primary: #e8eaf0
--text-secondary: #9ba1b8
--text-muted: #6b7194
--text-accent: #7b8cff

/* Typography */
--font-main: 'Pretendard', ...
--font-mono: 'JetBrains Mono', ...

/* Transitions */
--transition-fast: 150ms ease
--transition-normal: 300ms ease
```

### Common CSS Classes

| Class | Purpose |
|-------|---------|
| `.slider-group` | Container for slider rows |
| `.slider-row` | Label + slider + value layout |
| `.slider-value` | Mono font value display |
| `.yaml-output` | Code block for YAML |
| `.mode-selector` | Button group container |
| `.mode-btn` | Mode selection button |
| `.mode-content` | Content panel for mode |
| `.compare-toggle` | A/B toggle container |
| `.compare-btn` | Toggle button |
| `.compare-content` | Toggle panel |
| `.alert-toggle` | Checkbox row |
| `.qos-card` | QoS class indicator |
| `.command-card` | Expandable command |
| `.flow-step` | Process flow step |
| `.animate-in` | Stagger animation target |
| `.node-grid` | Node status grid |

### JavaScript Patterns

```javascript
// IIFE scope isolation
(function() {
  // All code here
})();

// Event delegation
element.addEventListener('click', () => { ... });

// requestAnimationFrame for smooth animation
function animate(timestamp) {
  // update logic
  if (running) requestAnimationFrame(animate);
}

// Staggered reveals
items.forEach((item, i) => {
  setTimeout(() => { item.classList.add('visible'); }, i * 150);
});
```
