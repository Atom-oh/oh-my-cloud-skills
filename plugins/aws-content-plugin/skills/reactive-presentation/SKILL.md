---
name: reactive-presentation
description: "Create interactive HTML presentation slideshows with Canvas animations, quizzes, light/dark themes, keyboard navigation, and screenshot-based PPTX export (editable/native PPTX is the aws-light-fcd skill). Deploy to GitHub Pages. Use when user asks to: create slides, build a presentation, make a slideshow, training slides, interactive presentation, Canvas animation slides, export web slides to PowerPoint images, or mentions 'reactive presentation'. Supports PPTX template theming and Remarp markdown content authoring. Supports multi-block training sessions (30min-3hr), technical deep-dives, and workshop content."
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
---

# Reactive Presentation

Build interactive HTML slideshows deployed via GitHub Pages. No build tools — pure HTML/CSS/JS with a shared framework (nav, animations, quizzes). Authoring format is **Remarp markdown** (Marp = legacy maintenance only).

> `{skill-dir}` = `{plugin-dir}/skills/reactive-presentation`. New to Remarp? See [REMARP.md](REMARP.md).
> **상세 작성 규칙·표·복사용 템플릿은 [references/authoring-rules.md](references/authoring-rules.md)** (validation 규칙, Forbidden AI-tells, Interactive 패턴/탭 템플릿, Slide Type 결정, HTML Architecture). 실제 슬라이드를 작성·검증할 때 이 문서를 읽으세요.

## Workflow (9 phases)

### Phase 1 — Theme Setup (optional, PPTX 제공 시)
```bash
python3 {skill-dir}/scripts/extract_pptx_theme.py <pptx_path> -o {repo}/common/pptx-theme/
```
생성물: `theme-manifest.json`(colors/fonts/logos/footer/layout) · `theme-override.css` · `images/`. 매니페스트 매핑 → `_presentation.md`: `slide_size.aspect_ratio`→`ratio`, `footer_text`→`theme.footer`, `logos[0]`→`theme.logo`. `theme-override.css`를 `common/`에 복사. 상세: [references/pptx-theme-guide.md](references/pptx-theme-guide.md). (AWS 아이콘은 build가 참조분만 자동 복사 — 수동 추출 불필요.)

### Phase 2 — Content Authoring
**플래닝 질문** (planning 시 확인, 빠진 것만 질문):
- Topic & audience / Duration(블록당 20-35분 + 5분 휴식) / Target repo(기본 `~/reactive_presentation/`) / Language(KO·EN, 기술용어는 영어) / Aspect ratio(기본 16:9)
- **Design refs** (REQUIRED, skippable): "참고 디자인(PPTX/PDF/이미지/기존 프레젠테이션 경로)이 있나요? (또는 skip)" → 제공 시 브랜딩+레이아웃 추출(`.pptx`=Phase 1, `.pdf`/이미지=시각 레이아웃 참고). 기존 프레젠테이션은 `~/oh-my-skill-tester/`도 자동 탐색해 목록 제시. skip 시 CSS-only cover + 기본 theme + **`_presentation.md`에 footer/logo 수동 설정 필수**.

**디자인 플랜 (필수 — 작성 전 2-pass)**: [references/design-direction.md](references/design-direction.md)를
읽고 Subject/Palette/Type/Signature 플랜을 세운 뒤 anti-default 자기비평을 통과하고 작성 시작.
테마 선택: 기본(AWS 콘솔 라이트) · `theme: { mode: dark }`(squid-ink night) ·
`theme: { preset: paper }`(구 웜 룩, 의도적 선택 시만) · PPTX 추출(항상 우선).
- **Speaker** (skippable): 이름·직함·소속 → frontmatter `speaker`{name,title,company} (MEMORY.md에 저장·재사용)
- **Level** (REQUIRED): 100/200/300/400 → frontmatter `level`
- **Quiz** (skippable): 블록 끝 복습 퀴즈? → frontmatter `quiz`(true/false). 미포함 시 Key Takeaways로 대체. 전체 시간 → `duration`(blocks 합과 일치)

