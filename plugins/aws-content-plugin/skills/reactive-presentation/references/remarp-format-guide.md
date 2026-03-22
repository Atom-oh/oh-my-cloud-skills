# Remarp Format Guide

Remarp is the next-generation content authoring format for reactive-presentation. It extends Marp-style markdown with enhanced directives, animations, layouts, and canvas DSL while maintaining backward compatibility.

## File Convention

### Single-File Format
For simple presentations, use a single `.md` file (previously `.remarp.md`):

```
my-presentation.md
```

### Multi-File Project Format
For larger presentations, split content into multiple files:

```
my-presentation/
  _presentation.md           # Global frontmatter (required)
  01-introduction.md         # Block 1
  02-architecture.md         # Block 2
  03-implementation.md       # Block 3
  assets/                    # Images, diagrams
```

The `_presentation.md` file contains only frontmatter and imports blocks by filename pattern (`01-*.md`, `02-*.md`, etc.). All files must have `remarp: true` in frontmatter to be recognized. The `.remarp.md` extension is also supported for backward compatibility.

---

## Global Frontmatter

The global frontmatter defines presentation-wide settings. In single-file format, place at the top. In multi-file format, use `_presentation.remarp.md`.

```yaml
---
remarp: true
version: 1
title: "AWS Architecture Deep Dive"
speaker:
  name: "오준석 (Junseok Oh)"
  title: "Sr. Solutions Architect"
  company: "AWS"
audience: "클라우드 엔지니어"
level: "300"
quiz: true
duration: 85
date: 2026-03-20
event: "AWS Summit 2025"
lang: ko

blocks:
  - name: fundamentals
    title: "Fundamentals"
    duration: 30
  - name: advanced
    title: "Advanced Patterns"
    duration: 25
  - name: hands-on
    title: "Hands-On Lab"
    duration: 30

theme:
  primary: "#232F3E"
  accent: "#6c5ce7"
  footer: "© 2026, Amazon Web Services, Inc. or its affiliates. All rights reserved. Amazon Confidential and Trademark."
  logo: "./common/pptx-theme/images/logo_1.png"
  badge: "./common/pptx-theme/images/Picture_8.png"
  background: "./common/pptx-theme/images/Picture_13.png"

transition:
  default: slide
  duration: 400
---
```

### Frontmatter Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `remarp` | boolean | Yes | Must be `true` to enable remarp processing |
| `version` | number | No | Format version (default: 1) |
| `title` | string | Yes | Presentation title (used in HTML `<title>`) |
| `speaker` | object | Yes | Speaker info (structured) |
| `speaker.name` | string | Yes | Speaker name |
| `speaker.title` | string | Yes | Job title |
| `speaker.company` | string | Yes | Company/organization |
| `audience` | string | Yes | Target audience (역할/직군) |
| `level` | string | Yes | Target level (`100`-`400` or 입문/중급/고급/전문가) |
| `quiz` | boolean | Yes | Include per-block quizzes |
| `duration` | number | Yes | Total duration in minutes — must match sum of blocks durations |
| `date` | date | No | Presentation date (YYYY-MM-DD) |
| `event` | string | No | Event or conference name |
| `lang` | string | No | Language code (`ko`, `en`, `ja`) |
| `blocks` | array | Yes | Block definitions (see below) |
| `theme` | object | No | Theme configuration |
| `author` | string | No | (deprecated) Fallback for `speaker.name` |
| `transition` | object | No | Transition defaults |
| `keys` | object | No | Keyboard shortcut overrides |

### Block Definition

```yaml
blocks:
  - name: architecture     # URL-safe slug (used in filenames)
    title: "Architecture"  # Human-readable title
    duration: 30           # Duration in minutes
```

### Theme Configuration

```yaml
theme:
  primary: "#232F3E"       # Primary color (headers, backgrounds)
  accent: "#FF9900"        # Accent color (highlights, links)
  font: "Amazon Ember"     # Body font family
  codeTheme: "github-dark" # Code syntax theme
  footer: "© 2026, ..."   # Footer text for all slides
  logo: "./common/pptx-theme/images/logo.png"       # Logo image path
  badge: "./common/pptx-theme/images/badge.png"      # Badge image path (optional)
  background: "./common/pptx-theme/images/bg.png"    # Background image path (optional)
```

### Transition Configuration

```yaml
transition:
  default: slide           # Default transition type
  duration: 400            # Transition duration in ms
```

Available transition types: `none`, `fade`, `slide`, `convex`, `concave`, `zoom`

---

## Block File Format

Each block file has local frontmatter followed by slides separated by `---`.

```markdown
---
remarp: true
block: fundamentals
---

# Introduction to AWS
Fundamentals (30 min)

---

## Why Cloud Computing?

- Scalability on demand
- Pay-as-you-go pricing
- Global infrastructure

---

## AWS Global Infrastructure

Content about regions and availability zones...
```

### Local Frontmatter

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `remarp` | boolean | Yes | Must be `true` to identify as remarp file |
| `block` | string | Yes | Block name (must match `blocks[].name` in global frontmatter) |
| `title` | string | No | Block title (overrides global blocks[].title) |

### Slide Separator Rules

Slides are separated by `---` on its own line. Directives go **immediately after** the separator, with NO extra `---` block.

#### Recommended: Slide Comment Pattern

소스 가독성을 위해 각 슬라이드에 번호/제목 주석을 권장합니다:

```markdown
---
<!-- Slide 1: Cover -->
@type: cover

# AIOps Deep Dive

---
<!-- Slide 2: Agenda -->

## 오늘의 내용
```

주석은 converter가 무시하므로 출력에 영향 없습니다. `<!-- Slide N: Title -->` 형식을 일관되게 사용하면 소스 탐색이 용이합니다.

#### WRONG — per-slide frontmatter (creates blank slides)

```markdown
---
<!-- Slide 2: Block Title -->
---
@type: title
@transition: fade
---

# AIOps Foundation
```

The converter splits on `---` and creates empty/comment-only slide fragments.

#### CORRECT — directives immediately after separator

```markdown
---
@type: title
@transition: fade

# AIOps Foundation
```

Directives use `@` prefix on lines immediately after `---`. No wrapping `---` block around them.

### Supported `:::` Block Types

Only these fenced div blocks are recognized by the converter:

| Block | Purpose |
|-------|---------|
| `:::click` | Fragment animation — content appears on click |
| `:::left` / `:::right` | Two-column layout halves |
| `:::col` | Generic column in grid layouts |
| `:::cell` | Grid cell |
| `:::notes` | Speaker notes (hidden in presentation) |
| `:::canvas` | Canvas DSL diagram block |
| `:::css` | Per-slide CSS overrides |
| `:::html` | Raw HTML block (no markdown processing) |
| `:::script` | JavaScript block (executes on slide load) |

| `::: tab "Title"` | Tab section in `@type: tabs` slides |

**NOT supported** (will render as literal text): `:::compare`, `:::option`, `:::buttons`, `:::tabs`, `:::timeline`

For tabs slides, use either `::: tab "Title"` blocks or `### ` headings — both are supported. For compare slides, use 2+ `### ` headings. For timeline, use ordered lists (NO `{.click}` — timeline has built-in ↑↓ keyboard step navigation via `__canvasStep`).

### :::html — Raw HTML Block

Embeds raw HTML directly into the slide body without markdown processing. Use for complex interactive layouts that can't be expressed in markdown.

```markdown
:::html
<div class="simulator-layout">
  <div class="slider-group">
    <input type="range" id="cpu" min="0" max="2000" value="500">
  </div>
  <div class="yaml-output" id="output"></div>
</div>
:::
```

- Content is inserted as-is (no markdown conversion)
- Position in slide is preserved (placeholder-based)
- Can be combined with :::css for styling and :::script for behavior
- Multiple :::html blocks per slide are supported

#### :::html 렌더링 컨텍스트

`:::html` 블록이 렌더링되는 환경을 이해해야 레이아웃 문제를 방지할 수 있습니다:

- **렌더링 위치**: `.slide-body` (`flex: 1`) 안에 삽입됨
- **슬라이드 패딩 이미 적용**: 외부에 `2rem 2.7rem` 패딩이 존재하므로 `:::html` 내부에서 추가 패딩을 최소화할 것 (합계 ≤60px)
- **CSS 변수 사용 가능**: `var(--bg-card)`, `var(--text)`, `var(--accent)`, `var(--border)` 등 테마 변수가 스코프 내에 있음
- **유틸리티 클래스 사용 가능**: `.col-2`, `.col-3`, `.flow-h`, `.flow-v` 등 테마 레이아웃 클래스 사용 가능
- **`<div>`가 `<p>` 안에 중첩되지 않도록 주의**: `:::html` 앞뒤에 빈 줄을 넣어 마크다운 파서가 `<p>` 태그로 감싸지 않게 할 것
- **max-height 필수**: 최상위 컨테이너에 `max-height: 500px` 또는 `calc(100% - 2rem)` 설정
- **반응형 단위 사용**: `px` 대신 `rem`, `%`, `fr`, `clamp()` 사용 (border/shadow 제외)
- **한국어 텍스트**: `word-break: keep-all; overflow-wrap: break-word;` 필수 적용

> 상세 레이아웃 규칙과 패턴은 `interactive-patterns-guide.md` §0 참조.

### :::script — JavaScript Block

Adds JavaScript that executes when the slide loads. Each block is wrapped in an IIFE for scope isolation.

