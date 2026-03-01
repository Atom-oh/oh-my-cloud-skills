---
name: reactive-presentation
description: "Create interactive HTML presentation slideshows with Canvas animations, quizzes, dark theme, and keyboard navigation. Deploy to GitHub Pages. Use when user asks to: create slides, build a presentation, make a slideshow, training slides, interactive presentation, Canvas animation slides, or mentions 'reactive presentation'. Supports PPTX template theming and Marp markdown content authoring. Supports multi-block training sessions (30min-3hr), technical deep-dives, and workshop content."
---

# Reactive Presentation

Build interactive HTML slideshow presentations deployed via GitHub Pages. No build tools required — pure HTML/CSS/JS with a shared framework for navigation, animations, and quizzes. Supports PPTX template theme extraction and Marp markdown for content authoring.

## Workflow

### Phase 1: Theme Setup (optional — when PPTX template provided)

If the user provides a `.pptx` template file, extract theme elements:

```bash
python3 {skill-dir}/scripts/extract_pptx_theme.py <pptx_path> -o {repo}/common/pptx-theme/
```

This generates:
- `theme-manifest.json` — extracted colors, fonts, logos, footer text, master texts, layout details
- `theme-override.css` — CSS variable overrides for the dark theme
- `images/` — extracted logos and background images

After extraction, read `theme-manifest.json` and apply in every block HTML:
- **`footer_text`** → `SlideFramework({ footer: manifest.footer_text })` — deduplicated footer from placeholder + master text shapes
- **`master_texts`** → additional branding text from slide master (copyright, event name, confidentiality notices); `is_footer_area: true` marks text in bottom 15%
- **`layout_details`** → reference original PPTX layout structure (Title Slide → §0a cover, Section Header → §1 title)
- **`logos[0].filename`** → `SlideFramework({ logoSrc: '../common/pptx-theme/images/...' })`

Copy `theme-override.css` into `common/` alongside `theme.css`. Review the manifest and adjust colors/logo positioning if needed.

### Phase 2: Content Authoring (Marp Markdown)

Plan the presentation structure with the user. **Ask these questions during planning:**
- **Topic & audience** — technical depth, pain points, learning objectives
- **Duration** — determines block count and slide count (see slide-patterns.md for pacing)
- **Blocks** — split into 20-35 min blocks with 5 min breaks
- **Target repo** — GitHub repo for deployment (default: `~/reactive_presentation/`)
- **Language** — Korean or English (technical terms always English)
- **Aspect ratio** — confirm 16:9 (default). The framework enforces 16:9 with letterboxing on non-16:9 displays
- **PPTX/PDF template** (REQUIRED, skippable) — "디자인 참고용 PPTX/PDF 파일이 있으신가요? (파일 경로 또는 'skip')"
  - Provided → run Phase 1 extraction first to apply corporate branding (colors, logo, fonts)
  - "skip" → use CSS-only fallback cover §0b
- **Speaker info** (REQUIRED, skippable) — "발표자 이름, 직함/소속? (또는 'skip')"
  - Provided → store in `MEMORY.md` for reuse across sessions. Used in the session cover slide (see slide-patterns.md §0a)
  - "skip" → omit speaker section from cover
  - Already in `MEMORY.md` → confirm with user or reuse

Write content as Marp markdown:
- Frontmatter with title, blocks config
- Slide separator: `---`
- Block markers: `<!-- block: name -->`
- Type directives: `<!-- type: compare|canvas|quiz|tabs|... -->`
- Speaker notes: `<!-- notes: text -->`

See [references/marp-format-guide.md](references/marp-format-guide.md) for full format specification.

### Phase 3: HTML Generation

**Option A — Script conversion:**
```bash
python3 {skill-dir}/scripts/marp_to_slides.py content.md -o {repo}/{slug}/ --theme-dir {repo}/common/pptx-theme/
```
Generates HTML files per block with proper framework references.

**Option B — Manual build (recommended for rich interactivity):**
Claude builds HTML directly from the Marp content, adding Canvas animations and complex interactive elements inline. Use the Marp as a content outline.

### Phase 4: Content Review & Iteration

