# Remarp MD Preview Parity Design Document

This document provides a comprehensive analysis and implementation guide for achieving parity between the VSCode extension preview (`preview.ts`) and the target HTML output from `remarp_to_slides.py`.

---

## A. Architecture Overview

### preview.ts Pipeline (VSCode Extension)

```
Markdown Document
      │
      ▼
_parseSlides()          Parse --- separators → Slide[]
      │
      ▼
_renderMarkdown()       Convert MD → HTML (inline markdown, blocks)
      │
      ▼
_parseBlocks()          Parse :::block ... ::: structures
      │                 Returns text with placeholders + rendered HTML[]
      ▼
_renderInlineMarkdown() Process inline elements (bold, italic, links, code)
      │
      ▼
_transformByType()      Type-specific transformations:
      │                 - cover → _renderCoverContent()
      │                 - section → _renderSectionContent()
      │                 - thankyou → _renderThankyouContent()
      │                 - tabs → _renderTabsContent()
      │                 - code → _renderCodeContent()
      │                 - default → _wrapHeadingBody()
      ▼
HTML Template           Single slide rendered in webview panel
```

**Key characteristics:**
- Renders one slide at a time in a webview
- Uses inline `<style>` block with CSS variables
- Slide structure: `.slide-wrapper` > `.slide` > `.slide-heading-area` + `.slide-body-area`
- Edit mode support via `data-remarp-id` attributes

### remarp_to_slides.py Pipeline (Target HTML Builder)

```
Markdown File(s)
      │
      ▼
RemarpParser._parse_slide()    Parse directives, notes, fragments, columns, canvas DSL
      │
      ▼
RemarpBuilder.slide_to_html()  Dispatch by SlideType enum
      │
      ▼
_gen_<type>_slide()            Per-type generator methods:
      │                        - _gen_cover_slide()
      │                        - _gen_compare_slide()
      │                        - _gen_tabs_slide()
      │                        - _gen_canvas_slide()
      │                        - _gen_quiz_slide()
      │                        - _gen_code_slide()
      │                        - _gen_checklist_slide()
      │                        - _gen_timeline_slide()
      │                        - _gen_cards_slide()
      │                        - _gen_thankyou_slide()
      │
      ▼
_parse_body_content()          Process lists, paragraphs, inline markdown
_highlight_code()              Syntax highlighting with line ranges
      │
      ▼
Full HTML Document             All slides in .slide-deck container
                               + slide-framework.js for navigation
```

**Key characteristics:**
- Generates all slides in a single HTML document
- Uses external `theme.css` file
- Slide structure: `.slide-deck` > `.slide` > `.slide-header` + `.slide-body`
- Per-element `data-remarp-id` attributes for visual editing

### Key Difference Summary

| Aspect | preview.ts | remarp_to_slides.py |
|--------|------------|---------------------|
| Output | Single slide at a time | All slides in document |
| CSS | Inline `<style>` block | External `theme.css` |
| Container | `.slide-wrapper` > `.slide` | `.slide-deck` > `.slide` |
| Header class | `.slide-heading-area` | `.slide-header` |
| Body class | `.slide-body-area` | `.slide-body` |
| Navigation | Extension controls | `slide-framework.js` |

---

## B. Gap Analysis Per Slide Type

### 1. Cover Slide (`@type cover`)

**Current Preview Output (preview.ts:793-811):**
```html
<div class="slide slide-type-cover">
  <div class="slide-heading-area">
    <h1>Title</h1>
    <h2>Subtitle</h2>
  </div>
  <div class="speaker-info">
    <strong>Speaker Name</strong><br>Role
  </div>
</div>
```
- CSS: centered flex, gradient background, `.speaker-info` box