```markdown
:::script
const slider = document.getElementById('cpu');
slider.oninput = () => {
  document.getElementById('output').textContent =
    `resources:\n  requests:\n    cpu: ${slider.value}m`;
};
:::
```

- Wrapped in `(function(){ ... })()` automatically
- Executes after slide HTML is in DOM
- Multiple :::script blocks per slide are supported
- Use with :::html for interactive widgets

---

## Slide Directives

Slide directives control individual slide behavior. Place them on the line immediately after `---`, before slide content. Use `@` prefix.

```markdown
---
@type: compare
@layout: two-column
@transition: zoom
@background: linear-gradient(135deg, #232F3E, #1a1a2e)
@class: highlight-slide
@timing: 3min
@canvas-id: arch-flow

## Slide Title
```

### Available Directives

| Directive | Values | Description |
|-----------|--------|-------------|
| `@type` | `content`, `compare`, `canvas`, `quiz`, `tabs`, `timeline`, `checklist`, `code`, `agenda`, `steps`, `cards`, `slider`, `cover`, `thankyou`, `iframe` | Slide type |
| `@layout` | `default`, `two-column`, `three-column`, `grid-2x2`, `split-left`, `split-right` | Layout preset |
| `@transition` | `none`, `fade`, `slide`, `convex`, `concave`, `zoom` | Slide-specific transition |
| `@background` | CSS color/gradient/image | Slide background |
| `@class` | CSS class names | Additional CSS classes |
| `@timing` | `Xmin` or `Xs` | Target duration for this slide |
| `@canvas-id` | identifier | Canvas element ID for `@type: canvas` |
| `@img` | `path [align] [size]` | Insert styled image (see below) |

### @img Directive

Insert styled images with alignment and size control:

```markdown
@img: diagrams/architecture.png center 80%
@img: screenshots/console.png left 60%
@img: logo.svg right 200px
```

Parameters (space-separated after path):
- **alignment**: `left`, `center` (default), `right`
- **size**: CSS max-width value (`80%`, `400px`, `50vh`)

Output: `<div>` with text-align + `<img class="slide-img">` with max-width constraint.

### Architecture Diagram 삽입 패턴

전체 아키텍처 개요는 draw.io로 제작한 PNG/SVG를 `@img:`로 삽입합니다.
Canvas DSL은 step animation이 유효한 경우에만 사용합니다.

```markdown
---
@type: content
---
## AWS AIOps Service Map

@img: diagrams/aiops-service-map.png center 90%

:::notes
{timing: 3min}
이 슬라이드는 전체 AIOps 아키텍처를 보여줍니다...
:::
```

Diagram 파일은 프레젠테이션 디렉토리의 `diagrams/` 폴더에 저장:
```
{slug}/
├── diagrams/
│   ├── aiops-service-map.png
│   └── container-observability.png
├── 01-aiops-foundation.md
└── ...
```

**선택 기준**: 아키텍처를 한눈에 보여주는 정적 구조 → `@img:` + draw.io 이미지. 단계별 흐름을 애니메이션으로 설명 → `@type: canvas` + `:::canvas` DSL.

### Type Auto-Detection

Some types are auto-detected from content:

| Content Pattern | Auto-Detected Type |
|-----------------|-------------------|
| `# ` (H1) at slide start | Title slide |
| Multiple `### ` headings | `compare` |
| `[x]` / `[ ]` checkboxes | `quiz` |
| Code fence with 10+ lines | `code` |
| `:::canvas` block | `canvas` |

---

## Column and Grid Layouts

Use fenced div syntax (`:::`) for multi-column layouts.

### Two-Column Layout

```markdown
---
@layout: two-column

## Feature Comparison

::: left
### Pros
- Fast deployment
- Lower cost
- Easy maintenance
:::

::: right
### Cons
- Limited customization
- Vendor lock-in
- Learning curve
:::
```

### Three-Column Layout

```markdown
---
@layout: three-column

## Service Options

::: col
### Basic
- 10 GB storage
- 1 vCPU
- $5/month
:::

::: col
### Standard
- 100 GB storage
- 2 vCPU
- $20/month
:::

::: col
### Premium
- 1 TB storage
- 8 vCPU
- $100/month
:::
```

### 2x2 Grid Layout

```markdown
---
@layout: grid-2x2

## AWS Pillars

::: cell
### Operational Excellence
Automate, document, iterate
:::

::: cell
### Security
Defense in depth, least privilege
:::

::: cell
### Reliability
Fault tolerance, recovery
:::

::: cell
### Performance
Right-size, monitor, optimize
:::
```

### Split Layouts

```markdown
---
@layout: split-left
@background: url(architecture.png) right/50% no-repeat

## Architecture Overview

::: left
The system uses a microservices architecture with:
- API Gateway for routing
- Lambda for compute
- DynamoDB for storage
:::
```

---

## Element Animations (Fragments)

Control reveal order of elements within a slide.

### Inline Click Animation

Add `{.click}` after any element to make it appear on click:

```markdown
## Build Process

1. Code commit triggers pipeline {.click}
2. Unit tests run in parallel {.click}
3. Integration tests validate APIs {.click}
4. Deployment to staging {.click}
5. Canary deployment to production {.click}
```

### Block Click Animation

Wrap multiple elements in `:::click` to animate together:

```markdown
## Deployment Stages

:::click
### Stage 1: Build
- Compile source code
- Run linters
- Generate artifacts
:::

:::click
### Stage 2: Test
- Unit tests
- Integration tests
- Security scans
:::

:::click
### Stage 3: Deploy
- Blue/green deployment
- Health checks
- Rollback capability
:::
```

### Animation Order

Control reveal order with `order=N`:

```markdown
## Out of Order Reveal

Item shown third {.click order=3}

Item shown first {.click order=1}

Item shown second {.click order=2}
```

### 동시 표시 (Same Fragment Index)

같은 `order` 값을 가진 항목들은 한 번의 클릭으로 **동시에** reveal됩니다:

```markdown
- 기능 A {.click order=1}
- 기능 B {.click order=1}
- 기능 C {.click order=1}
```

→ ArrowDown 1번에 A, B, C 동시 표시

같은 `order`를 공유하는 fragment는 내부적으로 같은 `data-fragment-index`를 받으며, 프레임워크가 동일 index 그룹을 한 번에 reveal/hide 합니다.

### Animation Types

Specify animation type with the animation name:

```markdown
## Animation Showcase

- Fade in (default) {.click}
- Fade from above {.click .fade-down}
- Fade from below {.click .fade-up}
- Fade from left {.click .fade-left}
- Fade from right {.click .fade-right}
- Grow in size {.click .grow}
- Shrink in size {.click .shrink}
- Highlight yellow {.click .highlight}
- Highlight red {.click .highlight-red}
- Highlight green {.click .highlight-green}
- Strikethrough {.click .strike}
- Fade out {.click .fade-out}
```

### Available Animation Types

| Class | Effect |
|-------|--------|
| `.fade-in` | Fade in (default) |
| `.fade-up` | Fade in from below |
| `.fade-down` | Fade in from above |
| `.fade-left` | Fade in from right |
| `.fade-right` | Fade in from left |
| `.grow` | Scale from 0 to 100% |
| `.shrink` | Scale from 150% to 100% |
| `.highlight` | Yellow background highlight |
| `.highlight-red` | Red background highlight |
| `.highlight-green` | Green background highlight |
| `.strike` | Strikethrough text |
| `.fade-out` | Fade out (for removing elements) |

### Fragment Best Practices

#### Avoid Excessive Per-Line `{.click}`

Adding `{.click}` to every bullet point creates a tedious one-by-one reveal that slows down the presentation. Instead, group related content with `:::click` blocks for meaningful reveals:

```markdown
<!-- BAD: every line clicks individually — boring and slow -->
- CloudWatch 기본 설정 {.click}
- 로그 중앙화 {.click}
- Anomaly Detection 활성화 {.click}
- DevOps Guru 도입 {.click}

<!-- GOOD: group by meaning with :::click blocks -->
:::click
### Phase 1: Foundation (1-2주)
- CloudWatch 기본 설정
- 로그 중앙화
:::

:::click
### Phase 2: Detection (2-4주)
- Anomaly Detection 활성화
- DevOps Guru 도입
:::
```

**When to use `{.click}` (individual):** Independent key points, statistics, or progressive number reveals.
**When to use `:::click` (block):** Title + list, phase + description, card + content — any semantic group.

#### Heading + Children: Use `:::click` Block

`{.click}` on a heading only animates the heading itself — child content below it is pre-visible. To animate a heading together with its content, use `:::click` block:

```markdown
<!-- BAD: heading animates but list stays visible -->
### ROI Analysis {.click}
- Cost savings: $10,000/month
- Time savings: 30hrs/week

<!-- GOOD: heading + list animate as one unit -->
:::click
### ROI Analysis
- Cost savings: $10,000/month
- Time savings: 30hrs/week
:::
```

#### Table Cells: Avoid `{.click}` Inside Tables

`{.click}` in table cells (`<td>`) has limited support. For progressive table reveals, use one of these alternatives:

```markdown
<!-- Option 1: Fragment the entire table row description outside the table -->
**MTTR**: 4hrs → 30min {.click}
**Alert noise**: 1000/day → 50/day {.click}

<!-- Option 2: Use two-column with left=labels, right=values with {.click} -->
@layout: two-column

::: left
### Before
- MTTR: 4 hours
- Alert noise: 1,000+/day
:::

::: right
### After
- MTTR: 30 min {.click}
- Alert noise: 50/day {.click}
:::
```

