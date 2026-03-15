---
name: reactive-presentation
description: "Create interactive HTML presentation slideshows with Canvas animations, quizzes, dark theme, and keyboard navigation. Deploy to GitHub Pages. Use when user asks to: create slides, build a presentation, make a slideshow, training slides, interactive presentation, Canvas animation slides, or mentions 'reactive presentation'. Supports PPTX template theming and Remarp markdown content authoring. Supports multi-block training sessions (30min-3hr), technical deep-dives, and workshop content."
model: opus
allowed-tools:
  - Read
  - Bash
---

# Reactive Presentation

Build interactive HTML slideshow presentations deployed via GitHub Pages. No build tools required — pure HTML/CSS/JS with a shared framework for navigation, animations, and quizzes. Supports PPTX template theme extraction and Remarp format for content authoring. Marp markdown is supported for legacy file maintenance only.

> **New to Remarp?** See [REMARP.md](REMARP.md) for a quick introduction and 5-minute getting started guide.

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

> **Note**: AWS Architecture Icons은 `remarp_to_slides.py build`가 HTML에서 참조된 아이콘만 자동으로 `common/aws-icons/`에 복사합니다. 수동 추출은 불필요합니다.
> 디버깅/확인 용도로만 `extract_aws_icons.py`를 사용하세요.

### Phase 2: Content Authoring

Plan the presentation structure with the user. **Ask these questions during planning:**
- **Topic & audience** — technical depth, pain points, learning objectives
- **Duration** — determines block count and slide count (see slide-patterns.md for pacing)
- **Blocks** — split into 20-35 min blocks with 5 min breaks
- **Target repo** — GitHub repo for deployment (default: `~/reactive_presentation/`)
- **Language** — Korean or English (technical terms always English)
- **Aspect ratio** — confirm 16:9 (default). The framework enforces 16:9 with letterboxing on non-16:9 displays
- **Design & layout references** (REQUIRED, skippable) — "참고할 디자인 자료가 있으신가요? PPTX, PDF, 이미지, 또는 기존 프레젠테이션 경로를 알려주세요. (또는 'skip')"
  - Provided → 제공된 자료에서 **브랜딩 + 레이아웃** 모두 추출하여 반영:
    - `.pptx` → Phase 1 테마 추출 실행: 색상, 로고, 폰트 + **Slide Master 레이아웃** (플레이스홀더 배치, 폰트 계층 구조, 여백/간격, 타이틀/본문 위치) + `layout_details`로 PPTX 레이아웃→슬라이드 타입 매핑 참고
    - `.pdf` / 이미지 → 시각적 레이아웃, 색상 배치, 콘텐츠 밀도, 타이포그래피 참고
    - 기존 프레젠테이션 경로 (slides.json, HTML, animations/ JS) → 슬라이드 타입 배치, body HTML 구조, Canvas 애니메이션 패턴, CSS 클래스 활용 참고
  - "skip" → CSS-only fallback cover §0b + 기본 테마(theme.css) + slide-patterns.md 표준 패턴으로 진행. **PPTX 없이 진행 시 `_presentation.md`의 `theme:` 섹션에 `footer`와 `logo`를 반드시 수동 설정** (아래 예시 참조)
  - **자동 탐색**: `~/oh-my-skill-tester/` 내 기존 프레젠테이션이 있으면 목록을 보여주고 참고 여부를 확인
- **Speaker info** (REQUIRED, skippable) — "발표자 이름, 직함/소속? (또는 'skip')"
  - Provided → store in `MEMORY.md` for reuse across sessions. Used in the session cover slide (see slide-patterns.md §0a)
  - "skip" → omit speaker section from cover
  - Already in `MEMORY.md` → confirm with user or reuse
- **Quiz inclusion** (REQUIRED, skippable) — "각 블록 끝에 복습 퀴즈를 포함할까요? (yes/no 또는 'skip' 입력 시 퀴즈 미포함)"
  - "yes" → 각 블록 끝에 Quiz 슬라이드 (3-4문항) 포함
  - "no" / "skip" → 퀴즈 미포함. Block summary는 Key Takeaways 또는 Summary 슬라이드로 대체

Remarp 마크다운으로 콘텐츠를 작성합니다 (기본). Remarp는 프래그먼트 애니메이션, Canvas DSL, 풍부한 스피커 노트, 슬라이드 전환 효과를 마크다운에서 직접 제어하는 차세대 포맷입니다.