**Target HTML Output (remarp_to_slides.py:1741-1765):**
```html
<div class="slide" style="background:linear-gradient(...); padding:0; overflow:hidden;">
  <h1 style="position:absolute; left:5%; top:45%; ...">Title</h1>
  <p style="position:absolute; left:5%; top:60%; ...">Subtitle</p>
  <div style="position:absolute; left:5%; top:75%;">
    <p style="...">Speaker Name</p>
    <p style="...">Speaker Title</p>
    <p style="...">Company</p>
  </div>
</div>
```
- Uses absolute positioning for precise control
- Gradient accents via positioned `<div>`

**Fixes Needed:**
1. Switch to absolute positioning layout matching Python output
2. Add gradient accent line (positioned div)
3. Separate speaker name/title/company into individual `<p>` tags
4. Support `@background` directive for image backgrounds
5. Support `@badge` directive for badge images

### 2. Compare Slide (`@type compare`)

**Current Preview Output (preview.ts:873-885):**
```html
<div class="slide slide-type-compare">
  <div class="slide-heading-area"><h2>Heading</h2></div>
  <div class="slide-body-area">
    <div class="columns-2">
      <div class="col">
        <h3>Option A</h3>
        ...
      </div>
      <div class="col">
        <h3>Option B</h3>
        ...
      </div>
    </div>
  </div>
</div>
```
- Uses `.columns-2` > `.col` structure
- CSS styling for cards with border-bottom on h3

**Target HTML Output (remarp_to_slides.py:1908-1918):**
```html
<div class="slide">
  <div class="slide-header"><h2>Heading</h2></div>
  <div class="slide-body" data-compare-mode="side-by-side">
    <div class="compare-toggle">
      <button class="compare-btn active" data-compare="option-a">Option A</button>
      <button class="compare-btn" data-compare="option-b">Option B</button>
    </div>
    <div class="col-2" style="flex:1">
      <div class="card compare-content active compare-highlight" data-compare="option-a">
        <h3 style="color:var(--text-accent);...">Option A</h3>
        ...
      </div>
      <div class="card compare-content active" data-compare="option-b">
        <h3 style="...">Option B</h3>
        ...
      </div>
    </div>
  </div>
</div>
```
- Toggle buttons for highlighting selection
- `.col-2` grid class
- `.card` + `.compare-content` + `.compare-highlight` classes
- `data-compare-mode="side-by-side"` attribute

**Fixes Needed:**
1. Rename `.columns-2` → `.col-2`
2. Rename `.col` → `.card.compare-content`
3. Add `.compare-toggle` button bar
4. Add `data-compare` attributes for toggle functionality
5. Add `.compare-highlight` class to selected column
6. Add `data-compare-mode` attribute to body

### 3. Tabs Slide (`@type tabs`)

**Current Preview Output (preview.ts:898-922):**
```html
<div class="slide slide-type-tabs">
  <div class="slide-heading-area"><h2>Heading</h2></div>
  <div class="tab-bar">
    <div class="tab-btn active" data-tab="tab-0">Tab 1</div>
    <div class="tab-btn" data-tab="tab-1">Tab 2</div>
  </div>
  <div class="tab-panel active" data-tab="tab-0">...</div>
  <div class="tab-panel" data-tab="tab-1">...</div>
</div>
```
- Uses `<div>` for tab buttons
- Class `.tab-panel`

**Target HTML Output (remarp_to_slides.py:1971-1979):**
```html
<div class="slide">
  <div class="slide-header"><h2>Heading</h2></div>
  <div class="slide-body">
    <div class="tab-bar">
      <button class="tab-btn active" data-tab="slug">Tab 1</button>
      <button class="tab-btn" data-tab="slug2">Tab 2</button>
    </div>
    <div class="tab-content active" data-tab="slug">...</div>
    <div class="tab-content" data-tab="slug2">...</div>
  </div>
</div>
```
- Uses `<button>` for tab buttons
- Class `.tab-content` (not `.tab-panel`)
- Slugified `data-tab` values

**Fixes Needed:**
1. Use `<button>` instead of `<div>` for tab buttons
2. Rename `.tab-panel` → `.tab-content`
3. Generate slugified `data-tab` values from tab titles
4. Wrap content in `.slide-body`

### 4. Timeline Slide (`@type timeline`)