**프로젝트 구조** (멀티파일): `_presentation.md`(글로벌 theme/footer/logo/blocks) + `NN-block.md`(remarp:true) + `animations/`(Canvas JS).

> **`_presentation.md` 필수 (ratio/footer/logo)**: `ratio: "16:9"` 누락 시 프리뷰 비율 깨짐. PPTX 없으면 `theme:`에 `footer`·`logo` 수동 설정:
> ```yaml
> ratio: "16:9"
> theme: { footer: "© 2026 Company. All rights reserved.", logo: "./common/logo.png" }
> ```

**Remarp 핵심**: `remarp: true` frontmatter · `@type`/`@layout`/`@transition`/`@theme` 디렉티브 · `{.click}`·`:::click` 프래그먼트 · `:::notes` 스피커 노트 · `:::canvas` DSL · `::: left`/`::: right` 컬럼. 전체 문법: [references/remarp-format-guide.md](references/remarp-format-guide.md).

> **스피커 노트 (필수)**: 모든 슬라이드에 `:::notes` — 150자+ (권장 300~500), `{timing}`/`{cue}` 마커 + `[요약]`(3~5 불릿) + 구어체 스크립트. 누락/무구조 시 `MISSING_NOTES`/`NOTE_STRUCTURE` 경고. 스키마: remarp-format-guide.md "Structured Note Schema".

> ⚠️ **Interactive-First**: 3+ 하위항목→탭 · 4+ 나열→grid 카드(불릿 금지) · 5+ 박스→`:::html`+`:::css`(canvas 금지) · `:::html`은 3+ 동위요소면 `fragment fade-up`로 reactive. 원칙·탭 템플릿·색상 토큰: **authoring-rules.md §4**.

**대안 포맷** (명시 요청 시만): slides.json(런타임 렌더, slide-patterns.md "JSON Authoring Mode") · Marp(레거시, marp-format-guide.md).

### Phase 2.5 — Convert PPTX/PDF (optional)
```bash
python3 {skill-dir}/scripts/convert_to_remarp.py <input.pptx|pdf> -o {repo}/{slug}/ --lang ko
#   --build(즉시 빌드) · --block-size N(분할) · --force(덮어쓰기+.bak)
```
변환 후 `.md`에서 `@speaker`/`{.click}`/`:::canvas`/`@type` 자유 편집. PDF는 이미지 배경+추출 텍스트.

### Phase 2.8 — Validate (Rejection Loop, 필수 — build 전)
```bash
python3 {skill-dir}/scripts/remarp_to_slides.py validate {repo}/{slug}/
```
> ⚠️ **CRITICAL 0건이어야 build**. 규칙 표·Verdict·자동교정 지침: **authoring-rules.md §1**. CRITICAL 있으면 수정 후 재검증(최대 3회).

### Phase 3 — Build
```bash
python3 {skill-dir}/scripts/remarp_to_slides.py build {repo}/{slug}/          # 전체
python3 {skill-dir}/scripts/remarp_to_slides.py build {repo}/{slug}/ --block 01-fundamentals
python3 {skill-dir}/scripts/remarp_to_slides.py sync  {repo}/{slug}/          # 변경분만(증분)
python3 {skill-dir}/scripts/remarp_to_slides.py issues {repo}/{slug}/ [--json]  # 이슈 어노테이션
```

### Phase 4 — Review & Iterate
콘텐츠 생성 후 사용자에게 선택지를 제시: ① Remarp 직접 수정 후 "반영해주세요"(→ Claude가 읽고 `sync`) · ② 프롬프트로 수정 요청(→ Remarp+HTML 동시 수정) · ③ 진행.
규칙: Remarp↔HTML 동기 유지(Remarp가 소스) · 기존 Canvas/quiz/인터랙션 보존 · 변경 슬라이드만 수정 · 무엇이 바뀌었는지 요약.