#### Two-Column Fragment Order

`gen_fragment_wrappers()` processes elements by **type** (`<p>` first, then `<li>`), not by DOM order. If left column uses `<li>` (list items) and right column uses `<p>` (bold text paragraphs), the right column gets lower fragment indices and appears first.

**Solutions:**
1. Use `order=N` to explicitly control reveal order across columns
2. Use the same element type in both columns (both lists or both bold paragraphs)

```markdown
<!-- BAD: mixed types — right column <p> appears before left column <li> -->
::: left
- Item A {.click}
- Item B {.click}
:::
::: right
**Item C** {.click}
**Item D** {.click}
:::

<!-- GOOD: explicit order controls left-to-right reveal -->
::: left
- Item A {.click order=1}
- Item B {.click order=2}
:::
::: right
**Item C** {.click order=3}
**Item D** {.click order=4}
:::
```

### Reference Links

슬라이드 하단에 참조 링크를 표시합니다. `{.reference}[텍스트](URL)` 형태로 사용:

```markdown
## AIOps 아키텍처

주요 구성 요소를 살펴봅니다.

{.reference}[EKS 모범 사례](https://docs.aws.amazon.com/eks/latest/best-practices/)
{.reference}[CloudWatch 가이드](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/)
```

여러 개를 한 슬라이드에 사용하면 `|`로 구분되어 하단에 작은 폰트로 표시됩니다. 본문에서는 자동 제거되므로 슬라이드 내용에 영향을 주지 않습니다.

#### Content Overflow Prevention (MANDATORY)

**Per-slide content limits** — exceeding these causes vertical overflow:

| Content type | Maximum per slide |
|-------------|------------------|
| Heading + bullet list | 1 heading + 6–8 bullets |
| Heading + paragraphs | 1 heading + 3–4 paragraphs |
| Numbered list + sub-bullets | 3 items with 2 sub-bullets each |
| Bold sections + descriptions | 3 sections (use two-column for 4+) |
| `:::html` block | max-height 500px, 패딩 합계 ≤60px, 반응형 단위 필수 |

**Rules**:
1. When a slide has 4+ major sections (e.g., a 4-phase roadmap), **must** use `@layout: two-column` and split evenly across `:::left` / `:::right`
2. Numbered list with 4+ items AND sub-bullets → split into two columns (items 1-2 left, 3-4+ right)
3. Never place more than 8 visible elements (bullets, paragraphs, or bold headings) on a single-column slide
4. If `{.click}` fragments reveal 4+ groups, ensure the fully-revealed state still fits within the slide area

When a slide has 4+ major sections, use `@layout: two-column` to split content:

```markdown
<!-- BAD: 4 phases overflow vertically -->
@type: content

## Roadmap
**Phase 1** ... **Phase 2** ... **Phase 3** ... **Phase 4** ...

<!-- GOOD: split into two columns -->
@layout: two-column

## Roadmap

::: left
**Phase 1: Foundation (1-2wk)** {.click}
- Item 1
- Item 2

**Phase 2: Detection (2-4wk)** {.click}
- Item 1
- Item 2
:::

::: right
**Phase 3: Analysis (2-4wk)** {.click}
- Item 1
- Item 2

**Phase 4: Self-Healing (4-8wk)** {.click}
- Item 1
- Item 2
:::
```

---

## Canvas DSL

The Canvas DSL provides a declarative way to create animated diagrams with step-based reveals.

### Canvas Layout Guidelines

Canvas uses a 960×400 coordinate space. Follow these rules to avoid overlapping:

| Rule | Constraint |
|------|-----------|
| **Box min spacing** | 40px gap between boxes (edge to edge) |
| **Icon min spacing** | 60px gap between icons (center to center) |
| **Arrow clearance** | Arrows must not pass through boxes/icons — route around them |
| **Label clearance** | Labels must not overlap with other elements — offset by 10px minimum |
| **X range** | Use 40–880 (leave 40px margins on both sides) |
| **Y range** | Use 30–350 (leave 30px top margin, 50px bottom for labels) |
| **Layer spacing** | Vertical layers should be 80–120px apart |
| **Box width** | `width ≥ label_length × 9` (한글 label: `× 14`). E.g., "API Gateway" (11 chars) → width ≥ 99 → use 120 |
| **Column formula** | `X_start = 40 + col_index × (880 / num_cols)`. E.g., 3 cols → X = 40, 333, 627 |
| **Label-arrow gap** | 20px minimum between label text and any arrow path |

**Workflow**: For complex diagrams, sketch in drawio or mermaid first to determine optimal layout, then convert coordinates to canvas DSL. This prevents alignment issues that are hard to fix after the fact.

**Column layout quick-reference** (960×400 space):

| Columns | X positions (box center) | Recommended box width |
|---------|-------------------------|----------------------|
| 2 | 240, 720 | 160–200 |
| 3 | 160, 480, 800 | 120–160 |
| 4 | 120, 340, 560, 780 | 100–130 |
| 5 | 100, 270, 480, 650, 820 | 80–110 |

```markdown
<!-- GOOD: evenly spaced 3-column layout -->
:::canvas
box a "Service A" at 80,180 size 120,50 color #FF9900 step 1
box b "Service B" at 380,180 size 120,50 color #FF9900 step 2
box c "Service C" at 680,180 size 120,50 color #3B48CC step 3
arrow a -> b "request" step 4
arrow b -> c "query" step 4
:::

<!-- BAD: elements too close, labels overlap -->
:::canvas
box a "Service A" at 100,200 size 120,60 color #FF9900
box b "Service B" at 180,200 size 120,60 color #FF9900
:::
```

### Basic Canvas Block

```markdown
---
@type: canvas
@canvas-id: simple-arch

## Simple Architecture

:::canvas
box api "API Gateway" at 100,200 size 120,60 color #FF9900
box lambda "Lambda" at 300,200 size 120,60 color #FF9900
box dynamo "DynamoDB" at 500,200 size 120,60 color #3B48CC

arrow api -> lambda "invoke"
arrow lambda -> dynamo "read/write"
:::
```

### Canvas Elements

#### Box Element
```
box <id> "<label>" at <x>,<y> size <width>,<height> color <color> [step <n>]
```

```markdown
:::canvas
box user "User" at 50,100 size 80,40 color #232F3E
box web "Web App" at 200,100 size 100,50 color #FF9900 step 2
box db "Database" at 400,100 size 100,50 color #3B48CC step 3
:::
```

#### Circle Element
```
circle <id> "<label>" at <x>,<y> radius <r> color <color> [step <n>]
```

```markdown
:::canvas
circle start "Start" at 50,100 radius 30 color #4CAF50
circle process "Process" at 200,100 radius 40 color #FF9900 step 2
circle end "End" at 350,100 radius 30 color #f44336 step 3
:::
```

#### Icon Element
```
icon <id> "<aws-service>" at <x>,<y> size <s> [step <n>]
```

AWS service names map to Architecture Icons:

```markdown
:::canvas
icon gw "API-Gateway" at 100,150 size 48
icon fn "Lambda" at 250,150 size 48 step 2
icon table "DynamoDB" at 400,150 size 48 step 3
:::
```

#### Arrow Element (Orthogonal Routing)

화살표는 자동으로 직교(orthogonal) 경로로 라우팅됩니다. 대각선 직선 대신 수평/수직 세그먼트만 사용하는 draw.io 스타일의 직각 꺾임 경로를 생성합니다.

```
arrow <from-id> -> <to-id> "<label>" [color <color>] [style <dashed|dotted>] [step <n>]
```

라우팅 패턴:
- **직선**: 두 요소가 같은 축에 정렬된 경우
- **L자형**: 측면↔상하 앵커 조합 (수평→수직 또는 수직→수평)
- **Z자형**: 같은 유형 앵커이면서 축이 어긋난 경우 (수평→수직→수평 또는 수직→수평→수직)

앵커 자동 선택: 주 이동 방향(dx vs dy)에 따라 최적 앵커 쌍(좌/우/상/하 중앙)이 선택됩니다. 중간에 다른 요소가 있으면 자동 충돌 회피 경로를 생성합니다.

```markdown
:::canvas
box a "Service A" at 50,100 size 100,50 color #232F3E
box b "Service B" at 250,100 size 100,50 color #232F3E

arrow a -> b "HTTP" step 2
arrow b -> a "Response" color #4CAF50 style dashed step 3
:::
```

#### Group Element
```
group "<label>" containing <id1>, <id2>, ... [color <color>] [step <n>]
```

```markdown
:::canvas
box web1 "Web 1" at 100,100 size 80,40 color #FF9900
box web2 "Web 2" at 100,160 size 80,40 color #FF9900
box web3 "Web 3" at 100,220 size 80,40 color #FF9900

group "Auto Scaling Group" containing web1, web2, web3 color #232F3E
:::
```

### Step-Based Reveal

Use `step N` on any element to control when it appears:

```markdown
---
@type: canvas
@canvas-id: data-flow

## Data Pipeline

:::canvas
# Step 1: Source appears first
icon s3src "S3" at 50,150 size 48 step 1
box source "Source Bucket" at 30,210 size 90,30 color #3B48CC step 1

# Step 2: Processing layer
icon lambda "Lambda" at 200,150 size 48 step 2
box transform "Transform" at 180,210 size 90,30 color #FF9900 step 2

# Step 3: Destination
icon s3dst "S3" at 350,150 size 48 step 3
box dest "Dest Bucket" at 330,210 size 90,30 color #3B48CC step 3

# Step 4: Arrows connect everything
arrow source -> transform "trigger" step 4
arrow transform -> dest "write" step 4
:::
```