**Current Preview Output (preview.ts:841-872):**
```html
<div class="slide slide-type-timeline">
  <div class="slide-heading-area"><h2>Heading</h2></div>
  <div class="slide-body-area">
    <div class="timeline-step">
      <span class="step-label">1</span>
      <div>
        <h3>Step Title</h3>
        <p>Description</p>
      </div>
    </div>
    <!-- connector via CSS ::before pseudo-element -->
  </div>
</div>
```
- Vertical layout with CSS pseudo-elements for connectors
- `.step-label` is positioned absolutely via CSS

**Target HTML Output (remarp_to_slides.py:2383-2434):**
```html
<div class="slide">
  <div class="slide-header"><h2>Heading</h2></div>
  <div class="slide-body">
    <div class="timeline">
      <div class="timeline-step" data-step="1">
        <div class="timeline-dot" style="width:1.67rem;height:1.67rem;font-size:0.82rem">1</div>
        <div class="timeline-label" style="max-width:5rem">Step Title</div>
        <div class="timeline-desc">Description</div>
      </div>
      <div class="timeline-connector"></div>
      <div class="timeline-step" data-step="2">...</div>
    </div>
  </div>
  <script>/* Timeline step navigation JS */</script>
</div>
```
- Horizontal layout with explicit `.timeline-connector` elements
- `.timeline-dot` + `.timeline-label` + `.timeline-desc` structure
- Dynamic sizing based on step count
- Inline `<script>` for keyboard navigation

**Fixes Needed:**
1. Add `.timeline` container wrapper
2. Change to horizontal layout structure
3. Use explicit `.timeline-connector` elements (not CSS pseudo)
4. Rename `.step-label` → `.timeline-dot`
5. Add `.timeline-label` and `.timeline-desc` elements
6. Add `data-step` attributes
7. Add dynamic sizing based on step count
8. Add navigation script for step progression

### 5. Checklist Slide (`@type checklist`)

**Current Preview Output (preview.ts:887-896):**
```html
<div class="slide slide-type-checklist">
  <div class="slide-heading-area"><h2>Heading</h2></div>
  <div class="slide-body-area">
    <ul>
      <li><input type="checkbox"> Item 1</li>
      <li><input type="checkbox" checked> Item 2</li>
    </ul>
  </div>
</div>
```
- Uses native `<input type="checkbox">`
- Simple list structure

**Target HTML Output (remarp_to_slides.py:2296-2313):**
```html
<div class="slide">
  <div class="slide-header"><h2>Heading</h2></div>
  <div class="slide-body">
    <ul class="checklist">
      <li class="has-detail" data-remarp-id="s0-li-0">
        <span class="check"></span>
        <span class="checklist-text">Item text</span>
        <div class="checklist-detail">Expandable detail content</div>
      </li>
    </ul>
  </div>
</div>
```
- Uses `.checklist` class on `<ul>`
- Custom `.check` span (styled via CSS)
- `.checklist-text` wrapper for text
- `.checklist-detail` for expandable content
- `.has-detail` class for items with detail

**Fixes Needed:**
1. Add `.checklist` class to `<ul>`
2. Replace `<input type="checkbox">` with `<span class="check"></span>`
3. Wrap item text in `<span class="checklist-text">`
4. Support `.checklist-detail` for expandable content
5. Add `.has-detail` class when detail present
6. Add `data-remarp-id` attributes

### 6. Quiz Slide (`@type quiz`)

**Current Preview Output (preview.ts:715-719):**
```html
<div class="slide">
  <div class="slide-heading-area"><h2>Quiz</h2></div>
  <div class="slide-body-area">
    <div class="quiz-option">Option A</div>
    <div class="quiz-option correct">Option B (correct)</div>
  </div>
</div>
```
- Simple option divs with `.correct` class