### Phase 5 — Enhancement
`@type: canvas` 슬라이드에 Canvas 애니메이션 구현(animation-utils.js) · 복잡 인터랙션 보강 · presenter view(P) 노트 확인.

### Phase 6 — Set Up Structure
스킬 `assets/*`를 repo `common/`에 복사: `cp {skill-dir}/assets/* {repo}/common/`. 구조: `{repo}/index.html`(허브) + `common/`(theme.css, slide-framework.js, slide-renderer.js, presenter-view.js, animation-utils.js, quiz-component.js, export-utils.js, [aws-icons/], [pptx-theme/]) + `{slug}/`(TOC index.html + `NN-block.html`). TOC에 export 버튼:
```html
<div class="export-toolbar">
  <button class="export-btn" onclick="ExportUtils.exportPDF({ title: 'Title' })">Export PDF</button>
  <button class="export-btn" onclick="ExportUtils.exportPPTX({ title: 'Title' })">Export PPTX</button>
  <button class="export-btn" onclick="ExportUtils.downloadZIP()">Download ZIP</button>
</div>
<script src="../common/export-utils.js"></script>
```
(빌드가 생성하는 `toc.html`에는 블록별/전체 PDF·ZIP·PPTX 버튼이 이미 포함됨.)

### Phase 7 — Quality Review (필수 — 생략 불가)
1. content-review-agent 호출 → `review content at [경로]` · 2. FAIL/REVIEW 시 수정 후 재리뷰(최대 3회) · 3. **PASS(≥85점) 후에만 완료 선언**.
> ⚠️ 이 단계를 건너뛰고 배포 금지.

### Phase 8 — Verify
블록별 점검: 슬라이드 수 일치 · `SlideFramework` 옵션(footer/logoSrc/presenterNotes) · 모든 Canvas ID에 `setupCanvas()` · quiz `data-quiz`/`data-correct` · `../common/` 상대경로 · **theme-override.css 링크됨(PPTX 추출 시)** · 언어 · 첫 슬라이드=Session Cover(§0a/§0b, `.title-slide` 아님) · 마지막=Thank You(목차 링크).

> **Screenshot 검증 (필수)**: Playwright MCP로 **FHD 1920×1080**(주 해상도) + **4K 3840×2160**에서 모든 인터랙티브/Canvas 슬라이드 캡처. 확인: 텍스트 가독성·캔버스 비율·오버플로우 없음·컨트롤 표시. 인터랙션(탭/슬라이더/버튼) 후 캡처. **Canvas step 슬라이드는 ArrowDown/Up으로 전체 step 순회하며 각 step 캡처**(겹침·정렬·가독성). N(노트)·F(풀스크린) 스케일링 확인. 캡처 검토 시 **디자인 자기비평: [references/design-direction.md](references/design-direction.md) §6 절제 체크리스트** 적용.
> 스케일링: 고정 1920×1080 디자인 캔버스 + `transform: scale(min(vw/1920, vh/1080))` → FHD/4K 픽셀 일관.

### Phase 8.5 — PPTX Export (요청 시)
"PPT/PPTX로 내보내기" 요청 시 두 경로:
```bash
# 권장 (headless, 픽셀 정확 — Playwright 네이티브 렌더링 + 스피커 노트 포함)
pip install playwright python-pptx && playwright install chromium   # 1회
python3 {skill-dir}/scripts/export_pptx.py {repo}/{slug}/ -o {slug}.pptx
```
- 브라우저 경로(도구 설치 불필요): `toc.html`의 **Export PPTX** 버튼(`ExportUtils.exportPPTX`, html2canvas+PptxGenJS CDN — 품질은 headless 경로가 우수).
- 각 슬라이드는 fragment 전체 공개 + Canvas 최종 step 상태로 캡처되고, `:::notes`가 PPTX 스피커 노트로 들어감.
- **네이티브(편집 가능한) PPTX가 필요하면** 이 스킬이 아니라 `aws-light-fcd` 스킬로 라우팅 (presentation-agent 디스패처 규칙).

