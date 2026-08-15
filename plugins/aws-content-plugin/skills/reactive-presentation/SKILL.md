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
> **Detailed authoring rules, tables, and copy-ready templates live in [references/authoring-rules.md](references/authoring-rules.md)** (validation rules, Forbidden AI-tells, Interactive patterns/tab templates, Slide Type decisions, HTML Architecture). Read that document when actually authoring or validating slides.

## Workflow (9 phases)

### Phase 1 — Theme Setup (optional, when a PPTX is provided)
```bash
python3 {skill-dir}/scripts/extract_pptx_theme.py <pptx_path> -o {repo}/common/pptx-theme/
```
Output: `theme-manifest.json` (colors/fonts/logos/footer/layout) · `theme-override.css` · `images/`. Manifest mapping → `_presentation.md`: `slide_size.aspect_ratio`→`ratio`, `footer_text`→`theme.footer`, `logos[0]`→`theme.logo`. Copy `theme-override.css` into `common/`. Details: [references/pptx-theme-guide.md](references/pptx-theme-guide.md). (AWS icons are auto-copied by the build, referenced icons only — manual extraction is unnecessary.)

### Phase 2 — Content Authoring
**Planning** (don't re-ask what the brief, existing documents, or MEMORY.md already answered — ask only about what's missing):
- Topic & audience / Duration (20-35 min per block + 5 min break) / Target repo (default `~/reactive_presentation/`) / Language (KO/EN, technical terms in English) / Aspect ratio (default 16:9)
- **Design refs**: check whether a reference design exists (PPTX/PDF/image/existing presentation path) → if provided, extract branding+layout (`.pptx`=Phase 1, `.pdf`/image=visual layout reference). Also auto-search `~/oh-my-skill-tester/` for existing presentations and present a list. If none, use a CSS-only cover + default theme + **manually set footer/logo in `_presentation.md` (required)**.
- Collect required frontmatter fields: `speaker`{name,title,company} (stored/reused via MEMORY.md, can be omitted), `level` (100-400), `quiz` (true/false — no reasonable default, so confirm if not in the brief; if not included, substitute Key Takeaways), `duration` (must match the sum of block durations)

**Design plan (2-pass before writing)**: read [references/design-direction.md](references/design-direction.md), set a Subject/Palette/Type/Signature plan, then go through the anti-default self-critique (§3 Pass 2) before starting to write.
Theme choice: default (AWS console light) · `theme: { mode: dark }` (squid-ink night) ·
`theme: { preset: paper }` (older warm look, only when deliberately chosen) · PPTX extraction (always preferred).

**Project structure** (multi-file): `_presentation.md` (global theme/footer/logo/blocks) + `NN-block.md` (remarp:true) + `animations/` (Canvas JS).

> **`_presentation.md` is required (ratio/footer/logo)**: omitting `ratio: "16:9"` breaks the preview aspect ratio. Without a PPTX, manually set `footer`/`logo` in `theme:`:
> ```yaml
> ratio: "16:9"
> theme: { footer: "© 2026 Company. All rights reserved.", logo: "./common/logo.png" }
> ```

**Remarp essentials**: `remarp: true` frontmatter · `@type`/`@layout`/`@transition`/`@theme` directives · `{.click}`/`:::click` fragments · `:::notes` speaker notes · `:::canvas` DSL · `::: left`/`::: right` columns. Full syntax: [references/remarp-format-guide.md](references/remarp-format-guide.md).

> **Speaker notes**: every slide needs `:::notes` — enough content and structure for the presenter to speak to that slide from the notes alone (`{timing}`/`{cue}` markers + `[요약]` ("Summary") bullets + a conversational script). Missing or unstructured notes are flagged by validate as `MISSING_NOTES`/`NOTE_STRUCTURE`. Schema: remarp-format-guide.md "Structured Note Schema".

> ⚠️ **Interactive-First**: the more information-dense a slide is, the more it should use interactive patterns (tabs, grid cards, fragments) — a wall of bullets doesn't get read. The canon for thresholds, tab templates, and color tokens: **authoring-rules.md §4·§5** (validate backstops this with `INTERACTIVE_FIRST`/`CANVAS_COMPLEXITY`).