**Target HTML Output (remarp_to_slides.py:2095-2108):**
```html
<div class="slide">
  <div class="slide-header"><h2>Quiz</h2></div>
  <div class="slide-body" style="overflow-y:auto">
    <div class="quiz" data-quiz="q1">
      <div class="quiz-question">Question text?</div>
      <div class="quiz-options">
        <button class="quiz-option" data-correct="false">Option A</button>
        <button class="quiz-option" data-correct="true">Option B</button>
      </div>
      <div class="quiz-feedback"></div>
    </div>
  </div>
</div>
```
- `.quiz` container with `data-quiz` id
- Separate `.quiz-question` and `.quiz-options` containers
- Uses `<button>` elements
- `data-correct="true|false"` attribute
- `.quiz-feedback` container for response

**Fixes Needed:**
1. Add `.quiz` wrapper with `data-quiz` id
2. Add `.quiz-question` container
3. Add `.quiz-options` wrapper
4. Use `<button>` instead of `<div>` for options
5. Add `data-correct` attribute (not `.correct` class)
6. Add `.quiz-feedback` container
7. Add `overflow-y:auto` to slide body

### 7. Code Slide (`@type code`)

**Current Preview Output (preview.ts:924-934):**
```html
<div class="slide slide-type-code">
  <div class="slide-heading-area"><h2>Heading</h2></div>
  <div class="slide-body-area">
    <pre><code>
      <span class="kw">const</span> x = <span class="str">"hello"</span>;
    </code></pre>
  </div>
</div>
```
- Uses `.kw`, `.str`, `.cm`, `.num` classes

**Target HTML Output (remarp_to_slides.py:2139-2152):**
```html
<div class="slide">
  <div class="slide-header"><h2>Heading</h2></div>
  <div class="slide-body">
    <div class="code-block">
      <span class="code-label">yaml</span>
      <span class="keyword">const</span> x = <span class="string">"hello"</span>;
    </div>
  </div>
</div>
```
- Uses `.code-block` container (not `<pre><code>`)
- Uses `.keyword`, `.string`, `.comment`, `.key`, `.value` classes
- Has `.code-label` for language/filename display
- Supports line highlighting with `.hl-line` class

**Fixes Needed:**
1. Use `.code-block` container class
2. Rename syntax classes: `.kw` → `.keyword`, `.str` → `.string`, `.cm` → `.comment`
3. Add `.key`, `.value` classes for YAML/JSON
4. Add `.code-label` element for filename/language
5. Support `highlight="1,3-5"` line highlighting

### 8. Canvas Slide (`@type canvas`)

**Current Preview Output (preview.ts:1254-1255):**
```html
<div class="canvas-placeholder">&#9881; Canvas DSL (preview unavailable)</div>
```
- Just a placeholder message

**Target HTML Output (remarp_to_slides.py:2024-2038):**
```html
<div class="slide">
  <div class="slide-header"><h2>Heading</h2></div>
  <div class="slide-body">
    <div class="canvas-container" id="canvas-1" data-max-step="3">
      <!-- SVG or Mermaid content -->
    </div>
    <div class="canvas-controls">
      <button class="btn btn-sm" onclick="...">Prev</button>
      <button class="btn btn-sm" onclick="...">Next</button>
    </div>
  </div>
  <script>/* Canvas animation/step logic */</script>
</div>
```
- `.canvas-container` with SVG/Mermaid content
- `.canvas-controls` with navigation buttons
- `data-max-step` attribute for step navigation
- Inline script for step progression

**Fixes Needed:**
1. Parse :::canvas DSL and render SVG elements
2. Support :::canvas mermaid variant
3. Add `.canvas-controls` buttons
4. Add step navigation script
5. Support `animate-path` DSL for element animation

### 9. Cards Slide (`@type cards`)

**Current Preview Output:**
(Not explicitly handled - falls through to default)
```html
<div class="slide">
  <div class="slide-body-area">
    <!-- Generic content -->
  </div>
</div>
```

