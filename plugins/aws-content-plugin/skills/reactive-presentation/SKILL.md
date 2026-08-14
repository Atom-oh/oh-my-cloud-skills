---
name: reactive-presentation
description: "Create interactive HTML presentation slideshows with Canvas animations, quizzes, light/dark themes, keyboard navigation, and screenshot-based PPTX export (editable/native PPTX is the aws-light-fcd skill). Deploy to GitHub Pages. Use when user asks to: create interactive/web slides, build an HTML presentation, make a web slideshow, training slides, Canvas animation slides, export web slides to PowerPoint images, or mentions 'reactive presentation'. Supports PPTX template theming and Remarp markdown content authoring. Supports multi-block training sessions (30min-3hr), technical deep-dives, and workshop content."
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
> **Detailed authoring rules, tables, and copy-ready templates live in [references/authoring-rules.md](references/authoring-rules.md)** (validation rules, forbidden AI-tells, interactive patterns/tab templates, slide type decisions, HTML architecture). Read this document when actually authoring or validating slides.

## Workflow (9 phases)

### Phase 1 — Theme Setup (optional, when a PPTX is provided)
```bash
python3 {skill-dir}/scripts/extract_pptx_theme.py <pptx_path> -o {repo}/common/pptx-theme/
```
Output: `theme-manifest.json` (colors/fonts/logos/footer/layout) · `theme-override.css` · `images/`. Manifest mapping → `_presentation.md`: `slide_size.aspect_ratio`→`ratio`, `footer_text`→`theme.footer`, `logos[0]`→`theme.logo`. Copy `theme-override.css` into `common/`. Details: [references/pptx-theme-guide.md](references/pptx-theme-guide.md). (AWS icons: the build automatically copies only the icons actually referenced — no manual extraction needed.)

