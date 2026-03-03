# AWS Content Plugin — Claude Code Configuration

A unified plugin for AWS cloud content creation: presentations, architecture diagrams, animated diagrams, documents, GitBook documentation sites, and workshops.

---

## Auto-Invocation Rules

When the following keywords are detected, automatically invoke the corresponding agent.

### Presentations

| Keywords | Agent | Description |
|----------|-------|-------------|
| "create presentation", "create slides", "make slideshow", "training slides", "interactive presentation", "reactive presentation" | `presentation-agent` | Interactive HTML slideshow creation |
| "PPTX theme", "extract theme", "corporate branding" | `presentation-agent` | PPTX theme extraction for presentations |
| "반영해주세요", "rebuild", "다시 빌드", "remarp 반영" | `presentation-agent` | Remarp → HTML 증분 빌드 |

### Architecture Diagrams (Static)

| Keywords | Agent | Description |
|----------|-------|-------------|
| "architecture diagram", "infrastructure diagram", "system architecture", "AWS architecture", "cloud diagram", "draw.io" | `architecture-diagram-agent` | Draw.io XML diagram generation |

### Animated Diagrams (Dynamic)

| Keywords | Agent | Description |
|----------|-------|-------------|
| "animated diagram", "traffic flow", "animated architecture", "dynamic diagram", "SMIL animation", "animated SVG" | `animated-diagram-agent` | SVG + SMIL animation diagrams |

### Documents

| Keywords | Agent | Description |
|----------|-------|-------------|
| "create document", "write report", "technical report", "comparison document", "guide document", "write guide" | `document-agent` | Markdown documents and reports |

### GitBook

| Keywords | Agent | Description |
|----------|-------|-------------|
| "gitbook", "documentation site", "create docs site", "gitbook project", "knowledge base" | `gitbook-agent` | GitBook documentation sites |

### Workshops

| Keywords | Agent | Description |
|----------|-------|-------------|
| "workshop", "lab content", "hands-on guide", "workshop create", "module content" | `workshop-agent` | AWS Workshop Studio content |

### Content Review

| Keywords | Agent | Description |
|----------|-------|-------------|
| "review content", "quality check", "review document", "review presentation", "review workshop" | `content-review-agent` | Cross-cutting quality review |

---

## Workflow Patterns

### Presentation Workflow
```
presentation-agent → content-review-agent → Deploy (GitHub Pages)
```

### Architecture Diagram Workflow
```
architecture-diagram-agent → .drawio → PNG export → (embed in presentation/document/gitbook)
```

### Animated Diagram Workflow
```
animated-diagram-agent → .html + .svg → (embed in presentation/gitbook or standalone)
```

### Document Workflow
```
document-agent → content-review-agent → .md output
```

### GitBook Workflow
```
gitbook-agent → content-review-agent → GitBook pages → git push
```

### Workshop Workflow
```
workshop-agent → content-review-agent → Workshop Studio content
```

---

## Quality Gate

All content types pass through content-review-agent before finalization.

| Verdict | Condition | Result |
|---------|-----------|--------|
| **PASS** | Critical 0, Warning ≤3, Score ≥85 | Approved |
| **REVIEW** | Critical 0, Warning 4-10, Score 70-84 | Fix and re-review |
| **FAIL** | Critical ≥1 or Warning >10 or Score <70 | Cannot proceed |

---

## Agents

| Agent | Model | Purpose |
|-------|-------|---------|
| `presentation-agent` | sonnet | Interactive HTML slideshows (reactive-presentation framework) |
| `architecture-diagram-agent` | sonnet | Static Draw.io XML diagrams → PNG/SVG export |
| `animated-diagram-agent` | sonnet | Dynamic SVG diagrams with SMIL animations |
| `document-agent` | sonnet | Markdown documents and reports |
| `gitbook-agent` | sonnet | GitBook documentation sites |
| `workshop-agent` | sonnet | AWS Workshop Studio content |
| `content-review-agent` | sonnet | Cross-cutting quality review (all content types) |

## Skills

| Skill | Purpose |
|-------|---------|
| `reactive-presentation` | Presentation framework assets, scripts, references, AWS icons |
| `architecture-diagram` | Draw.io templates, AWS icon reference, layout patterns |
| `animated-diagram` | SMIL animation guide, HTML templates, AWS diagram patterns |
| `gitbook` | GitBook structure guide, component patterns |
| `workshop-creator` | Workshop Studio directives, templates, references |

---

## AWS Icons

AWS Architecture Icons are located in `skills/reactive-presentation/icons/`:
- `Architecture-Service-Icons_07312025/` — Service-level icons (121 categories)
- `Architecture-Group-Icons_07312025/` — Group icons (Cloud, VPC, Region, Subnet)
- `Category-Icons_07312025/` — Category-level icons (4 sizes)
- `Resource-Icons_07312025/` — Resource-level icons (22 categories)
- `others/` — Third-party icons (LangChain, Grafana, etc.)

---

## Diagram Agent Selection Guide

| Need | Agent | Output |
|------|-------|--------|
| Static AWS architecture | `architecture-diagram-agent` | .drawio → .png |
| Animated traffic flow | `animated-diagram-agent` | .html with SVG + SMIL |
| Workshop inline diagram | `workshop-agent` (Mermaid) | Mermaid in markdown |
| Presentation Canvas animation | `presentation-agent` | Canvas JS in HTML slides |