### JavaScript Escape Hatch

For complex animations beyond DSL capabilities, use raw JavaScript:

```markdown
:::canvas js
const canvas = document.getElementById('complex-animation');
const ctx = canvas.getContext('2d');

// Custom animation logic
function animate() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  // ... custom drawing code
  requestAnimationFrame(animate);
}
animate();
:::
```

### Canvas Prompt (LLM-Assisted)

Use `:::canvas prompt` or the shorthand `:::prompt` to describe an animation in natural language. The presentation-agent reads the prompt, consults the `canvas-animation-prompt.md` reference, generates Canvas JS code, and replaces the block with `:::canvas js` before building HTML.

```markdown
:::prompt
ALB → Lambda → DynamoDB 트래픽 흐름
Step 1: 서비스 아이콘 표시
Step 2: 화살표 연결하며 데이터 흐름 표시
:::
```

> `:::prompt`는 `:::canvas prompt`의 축약형입니다. 둘 다 동일하게 동작합니다.

#### Prompt Structure Guidelines

For best results, structure prompts with these elements:

| Element | Description | Example |
|---------|-------------|---------|
| **Components** | AWS services or boxes to display | `ALB, Lambda, DynamoDB` |
| **Flow** | Connections and data direction | `ALB → Lambda → DynamoDB` |
| **Steps** | Reveal order for keyboard navigation | `Step 1: ..., Step 2: ...` |
| **Style** | Animation style or visual effects | `파티클 효과`, `펄스 애니메이션` |

#### Workflow

```
1. Author writes :::prompt (or :::canvas prompt) in .md
2. Converter outputs placeholder HTML (CANVAS_PROMPT_PENDING)
3. 사용자가 prompt 텍스트를 리뷰/수정 (선택)
4. "반영해주세요" / "rebuild" → Agent reads prompt + canvas-animation-prompt.md
5. Agent generates Canvas JS and replaces :::prompt → :::canvas js
6. Re-run converter for final HTML with working animation
```

> **Note**: The converter treats `:::canvas prompt` and `:::prompt` as passthrough — it outputs a placeholder. The actual code generation happens at the agent level (Phase 6 rebuild or Phase 7 enhancement), not in the converter.

---

## Speaker Notes

Add presenter notes with timing cues and markers.

### Basic Notes

```markdown
## Slide Title

Content here

:::notes
Remember to explain the cost implications.
Mention that this feature was added in version 2.3.
:::
```

### Timing Markers

```markdown
:::notes
{timing: 3min}
This slide should take about 3 minutes to cover.
Key points:
- Explain the architecture
- Show the demo
- Answer questions
:::
```

### Good Speaker Notes Example

```markdown
:::notes
{timing: 2min}
{cue: pause}
이 슬라이드에서는 CloudWatch Container Insights의 핵심 메트릭 3가지를 살펴보겠습니다.

먼저 CPU 사용률인데요, 단순히 높다 낮다가 아니라 request 대비 실제 사용량의 비율을 봐야 합니다.
실무에서 흔한 실수가 limit만 설정하고 request를 너무 낮게 잡는 건데, 이러면 스케줄러가 노드를 과밀하게 채워서 throttling이 발생합니다.

두 번째로 메모리 Working Set인데요, RSS가 아니라 Working Set을 봐야 하는 이유는 커널이 실제로 회수할 수 없는 메모리가 이것이기 때문입니다.

{cue: question}
혹시 여기서 OOMKilled를 경험해보신 분 계신가요? — 네, 대부분 이 메트릭을 모니터링하지 않아서 발생합니다.

{cue: transition}
그러면 이 메트릭들을 실시간으로 어떻게 대시보드에 구성하는지 다음 슬라이드에서 보겠습니다.
:::
```

### Cue Markers

```markdown
:::notes
{timing: 5min}
{cue: demo}
Live demo of the deployment pipeline.

{cue: pause}
Give audience time to absorb the architecture diagram.

{cue: question}
Ask: "Has anyone implemented this pattern?"

{cue: transition}
Transition to the next section on security.
:::
```

### Available Cues

| Cue | Purpose |
|-----|---------|
| `{cue: demo}` | Reminder to show live demonstration |
| `{cue: pause}` | Pause for audience absorption |
| `{cue: question}` | Ask audience a question |
| `{cue: transition}` | Verbal transition to next topic |
| `{cue: poll}` | Launch audience poll |
| `{cue: break}` | Take a break |

---

## Interactive Slide Types

### Quiz Slides

Quizzes are auto-detected when content contains `[x]` or `[ ]` checkboxes:

```markdown
---
@type: quiz

## Knowledge Check

**Q1: Which service provides serverless compute?**
- [ ] EC2
- [x] Lambda
- [ ] ECS
- [ ] EKS

**Q2: What is the maximum Lambda timeout?**
- [ ] 5 minutes
- [x] 15 minutes
- [ ] 30 minutes
- [ ] 60 minutes

**Q3: Lambda supports which runtimes? (Select all)**
- [x] Python
- [x] Node.js
- [x] Java
- [ ] COBOL
```

### Compare Slides

Comparison slides use toggle buttons to switch between options:

```markdown
---
@type: compare

## EC2 vs Lambda

### EC2
- Full control over instance
- Persistent compute
- Pay per hour
- Best for: Long-running workloads

### Lambda
- Serverless, no management
- Event-driven
- Pay per invocation
- Best for: Short, bursty workloads
```

### Tabs Slides

Tabbed content for organizing related information:

````markdown
---
@type: tabs

## Configuration Examples

### YAML
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  database_url: "postgres://..."
```

### JSON
```json
{
  "apiVersion": "v1",
  "kind": "ConfigMap",
  "metadata": {
    "name": "app-config"
  }
}
```

### TOML
```toml
[database]
url = "postgres://..."
```
````

### Timeline Slides

Horizontal timeline for sequential events with step descriptions and ↑↓ keyboard navigation.

Two input formats supported:

**Format 1: ### headings with description lines**
```markdown
---
@type: timeline

## Project Milestones

### Q1 2025
Design phase complete
Architecture approved

### Q2 2025
Development sprint 1-3
Alpha release

### Q3 2025
Beta testing
Performance optimization

### Q4 2025
Production launch
GA release
```

**Format 2: Numbered list with bold title + description**
```markdown
---
@type: timeline

## Upgrade Steps

1. **Pre-check** — Verify cluster health and backup
2. **Control Plane** — Upgrade EKS control plane version
3. **Add-ons** — Update CoreDNS, kube-proxy, VPC CNI
4. **Node Groups** — Rolling update managed node groups
5. **Validation** — Run smoke tests and verify workloads
```

Features:
- **Dynamic dot sizing**: Dots scale based on step count (≤3: large, 4-5: medium, 6-7: small, ≥8: compact)
- **Description text**: Lines below each `###` heading appear as description text
- **Keyboard navigation**: ↑↓ keys step through timeline, highlighting active step with done/active states

> **WARNING**: Do NOT add `{.click}` to timeline items. Timeline uses its own `__canvasStep` keyboard navigation (↑↓ keys). Adding `{.click}` breaks the bold-title regex parsing in the converter and prevents step separation. Timeline items are revealed by ↑↓ navigation, not by click fragments.

### Agenda Slides

Session agenda with numbered dots, time labels, connectors, and optional break markers.

**Directives:**
- `@timing` — total session duration (displayed as subtitle)

**Syntax:**

```markdown
@type: agenda
@timing: 40min

## Agenda

1. 개요 & 아키텍처 (10분)
2. 네트워킹 & 트래픽 (10분)
3. 노드 구성 & 운영 (10분)
- Break (5분)
4. 고급 패턴 & 전략적 가치 (10분)

> 질문은 각 Block 종료 시에 받겠습니다.
```

**Rules:**
- Use topic names only — do NOT prefix with "Block N" (the renderer adds numbered dots automatically)
- Break items: `- Break (duration)` or `- 휴식 (duration)` — rendered as ☕ break marker
- Use `@timing` directive to show total session duration
- Add a `> blockquote` for callout text below the timeline

**Rendering:**
- Numbered items → horizontal dots with connectors
- `- Break (duration)` or `- 휴식 (duration)` → yellow break marker with ☕
- First numbered step gets `active` highlight
- `> blockquote` text → callout box below the timeline
- `@timing` value → subtitle "총 X 세션"

### Steps Slides

Process visualization with numbered step indicators. Unlike agenda (which shows session schedule with time labels), steps are for generic process/workflow diagrams.

**Directives:**
- `@steps-shape`: `circle` (default), `rect`, or `icon`
- `@steps-layout`: `horizontal` (default) or `vertical`
- `@steps-icon`: path to icon file (used when shape is `icon`)

**Format 1: ### headings with descriptions**
```markdown
---
@type: steps
@steps-shape: circle
@steps-layout: horizontal

## 이번 세션에서 다룰 내용

### 현황 분석
운영 환경의 문제점과 과제

### 자동화 설계
이벤트 기반 자동 복구 아키텍처

### 구현 및 검증
Lambda + EventBridge 실전 구현
```

**Format 2: Numbered list with bold title + description**
```markdown
---
@type: steps
@steps-shape: rect

## Agenda

1. **Problem Statement** — Why manual remediation fails at scale
2. **Architecture Design** — Event-driven auto-remediation patterns
3. **Implementation** — Step-by-step Lambda + EventBridge walkthrough
4. **Live Demo** — See it in action {.click}
```