**멀티파일 프로젝트 구조:**
```
{slug}/
├── _presentation.md           ← 글로벌 설정 (theme, footer, logo)
├── 01-fundamentals.md         ← 블록 1
├── 02-deep-dive.md            ← 블록 2
└── animations/                ← Canvas 애니메이션 JS 모듈 (해당 시)
    └── slide-05-flow.js
```

> **`_presentation.md` footer/logo 설정 (필수)**:
> - **PPTX 있는 경우**: Phase 1에서 `theme-manifest.json`의 `footer_text` → `theme.footer`, `logos[0].filename` → `theme.logo`로 자동 반영
> - **PPTX 없는 경우**: `_presentation.md`의 `theme:` 섹션에 반드시 수동 설정:
>   ```yaml
>   theme:
>     footer: "© 2026 Company Name. All rights reserved."
>     logo: "../common/logo.png"
>   ```
> - footer/logo가 누락되면 `SlideFramework` 초기화에서 해당 옵션이 빠져 빈 영역으로 렌더링됩니다.

> `.md` 확장자 사용 (이전: `.remarp.md`). `remarp: true` frontmatter로 일반 마크다운과 구분됩니다. `.remarp.md` 확장자도 하위호환 지원.

**핵심 기능:**
- `remarp: true` frontmatter로 시작
- `@type`, `@layout`, `@transition` 슬라이드 디렉티브
- `{.click}` 인라인 프래그먼트 + `:::click` 블록 애니메이션
- `:::notes` 블록으로 스피커 노트 (타이밍, 큐 마커 지원)

> **스피커 노트 품질 기준 (필수)**:
> 모든 슬라이드에는 반드시 `:::notes` 블록을 포함하며, 다음 기준을 충족해야 합니다:
> - **분량**: 슬라이드당 최소 150자, 권장 300~500자 (발표 시 1~3분 분량)
> - **구조**: `{timing: Nmin}` 마커로 시작 → 도입 멘트 → 핵심 포인트 설명 (슬라이드에 없는 보충 설명, 예시, 비유 포함) → 청중 인터랙션 큐 (`{cue: question}`, `{cue: pause}`) → 전환 멘트
> - **톤**: 발표자가 그대로 읽어도 자연스러운 구어체. "~입니다", "~해보겠습니다" 스타일
> - **내용**: 슬라이드 텍스트를 반복하지 말고, 왜 중요한지, 실무에서 어떻게 적용하는지, 흔한 실수나 팁을 보충
> - **전환**: 마지막에 `{cue: transition}` + 다음 슬라이드로 이어지는 브릿지 문장
- `:::canvas` DSL로 선언적 Canvas 애니메이션
- `::: left`/`::: right` 컬럼 레이아웃

See [references/remarp-format-guide.md](references/remarp-format-guide.md) for full format specification.

> ⚠️ 에이전트는 사용자가 명시하지 않는 한 항상 Remarp로 진행합니다.

**Alternative Formats (명시적 요청 시에만):**

**slides.json** — 사용자가 JSON 런타임 렌더링을 명시적으로 요청할 때만 사용합니다. 각 블록별 `slides.json` 파일을 작성하면 `slide-renderer.js`가 런타임에 HTML을 생성합니다.
- JSON 스키마: [references/slide-patterns.md](references/slide-patterns.md) → "JSON Authoring Mode" 섹션

**Marp Markdown (레거시)** — 기존 Marp 파일 유지보수 또는 사용자가 Marp를 명시적으로 요청할 때만 사용합니다.
- See [references/marp-format-guide.md](references/marp-format-guide.md) for full format specification.

### Phase 2.5: Convert Existing PPTX/PDF (optional)

기존 PPTX 또는 PDF 파일을 Remarp 프로젝트로 변환합니다. 변환된 `.md` 파일을 편집한 후 Phase 3에서 HTML을 빌드합니다.

```bash
# PPTX → Remarp 프로젝트 (테마 자동 추출 포함)
python3 {skill-dir}/scripts/convert_to_remarp.py <input.pptx> -o {repo}/{slug}/ --lang ko

# PDF → Remarp 프로젝트 (이미지 배경 + 텍스트 추출)
python3 {skill-dir}/scripts/convert_to_remarp.py <input.pdf> -o {repo}/{slug}/ --lang ko

# 변환 + 즉시 HTML 빌드
python3 {skill-dir}/scripts/convert_to_remarp.py <input.pptx> -o {repo}/{slug}/ --build

# 블록 분할 크기 지정 (기본: Section Header 기반, 없으면 15 슬라이드씩)
python3 {skill-dir}/scripts/convert_to_remarp.py <input.pptx> -o {repo}/{slug}/ --block-size 10

# 기존 변환 결과 덮어쓰기 (타임스탬프 .bak 백업 생성)
python3 {skill-dir}/scripts/convert_to_remarp.py <input.pptx> -o {repo}/{slug}/ --force
```

