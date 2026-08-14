# Remarp — Reactive Markdown for Presentations

Remarp is the next-generation markdown format for the **reactive-presentation** framework. A single human-readable, human-editable `.remarp.md` file becomes the **single source** for the presentation.

---

## Why Remarp?

| | Marp (existing) | JSON+Renderer | **Remarp (new)** |
|---|---|---|---|
| Source format | Markdown | JSON | **Markdown** |
| Human readability | Easy | Hard | **Easy** |
| Fragment animation | Not supported | Manual HTML | **One line: `{.click}`** |
| Canvas animation | Not supported (manual JS) | Separate JS module | **`:::canvas` DSL** |
| Speaker notes | `<!-- notes: -->` | JSON field | **`:::notes` + timing/cues** |
| Column layout | Not supported | Manual HTML | **`::: left`/`::: right`** |
| Slide transitions | Not supported | Not supported | **`@transition fade`** |
| Keyboard customization | Not supported | Not supported | **`keys:` frontmatter** |
| Per-block incremental build | Not supported | N/A | **`sync` command** |
| Backward compatibility | — | — | **`marp: true` supported** |

> **In short**: Marp's editing convenience + JSON mode's interactive features = Remarp

---

## 5-Minute Quickstart

### 1. Create the file

Create a `my-talk.remarp.md` file:

```markdown
---
remarp: true
title: "My First Remarp Presentation"
author: "Your Name"
audience: "Cloud Engineers"
lang: ko

theme:
  source: "./company-template.pptx"   # 또는 skip
  footer: "© 2026 My Company"

transition:
  type: fade
  duration: 350
---

# My First Remarp Presentation

Your Name | 2026

:::notes
{timing: 1min}
인사하고 자기소개.
:::

---

## 핵심 포인트

- 첫 번째 포인트{.click}
- 두 번째 포인트{.click}
- 세 번째 포인트{.click animation=fade-up}

:::notes
{timing: 3min}
**핵심**: 각 포인트를 클릭하며 설명.
{cue: question} "질문 있으신가요?"
:::

---
@type compare
@layout two-column

## 비교

::: left
### Option A
- 빠른 배포
- 간단한 구성
:::

::: right
### Option B
- 높은 확장성
- 세밀한 제어
:::

---
@type canvas
@canvas-id arch-flow

## 아키텍처

:::canvas width=960 height=400
box "API GW" at 50,170 size 130x60 color=accent
box "Lambda" at 260,170 size 130x60 color=green
box "DynamoDB" at 470,170 size 130x60 color=blue

arrow from "API GW" to "Lambda" at step=1 animate=draw
arrow from "Lambda" to "DynamoDB" at step=2 animate=draw

group "VPC" at 30,100 size 580x180 color=border
:::

:::notes
{timing: 5min}
{cue: demo} 아키텍처 흐름을 step별로 보여주기.
:::
```

### 2. Build HTML

```bash
python3 remarp_to_slides.py build my-talk.remarp.md
```

### 3. Open in the browser

Open the generated HTML in a browser and you're done!

---

## Multi-file Projects (for long sessions)

For sessions longer than 30 minutes, split files by block:

```
aws-scaling/
├── _presentation.remarp.md       # 글로벌 설정
├── 01-fundamentals.remarp.md     # Block 1 (25분)
├── 02-advanced.remarp.md         # Block 2 (30분)
└── build/                        # 생성된 HTML
    ├── index.html
    ├── 01-fundamentals.html
    └── 02-advanced.html
```

**`_presentation.remarp.md`** (global settings only):
```yaml
---
remarp: true
title: "AWS Auto Scaling Deep Dive"
author: "Cloud Architect"
event: "AWS Summit Seoul 2026"
lang: ko

blocks:
  - file: 01-fundamentals.remarp.md
    name: fundamentals
    title: "Block 1: Fundamentals"
    duration: 25
  - file: 02-advanced.remarp.md
    name: advanced
    title: "Block 2: Advanced Patterns"
    duration: 30

theme:
  source: "./company.pptx"
  footer: "© 2026, Amazon Web Services, Inc."
---
```