**Format 3: Vertical layout with icons**
```markdown
---
@type: steps
@steps-shape: icon
@steps-layout: vertical
@steps-icon: icons/Architecture-Service-Icons_07312025/Arch_AWS-Lambda_48.svg

## Process Flow

### Detect
CloudWatch alarm triggers EventBridge rule

### Evaluate
Lambda function assesses the incident severity

### Remediate
Automated runbook executes corrective action
```

Features:
- **Shape options**: `circle` (numbered circles), `rect` (rounded rectangles), `icon` (custom SVG/PNG)
- **Layout options**: `horizontal` (side-by-side) or `vertical` (stacked)
- **Click reveal**: Add `{.click}` to step titles for fragment animation
- **Connectors**: Automatic lines between steps

### Checklist Slides

Interactive click-to-toggle checklists. Items can include expandable code blocks that reveal on check:

```markdown
---
@type: checklist

## Deployment Checklist

- [ ] Code review approved
- [ ] Unit tests passing
- [ ] Enable Network Policy
  ```yaml
  apiVersion: networking.k8s.io/v1
  kind: NetworkPolicy
  metadata:
    name: deny-all
  ```
- [ ] Configure Pod Identity
  ```bash
  aws eks create-pod-identity-association \
    --cluster-name my-cluster \
    --namespace default \
    --service-account my-sa
  ```
- [ ] Monitoring alerts configured
```

When a checklist item has a code block underneath, clicking the checkbox expands/collapses the code block.

---

## Data Visualization in Remarp

Remarp supports data visualization through Chart.js integration and custom HTML/CSS patterns for KPI cards, dashboards, and infographics.

### Chart.js Slides

To use Chart.js in Remarp slides, inject the Chart.js CDN via the `@head` directive in frontmatter:

```markdown
---
@type: content
@head: <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
---
```

Alternatively, inject Chart.js directly in an `:::html` block within the slide.

**IMPORTANT**: Always include `Chart.defaults.animation = false;` before creating charts. This ensures reliable rendering, especially when navigating between slides or exporting to PDF.

### Chart.js in :::canvas js vs HTML <canvas>

There are two approaches for canvas-based graphics in Remarp:

| Approach | Use Case | API |
|----------|----------|-----|
| `:::canvas js` block | Custom canvas drawing with step navigation | Uses reactive-presentation canvas system (`setupCanvas`, `Colors`, step navigation) |
| `<canvas>` in `:::html` block | Standard Chart.js charts | Uses Chart.js API directly |

**Recommendation**: Use `:::html` with `<canvas>` for Chart.js charts (bar, line, pie, doughnut, etc.). Use `:::canvas js` only for custom procedural drawing that needs the reactive-presentation canvas system with step-based reveals.

### KPI Card Slide Example

KPI cards display key metrics with delta indicators:

```markdown
---
@type: content
---
# Monthly Performance

:::html
<div class="kpi-row">
  <div class="kpi-card">
    <div class="kpi-value">$2.4M</div>
    <div class="kpi-delta positive">↑ 12.5%</div>
    <div class="kpi-label">Revenue</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-value">1,847</div>
    <div class="kpi-delta positive">↑ 8.3%</div>
    <div class="kpi-label">Active Users</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-value">99.9%</div>
    <div class="kpi-delta negative">↓ 0.1%</div>
    <div class="kpi-label">Uptime</div>
  </div>
</div>
:::
```

The `.kpi-row`, `.kpi-card`, `.kpi-value`, `.kpi-delta`, and `.kpi-label` classes are provided by the reactive-presentation theme. Use `.positive` or `.negative` on `.kpi-delta` to show green/red coloring.

### Dashboard Slide Example

Combine KPI cards with Chart.js charts for dashboard-style slides:

```markdown
---
@type: content
@head: <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
---
# Service Dashboard

:::html
<div class="kpi-row" style="margin-bottom: 1rem;">
  <div class="kpi-card">
    <div class="kpi-value">342</div>
    <div class="kpi-delta positive">↑ 15%</div>
    <div class="kpi-label">Requests/sec</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-value">23ms</div>
    <div class="kpi-delta positive">↑ 5%</div>
    <div class="kpi-label">P99 Latency</div>
  </div>
</div>
<div class="chart-container">
  <canvas id="dash-chart"></canvas>
</div>
<script>
Chart.defaults.animation = false;
new Chart(document.getElementById('dash-chart'), {
  type: 'line',
  data: {
    labels: ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],
    datasets: [{
      label: 'Requests',
      data: [280,310,295,342,380,290,310],
      borderColor: '#6c5ce7',
      backgroundColor: 'rgba(108,92,231,0.1)',
      fill: true, tension: 0.3
    }]
  },
  options: { plugins: { legend: { labels: { color: '#9ba1b8' }}}, scales: { x: { ticks: { color: '#6b7194' }}, y: { ticks: { color: '#6b7194' }, grid: { color: '#2d3250' }}}}
});
</script>
:::
```

### Infographic Slide Example

Create infographic-style slides with hero stats, icon grids, and progress bars:

```markdown
---
@type: content
---
# Cloud Migration Progress

:::html
<div class="infographic">
  <!-- Hero Stat -->
  <div class="hero-stat">
    <div class="hero-value">78%</div>
    <div class="hero-label">Migration Complete</div>
  </div>

  <!-- Icon Grid -->
  <div class="icon-grid">
    <div class="icon-item completed">
      <img src="icons/Arch_Amazon-EC2_48.svg" alt="EC2">
      <span>EC2 Instances</span>
    </div>
    <div class="icon-item completed">
      <img src="icons/Arch_Amazon-RDS_48.svg" alt="RDS">
      <span>Databases</span>
    </div>
    <div class="icon-item in-progress">
      <img src="icons/Arch_Amazon-S3_48.svg" alt="S3">
      <span>Storage</span>
    </div>
    <div class="icon-item pending">
      <img src="icons/Arch_AWS-Lambda_48.svg" alt="Lambda">
      <span>Serverless</span>
    </div>
  </div>

  <!-- Progress Bars -->
  <div class="progress-section">
    <div class="progress-item">
      <span class="progress-label">Compute</span>
      <div class="progress-bar"><div class="progress-fill" style="width: 100%"></div></div>
      <span class="progress-value">100%</span>
    </div>
    <div class="progress-item">
      <span class="progress-label">Database</span>
      <div class="progress-bar"><div class="progress-fill" style="width: 85%"></div></div>
      <span class="progress-value">85%</span>
    </div>
    <div class="progress-item">
      <span class="progress-label">Storage</span>
      <div class="progress-bar"><div class="progress-fill" style="width: 60%"></div></div>
      <span class="progress-value">60%</span>
    </div>
  </div>
</div>
:::
```

Use the `.completed`, `.in-progress`, and `.pending` classes on `.icon-item` elements to indicate status with appropriate styling.

---

## Code Blocks

Enhanced code blocks with highlighting and metadata.

### Basic Code Block

````markdown
```python
def handler(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
```
````

### Line Highlighting

Highlight specific lines with `{highlight="..."}`:

````markdown
```python {highlight="3-5"}
def handler(event, context):
    # Process the event
    user_id = event['pathParameters']['userId']
    action = event['queryStringParameters'].get('action', 'read')
    timestamp = datetime.now().isoformat()

    return {'statusCode': 200, 'body': 'OK'}
```
````

Highlight formats:
- `{highlight="3"}` - Single line
- `{highlight="3-5"}` - Range
- `{highlight="1,3,7-9"}` - Multiple lines/ranges

### Filename Display

Show filename above code block:

````markdown
```yaml {filename="serverless.yml"}
service: my-api
provider:
  name: aws
  runtime: python3.9
  region: us-east-1

functions:
  hello:
    handler: handler.hello
    events:
      - http:
          path: /hello
          method: get
```
````

### Combined Attributes

````markdown
```typescript {filename="handler.ts" highlight="5-8"}
import { APIGatewayEvent, Context } from 'aws-lambda';

export async function handler(event: APIGatewayEvent, context: Context) {
  const userId = event.pathParameters?.userId;

  // Highlighted: Input validation
  if (!userId) {
    return { statusCode: 400, body: 'Missing userId' };
  }

  return { statusCode: 200, body: `Hello ${userId}` };
}
```
````

### Diff Display

Show code changes with diff syntax:

````markdown
```diff {filename="config.yaml"}
 database:
   host: localhost
-  port: 5432
+  port: 5433
   name: myapp
+  pool_size: 10
```
````

---

## Backward Compatibility

Remarp maintains backward compatibility with Marp format:

| Marp Syntax | Remarp Equivalent | Notes |
|-------------|-------------------|-------|
| `marp: true` | `remarp: true` | Both work, remarp enables new features |
| `<!-- type: X -->` | `@type: X` | HTML comments still work |
| `<!-- notes: ... -->` | `:::notes ... :::` | Both supported |
| `<!-- block: name -->` | `block: name` in frontmatter | Frontmatter preferred |
| Plain markdown | Same | Full markdown support |

### Migration Example

**Marp format:**
```markdown
---
marp: true
title: My Presentation
blocks:
  - name: intro
    title: "Introduction"
    duration: 20
---

<!-- block: intro -->

# Welcome
Introduction content

---
<!-- type: compare -->
## Options

### Option A
Content A

### Option B
Content B

<!-- notes: Remember to explain both options -->
```