**변환 결과물:**
```
{slug}/
├── _presentation.md       ← 글로벌 설정 (theme, blocks)
├── 01-introduction.md     ← 블록 1 (remarp: true)
├── 02-deep-dive.md        ← 블록 2
├── assets/                ← 추출된 이미지
│   ├── slide-00-logo.png
│   └── slide-03-diagram.png
└── _theme/{stem}/         ← 추출된 테마 (PPTX만)
    ├── theme-manifest.json
    ├── theme-override.css
    └── images/
```

**변환 후 편집**: 생성된 `.md` 파일에서 `@speaker`, `{.click}` 프래그먼트, `:::canvas` DSL, `@type: quiz` 등을 자유롭게 추가/수정할 수 있습니다. Remarp 문법은 [references/remarp-format-guide.md](references/remarp-format-guide.md) 참조.

**PDF 변환 참고**: PDF 슬라이드는 이미지 배경(`@background: assets/page-NN.png`) + 추출 텍스트로 변환됩니다. 정확한 텍스트가 필요하면 `@background`를 제거하고 텍스트를 직접 작성하세요.

### Phase 3: HTML Generation

Remarp 프로젝트 디렉토리를 빌드합니다:
```bash
# 전체 빌드
python3 {skill-dir}/scripts/remarp_to_slides.py build {repo}/{slug}/

# 특정 블록만 빌드
python3 {skill-dir}/scripts/remarp_to_slides.py build {repo}/{slug}/ --block 01-fundamentals

# 변경된 블록만 빌드 (증분 빌드)
python3 {skill-dir}/scripts/remarp_to_slides.py sync {repo}/{slug}/

# Marp에서 Remarp로 마이그레이션
python3 {skill-dir}/scripts/remarp_to_slides.py migrate content.md -o {repo}/{slug}/
```

**Alternative Formats (명시적 요청 시에만):**

**slides.json** — `index.html` 보일러플레이트를 생성합니다. `slide-renderer.js`가 런타임에 `slides.json`을 읽어 HTML을 동적 생성합니다.
```html
<div class="slide-deck"></div>
<script src="../common/slide-renderer.js"></script>
<script>
  new SlideRenderer({ footer, logoSrc }).render('./slides.json');
</script>
```
보일러플레이트 전체 템플릿: [references/framework-guide.md](references/framework-guide.md) → "index.html 보일러플레이트"

**Marp (레거시 유지보수 전용 — 새 프레젠테이션에 사용 금지)**:
```bash
python3 {skill-dir}/scripts/marp_to_slides.py content.md -o {repo}/{slug}/ --theme-dir {repo}/common/pptx-theme/
```

### Phase 4: Content Review & Iteration

After generating Remarp markdown and/or initial HTML, enter a feedback loop with the user. **Always ask:**

> 콘텐츠를 검토해 주세요. 수정 방법을 선택해 주세요:
> 1. **Remarp 직접 수정** — `.remarp.md` 파일을 직접 편집하신 후 "반영해주세요"라고 알려주시면, 변경 사항을 읽어서 HTML에 반영합니다.
> 2. **프롬프트로 수정 요청** — 변경하고 싶은 내용을 말씀해 주시면 Remarp와 HTML을 함께 수정합니다.
> 3. **진행** — 현재 내용이 좋으면 다음 단계로 넘어갑니다.

**Option 1 — User edits Remarp directly:**
1. User opens and edits the `.md` file(s) in their editor
2. User signals completion (e.g., "반영해주세요", "done editing")
3. Claude reads the updated Remarp file(s), diffs against the previous version
4. Claude runs `remarp_to_slides.py sync` to rebuild changed blocks
5. Return to feedback prompt (user may iterate multiple times)

**Option 2 — User requests changes via prompt:**
1. User describes what to change (e.g., "슬라이드 5에 비교 탭 추가해줘", "퀴즈 문제를 3개로 줄여줘")
2. Claude updates both the Remarp source file AND rebuilds the HTML block files to stay in sync
3. Return to feedback prompt

**Option 3 — Proceed:**
Continue to Enhancement phase.

Key rules for iteration:
- **Remarp ↔ HTML sync**: When either is modified, keep both in sync. Remarp is the content source of truth; HTML adds interactivity on top.
- **Preserve interactivity**: When updating HTML from Remarp changes, preserve existing Canvas animations, quiz components, and interactive elements unless the user explicitly removed them.
- **Incremental updates**: Only modify the slides that changed, not the entire file.
- **Show what changed**: After applying updates, briefly summarize which slides were modified and what changed.