**Block file** (`01-fundamentals.remarp.md`):
```markdown
---
remarp: true
block: fundamentals
title: "Block 1: Fundamentals"
---

# AWS Auto Scaling Fundamentals

Block 1: Fundamentals (25 min)

:::notes
{timing: 1min}
Welcome!
:::

---

## Why Auto Scaling?
...
```

### Build commands

```bash
# 전체 빌드
python3 remarp_to_slides.py build ./aws-scaling/

# 특정 블록만 빌드
python3 remarp_to_slides.py build ./aws-scaling/ --block 01-fundamentals

# 변경된 블록만 증분 빌드
python3 remarp_to_slides.py sync ./aws-scaling/
```

---

## Syntax Summary

### Slide separators

Use `---` lines to separate slides. Place `@directive`s right after the `---`.

### Directives (`@`)

```markdown
---
@type canvas
@layout two-column
@transition zoom
@background #1a1d2e
@timing 3min
```

| Directive | Description | Values |
|-----------|------|-----|
| `@type` | Slide type | content, compare, canvas, quiz, tabs, timeline, checklist, slider, code |
| `@layout` | Layout | default, two-column, three-column, grid-2x2 |
| `@transition` | Transition effect | fade, slide, zoom, none |
| `@background` | Background color | CSS color or `url(...)` |
| `@timing` | Presentation time | 3min, 90s |
| `@canvas-id` | Canvas ID | Identifier |

### Fragment Animation (`{.click}`)

Elements that appear one at a time with Space/→:

```markdown
- 첫 번째{.click}
- 두 번째{.click}
- 세 번째{.click animation=fade-up}
```

Block-level fragments are also supported:
```markdown
:::click animation=grow
### Phase 1
전체 블록이 클릭 시 나타남.
:::
```

12 animation types: `fade-in`, `fade-up`, `fade-down`, `fade-left`, `fade-right`, `grow`, `shrink`, `highlight`, `highlight-red`, `highlight-green`, `strike`, `fade-out`

### Column Layout

```markdown
@layout two-column

::: left
왼쪽 내용
:::

::: right
오른쪽 내용
:::
```

### Canvas DSL

```markdown
:::canvas width=960 height=400
box "서비스A" at 50,170 size 130x60 color=accent
arrow from "서비스A" to "서비스B" at step=1 animate=draw
:::
```

### Speaker Notes

```markdown
:::notes
{timing: 3min}
**핵심 포인트** 설명.
{cue: demo} 대시보드 보여주기.
{cue: question} "경험 있으신 분?"
:::
```

Cue types: `demo`, `pause`, `question`, `transition`

---

## Theme Integration

### PPTX/PDF Theme Source

Specify a PPTX or PDF file as the theme source in frontmatter:

```yaml
---
remarp: true
title: "My Presentation"

theme:
  source: "./company-template.pptx"   # 또는 PDF 파일
  footer: auto                         # 자동으로 PPTX에서 추출
  pagination: true                     # 페이지 번호 표시
  logo: auto                           # 첫 번째 로고 자동 사용
---
```

- `source` — path to the PPTX/PDF file, or an already-extracted theme directory
- `footer` — auto-extracted from the PPTX when set to `auto`, or specify a literal string
- `pagination` — `true`/`false` to show page numbers
- `logo` — `auto` to auto-extract, or specify a direct path

Extracted themes are cached in the `_theme/` directory.

### Automatic CSS Variable Generation

PPTX color schemes are automatically converted into CSS variables:

```css
:root {
  --pptx-accent1: #FF9900;
  --pptx-accent2: #232F3E;
  --pptx-dk1: #000000;
  --pptx-lt1: #FFFFFF;
  /* ... */
}
```

---

## Preset DSL

A preset system for complex Canvas animations:

```markdown
:::canvas
preset eks-scaling {
  cluster "Production EKS" at 40,30
    node "node-1" pods=3 max=4
    node "node-2" pods=2 max=4

  step 1 scale-out node=0 "Pod 추가"
  step 2 scale-out node=0 "Pod 추가"
  step 3 add-node "Node 추가"
}
:::
```