**Target HTML Output (remarp_to_slides.py:2503-2517):**
```html
<div class="slide">
  <div class="slide-header"><h2>Heading</h2></div>
  <div class="slide-body">
    <div class="col-3">
      <div class="card" data-remarp-id="s0-card-0">
        <div class="card-title">Card Title</div>
        <p>Card content</p>
      </div>
      <div class="card" data-remarp-id="s0-card-1">...</div>
    </div>
  </div>
</div>
```
- `.col-N` grid based on `@columns` directive
- `.card` + `.card-title` structure
- Per-card `data-remarp-id`

**Fixes Needed:**
1. Add cards type detection and rendering
2. Parse `### ` headings as card titles
3. Use `.col-{N}` grid class from `@columns` directive
4. Add `.card` + `.card-title` structure

### 10. Thankyou Slide (`@type thankyou`)

**Current Preview Output (preview.ts:826-839):**
```html
<div class="slide slide-type-thankyou">
  <h1>Thank You</h1>
  <p>Message text</p>
</div>
```
- CSS-only gradient text effect

**Target HTML Output (remarp_to_slides.py:2541-2550):**
```html
<div class="slide">
  <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; gap:24px; text-align:center;">
    <h1 style="font-size:3rem; background:linear-gradient(...); -webkit-background-clip:text; ...">Thank You</h1>
    <p style="color:var(--text-secondary); ...">Message</p>
    <p style="color:var(--text-muted); ...">수고하셨습니다!</p>
    <div style="display:flex; gap:16px; margin-top:20px;">
      <a href="index.html" class="btn btn-primary btn-sm">← 목차로 돌아가기</a>
      <a href="next.html" class="btn btn-primary btn-sm">다음 →</a>
    </div>
  </div>
</div>
```
- Inline styles for layout
- Navigation buttons (TOC + Next)
- Support for `@toc`, `@next`, `@next-label`, `@message` directives
- Conditional "수고하셨습니다!" for final blocks

**Fixes Needed:**
1. Add navigation buttons from directives
2. Support `@message`, `@toc`, `@next`, `@next-label` directives
3. Add conditional congrats message for final blocks

---

## C. Theme Alignment

CSS variable mapping between preview.ts inline styles and theme.css:

| Token | Preview (current) | theme.css (target) | Action |
|-------|-------------------|-------------------|--------|
| `--bg-primary` | `#1e1e1e` | `#0f1117` | Update |
| `--bg-secondary` | `#2d2d2d` | `#1a1d2e` | Update |
| `--bg-tertiary` | (not defined) | `#232740` | Add |
| `--bg-card` | (not defined) | `#1e2235` | Add |
| `--surface` | (not defined) | `#282d45` | Add |
| `--border` | `#3c3c3c` | `#2d3250` | Update |
| `--border-focus` | (not defined) | `#5b6abf` | Add |
| `--text-primary` | `#e0e0e0` | `#e8eaf0` | Update |
| `--text-secondary` | `#aaa` | `#9ba1b8` | Update |
| `--text-muted` | `#888` | `#6b7194` | Update |
| `--text-accent` | (not defined) | `#7b8cff` | Add |
| `--accent` | `#FF9900` / `#6c5ce7` | `#6c5ce7` | Standardize to purple |
| `--accent-light` | (not defined) | `#a29bfe` | Add |
| `--accent-glow` | (not defined) | `rgba(108, 92, 231, .3)` | Add |
| `--green` | `#27ae60` | `#00b894` | Update |
| `--yellow` | (not defined) | `#fdcb6e` | Add |
| `--red` | (not defined) | `#e17055` | Add |
| `--blue` | `#3498db` | `#74b9ff` | Update |
| `--cyan` | (not defined) | `#00cec9` | Add |
| `--font-main` | system fonts | `'Pretendard', system fonts` | Add Pretendard |
| `--font-mono` | `monospace` | `'JetBrains Mono', 'Fira Code'` | Add JetBrains Mono |
| Heading color | inherit | `var(--text-primary)` | Match |

---

## D. Class Name Alignment