### Phase 2 — Content Authoring
**Planning questions** (confirm during planning, ask only about what's missing):
- Topic & audience / Duration (20-35 min per block + 5 min break) / Target repo (default `~/reactive_presentation/`) / Language (KO/EN, technical terms in English) / Aspect ratio (default 16:9)
- **Design refs** (REQUIRED, skippable): "Do you have a reference design (path to a PPTX/PDF/image/existing presentation)? (or skip)" → if provided, extract branding+layout (`.pptx`=Phase 1, `.pdf`/image=visual layout reference). Also auto-search `~/oh-my-skill-tester/` for existing presentations and present the list. If skipped: CSS-only cover + default theme + **footer/logo must be set manually in `_presentation.md`**.

**Design plan (required — 2-pass before writing)**: read [references/design-direction.md](references/design-direction.md),
set a Subject/Palette/Type/Signature plan, pass the anti-default self-critique, and only then start writing.
Theme choice: default (AWS console light) · `theme: { mode: dark }` (squid-ink night) ·
`theme: { preset: paper }` (old warm look, only when deliberately chosen) · PPTX extraction (always preferred when available).
- **Speaker** (skippable): name/title/company → frontmatter `speaker`{name,title,company} (stored in and reused from MEMORY.md)
- **Level** (REQUIRED): 100/200/300/400 → frontmatter `level`
- **Quiz** (skippable): review quiz at the end of the block? → frontmatter `quiz` (true/false). If not included, replace with Key Takeaways. Total time → `duration` (must match the sum of block durations)

**Project structure** (multi-file): `_presentation.md` (global theme/footer/logo/blocks) + `NN-block.md` (remarp:true) + `animations/` (Canvas JS).

> **`_presentation.md` is required (ratio/footer/logo)**: omitting `ratio: "16:9"` breaks the preview aspect ratio. Without a PPTX, set `footer` and `logo` manually under `theme:`:
> ```yaml
> ratio: "16:9"
> theme: { footer: "© 2026 Company. All rights reserved.", logo: "./common/logo.png" }
> ```

**Remarp essentials**: `remarp: true` frontmatter · `@type`/`@layout`/`@transition`/`@theme` directives · `{.click}`/`:::click` fragments · `:::notes` speaker notes · `:::canvas` DSL · `::: left`/`::: right` columns. Full syntax: [references/remarp-format-guide.md](references/remarp-format-guide.md).

> **Speaker notes (required)**: every slide needs `:::notes` — 150+ characters (300-500 recommended), `{timing}`/`{cue}` markers + `[Summary]` (3-5 bullets) + a conversational script. Missing or unstructured notes trigger `MISSING_NOTES`/`NOTE_STRUCTURE` warnings. Schema: remarp-format-guide.md "Structured Note Schema".

> ⚠️ **Interactive-First**: 3+ sub-items → tabs · 4+ listed items → grid cards (no bullets) · 5+ boxes → `:::html`+`:::css` (no canvas) · for `:::html` with 3+ sibling elements, make them reactive with `fragment fade-up`. Principles, tab templates, and color tokens: **authoring-rules.md §4**.

**Alternative formats** (only on explicit request): slides.json (runtime-rendered, slide-patterns.md "JSON Authoring Mode") · Marp (legacy, marp-format-guide.md).

### Phase 2.5 — Convert PPTX/PDF (optional)
```bash
python3 {skill-dir}/scripts/convert_to_remarp.py <input.pptx|pdf> -o {repo}/{slug}/ --lang ko
#   --build(즉시 빌드) · --block-size N(분할) · --force(덮어쓰기+.bak)
```
After conversion, freely edit `@speaker`/`{.click}`/`:::canvas`/`@type` in the `.md`. For PDFs: image background + extracted text.

### Phase 2.8 — Validate (Rejection Loop, required before build)
```bash
python3 {skill-dir}/scripts/remarp_to_slides.py validate {repo}/{slug}/
```
> ⚠️ **Build only when CRITICAL count is 0**. Rule tables, verdicts, and auto-correction guidance: **authoring-rules.md §1**. If any CRITICAL issues exist, fix and re-validate (up to 3 times).

### Phase 3 — Build
```bash
python3 {skill-dir}/scripts/remarp_to_slides.py build {repo}/{slug}/          # 전체
python3 {skill-dir}/scripts/remarp_to_slides.py build {repo}/{slug}/ --block 01-fundamentals
python3 {skill-dir}/scripts/remarp_to_slides.py sync  {repo}/{slug}/          # 변경분만(증분)
python3 {skill-dir}/scripts/remarp_to_slides.py issues {repo}/{slug}/ [--json]  # 이슈 어노테이션
```

### Phase 4 — Review & Iterate
After content generation, present the user with options: (1) edit the Remarp directly and say "please apply this" (→ Claude reads it and runs `sync`) · (2) request changes via prompt (→ Remarp and HTML are updated together) · (3) proceed.
Rules: keep Remarp and HTML in sync (Remarp is the source of truth) · preserve existing Canvas/quiz/interactions · only modify the changed slides · summarize what changed.

### Phase 5 — Enhancement
Implement Canvas animations on `@type: canvas` slides (animation-utils.js) · strengthen complex interactions · check speaker notes in presenter view (P).

### Phase 6 — Set Up Structure
Copy the skill's `assets/*` into the repo's `common/`: `cp {skill-dir}/assets/* {repo}/common/`. Structure: `{repo}/index.html` (hub) + `common/` (theme.css, slide-framework.js, slide-renderer.js, presenter-view.js, animation-utils.js, quiz-component.js, export-utils.js, [aws-icons/], [pptx-theme/]) + `{slug}/` (TOC index.html + `NN-block.html`). Export buttons on the TOC:
```html
<div class="export-toolbar">
  <button class="export-btn" onclick="ExportUtils.exportPDF({ title: 'Title' })">Export PDF</button>
  <button class="export-btn" onclick="ExportUtils.exportPPTX({ title: 'Title' })">Export PPTX</button>
  <button class="export-btn" onclick="ExportUtils.downloadZIP()">Download ZIP</button>
</div>
<script src="../common/export-utils.js"></script>
```
(The `toc.html` generated by the build already includes per-block and overall PDF/ZIP/PPTX buttons.)

### Phase 7 — Quality Review (required — cannot be skipped)
1. Call content-review-agent → `review content at [path]` · 2. On FAIL/REVIEW, fix and re-review (up to 3 times) · 3. **Only declare completion after PASS (score ≥85)**.
> ⚠️ Do not deploy by skipping this step.

### Phase 8 — Verify
Per-block checks: slide count matches · `SlideFramework` options (footer/logoSrc/presenterNotes) · `setupCanvas()` on every Canvas ID · quiz `data-quiz`/`data-correct` · relative `../common/` paths · **theme-override.css is linked (when a PPTX was extracted)** · language · first slide = Session Cover (§0a/§0b, not `.title-slide`) · last slide = Thank You (with a link back to the table of contents).

> **Screenshot verification (required)**: use Playwright MCP to capture every interactive/Canvas slide at **FHD 1920×1080** (primary resolution) + **4K 3840×2160**. Check: text readability, canvas proportions, no overflow, controls visible. Capture after interactions (tabs/sliders/buttons). **For Canvas step slides, step through every step with ArrowDown/Up and capture each one** (overlap, alignment, readability). Verify N (notes) and F (fullscreen) scaling. When reviewing captures, apply the **design self-critique: [references/design-direction.md](references/design-direction.md) §6 restraint checklist**.
> Scaling: a fixed 1920×1080 design canvas + `transform: scale(min(vw/1920, vh/1080))` → consistent pixels across FHD/4K.

### Phase 8.5 — PPTX Export (on request)
When "export to PPT/PPTX" is requested, two paths:
```bash
# 권장 (headless, 픽셀 정확 — Playwright 네이티브 렌더링 + 스피커 노트 포함)
pip install 'playwright>=1.40' 'python-pptx>=1.0' && playwright install chromium   # 1회
python3 {skill-dir}/scripts/export_pptx.py {repo}/{slug}/ -o {slug}.pptx
```
- Browser path (no tool install needed): the **Export PPTX** button in `toc.html` (`ExportUtils.exportPPTX`, html2canvas+PptxGenJS CDN — the headless path gives better quality).
- Each slide is captured with all fragments revealed and the Canvas at its final step state, and `:::notes` become the PPTX speaker notes.
- Trust boundary: export **only decks you built yourself** (during capture, the deck's HTML/JS executes in a headless browser).
- **If a native (editable) PPTX is needed**, route to the `aws-light-fcd` skill instead of this one (per the presentation-agent dispatcher rule).

### Phase 9 — Deploy
```bash
git add common/ {slug}/ index.html && git commit -m "feat: add {name} interactive training" && git push origin main
```
GitHub Pages: Settings → Pages → main / root.

## Authoring Rules & Patterns (detailed — read when authoring/validating)
- **[references/authoring-rules.md](references/authoring-rules.md)** — Validation rules (§1) · Forbidden AI-tells (§2) · Slide Title Voice (§3) · Interactive patterns + tab templates + color tokens (§4) · Slide type decisions + Canvas vs html/diagram (§5) · HTML architecture flow patterns (§6)
- Before writing `:::canvas`, always read **[references/canvas-authoring-guide.md](references/canvas-authoring-guide.md)** (DSL syntax, required coordinate formulas, fragment order). `validate` acts as a CANVAS_OVERLAP backstop.
- Viewer keyboard shortcuts (←→ Space ↑↓ F N P O S B Esc 1-9): [references/keyboard-shortcuts.md](references/keyboard-shortcuts.md).

## Quality Assurance (fact-check when citing YAML/config)
- **Canvas proportional scaling**: every Canvas must use the `ResizeObserver` + `BASE_W/BASE_H` + `ctx.scale(scale*dpr, scale*dpr)` pattern (for FHD/4K support). `setupCanvas()` alone is forbidden (it fixes a px max-width). slide-patterns.md §5.
- **Karpenter v1**: `expireAfter` lives under `spec.template.spec` (NOT `spec.disruption`). Metrics use the `_total` suffix. (verified against karpenter.sh)
- **Grafana Loki**: derivedFields use `regex` (NOT `matcherRegex`).
- **GitBook anchors**: Korean titles get Korean slugs (`## 1. 관측성` → `#1-관측성`, drop the period after the number, spaces become hyphens).
- **K8s**: `topologySpreadConstraints` requires `labelSelector`. VPA `Auto` is deprecated (→ `Recreate`).

## Resources
**assets/** (→ `common/`): design-tokens.css · theme.css · theme-override-template.css · slide-framework.js · slide-renderer.js · presenter-view.js · animation-utils.js · quiz-component.js · export-utils.js
**scripts/**: extract_pptx_theme.py · remarp_to_slides.py · export_pptx.py (headless PPTX) · marp_to_slides.py (legacy) · extract_aws_icons.py
**references/**: design-direction.md (design principles/theme selection) · authoring-rules.md (authoring rules/patterns) · framework-guide.md (CSS/JS API) · slide-patterns.md (per-type patterns) · remarp-format-guide.md (Remarp syntax) · interactive-patterns-guide.md (advanced interactions) · canvas-authoring-guide.md (Canvas DSL) · colors-reference.md (tokens) · pptx-theme-guide.md · aws-icons-guide.md · keyboard-shortcuts.md · marp-format-guide.md (legacy)

> ⚡ **Token savings**: `slide-patterns.md`, `interactive-patterns-guide.md`, and `remarp-format-guide.md` are large files (~25K tokens each). Instead of reading the whole file, **offset-read only the needed `##` section using the exact line numbers from the `<!-- SECTION INDEX -->` at the top** (e.g. `Read(file, offset=L, limit=nextSectionL−L)`). If that section references another `##`/`§`, read that section too (to avoid missing cross-references).
