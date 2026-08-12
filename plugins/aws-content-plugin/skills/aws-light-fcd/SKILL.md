---
name: aws-light-fcd
description: "Generate AWS Light-themed PowerPoint presentations (.pptx) with Pretendard typography, white canvas, and the signature purple→blue→green AWS gradient. Use this skill whenever the user asks to create, build, or generate AWS-style slides, decks, or presentations in the LIGHT theme — especially Korean/bilingual customer briefings, technical deep-dives, or anything mentioning Amazon Bedrock, AgentCore, EKS, SageMaker, or AWS architecture diagrams. Trigger on phrases like 'AWS 라이트 deck', 'AWS 슬라이드 만들어줘', 'Bedrock 발표자료', 'AgentCore 슬라이드', '아키텍처 다이어그램', 'AWS 고객 브리핑', or any request to turn notes/docs into AWS-branded light-theme slides. Provides ready-made layouts: cover, agenda, big-stat, AgentCore 3-card, and AWS architecture diagrams, plus bundled AgentCore + AWS service icon libraries."
---

# AWS Light FCD

Generate polished **AWS Light-theme** PowerPoint decks (.pptx) via PptxGenJS, using a
pre-built design system extracted from real AWS Korea customer decks. Pretendard
typography, white canvas, near-black ink, and a single signature gradient
(purple→blue→green). Every layout is already validated visually.

## What you get

- A shared kit (`scripts/deck_kit.js`) with design tokens + 4 layout builders
  (`cover`, `agenda`, `agentcoreCards`, `bigStat`) and footer/logo helpers.
- An architecture-diagram kit (`scripts/arch_kit.js`) — declarative auto-layout
  (`archFlow`, preferred) plus primitives (`groupBox`, `svc`, `stepMarker`, `arrow`,
  `stepLegend`, `chip`) for irregular topologies, + a react-icon renderer.
- Bundled icon libraries: 11 **AgentCore** icons + 10 **AWS service** icons
  (`assets/icons/`), the **AWS logo**, and background images (`assets/backgrounds/`).
- The full **AWS Architecture Icons** set (811 icons) via `kit.icon("<Name>")` —
  shared in place from the sibling `reactive-presentation` skill, not duplicated.
  Use it whenever the curated set lacks a service. See `references/icons.md`.

## Workflow

1. **Read the source** thoroughly if the user provides a doc (Read for md/txt,
   python-pptx for an existing .pptx, python-docx for .docx). Build a section map.
2. **Confirm** presenter (default: 오준석 · Senior Solutions Architect · AWS Korea),
   language, and rough slide count. Don't over-ask — proceed with defaults if unanswered.
3. **Read `references/layouts.md`** to pick the right layout per section, and
   **`references/icons.md`** for the exact icon names available.
4. **Write a build script** that `require("./scripts/deck_kit.js")` (and
   `arch_kit.js` if drawing diagrams), calls the layout builders, then
   `await pres.writeFile(...)`. Run it with `NODE_PATH=$(npm root -g) node build.js`.
5. **QA (거절 루프)**: `python3 scripts/check_pptx.py "$DECK"` — fix every finding and
   rerun until it passes. **The gate is `score ≥80` AND zero `[geometry]` findings**
   (a geometry defect — overflow/overlap/off-canvas — never passes, no matter the
   score, because content-review-agent treats it as Critical). Optional visual spot
   check if `soffice` is installed: `soffice --headless --convert-to pdf "$DECK" &&
   pdftoppm -jpeg -r 130 "${DECK%.pptx}.pdf" preview`.
6. **Embed fonts** — run `python scripts/embed_fonts.py "$DECK"` so the deck
   carries Pretendard and renders identically everywhere.
7. **Deliver** — leave the `.pptx` in the working/output directory and report its
   absolute path. Per the plugin's Quality Gate, a completed deck then goes through
   `content-review-agent` before it's declared done.

A complete working example lives in `scripts/demo_build.js` — read it first; it
exercises every layout builder, including the declarative `arch.archFlow`, and is the
fastest way to learn the API.

## Core rules (디자인 시스템 계약)

1. **Font: Pretendard only.** No fallbacks. (Preview renders via a substitute font,
   so trust the layout, not the exact glyph widths in the JPG. See font note below.)
2. **16:9 only** — the kit defines `W16x9` (13.333 × 7.5).
3. **One gradient, used as image/shape only.** The signature gradient
   (`AD5CFF→41B3FF→00E500`) appears on pill headers and similar — **never on text.**
   Big numbers and headings are **solid color** (`C.gradBlue` / `C.ink`). Text
   gradients don't preview in LibreOffice and look heavy; solid blue matches the
   reference decks better anyway.
4. **Footer on every content slide**: copyright (left) + small AWS logo + page number
   (right). Cover gets the big bottom-right logo and **no** small footer logo.
   `addFooter(pres, s, pageNum)` handles this; cover uses the built-in `cover()`.
5. **Agenda lists content chapters only** — "다음 단계 / 감사합니다"류 closing 항목은
   목차가 아니라 덱 끝의 closing 슬라이드(`kit.closing`)에 속한다. Section divider와
   closing의 full-gradient 배경 + 흰 푸터는 빌더가 처리하므로 오버라이드하지 않는다.
6. **Background is white by default.** Use the subtle top-right glow (`bg: "glow"`)
   only on slides that deserve emphasis (e.g. big-stat, section openers) — not everywhere.