| Preview (current) | HTML builder (target) | Action |
|-------------------|----------------------|--------|
| `.slide-heading-area` | `.slide-header` | Rename |
| `.slide-body-area` | `.slide-body` | Rename |
| `.columns-2` | `.col-2` | Rename |
| `.columns-3` | `.col-3` | Rename |
| `.col` (in columns) | `.col` (same) | Keep |
| `.tab-panel` | `.tab-content` | Rename |
| `.tab-btn` (div) | `.tab-btn` (button) | Change element |
| `.quiz-option.correct` | `.quiz-option[data-correct="true"]` | Change to attr |
| `.step-label` | `.timeline-dot` | Rename |
| (none) | `.timeline-connector` | Add |
| (none) | `.timeline-label` | Add |
| (none) | `.timeline-desc` | Add |
| (none) | `.timeline` | Add container |
| `<input type="checkbox">` | `<span class="check">` | Replace |
| (none) | `.checklist` | Add |
| (none) | `.checklist-text` | Add |
| (none) | `.checklist-detail` | Add |
| `<pre><code>` | `.code-block` | Replace |
| `.kw` | `.keyword` | Rename |
| `.str` | `.string` | Rename |
| `.cm` | `.comment` | Rename |
| `.num` | `.number` | Rename (optional) |
| (none) | `.code-label` | Add |
| `.canvas-placeholder` | `.canvas-container` | Replace |
| (none) | `.canvas-controls` | Add |
| (none) | `.compare-toggle` | Add |
| (none) | `.compare-btn` | Add |
| (none) | `.compare-content` | Add |
| (none) | `.compare-highlight` | Add |
| (none) | `.quiz` | Add container |
| (none) | `.quiz-question` | Add |
| (none) | `.quiz-options` | Add |
| (none) | `.quiz-feedback` | Add |
| (none) | `.card` | Add |
| (none) | `.card-title` | Add |

---

## E. Implementation Priority

### Phase 1: Core Structure (High Priority)
1. Rename `.slide-heading-area` → `.slide-header`
2. Rename `.slide-body-area` → `.slide-body`
3. Update CSS variables to match theme.css
4. Rename `.columns-2/.columns-3` → `.col-2/.col-3`

### Phase 2: Tabs and Compare (High Priority)
5. Rename `.tab-panel` → `.tab-content`
6. Add compare slide toggle structure
7. Add compare buttons and highlight class

### Phase 3: Timeline (Medium Priority)
8. Add horizontal timeline layout
9. Add explicit connector elements
10. Add step navigation script

### Phase 4: Interactive Elements (Medium Priority)
11. Update quiz structure with proper containers
12. Update checklist with custom checkmarks
13. Add code block improvements

### Phase 5: Advanced Features (Lower Priority)
14. Add cards slide type
15. Improve canvas DSL rendering
16. Add cover slide absolute positioning
17. Add thankyou navigation buttons

---

## F. Testing Checklist

For each slide type, verify:

- [ ] **cover**: Gradient background, absolute positioning, speaker info, badge support
- [ ] **compare**: Toggle buttons, side-by-side columns, highlight animation
- [ ] **tabs**: Button elements, tab-content class, slug IDs, switching works
- [ ] **timeline**: Horizontal layout, connectors, dots, step navigation
- [ ] **checklist**: Custom checkmarks, detail expansion, CSS styling
- [ ] **quiz**: Question/options structure, data-correct attrs, feedback area
- [ ] **code**: code-block class, syntax class names, code-label, line highlight
- [ ] **canvas**: SVG rendering, step controls, mermaid support
- [ ] **cards**: Grid layout, card structure, column count directive
- [ ] **thankyou**: Navigation buttons, directives, gradient text

---

## G. Reference Files

| File | Purpose |
|------|---------|
| `tools/remarp-vscode/src/preview.ts` | Current preview renderer |
| `docs/static/demos/common/theme.css` | Target theme CSS |
| `plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py` | Target HTML builder |
| `docs/static/demos/common/slide-framework.js` | Navigation framework |
| `plugins/aws-content-plugin/skills/reactive-presentation/assets/quiz-component.js` | Quiz interactivity |