### Phase 5: Enhancement

- Add Canvas animations to `@type: canvas` slides (implement JS using animation-utils.js)
- Add complex interactive elements (the Remarp/Marp converter creates placeholders)
- AWS Architecture Icons은 `build` 시 HTML에서 참조된 아이콘만 자동 복사됩니다 (see [references/aws-icons-guide.md](references/aws-icons-guide.md))
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
│   ├── slide-renderer.js           # JSON → HTML renderer
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

### Phase 7: Quality Review (필수 — 생략 불가)

콘텐츠 완성 후 배포/완료 선언 전에 반드시:
1. content-review-agent 호출 → `review content at [파일경로]`
2. FAIL/REVIEW 판정 시 수정 후 재리뷰 (최대 3회)
3. PASS (≥85점) 획득 후에만 완료 선언

> ⚠️ 이 단계를 건너뛰고 배포하는 것은 금지됩니다.

### Phase 8: Verify

For each block HTML file, check:
- Slide count matches plan
- `SlideFramework` initialized with correct options (footer, logoSrc, presenterNotes)
- All Canvas IDs have `setupCanvas()` calls
- **Canvas Layout Quality Check (필수)**:
  - Playwright로 각 Canvas 슬라이드 스크린샷 촬영
  - 요소 겹침 확인: 박스/아이콘이 서로 겹치지 않는지, 화살표가 텍스트를 가리지 않는지
  - 정렬·여백 확인: 같은 행/열 요소의 수평·수직 정렬, 요소 간 간격 균등 (최소 20px)
  - 텍스트 가독성: 캔버스 내 텍스트가 읽을 수 있는 크기 (최소 12px)
  - ↑↓ Step 내비게이션 검증: ArrowDown으로 step 0→MAX_STEP 순차 진행, ArrowUp으로 역순 후퇴
  - 각 step별 스크린샷 촬영하여 요소가 논리적 순서로 나타나는지 확인
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
- **↑↓ tab/step navigation**: Verify tab cycling and animation step control work correctly at both resolutions. **Canvas step 슬라이드의 경우 반드시 ArrowDown/ArrowUp으로 전체 step을 순회하며 각 step 스크린샷을 촬영하여 레이아웃 겹침·정렬·가독성을 확인할 것**
- **Speaker notes panel (N key)**: Verify notes panel layout doesn't break presentation scaling
- **Fullscreen (F key)**: Verify auto-hide controls and proper scaling in fullscreen mode

**Scaling approach**: Presentations use a fixed 1920×1080 design canvas with `transform: scale()` to fit any viewport. All internal dimensions are in `px`. The scale factor is calculated as `Math.min(viewportWidth/1920, viewportHeight/1080)` and applied via CSS transform. This ensures pixel-perfect consistency across FHD, 4K, and arbitrary resolutions.

### Phase 9: Deploy

```bash
git add common/ {slug}/ index.html
git commit -m "feat: add {presentation-name} interactive training"
git push origin main
```

Enable GitHub Pages: Settings → Pages → main branch / root.

## Slide Type Decision Guide

| Content Type | Slide Pattern | Interactive Element |
|---|---|---|
| Architecture overview (static) | Diagram Image | draw.io → PNG/SVG, `@img:` directive |
| Step-by-step flow/process | Canvas Animation | Step animation with ↑↓ navigation |
| A vs B comparison | Compare Toggle | `.compare-toggle` buttons |
| Config variants | Tab Content | `.tab-bar` with YAML code blocks |
| Step-by-step process | Timeline | `.timeline` with animated steps |
| Monitoring/dashboard | Canvas Animation | Node grid + event log + buttons |
| Parameter exploration | Slider | `input[type=range]` + live output |
| Best practices | Checklist | `.checklist` with click-to-toggle |
| Best practices + config | Checklist with YAML | `.checklist` + `.check-yaml` expand on click (see slide-patterns.md §7b) |
| YAML/code example | Code Block | `.code-block` with syntax spans |
| Customer problem | Pain Quote | `.pain-quote` + challenge list |
| Block summary (퀴즈 포함 시) | Quiz | `data-quiz` + 3-4 questions |
| Block summary (퀴즈 미포함 시) | Content | Key Takeaways 요약 리스트 |
| Block closing | Thank You | Gradient heading + TOC link + next block link |

### Canvas vs Diagram 선택 기준