7. **AgentCore content → AgentCore icons.** When a slide is about AgentCore or its
   components (Runtime, Gateway, Memory, Identity, etc.), use the bundled AgentCore
   icon set, matched by component (see `references/icons.md`).
8. **AWS architecture → `arch.archFlow` first, primitives only for irregular topologies.**
   Declare columns of services/groups/chips and let `archFlow` compute positions — this
   is `arch_kit.js`'s equivalent of the architecture-diagram skill's spec generator: an
   LLM hand-placing pixel coordinates is the #1 cause of amateur-looking output. Fall
   back to the raw primitives (`groupBox`, `svc`, `stepMarker`, `arrow`, `stepLegend`)
   only for topologies the column model doesn't fit (mesh/non-linear flows), and prefer
   using `archFlow`'s returned `cols[]` geometry to anchor them rather than picking
   fresh coordinates from scratch. Don't use emoji for endpoints; use `arch.chip`. For
   service icons, use the curated `kit.awsIcon` names when they exist, otherwise pull
   from the shared 811-icon library with `kit.icon("Amazon-…")` — `arch.svc` handles
   both and reports near-match suggestions on a typo instead of a bare crash. Don't
   re-extract icons that already exist in the shared library (`references/icons.md`).
9. **External tool logos (Ray, vLLM, Hugging Face, PyTorch, NVIDIA, …):** don't render
   them as plain text in diagrams — fetch the real logo. Priority: (1) Simple Icons via
   `react-icons/si` (local, 3300+ brands), (2) extract from a user-provided reference
   deck's `ppt/media/`, (3) `web_search`/`web_fetch` the official source. See
   `references/icons.md` → "External tool icons". Bundled so far: `ray`, `vllm`.

## Layout quick reference

| Builder | Use for | Key opts |
|---|---|---|
| `kit.cover(pres, o)` | Title slide | `product, subtitle, date, presenter` |
| `kit.agenda(pres, o)` | Table of contents (≤6 content chapters) | `items:[{num,title,desc,iconData}]` |
| `kit.bigStat(pres, o)` | 2–4 large headline numbers | `stats:[{num,lines,source}], bg` |
| `kit.agentcoreCards(pres, o)` | 3 feature cards w/ gradient pill | `headerTitle, cards:[{title,icon,desc}]` |
| `kit.titleWithVisual(pres, o)` | Big left title + right hero diagram (EKS-21 style) | `title, caption, draw(pres,s,region)` |
| `kit.pipeline(pres, o)` | Numbered left→right step flow | `steps:[{n,title,desc}]` |
| `kit.whyWhat(pres, o)` | WHY panel + WHAT cards w/ 차별점 box | `why:[...], what:[{n,t,d,diff,dc}]` |
| `kit.chartWithCallout(pres, o)` | Native editable chart + side callout | `series:[...], callout:{big,lines}` |
| `kit.chipGrid(pres, o)` | Vendor-colored chip rows (EKS-23 style) | `vendorBoxes:[...], rows:[...]` |
| `kit.sectionDivider(pres, o)` | Chapter-transition slide (full gradient bg) | `num, title, kicker` |
| `kit.closing(pres, o)` | "Thank you." closing (full gradient bg) | `text` (default "Thank you.") |
| `arch.archFlow(kit, pres, o)` | AWS architecture diagram — declarative, auto-layout (preferred) | `columns:[{label?, items:[{icon\|chip,label,step?}]}], arrows, legend` |
| `arch.*` primitives (`groupBox`, `svc`, `chip`, `stepMarker`, `arrow`, `stepLegend`) | Irregular topologies only | see `arch_kit.js` + demo |

Full option details and more layout patterns: **`references/layouts.md`**.

## Tokens (from `deck_kit.js`)

```
bg #FFFFFF · card #F4F4F8 · hairline #D2D2D5
ink #161D26 · body #3F4858 · muted #6B7280 · faint #999999
gradient stops: gradPurple #AD5CFF · gradBlue #41B3FF · gradGreen #00E500
solid accents: blue #3B82F6 · blueBright #007DFF · magenta #E91E63
tints: blueTint #EAF2FF · purpleTint #F2EEFF
```

## Font note (Pretendard) — now bundled + embeddable

The `.pptx` is written with `fontFace: "Pretendard"`. Pretendard (Regular + Bold, SIL
OFL) is **bundled** in `assets/fonts/`, so you can embed it directly into the deck and
it will render identically on any machine — even ones without Pretendard installed.

**Always run the embed step as the last build action:**

```bash
python scripts/embed_fonts.py your_deck.pptx
```

This injects the TTFs into the pptx (OOXML `embeddedFontLst`), leaving a `.bak` copy.
The file grows ~2MB. It's validated to reopen cleanly in PowerPoint/LibreOffice.

If you add italic or more weights, drop the TTFs in `assets/fonts/` (filenames
containing `regular`/`bold`/`italic`) and the script picks them up automatically.
For QA rendering inside this environment, also `cp assets/fonts/*.ttf ~/.fonts/ &&
fc-cache -f` so the preview uses real Pretendard instead of a substitute.

## Dependencies

- `npm install -g pptxgenjs react-icons react react-dom sharp` (sharp + react-icons
  only needed for `arch_kit.renderIcon` agenda tiles). Run builds with
  `NODE_PATH=$(npm root -g) node build.js`.
- `python-pptx` (required) for `scripts/check_pptx.py` — the QA gate in step 5.
- LibreOffice + Poppler (optional) for the visual PDF→JPG spot-check in step 5.