Supported presets:
- `eks-scaling` — EKS cluster scaling visualization
- `serverless-flow` — Lambda event flow
- `vpc-architecture` — VPC network diagram
- `cicd-pipeline` — CI/CD pipeline
- `data-pipeline` — data processing pipeline

---

## Mermaid Diagrams

Mermaid diagrams are supported via the `:::canvas mermaid` variant:

```markdown
:::canvas mermaid
graph LR
    A[Client] --> B[API Gateway]
    B --> C[Lambda]
    C --> D[DynamoDB]
:::
```

The Mermaid CDN is injected automatically.

---

## Using Icons

Using AWS icons in the Canvas DSL:

```markdown
:::canvas
# 서비스 이름으로 참조 (자동 매핑)
icon gw "API-Gateway" at 100,150 size 48
icon fn "Lambda" at 250,150 size 48
icon db "DynamoDB" at 400,150 size 48

# 또는 전체 경로로 참조
icon custom "../common/aws-icons/services/Arch_Amazon-S3_48.svg" at 100,250 size 48
:::
```

Supported service names: `Lambda`, `EKS`, `API-Gateway`, `DynamoDB`, `S3`, `CloudWatch`, `EC2`, `VPC`, `RDS`, `SQS`, `SNS`, `CloudFront`, `Route53`, `Cognito`, `StepFunctions`, `Fargate`, `ECS`, `ALB`, `IAM`, `KMS`

---

## Reference Links (@ref)

Add reference links to a slide:

```markdown
---
@type content
@ref "https://docs.aws.amazon.com/lambda/" "Lambda Documentation"
@ref "https://aws.amazon.com/blogs/compute/" "AWS Compute Blog"

## Lambda Best Practices

Content here...
```

References are stored on the slide as a `data-refs` attribute and shown in the presenter view.

---

## PPTX Export

Export the presentation to PPTX:

```javascript
// 브라우저에서
ExportUtils.exportPPTX({ title: 'My Presentation' });

// 또는 index.html의 Export PPTX 버튼 클릭
```

Export options:
- **PDF** — all slides as PDF
- **ZIP** — a complete package including HTML, CSS, JS
- **PPTX** — export in PowerPoint format (including theme colors)

---

## Keyboard Shortcuts

| Key | Action |
|----|------|
| ← → | Previous/next slide |
| Space | Next fragment → next slide |
| ↑ ↓ | Switch tabs/comparisons, animation steps |
| F | Fullscreen |
| N | Speaker notes panel |
| P | Presenter view (new window) |
| O | Slide overview (grid) |
| B | Blackout |
| Esc | Exit fullscreen/overview |

Keyboard customization is configured in the `keys:` section of frontmatter.

---

## Migrating from Marp

Automatically convert existing Marp files to Remarp:

```bash
python3 remarp_to_slides.py migrate ./old-content.md -o ./my-presentation/
```

What gets converted:
| Marp | Remarp |
|------|--------|
| `marp: true` | `remarp: true` |
| `<!-- type: canvas -->` | `@type canvas` |
| `<!-- block: name -->` | Separate block file |
| `<!-- notes: text -->` | `:::notes` block |

Backward compatibility: `marp: true` files are handled as-is by the Remarp parser too.

---

## VSCode Extension

A VSCode extension is included at `tools/remarp-vscode/`:

- **Syntax highlighting** — `@directive`, `:::block`, `{.click}`, Canvas DSL
- **Live preview** — preview the current slide in a side panel
- **Slide outline** — a tree view of the slide list in the explorer
- **Autocomplete** — IntelliSense for `@type`, `@layout`, `@transition`, animation types

---

## Learn More

- [Full Remarp format specification](references/remarp-format-guide.md) — detailed explanations and examples of all syntax
- [Slide patterns guide](references/slide-patterns.md) — HTML patterns for 13 slide types
- [Framework guide](references/framework-guide.md) — CSS/JS API reference
- [PPTX theme guide](references/pptx-theme-guide.md) — how to extract corporate themes
- [AWS icons guide](references/aws-icons-guide.md) — how to use AWS architecture icons