**Alternative formats** (only on explicit request): slides.json (runtime rendering, slide-patterns.md "JSON Authoring Mode") · Marp (legacy, marp-format-guide.md).

### Phase 2.5 — Convert PPTX/PDF (optional)
```bash
python3 {skill-dir}/scripts/convert_to_remarp.py <input.pptx|pdf> -o {repo}/{slug}/ --lang ko
#   --build(build immediately) · --block-size N(split) · --force(overwrite+.bak)
```
After conversion, freely edit `@speaker`/`{.click}`/`:::canvas`/`@type` in the `.md`. PDFs use an image background + extracted text.

### Phase 2.8 — Validate (Rejection Loop, required before build)
```bash
python3 {skill-dir}/scripts/remarp_to_slides.py validate {repo}/{slug}/
```
> ⚠️ **Must have 0 CRITICAL findings to build**. Rule table, verdicts, and auto-fix guidance: **authoring-rules.md §1**. If CRITICAL findings remain, fix and re-validate (up to 3 times).

### Phase 3 — Build
```bash
python3 {skill-dir}/scripts/remarp_to_slides.py build {repo}/{slug}/          # full build
python3 {skill-dir}/scripts/remarp_to_slides.py build {repo}/{slug}/ --block 01-fundamentals
python3 {skill-dir}/scripts/remarp_to_slides.py sync  {repo}/{slug}/          # changed blocks only (incremental)
python3 {skill-dir}/scripts/remarp_to_slides.py issues {repo}/{slug}/ [--json]  # issue annotations
```

### Phase 4 — Review & Iterate
After generating content, present the user with options: ① edit Remarp directly and say "please apply this" (→ Claude reads it and runs `sync`) · ② request changes via prompt (→ Remarp+HTML edited simultaneously) · ③ proceed.
Rules: keep Remarp↔HTML in sync (Remarp is the source) · preserve existing Canvas/quiz/interactions · modify only changed slides · summarize what changed.

### Phase 5 — Enhancement
Implement Canvas animations (animation-utils.js) on `@type: canvas` slides · enhance complex interactions · verify presenter view (P) notes.

### Phase 6 — Set Up Structure
Copy the skill's `assets/*` into the repo's `common/`: `cp {skill-dir}/assets/* {repo}/common/`. Structure: `{repo}/index.html` (hub) + `common/` (theme.css, slide-framework.js, slide-renderer.js, presenter-view.js, animation-utils.js, quiz-component.js, export-utils.js, [aws-icons/], [pptx-theme/]) + `{slug}/` (TOC index.html + `NN-block.html`). Export buttons in the TOC:
```html
<div class="export-toolbar">
  <button class="export-btn" onclick="ExportUtils.exportPDF({ title: 'Title' })">Export PDF</button>
  <button class="export-btn" onclick="ExportUtils.exportPPTX({ title: 'Title' })">Export PPTX</button>
  <button class="export-btn" onclick="ExportUtils.downloadZIP()">Download ZIP</button>
</div>
<script src="../common/export-utils.js"></script>
```
(The `toc.html` the build generates already includes per-block/overall PDF/ZIP/PPTX buttons.)

### Phase 7 — Quality Review
Get a content-review-agent PASS via `review content at [path]` before declaring deployment/completion — the Quality Gate rule from the plugin's CLAUDE.md.

### Phase 8 — Verify
Per-block checks: slide count matches · `SlideFramework` options (footer/logoSrc/presenterNotes) · every Canvas ID has `setupCanvas()` · quiz `data-quiz`/`data-correct` · `../common/` relative paths · **theme-override.css linked (when extracted from PPTX)** · language · first slide = Session Cover (§0a/§0b, not `.title-slide`) · last slide = Thank You (with a TOC link).

> **Screenshot verification (required)**: use Playwright MCP to capture all interactive/Canvas slides at **FHD 1920×1080** (primary resolution) + **4K 3840×2160**. Check: text legibility, canvas proportions, no overflow, controls visible. Capture after interactions (tabs/sliders/buttons). **For Canvas step slides, walk through all steps with ArrowDown/Up, capturing each step** (check for overlap, alignment, legibility). Verify scaling with N (notes) and F (fullscreen). When reviewing captures, apply the **design self-critique: [references/design-direction.md](references/design-direction.md) §6 restraint checklist**.
> Scaling: fixed 1920×1080 design canvas + `transform: scale(min(vw/1920, vh/1080))` → consistent pixels across FHD/4K.

