# Marp Format Guide

Marp markdown is the content authoring format for reactive-presentation. Write content in Marp-style markdown and convert to HTML using `marp_to_slides.py`.

## Frontmatter

```yaml
---
marp: true
title: Presentation Title
theme: theme-name
blocks:
  - name: block-slug
    title: "Block 1: Display Title"
    duration: 30
  - name: block-slug-2
    title: "Block 2: Display Title"
    duration: 25
---
```

- `title`: Presentation title (used in HTML `<title>`)
- `theme`: Theme name (informational, actual theme comes from CSS)
- `blocks`: Array of block definitions
  - `name`: URL-safe slug used for filenames (`01-block-slug.html`)
  - `title`: Human-readable title shown on title slide
  - `duration`: Block duration in minutes (for pacing)

## Slide Separator

Use `---` (three dashes on its own line) to separate slides:

```markdown
# First Slide

Content here

---

## Second Slide

More content
```

## Block Markers

Use HTML comments to mark where each block starts:

```markdown
<!-- block: architecture -->

# Block 1 Title
...

---

<!-- block: monitoring -->

# Block 2 Title
...
```

## Slide Type Directives

Control slide type with HTML comments. Place AFTER the `---` separator and before content:

```markdown
---
<!-- type: compare -->
## Comparison Title
...
```

### Available Types

| Directive | Auto-detected? | Description |
|-----------|---------------|-------------|
| `<!-- type: content -->` | Default | Standard content slide |
| `<!-- type: compare -->` | Yes (multiple `###`) | Comparison toggle |
| `<!-- type: canvas, id: name -->` | No | Canvas animation placeholder |
| `<!-- type: quiz -->` | Yes (`[x]`/`[ ]`) | Quiz with auto-grading |
| `<!-- type: tabs -->` | No | Tabbed content |
| `<!-- type: timeline -->` | No | Horizontal timeline |
| `<!-- type: slider -->` | No | Interactive range slider |
| `<!-- type: checklist -->` | No | Click-to-toggle checklist |
| `<!-- type: code -->` | Yes (code fences) | Code block slide |
| (auto) | `# ` at start | Title slide |

## Speaker Notes

Add notes for the presenter view (opened with 'P' key):

```markdown
## Slide Title

Content here

<!-- notes: Remember to demo the live dashboard. Mention that this feature shipped in v2.3. -->
```

Notes are extracted and passed to `SlideFramework` as `presenterNotes`.

## Content Formatting

### Standard Markdown
- `**bold**` → `<strong>bold</strong>`
- `*italic*` → `<em>italic</em>`
- `` `code` `` → `<code>code</code>`
- `[text](url)` → `<a href="url">text</a>`
- `- item` → unordered list
- `1. item` → ordered list

### Comparison Slides

Use `### ` headings to define comparison options:

```markdown
<!-- type: compare -->
## Feature Comparison

### Option A
- Fast deployment
- Lower cost

### Option B
- More features
- Better scaling
```

### Canvas Slides

Describe the animation; Claude implements the JS later:

```markdown
<!-- type: canvas, id: arch-flow -->
## Architecture Flow

Draw a data pipeline:
- Source DB on left
- Processing service in center
- Target storage on right
- Animated arrows showing data flow
```

### Quiz Slides

Use `[x]` for correct answers, `[ ]` for wrong:

```markdown
<!-- type: quiz -->
## Knowledge Check

**Q1: Which service handles auto-scaling?**
- [ ] CloudWatch
- [x] Auto Scaling Groups
- [ ] CloudTrail
- [ ] Config

**Q2: Default cooldown period?**
- [x] 300 seconds
- [ ] 60 seconds
- [ ] 600 seconds
```

## Example: Complete 2-Block Presentation

```markdown
---
marp: true
title: AWS Auto Scaling Deep Dive
blocks:
  - name: fundamentals
    title: "Block 1: Fundamentals"
    duration: 25
  - name: advanced
    title: "Block 2: Advanced Patterns"
    duration: 25
---

<!-- block: fundamentals -->

# AWS Auto Scaling Deep Dive
Block 1: Fundamentals (25 min)

<!-- notes: Welcome everyone. This block covers the basics. -->

---

## Why Auto Scaling?

- Handle traffic spikes automatically
- Reduce costs during low traffic
- Improve availability

---
<!-- type: compare -->
## Scaling Strategies

### Target Tracking
- Set target metric value
- AWS adjusts capacity automatically
- Best for: steady-state workloads

### Step Scaling
- Define scaling steps based on thresholds
- More control over scaling behavior
- Best for: variable workloads

---
<!-- type: quiz -->
## Summary Quiz

**Q1: Which scaling policy is simplest to configure?**
- [x] Target Tracking
- [ ] Step Scaling
- [ ] Scheduled Scaling

---

<!-- block: advanced -->

# Advanced Patterns
Block 2 (25 min)

---
<!-- type: canvas, id: predictive-scaling -->
## Predictive Scaling

Show ML-based prediction curve:
- Historical data points (blue dots)
- Predicted demand curve (green line)
- Actual scaling actions (orange steps)

---

## Best Practices

- [ ] Enable multiple metric types
- [ ] Set appropriate cooldown periods
- [ ] Use lifecycle hooks
- [ ] Monitor with CloudWatch dashboards
```

## CLI Usage

```bash
# Basic conversion
python3 marp_to_slides.py presentation.md -o ./my-slides/

# With PPTX theme
python3 marp_to_slides.py presentation.md -o ./my-slides/ --theme-dir ../common/pptx-theme/

# English language
python3 marp_to_slides.py presentation.md -o ./my-slides/ --lang en
```