After generating Marp markdown and/or initial HTML, enter a feedback loop with the user. **Always ask:**

> 콘텐츠를 검토해 주세요. 수정 방법을 선택해 주세요:
> 1. **Marp 직접 수정** — Marp 파일을 직접 편집하신 후 알려주시면, 변경 사항을 읽어서 HTML에 반영합니다.
> 2. **프롬프트로 수정 요청** — 변경하고 싶은 내용을 말씀해 주시면 Marp와 HTML을 함께 수정합니다.
> 3. **진행** — 현재 내용이 좋으면 다음 단계로 넘어갑니다.

**Option 1 — User edits Marp directly:**
1. User opens and edits the Marp `.md` file in their editor
2. User signals completion (e.g., "수정 완료", "done editing")
3. Claude reads the updated Marp file, diffs against the previous version
4. Claude applies the content changes to the corresponding HTML block files
5. Return to feedback prompt (user may iterate multiple times)

**Option 2 — User requests changes via prompt:**
1. User describes what to change (e.g., "슬라이드 5에 비교 탭 추가해줘", "퀴즈 문제를 3개로 줄여줘")
2. Claude updates both the Marp source file AND the HTML block files to stay in sync
3. Return to feedback prompt

**Option 3 — Proceed:**
Continue to Enhancement phase.

Key rules for iteration:
- **Marp ↔ HTML sync**: When either is modified, keep both in sync. Marp is the content source of truth; HTML adds interactivity on top.
- **Preserve interactivity**: When updating HTML from Marp changes, preserve existing Canvas animations, quiz components, and interactive elements unless the user explicitly removed them.
- **Incremental updates**: Only modify the slides that changed, not the entire file.
- **Show what changed**: After applying updates, briefly summarize which slides were modified and what changed.

### Phase 5: Enhancement

- Add Canvas animations to `<!-- type: canvas -->` slides (implement JS using animation-utils.js)
- Add complex interactive elements (the Marp converter creates placeholders)
- Extract AWS Architecture Icons for architecture/service diagrams (see [references/aws-icons-guide.md](references/aws-icons-guide.md)):
  ```bash
  python3 {skill-dir}/scripts/extract_aws_icons.py -o {repo}/common/aws-icons/
  ```
- Test presenter view (P key) with speaker notes

### Phase 6: Set Up Structure

Copy framework assets from this skill into the repo's `common/` directory:

```
{repo}/
├── index.html                      # Hub page (all presentations)
├── common/                         # Copy from skill assets/
│   ├── theme.css                   # Dark theme, 16:9
│   ├── theme-override.css          # PPTX theme overrides (optional)
│   ├── slide-framework.js          # Keyboard/touch nav, progress, presenter
│   ├── presenter-view.js           # Presenter view (P key)
│   ├── animation-utils.js          # Canvas primitives
│   ├── quiz-component.js           # Quiz component
│   ├── aws-icons/                  # AWS Architecture Icons (optional, see aws-icons-guide.md)
│   │   ├── services/               # Service-level icons (EKS, Lambda, etc.)
│   │   ├── categories/             # Category icons (Compute, Containers, etc.)
│   │   ├── resources/              # Resource-level icons (EC2 Instance, etc.)
│   │   └── groups/                 # Group icons (VPC, Subnet, Region)
│   └── pptx-theme/                 # Extracted PPTX assets (optional)
│       ├── theme-manifest.json
│       └── images/
└── {presentation-slug}/
    ├── index.html                  # TOC page with block links
    ├── 01-block-name.html          # Block 1
    ├── 02-block-name.html          # Block 2
    └── ...
```

Copy assets: `cp {skill-dir}/assets/* {repo}/common/`

For TOC `index.html` pages, add export buttons and include the export script:
```html
<div class="export-toolbar">
  <button class="export-btn" onclick="ExportUtils.exportPDF({ title: 'Title' })">Export PDF</button>
  <button class="export-btn" onclick="ExportUtils.downloadZIP()">Download ZIP</button>
</div>
<script src="../common/export-utils.js"></script>
```

If `index.html` hub already exists, add a new card. If new repo, create the hub page.