### Phase 9 — Deploy
```bash
git add common/ {slug}/ index.html && git commit -m "feat: add {name} interactive training" && git push origin main
```
GitHub Pages: Settings → Pages → main / root.

## 작성 규칙·패턴 (상세 — 작성/검증 시 읽기)
- **[references/authoring-rules.md](references/authoring-rules.md)** — Validation 규칙(§1) · Forbidden AI-tells(§2) · Slide Title Voice(§3) · Interactive 패턴+탭 템플릿+색상 토큰(§4) · Slide Type 결정 + Canvas vs html/diagram(§5) · HTML Architecture flow 패턴(§6)
- `:::canvas`를 쓰기 전 반드시 **[references/canvas-authoring-guide.md](references/canvas-authoring-guide.md)** (DSL 문법, 필수 좌표 공식, fragment 순서). `validate`가 CANVAS_OVERLAP backstop.
- 뷰어 단축키(←→ Space ↑↓ F N P O S B Esc 1-9): [references/keyboard-shortcuts.md](references/keyboard-shortcuts.md).

## Quality Assurance (사실 검증 — YAML/config 인용 시)
- **Canvas 비례 스케일**: 모든 Canvas는 `ResizeObserver` + `BASE_W/BASE_H` + `ctx.scale(scale*dpr, scale*dpr)` 패턴 필수 (FHD/4K 대응). `setupCanvas()` 단독 금지 (px max-width 고정됨). slide-patterns.md §5.
- **Karpenter v1**: `expireAfter`는 `spec.template.spec` (NOT `spec.disruption`). 메트릭은 `_total` 접미사. (karpenter.sh 확인)
- **Grafana Loki**: derivedFields는 `regex` (NOT `matcherRegex`).
- **GitBook 앵커**: 한글 제목은 한글 슬러그 (`## 1. 관측성` → `#1-관측성`, 숫자 뒤 점 제거, 공백→하이픈).
- **K8s**: `topologySpreadConstraints`는 `labelSelector` 필요. VPA `Auto`는 deprecated (→ `Recreate`).

## Resources
**assets/** (→ `common/`): design-tokens.css · theme.css · theme-override-template.css · slide-framework.js · slide-renderer.js · presenter-view.js · animation-utils.js · quiz-component.js · export-utils.js
**scripts/**: extract_pptx_theme.py · remarp_to_slides.py · export_pptx.py(headless PPTX) · marp_to_slides.py(레거시) · extract_aws_icons.py
**references/**: design-direction.md(디자인 원칙/테마 선택) · authoring-rules.md(작성 규칙/패턴) · framework-guide.md(CSS/JS API) · slide-patterns.md(타입별 패턴) · remarp-format-guide.md(Remarp 문법) · interactive-patterns-guide.md(고급 인터랙션) · canvas-authoring-guide.md(Canvas DSL) · colors-reference.md(토큰) · pptx-theme-guide.md · aws-icons-guide.md · keyboard-shortcuts.md · marp-format-guide.md(레거시)

> ⚡ **토큰 절약**: `slide-patterns.md`·`interactive-patterns-guide.md`·`remarp-format-guide.md`는 큰 파일(각 ~25K토큰)입니다. 전체를 Read하지 말고 **상단 `<!-- SECTION INDEX -->`의 정확 라인번호로 필요한 `##` 섹션을 offset-read** 하세요 (예: `Read(file, offset=L, limit=다음섹션L−L)`). 해당 섹션이 다른 `##`/`§`를 참조하면 그 섹션도 함께 읽으세요(교차참조 누락 방지).