**Remarp format:**
```markdown
---
remarp: true
version: 1
title: My Presentation
blocks:
  - name: intro
    title: "Introduction"
    duration: 20
---

---
remarp: true
block: intro
---

# Welcome
Introduction content

---
@type: compare

## Options

::: left
### Option A
Content A
:::

::: right
### Option B
Content B
:::

:::notes
Remember to explain both options
:::
```

---

## Complete Example: Multi-Block Presentation

### _presentation.md

```yaml
---
remarp: true
version: 1
title: "AWS Serverless Architecture"
author: "Cloud Team"
date: 2025-03-01
event: "AWS Tech Talk"
lang: en

blocks:
  - name: fundamentals
    title: "Serverless Fundamentals"
    duration: 25
  - name: patterns
    title: "Architecture Patterns"
    duration: 30
  - name: hands-on
    title: "Hands-On Lab"
    duration: 35

theme:
  primary: "#232F3E"
  accent: "#FF9900"

transition:
  default: slide
  duration: 400
---
```

### 01-fundamentals.md

```markdown
---
remarp: true
block: fundamentals
---

# AWS Serverless Architecture
Serverless Fundamentals (25 min)

:::notes
{timing: 2min}
Welcome everyone. Quick intro, then dive into serverless concepts.
:::

---

## What is Serverless?

- No server management {.click}
- Auto-scaling built-in {.click}
- Pay-per-use pricing {.click}
- Event-driven execution {.click}

:::notes
{timing: 3min}
{cue: question}
Ask who has used Lambda before.
:::

---
@type: compare

## Serverless vs Traditional

::: left
### Traditional
- Provision servers
- Manage capacity
- Pay for idle time
- OS patching required
:::

::: right
### Serverless
- No servers to manage
- Auto-scales to zero
- Pay only for execution
- Fully managed
:::

---
@type: canvas
@canvas-id: lambda-flow

## Lambda Execution Model

:::canvas
icon trigger "API-Gateway" at 50,150 size 48 step 1
icon lambda "Lambda" at 200,150 size 48 step 2
icon dynamo "DynamoDB" at 350,150 size 48 step 3

arrow trigger -> lambda "invoke" step 4
arrow lambda -> dynamo "read/write" step 5
:::

:::notes
{timing: 5min}
{cue: demo}
Show the Lambda console and execution flow.
:::

---
@type: quiz

## Quick Check

**Q1: Lambda maximum timeout?**
- [ ] 5 minutes
- [x] 15 minutes
- [ ] 30 minutes

**Q2: Lambda pricing is based on?**
- [ ] Provisioned capacity
- [x] Request count + duration
- [ ] Fixed monthly fee
```

### 02-patterns.md

````markdown
---
remarp: true
block: patterns
---

# Architecture Patterns
Architecture Patterns (30 min)

---
@layout: two-column

## Common Patterns

::: left
### Synchronous
- API Gateway + Lambda
- Direct invocation
- Request/Response
:::

::: right
### Asynchronous
- S3 + Lambda
- SQS + Lambda
- EventBridge + Lambda
:::

---
@type: canvas
@canvas-id: api-pattern

## API Backend Pattern

:::canvas
box client "Client" at 30,150 size 80,40 color #232F3E step 1

icon apigw "API-Gateway" at 150,140 size 48 step 2
icon lambda "Lambda" at 280,140 size 48 step 3
icon dynamo "DynamoDB" at 410,140 size 48 step 4

arrow client -> apigw "HTTPS" step 5
arrow apigw -> lambda "invoke" step 5
arrow lambda -> dynamo "query" step 6
:::

---
@type: tabs

## Code Examples

### Python
```python {filename="handler.py" highlight="4-6"}
import json
import boto3

def handler(event, context):
    # Extract path parameter
    user_id = event['pathParameters']['userId']

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('Users')

    response = table.get_item(Key={'userId': user_id})
    return {
        'statusCode': 200,
        'body': json.dumps(response.get('Item', {}))
    }
```

### Node.js
```javascript {filename="handler.js" highlight="3-5"}
const AWS = require('aws-sdk');

exports.handler = async (event) => {
  // Extract path parameter
  const userId = event.pathParameters.userId;

  const dynamodb = new AWS.DynamoDB.DocumentClient();
  const result = await dynamodb.get({
    TableName: 'Users',
    Key: { userId }
  }).promise();

  return {
    statusCode: 200,
    body: JSON.stringify(result.Item || {})
  };
};
```

---
@type: timeline

## Evolution of Serverless

### 2014
AWS Lambda launched
Event-driven compute

### 2016
API Gateway integration
Serverless APIs

### 2019
Lambda Layers
Provisioned Concurrency

### 2022
Lambda SnapStart
Function URLs

### 2024
Advanced observability
Native OpenTelemetry
````

### 03-hands-on.md

````markdown
---
remarp: true
block: hands-on
---

# Hands-On Lab
Hands-On Lab (35 min)

:::notes
{timing: 2min}
{cue: transition}
Now let's build something together.
:::

---
@type: checklist

## Lab Prerequisites

- [ ] AWS Account with admin access
- [ ] AWS CLI installed and configured
- [ ] Node.js 18+ or Python 3.9+
- [ ] SAM CLI installed
- [ ] Code editor (VS Code recommended)

---

## Step 1: Create Lambda Function

```bash {filename="terminal"}
# Initialize SAM project
sam init --runtime python3.9 --name my-api

# Navigate to project
cd my-api
```

:::click
After running these commands, you'll have a project structure:
```
my-api/
  template.yaml
  hello_world/
    app.py
    requirements.txt
```
:::

---
@layout: split-left

## Step 2: Deploy

::: left
```bash {filename="terminal" highlight="2,5"}
# Build the application
sam build

# Deploy with guided prompts
sam deploy --guided
```

Follow the prompts:
1. Stack name: `my-api`
2. Region: `us-east-1`
3. Confirm changes: `Y`
:::

:::notes
{timing: 10min}
{cue: demo}
Walk through deployment in terminal.
Explain each SAM deploy prompt.
:::

---
@type: canvas
@canvas-id: final-arch

## Final Architecture

:::canvas
group "AWS Cloud" containing apigw, lambda, dynamo, logs color #232F3E

icon apigw "API-Gateway" at 100,150 size 48 step 1
icon lambda "Lambda" at 250,150 size 48 step 2
icon dynamo "DynamoDB" at 400,150 size 48 step 3
icon logs "CloudWatch" at 250,280 size 48 step 4

arrow apigw -> lambda "REST" step 5
arrow lambda -> dynamo "CRUD" step 5
arrow lambda -> logs "logs" style dashed step 6
:::

---

## Lab Complete!

:::click
### What We Built
- Serverless REST API
- Lambda function with DynamoDB
- CloudWatch logging
:::

:::click
### Next Steps
- Add authentication with Cognito
- Implement CI/CD with CodePipeline
- Add custom domain with Route 53
:::

:::notes
{timing: 3min}
Wrap up, answer questions.
Share links to documentation.
:::
````

---

## CLI Usage

```bash
# Convert single file
remarp build presentation.md -o ./output/

# Convert multi-file project
remarp build ./my-presentation/ -o ./output/

# Watch mode for development
remarp watch ./my-presentation/ -o ./output/

# Export to PDF
remarp export presentation.md --format pdf

# Validate without building
remarp validate presentation.md
```

---

## Quick Reference

### Directives
```
@type: content|compare|canvas|quiz|tabs|timeline|checklist|code
@layout: default|two-column|three-column|grid-2x2|split-left|split-right
@transition: none|fade|slide|convex|concave|zoom
@background: <css-value>
@class: <css-classes>
@timing: Xmin|Xs
@canvas-id: <identifier>
```

### Layouts
```
::: left ... :::      Two-column left
::: right ... :::     Two-column right
::: col ... :::       Three-column
::: cell ... :::      Grid cell
```

### Animations
```
{.click}              Basic click reveal
{.click order=N}      Ordered reveal
{.click .fade-up}     Animation type
:::click ... :::      Block reveal
```

### Canvas DSL
```
box <id> "<label>" at X,Y size W,H color #HEX [step N]
circle <id> "<label>" at X,Y radius R color #HEX [step N]
icon <id> "<service>" at X,Y size S [step N]
arrow <from> -> <to> "<label>" [color #HEX] [style dashed|dotted] [step N]
group "<label>" containing id1, id2, ... [color #HEX] [step N]
```

### Notes
```
:::notes
{timing: Xmin}
{cue: demo|pause|question|transition|poll|break}
Note content here
:::
```

---

## Theme Frontmatter Schema

Extended theme configuration in global frontmatter:

```yaml
---
remarp: true
title: "My Presentation"

theme:
  source: "./company-template.pptx"  # PPTX/PDF file or pre-extracted directory
  footer: auto                        # "auto" extracts from PPTX, or string value
  pagination: true                    # Show/hide page numbers
  logo: auto                          # "auto" uses first extracted logo, or path

transition:
  default: slide
  duration: 400
---
```

### Theme Source Types

| Source Type | Example | Behavior |
|-------------|---------|----------|
| PPTX file | `./template.pptx` | Extract theme to `_theme/` directory |
| PDF file | `./template.pdf` | Extract colors and images |
| Directory | `./_theme/template/` | Use pre-extracted theme |

### Generated CSS Variables

When theme is extracted, the following CSS variables are generated in `theme-override.css`:

```css
:root {
  --pptx-accent1: #FF9900;
  --pptx-accent2: #232F3E;
  --pptx-accent3: #146EB4;
  --pptx-accent4: #4CAF50;
  --pptx-accent5: #f44336;
  --pptx-accent6: #9C27B0;
  --pptx-dk1: #000000;
  --pptx-lt1: #FFFFFF;
  --pptx-dk2: #1A1A1A;
  --pptx-lt2: #F5F5F5;
}
```

---

## Canvas DSL Preset Specification

Presets provide pre-built animated diagram patterns for common AWS scenarios.

### Preset Syntax

```
preset <type> {
  <preset-specific-configuration>
}
```

### EKS Scaling Preset

```markdown
:::canvas
preset eks-scaling {
  cluster "Production EKS" at 40,30
    node "node-1" pods=3 max=4
    node "node-2" pods=2 max=4
    node "node-3" pods=1 max=4

  step 1 scale-out node=0 "Add pod to node-1"
  step 2 scale-out node=1 "Add pod to node-2"
  step 3 add-node "Add new node"
  step 4 scale-out node=3 "Schedule to new node"
}
:::
```

### Preset Actions

| Action | Parameters | Description |
|--------|------------|-------------|
| `scale-out` | `node=N` | Add pod to specified node |
| `scale-in` | `node=N` | Remove pod from specified node |
| `add-node` | none | Add new node to cluster |
| `remove-node` | `node=N` | Remove node from cluster |
| `migrate` | `node=N to=M` | Move pod between nodes |

---

## Canvas DSL Icon Specification

Icons can be referenced by AWS service name or full path.

### Service Name Mapping

```markdown
:::canvas
icon gw "API-Gateway" at 100,150 size 48
icon fn "Lambda" at 250,150 size 48
icon db "DynamoDB" at 400,150 size 48
:::
```

### Supported Service Names

**Compute**

| Name | Icon File |
|------|-----------|
| `Lambda` | `Arch_AWS-Lambda_48.svg` |
| `EC2` | `Arch_Amazon-EC2_48.svg` |
| `ECS` | `Arch_Amazon-Elastic-Container-Service_48.svg` |
| `EKS` | `Arch_Amazon-Elastic-Kubernetes-Service_48.svg` |
| `Fargate` | `Arch_AWS-Fargate_48.svg` |
| `Lightsail` | `Arch_Amazon-Lightsail_48.svg` |
| `Batch` | `Arch_AWS-Batch_48.svg` |
| `App-Runner` | `Arch_AWS-App-Runner_48.svg` |

**Containers**

| Name | Icon File |
|------|-----------|
| `ECR` | `Arch_Amazon-Elastic-Container-Registry_48.svg` |
| `App-Mesh` | `Arch_AWS-App-Mesh_48.svg` |

**Storage**

| Name | Icon File |
|------|-----------|
| `S3` | `Arch_Amazon-Simple-Storage-Service_48.svg` |
| `EFS` | `Arch_Amazon-EFS_48.svg` |
| `EBS` | `Arch_Amazon-Elastic-Block-Store_48.svg` |
| `FSx` | `Arch_Amazon-FSx_48.svg` |

**Database**

| Name | Icon File |
|------|-----------|
| `DynamoDB` | `Arch_Amazon-DynamoDB_48.svg` |
| `RDS` | `Arch_Amazon-RDS_48.svg` |
| `Aurora` | `Arch_Amazon-Aurora_48.svg` |
| `ElastiCache` | `Arch_Amazon-ElastiCache_48.svg` |
| `Redshift` | `Arch_Amazon-Redshift_48.svg` |
| `Neptune` | `Arch_Amazon-Neptune_48.svg` |

**Networking**

| Name | Icon File |
|------|-----------|
| `VPC` | `Virtual-private-cloud-VPC_32.svg` |
| `CloudFront` | `Arch_Amazon-CloudFront_48.svg` |
| `Route53` | `Arch_Amazon-Route-53_48.svg` |
| `ALB` | `Arch_Elastic-Load-Balancing_48.svg` |
| `API-Gateway` | `Arch_Amazon-API-Gateway_48.svg` |
| `Transit-Gateway` | `Arch_AWS-Transit-Gateway_48.svg` |
| `Direct-Connect` | `Arch_AWS-Direct-Connect_48.svg` |
| `PrivateLink` | `Arch_AWS-PrivateLink_48.svg` |
| `Global-Accelerator` | `Arch_AWS-Global-Accelerator_48.svg` |

**App Integration**

| Name | Icon File |
|------|-----------|
| `SQS` | `Arch_Amazon-Simple-Queue-Service_48.svg` |
| `SNS` | `Arch_Amazon-Simple-Notification-Service_48.svg` |
| `EventBridge` | `Arch_Amazon-EventBridge_48.svg` |
| `StepFunctions` | `Arch_AWS-Step-Functions_48.svg` |
| `AppSync` | `Arch_AWS-AppSync_48.svg` |
| `MQ` | `Arch_Amazon-MQ_48.svg` |

**AI/ML**

| Name | Icon File |
|------|-----------|
| `Bedrock` | `Arch_Amazon-Bedrock_48.svg` |
| `SageMaker` | `Arch_Amazon-SageMaker_48.svg` |
| `Comprehend` | `Arch_Amazon-Comprehend_48.svg` |
| `Rekognition` | `Arch_Amazon-Rekognition_48.svg` |
| `Lex` | `Arch_Amazon-Lex_48.svg` |

**Security**

| Name | Icon File |
|------|-----------|
| `IAM` | `Arch_AWS-Identity-and-Access-Management_48.svg` |
| `KMS` | `Arch_AWS-Key-Management-Service_48.svg` |
| `Cognito` | `Arch_Amazon-Cognito_48.svg` |
| `WAF` | `Arch_AWS-WAF_48.svg` |
| `Shield` | `Arch_AWS-Shield_48.svg` |
| `Secrets-Manager` | `Arch_AWS-Secrets-Manager_48.svg` |
| `GuardDuty` | `Arch_Amazon-GuardDuty_48.svg` |
| `Inspector` | `Arch_Amazon-Inspector_48.svg` |
| `Security-Hub` | `Arch_AWS-Security-Hub_48.svg` |
| `Certificate-Manager` | `Arch_AWS-Certificate-Manager_48.svg` |

**Management & Monitoring**

| Name | Icon File |
|------|-----------|
| `CloudWatch` | `Arch_Amazon-CloudWatch_48.svg` |
| `CloudTrail` | `Arch_AWS-CloudTrail_48.svg` |
| `CloudFormation` | `Arch_AWS-CloudFormation_48.svg` |
| `Config` | `Arch_AWS-Config_48.svg` |
| `Systems-Manager` | `Arch_AWS-Systems-Manager_48.svg` |
| `X-Ray` | `Arch_AWS-X-Ray_48.svg` |
| `Organizations` | `Arch_AWS-Organizations_48.svg` |
| `Control-Tower` | `Arch_AWS-Control-Tower_48.svg` |
| `DevOps-Guru` | `Arch_Amazon-DevOps-Guru_48.svg` |

**Analytics**

| Name | Icon File |
|------|-----------|
| `Kinesis` | `Arch_Amazon-Kinesis_48.svg` |
| `Athena` | `Arch_Amazon-Athena_48.svg` |
| `OpenSearch` | `Arch_Amazon-OpenSearch-Service_48.svg` |
| `Glue` | `Arch_AWS-Glue_48.svg` |
| `QuickSight` | `Arch_Amazon-QuickSight_48.svg` |
| `EMR` | `Arch_Amazon-EMR_48.svg` |

**Developer Tools**

| Name | Icon File |
|------|-----------|
| `CodePipeline` | `Arch_AWS-CodePipeline_48.svg` |
| `CodeBuild` | `Arch_AWS-CodeBuild_48.svg` |
| `CodeDeploy` | `Arch_AWS-CodeDeploy_48.svg` |
| `CodeCommit` | `Arch_AWS-CodeCommit_48.svg` |

**Other**

| Name | Icon File |
|------|-----------|
| `Amplify` | `Arch_AWS-Amplify_48.svg` |
| `AppConfig` | `Arch_AWS-AppConfig_48.svg` |

### Full Path Reference

```markdown
:::canvas
icon custom "../common/aws-icons/services/Arch_Amazon-S3_48.svg" at 100,250 size 48
:::
```

---

## Mermaid Block Specification

Embed Mermaid diagrams in canvas blocks.

### Syntax

```markdown
:::canvas mermaid
graph LR
    A[Client] --> B[API Gateway]
    B --> C[Lambda]
    C --> D[DynamoDB]
:::
```

### Supported Diagram Types

- `graph` / `flowchart` — Flow diagrams
- `sequenceDiagram` — Sequence diagrams
- `classDiagram` — Class diagrams
- `stateDiagram` — State diagrams
- `erDiagram` — Entity-relationship diagrams
- `gantt` — Gantt charts
- `pie` — Pie charts

### Theme Integration

Mermaid uses dark theme by default to match the presentation theme:

```javascript
mermaid.initialize({ startOnLoad: true, theme: 'dark' });
```

---

## @ref Directive Specification

Add reference links to slides for presenter view.

### Syntax

```markdown
---
@type content
@ref "https://docs.aws.amazon.com/lambda/" "Lambda Documentation"
@ref "https://aws.amazon.com/blogs/compute/" "AWS Compute Blog"

## Slide Content
```

### Multiple References