### Phase 8.5 — PPTX Export (on request)
When asked to "export to PPT/PPTX", there are two paths:
```bash
# Recommended (headless, pixel-accurate — Playwright native rendering + includes speaker notes)
pip install 'playwright>=1.40' 'python-pptx>=1.0' && playwright install chromium   # one-time
python3 {skill-dir}/scripts/export_pptx.py {repo}/{slug}/ -o {slug}.pptx
```
- Browser path (no tool installation needed): the **Export PPTX** button in `toc.html` (`ExportUtils.exportPPTX`, html2canvas+PptxGenJS CDN — the headless path gives better quality).
- Each slide is captured with all fragments revealed and the Canvas in its final step state, and `:::notes` becomes the PPTX speaker notes.
- Trust boundary: export only **decks you built yourself** (during capture, the deck's HTML/JS executes in a headless browser).
- **If a native (editable) PPTX is needed**, route to the `aws-light-fcd` skill instead of this one (per the presentation-agent dispatcher rule).

### Phase 9 — Deploy
```bash
git add common/ {slug}/ index.html && git commit -m "feat: add {name} interactive training" && git push origin main
```
GitHub Pages: Settings → Pages → main / root.

## Authoring Rules & Patterns (detailed — read while authoring/validating)
- **[references/authoring-rules.md](references/authoring-rules.md)** — Validation rules (§1) · Forbidden AI-tells (§2) · Slide Title Voice (§3) · Interactive patterns + tab templates + color tokens (§4) · Slide Type decisions + Canvas vs html/diagram (§5) · HTML Architecture flow patterns (§6)
- Before using `:::canvas`, always read **[references/canvas-authoring-guide.md](references/canvas-authoring-guide.md)** (DSL syntax, required coordinate formulas, fragment ordering). `validate` backstops this with CANVAS_OVERLAP.
- Viewer keyboard shortcuts (←→ Space ↑↓ F N P O S B Esc 1-9): [references/keyboard-shortcuts.md](references/keyboard-shortcuts.md).

## Quality Assurance
- **Canvas proportional scaling (framework contract)**: every Canvas must use the `ResizeObserver` + `BASE_W/BASE_H` + `ctx.scale(scale*dpr, scale*dpr)` pattern (for FHD/4K support). `setupCanvas()` alone is forbidden (it fixes a px max-width). slide-patterns.md §5.
- **Fact verification**: slides that cite YAML/config/API values must include only values confirmed against official documentation — one wrong config key in a technical deck undermines credibility for the whole talk.

## Resources
**assets/** (→ `common/`): design-tokens.css · theme.css · theme-override-template.css · slide-framework.js · slide-renderer.js · presenter-view.js · animation-utils.js · quiz-component.js · export-utils.js
**scripts/**: extract_pptx_theme.py · remarp_to_slides.py · export_pptx.py (headless PPTX) · marp_to_slides.py (legacy) · extract_aws_icons.py
**references/**: design-direction.md (design principles/theme selection) · authoring-rules.md (authoring rules/patterns) · framework-guide.md (CSS/JS API) · slide-patterns.md (patterns by type) · remarp-format-guide.md (Remarp syntax) · interactive-patterns-guide.md (advanced interactions) · canvas-authoring-guide.md (Canvas DSL) · colors-reference.md (tokens) · pptx-theme-guide.md · aws-icons-guide.md · keyboard-shortcuts.md · marp-format-guide.md (legacy)

> ⚡ **Token savings**: `slide-patterns.md`, `interactive-patterns-guide.md`, and `remarp-format-guide.md` are large files (~25K tokens each). Don't Read the whole file — instead **offset-read only the `##` section you need, using the exact line numbers from the `<!-- SECTION INDEX -->` at the top** (e.g., `Read(file, offset=L, limit=nextSectionL−L)`). If that section references another `##`/`§`, read that section too (to avoid missing cross-references).