### Phase 7: Verify

For each block HTML file, check:
- Slide count matches plan
- `SlideFramework` initialized with correct options (footer, logoSrc, presenterNotes)
- All Canvas IDs have `setupCanvas()` calls
- Quiz components use correct `data-quiz` / `data-correct` attributes
- Framework file references use correct relative paths (`../common/`)
- Theme override CSS is linked (if PPTX theme was extracted)
- Content is in the correct language
- Presenter view (P key) shows notes correctly
- First slide is Session Cover (§0a or §0b) — NOT `.title-slide` class
- Last slide is a Thank You closing slide with `← 목차로 돌아가기` link to `index.html` and optional next block link

**Screenshot Verification (필수 — FHD/4K 해상도 검증):**

모든 프레젠테이션은 FHD(1920×1080)와 4K(3840×2160) 두 해상도에서 레이아웃을 캡쳐하여 검증해야 합니다. 이 단계를 건너뛰지 마세요.

Use Playwright MCP to capture and visually review every interactive slide at two resolutions:

1. **FHD (1920×1080)** — primary target resolution
   ```
   browser_resize({ width: 1920, height: 1080 })
   ```
2. **4K (3840×2160)** — high-DPI scaling verification
   ```
   browser_resize({ width: 3840, height: 2160 })
   ```

For each resolution:
- Navigate to each Canvas/interactive slide and take a screenshot (`browser_take_screenshot`)
- Visually confirm: text readability, canvas proportions, layout not overflowing, buttons/controls visible
- Test interactive elements: tab switching, slider input, button clicks — screenshot after interaction
- Verify responsive canvas fills container proportionally (no letterboxing, no cropping)
- Check that DPR-aware rendering produces crisp text/lines at 4K (no blurry upscaling)
- **↑↓/Enter focus navigation**: Verify focus highlight and triggered state render correctly at both resolutions
- **Speaker notes panel (N key)**: Verify notes panel layout doesn't break presentation scaling
- **Fullscreen (F key)**: Verify auto-hide controls and proper scaling in fullscreen mode

**Scaling approach**: Presentations use a fixed 1920×1080 design canvas with `transform: scale()` to fit any viewport. All internal dimensions are in `px`. The scale factor is calculated as `Math.min(viewportWidth/1920, viewportHeight/1080)` and applied via CSS transform. This ensures pixel-perfect consistency across FHD, 4K, and arbitrary resolutions.

### Phase 8: Deploy

```bash
git add common/ {slug}/ index.html
git commit -m "feat: add {presentation-name} interactive training"
git push origin main
```

Enable GitHub Pages: Settings → Pages → main branch / root.

## Slide Type Decision Guide

| Content Type | Slide Pattern | Interactive Element |
|---|---|---|
| Architecture overview | Canvas Animation | Component flow with Play button |
| A vs B comparison | Compare Toggle | `.compare-toggle` buttons |
| Config variants | Tab Content | `.tab-bar` with YAML code blocks |
| Step-by-step process | Timeline | `.timeline` with animated steps |
| Monitoring/dashboard | Canvas Animation | Node grid + event log + buttons |
| Parameter exploration | Slider | `input[type=range]` + live output |
| Best practices | Checklist | `.checklist` with click-to-toggle |
| Best practices + config | Checklist with YAML | `.checklist` + `.check-yaml` expand on click (see slide-patterns.md §7b) |
| YAML/code example | Code Block | `.code-block` with syntax spans |
| Customer problem | Pain Quote | `.pain-quote` + challenge list |
| Block summary | Quiz | `data-quiz` + 3-4 questions |
| Block closing | Thank You | Gradient heading + TOC link + next block link |

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| ← → | Previous / Next slide |
| Space | Next slide |
| ↑ ↓ | Focus navigation within slide (cycle through interactive cards/elements) |
| Enter | Trigger/activate focused element (expand card, show detail, animate) |
| F | Toggle fullscreen |
| N | Toggle speaker notes panel (bottom 20% overlay) |
| P | Open presenter view (new window with notes, timer, slide sync) |
| Esc | Exit fullscreen / dismiss notes panel |
| Home/End | First/Last slide |
| 1-9 | Jump to slide number |