```markdown
@ref "https://example.com/doc1" "Primary Reference"
@ref "https://example.com/doc2" "Secondary Reference"
@ref "https://example.com/doc3" "Additional Reading"
```

### Data Attribute

References are stored in the slide's `data-refs` attribute as JSON:

```html
<div class="slide" data-refs='[{"url":"https://...","label":"..."}]'>
```

---

## Animations Field Schema

Custom animations can be defined in frontmatter for complex scenarios.

### Syntax

```yaml
---
remarp: true
title: "Custom Animations"

animations:
  arch-flow:
    module: "./animations/arch-flow.js"
    config:
      duration: 500
      easing: "ease-out"
  data-pipeline:
    module: "./animations/data-pipeline.js"
    config:
      steps: 5
---
```

### Animation Module Interface

```javascript
// animations/arch-flow.js
export function init(canvas, config) {
  const ctx = canvas.getContext('2d');
  // Setup code
  return {
    play: () => { /* Start animation */ },
    reset: () => { /* Reset to initial state */ },
    stepForward: () => { /* Advance one step */ },
    stepBackward: () => { /* Go back one step */ }
  };
}
```

### Using Custom Animations

```markdown
---
@type canvas
@canvas-id arch-flow

## Architecture Flow

:::canvas
# Uses the arch-flow animation module defined in frontmatter
:::
```

---

## Remarp Component Examples

Self-contained, copy-paste ready component snippets using `:::html`, `:::script`, and `:::css` blocks.

### Gauge Component

An animated circular gauge that fills to a target percentage.

```markdown
---
@type: content
---
## System Health

:::html
<div class="gauge-container">
  <svg class="gauge" viewBox="0 0 100 100">
    <circle class="gauge-bg" cx="50" cy="50" r="45" fill="none" stroke="#2d3250" stroke-width="8"/>
    <circle class="gauge-fill" cx="50" cy="50" r="45" fill="none" stroke="#00d68f" stroke-width="8"
            stroke-dasharray="283" stroke-dashoffset="283" stroke-linecap="round"
            transform="rotate(-90 50 50)"/>
    <text class="gauge-value" x="50" y="55" text-anchor="middle" fill="#e8eaed" font-size="20">0%</text>
  </svg>
  <div class="gauge-label">CPU Usage</div>
</div>
:::

:::css
.gauge-container { text-align: center; }
.gauge { width: 200px; height: 200px; }
.gauge-fill { transition: stroke-dashoffset 1s ease-out; }
.gauge-label { color: #9ba1b8; margin-top: 0.5rem; }
:::

:::script
const target = 73;
const circle = document.querySelector('.gauge-fill');
const text = document.querySelector('.gauge-value');
const circumference = 2 * Math.PI * 45;
const offset = circumference - (target / 100) * circumference;
circle.style.strokeDashoffset = offset;
text.textContent = target + '%';
:::
```

### Sparkline Component

A compact inline SVG sparkline chart generated from data.

```markdown
---
@type: content
---
## Weekly Trends

:::html
<div class="sparkline-row">
  <div class="sparkline-item">
    <span class="sparkline-label">Requests</span>
    <svg class="sparkline" id="spark-requests" viewBox="0 0 100 30" preserveAspectRatio="none"></svg>
    <span class="sparkline-value" id="spark-requests-val"></span>
  </div>
  <div class="sparkline-item">
    <span class="sparkline-label">Latency</span>
    <svg class="sparkline" id="spark-latency" viewBox="0 0 100 30" preserveAspectRatio="none"></svg>
    <span class="sparkline-value" id="spark-latency-val"></span>
  </div>
</div>
:::

:::css
.sparkline-row { display: flex; gap: 2rem; justify-content: center; margin: 2rem 0; }
.sparkline-item { display: flex; align-items: center; gap: 0.5rem; }
.sparkline-label { color: #9ba1b8; min-width: 80px; }
.sparkline { width: 120px; height: 30px; }
.sparkline-value { color: #e8eaed; font-weight: bold; min-width: 60px; }
:::

:::script
function drawSparkline(id, data, color) {
  const svg = document.getElementById(id);
  const valEl = document.getElementById(id + '-val');
  const max = Math.max(...data), min = Math.min(...data);
  const range = max - min || 1;
  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * 100;
    const y = 30 - ((v - min) / range) * 28;
    return `${x},${y}`;
  }).join(' ');
  svg.innerHTML = `<polyline points="${points}" fill="none" stroke="${color}" stroke-width="2"/>`;
  valEl.textContent = data[data.length - 1].toLocaleString();
}
drawSparkline('spark-requests', [120, 145, 132, 178, 156, 189, 210], '#6c5ce7');
drawSparkline('spark-latency', [45, 42, 48, 39, 44, 41, 38], '#00d68f');
:::
```

### Progress Ring Component

A CSS-animated progress ring with percentage display.

```markdown
---
@type: content
---
## Migration Status

:::html
<div class="progress-rings">
  <div class="ring-item">
    <div class="ring" style="--progress: 85; --color: #00d68f;">
      <span class="ring-value">85%</span>
    </div>
    <span class="ring-label">Compute</span>
  </div>
  <div class="ring-item">
    <div class="ring" style="--progress: 62; --color: #6c5ce7;">
      <span class="ring-value">62%</span>
    </div>
    <span class="ring-label">Storage</span>
  </div>
  <div class="ring-item">
    <div class="ring" style="--progress: 94; --color: #00b8d9;">
      <span class="ring-value">94%</span>
    </div>
    <span class="ring-label">Network</span>
  </div>
</div>
:::

:::css
.progress-rings { display: flex; gap: 3rem; justify-content: center; margin: 2rem 0; }
.ring-item { text-align: center; }
.ring {
  width: 120px; height: 120px; border-radius: 50%;
  background: conic-gradient(var(--color) calc(var(--progress) * 3.6deg), #2d3250 0);
  display: flex; align-items: center; justify-content: center;
  position: relative;
}
.ring::before {
  content: ''; position: absolute; width: 90px; height: 90px;
  background: #1a1a2e; border-radius: 50%;
}
.ring-value { position: relative; z-index: 1; color: #e8eaed; font-size: 1.5rem; font-weight: bold; }
.ring-label { display: block; color: #9ba1b8; margin-top: 0.5rem; }
:::
```

### Data Table Component

A styled data table using the built-in `.data-table` class.

```markdown
---
@type: content
---
## Instance Comparison

:::html
<table class="data-table">
  <thead>
    <tr>
      <th>Instance</th>
      <th>vCPU</th>
      <th>Memory</th>
      <th>Price/hr</th>
      <th>Use Case</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>t3.medium</code></td>
      <td>2</td>
      <td>4 GB</td>
      <td>$0.0416</td>
      <td>Dev/Test</td>
    </tr>
    <tr>
      <td><code>m6i.large</code></td>
      <td>2</td>
      <td>8 GB</td>
      <td>$0.096</td>
      <td>General</td>
    </tr>
    <tr>
      <td><code>c6i.xlarge</code></td>
      <td>4</td>
      <td>8 GB</td>
      <td>$0.17</td>
      <td>Compute</td>
    </tr>
    <tr>
      <td><code>r6i.large</code></td>
      <td>2</td>
      <td>16 GB</td>
      <td>$0.126</td>
      <td>Memory</td>
    </tr>
  </tbody>
</table>
:::
```

The `.data-table` class is provided by the reactive-presentation theme and includes dark styling, hover effects, and responsive behavior.

### CSS-only Donut Chart

A donut chart using pure CSS conic-gradient — no JavaScript required.

```markdown
---
@type: content
---
## Cost Breakdown

:::html
<div class="donut-chart-container">
  <div class="donut-chart">
    <div class="donut-hole">
      <span class="donut-total">$4,250</span>
      <span class="donut-subtitle">Monthly</span>
    </div>
  </div>
  <div class="donut-legend">
    <div class="legend-item"><span class="legend-color" style="background: #6c5ce7;"></span>Compute (45%)</div>
    <div class="legend-item"><span class="legend-color" style="background: #00d68f;"></span>Storage (25%)</div>
    <div class="legend-item"><span class="legend-color" style="background: #00b8d9;"></span>Network (18%)</div>
    <div class="legend-item"><span class="legend-color" style="background: #ff6b6b;"></span>Other (12%)</div>
  </div>
</div>
:::

:::css
.donut-chart-container { display: flex; align-items: center; justify-content: center; gap: 3rem; margin: 2rem 0; }
.donut-chart {
  width: 200px; height: 200px; border-radius: 50%;
  background: conic-gradient(
    #6c5ce7 0deg 162deg,
    #00d68f 162deg 252deg,
    #00b8d9 252deg 316.8deg,
    #ff6b6b 316.8deg 360deg
  );
  display: flex; align-items: center; justify-content: center;
}
.donut-hole {
  width: 120px; height: 120px; border-radius: 50%;
  background: #1a1a2e; display: flex; flex-direction: column;
  align-items: center; justify-content: center;
}
.donut-total { color: #e8eaed; font-size: 1.5rem; font-weight: bold; }
.donut-subtitle { color: #9ba1b8; font-size: 0.875rem; }
.donut-legend { display: flex; flex-direction: column; gap: 0.5rem; }
.legend-item { display: flex; align-items: center; gap: 0.5rem; color: #e8eaed; }
.legend-color { width: 12px; height: 12px; border-radius: 2px; }
:::
```

---

For complex interactive patterns (simulators, dashboards, YAML builders), see [interactive-patterns-guide.md](interactive-patterns-guide.md).