| 기준 | Canvas (`@type: canvas`) | Diagram (`@img:`) |
|------|--------------------------|---------------------|
| 목적 | 단계별 흐름을 애니메이션으로 설명 | 전체 아키텍처를 한눈에 보여줌 |
| 예시 | Auto-scaling 과정, 데이터 파이프라인 단계, 장애 전파 흐름 | AWS 서비스 맵, 3-tier 아키텍처, VPC 네트워크 구성 |
| 장점 | ↑↓ step 내비게이션으로 순차적 설명 가능 | 복잡한 레이아웃/화살표를 정확하게 표현 |
| 제작 | Canvas DSL로 직접 코딩 | draw.io/architecture-diagram-agent로 제작 → PNG/SVG |
| 삽입 | `@type: canvas` + `:::canvas` 블록 | `@type: content` + `@img: diagrams/arch.png center 90%` |

**원칙**: 애니메이션이 설명력을 높이지 않는다면 diagram 이미지를 사용한다.

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| ← → | Previous / Next slide |
| Space | Next slide |
| ↑ ↓ | Cycle tabs/compare options on current slide; step animation if registered |
| F | Toggle fullscreen |
| N | Toggle speaker notes panel (bottom 20% overlay) |
| P | Open presenter view (new window with notes, timer, slide sync) |
| O | Toggle overview mode (slide grid thumbnails) |
| S | Toggle slide sidebar (non-fullscreen only) |
| B | Blackout screen |
| Esc | Exit fullscreen / dismiss notes panel / exit overview |
| Home/End | First/Last slide |
| 1-9 | Jump to slide number |

### Tab/Step Navigation (↑↓)

The ↑↓ arrow keys control interactive elements on the current slide:

- **↓ key**: Next tab, next compare option, or next animation step
- **↑ key**: Previous tab, previous compare option, or previous animation step

Detection priority:
1. **Registered slide action** (`deck.registerSlideAction(index, { up, down })`) — takes priority. Used for animation step control where JS state can't be auto-detected from DOM.
2. **Auto-detect `.tab-bar`** on current slide — cycles through `.tab-btn` elements
3. **Auto-detect `.compare-toggle`** on current slide — cycles through `.compare-btn` elements
4. **No interactive element** — does nothing

Register animation step control:
```javascript
deck.registerSlideAction(SLIDE_INDEX, {
  down: () => timeline.nextStep(),
  up: () => timeline.prevStep(),
});
```

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
- `slide-renderer.js` — SlideRenderer class: JSON → HTML 동적 렌더링 (13개 슬라이드 타입 지원)
- `presenter-view.js` — PresenterView class (draggable splitters, large notes area, Pretendard font, localStorage persistence, BroadcastChannel sync)
- `animation-utils.js` — Canvas primitives, AnimationLoop, TimelineAnimation, Colors, Ease
- `quiz-component.js` — QuizManager with auto-grading and feedback
- `export-utils.js` — ExportUtils with PDF export (browser print) and ZIP download (JSZip CDN, auto-discovers and bundles all referenced images)

### scripts/
- `extract_pptx_theme.py` — Extract PPTX theme → CSS overrides + images (see [references/pptx-theme-guide.md](references/pptx-theme-guide.md))
- `remarp_to_slides.py` — Convert Remarp markdown → HTML slide files with fragments, transitions, canvas DSL, rich notes (see [references/remarp-format-guide.md](references/remarp-format-guide.md))
- `marp_to_slides.py` — Convert Marp markdown → HTML slide files (legacy, see [references/marp-format-guide.md](references/marp-format-guide.md))
- `extract_aws_icons.py` — Extract AWS Architecture Icons from bundled zip → SVG files organized by category (see [references/aws-icons-guide.md](references/aws-icons-guide.md))

### references/
- [framework-guide.md](references/framework-guide.md) — Complete API reference for CSS classes, JS functions, HTML template
- [slide-patterns.md](references/slide-patterns.md) — Copy-paste HTML patterns for each slide type, Canvas animation patterns
- [remarp-format-guide.md](references/remarp-format-guide.md) — Remarp markdown format specification (recommended) — fragments, canvas DSL, rich notes, transitions
- [marp-format-guide.md](references/marp-format-guide.md) — Marp markdown format specification (legacy)
- [pptx-theme-guide.md](references/pptx-theme-guide.md) — PPTX theme extraction usage, color mapping, troubleshooting
- [aws-icons-guide.md](references/aws-icons-guide.md) — AWS Architecture Icons usage, naming conventions, commonly used icons by topic