### Focus Navigation (↑↓ / Enter)

Slides with interactive elements (cards, panels, sections) support keyboard-driven focus navigation:

- **↓ key**: Move focus highlight to the next interactive element in the current slide
- **↑ key**: Move focus to the previous element
- **Enter key**: Toggle "triggered" state — expands the focused element (scale + glow), dims siblings, and optionally shows detail panels (e.g., scenario details with PII types, processing flow, and output)
- Focus resets to none on slide change
- Visual: focused element gets `outline: 3px solid accent + box-shadow glow`; triggered element scales up with enhanced glow while siblings dim

Supported element types: `.card`, `.tech-card`, `.scenario-card`, `.security-card`, `.concept-point`, `.booth-section`, `.pii-box`, or any custom focusable class defined per slide.

## Quality Assurance

When slides contain YAML/config examples, verify against official documentation:

- **Canvas proportional scaling**: All canvas animations MUST use `ResizeObserver` + `BASE_W/BASE_H` + `ctx.scale(scale * dpr, scale * dpr)` pattern for FHD/4K responsiveness. Never use `setupCanvas()` alone (it sets `max-width` in pixels). See slide-patterns.md §5 for the full pattern.
- **Karpenter v1 API**: `expireAfter` is under `spec.template.spec`, NOT `spec.disruption`. Verify at https://karpenter.sh/docs/concepts/nodepools/
- **Karpenter metrics**: Use `_total` suffix for counters (e.g., `karpenter_nodeclaims_terminated_total`). Verify at https://karpenter.sh/docs/reference/metrics/
- **Grafana datasources**: Loki derivedFields uses `regex` (not `matcherRegex`). Verify at https://grafana.com/docs/grafana/latest/datasources/loki/
- **GitBook anchors**: Korean headings generate Korean slug anchors (e.g., `## 1. 관측성 스택 아키텍처` → `#1-관측성-스택-아키텍처`). Dots after numbers are removed, Korean chars preserved, spaces→hyphens.
- **Kubernetes API**: `topologySpreadConstraints` requires `labelSelector`. VPA `Auto` mode is deprecated (use `Recreate`).

## Resources

### assets/
Framework files to copy into `common/`:
- `theme.css` — dark theme, Pretendard font, 16:9 layout, all component styles
- `theme-override-template.css` — template for PPTX-extracted CSS overrides
- `slide-framework.js` — SlideFramework class (keyboard, touch, progress, hash nav, footer, logo, presenter view)
- `presenter-view.js` — PresenterView class (draggable splitters, large notes area, Pretendard font, localStorage persistence, BroadcastChannel sync)
- `animation-utils.js` — Canvas primitives, AnimationLoop, TimelineAnimation, Colors, Ease
- `quiz-component.js` — QuizManager with auto-grading and feedback
- `export-utils.js` — ExportUtils with PDF export (browser print) and ZIP download (JSZip CDN, auto-discovers and bundles all referenced images)

### scripts/
- `extract_pptx_theme.py` — Extract PPTX theme → CSS overrides + images (see [references/pptx-theme-guide.md](references/pptx-theme-guide.md))
- `marp_to_slides.py` — Convert Marp markdown → HTML slide files (see [references/marp-format-guide.md](references/marp-format-guide.md))
- `extract_aws_icons.py` — Extract AWS Architecture Icons from bundled zip → SVG files organized by category (see [references/aws-icons-guide.md](references/aws-icons-guide.md))

### references/
- [framework-guide.md](references/framework-guide.md) — Complete API reference for CSS classes, JS functions, HTML template
- [slide-patterns.md](references/slide-patterns.md) — Copy-paste HTML patterns for each slide type, Canvas animation patterns
- [marp-format-guide.md](references/marp-format-guide.md) — Marp markdown format specification with examples
- [pptx-theme-guide.md](references/pptx-theme-guide.md) — PPTX theme extraction usage, color mapping, troubleshooting
- [aws-icons-guide.md](references/aws-icons-guide.md) — AWS Architecture Icons usage, naming conventions, commonly used icons by topic
