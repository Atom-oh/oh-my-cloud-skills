# Plan — Finish the demos/docs overhaul on the v1.9.0 token design system

## Goal
The `docs/static/demos` decks showcase the plugins, so they must reflect the current
(v1.9.0) reactive-presentation token design system, and the Docusaurus guide docs must be
filled out with current, screenshot-backed content. Run multi-agent consensus review at
the gates.

## Context / done so far (committed on `main`)
- `310be5a` — regenerated AWS `theme-override.css` (`--pptx-*` brand inputs only) + rebuilt
  5 Remarp demos (bedrock-first-calldeck, canvas-animation, compare-tabs, quiz-slides,
  remarp-source) on the new token theme. Fixes readability/box/footer.
- `9f3cbef` / `82bfa7e` — repointed/refreshed demo pages + new-theme screenshots; fixed the
  basic-presentation broken embed.
- Constraint found: Canvas **DSL** slides adapt to role tokens automatically; aiops's custom
  `:::script` canvases do NOT (canvas ctx can't read CSS vars) — they need per-slide work.

## Out of scope
- The user's separate uncommitted work (`decision-reconcile` skill, CLAUDE.md edit) — do not touch.
- architecture-diagram / animated-diagram demos (not reactive-presentation theme-affected).

## Tasks

### A. aiops-deep-dive — migrate to the v1.9.0 token theme (the remaining demo)
- [ ] A1. Migrate static HTML/CSS colors in the 3 aiops `.md` blocks to role tokens
  (`--accent/--info/--success/--warning/--danger` + `*-subtle`, `#fff`→`var(--on-surface)`),
  but ONLY outside `:::script` blocks. Files: `docs/static/demos/aiops-deep-dive/0{1,2,3}-*.md`.
- [ ] A2. For each `:::script` canvas slide, replace literal/var colors used in `ctx.fillStyle`/
  `strokeStyle` with values read at runtime via `getComputedStyle(document.documentElement)
  .getPropertyValue('--token')` (canvas cannot resolve CSS vars). Verify no black-blob render.
- [ ] A3. `rm -rf aiops-deep-dive/common && build`; `validate` (0 CRITICAL); FHD screenshot
  each interactive/canvas slide (sidebar hidden via `s`, fragments revealed) — confirm
  readability + correct colors.
- [ ] A4. Refresh `full-presentation-demo.mdx` + `basic-presentation.mdx` screenshots to the
  new theme; verify embeds resolve.

### B. Guide docs — fill thoroughly with screenshots (v1.9.0 token system)
- [ ] B1. `docs/docs/remarp-guide/quick-start.mdx` — author a Remarp deck end to end on the
  token system; embed 1-2 fresh screenshots.
- [ ] B2. `docs/docs/remarp-guide/build-cli.mdx` — validate/build/sync CLI, the rejection
  loop, and the lint rules table; show real terminal output.
- [ ] B3. `docs/docs/remarp-guide/examples/*` — ensure each example reflects current syntax;
  refresh screenshots.
- [ ] B4. `docs/docs/aws-content-plugin/skills/reactive-presentation.mdx` — document the
  token design system (light default, role tokens, `.card-grid`/`.metric-card`/`.callout`/
  `.flow-h`, AWS `--pptx-*` brand-input override), with a screenshot.

### C. Verify
- [ ] C1. `cd docs && npm run build` succeeds (no broken links / missing images).
- [ ] C2. Every demo `DemoEmbed src` and every `/img/demos/...` reference resolves on disk.
- [ ] C3. All screenshots are FHD, light-theme, sidebar-hidden, fragments revealed.

## Plan-gate fixes incorporated (Codex + Gemini consensus: GO-WITH-FIXES)
- **A2 canvas tokens**: read each token ONCE at slide-enter via `getComputedStyle` of the
  nearest themed ancestor (the `.slide-deck`/`.slide`, falling back to `documentElement`),
  cache the values, and provide a literal fallback (`getVar('--accent') || '#2563EB'`). Do
  NOT call `getComputedStyle` inside the draw/animation loop. Re-read on a `MutationObserver`
  watching the deck root's class/`data-theme` so a theme toggle repaints. Re-read on resize.
- **Regression gate (mechanical, not eyeball)**: after each rebuild, grep the demo's HTML for
  raw hex/rgba *outside* `--pptx-*`/`#fff`-in-script and confirm 0 in slide content; assert the
  deck still carries `.theme-light`/`.theme-dark` scoping and no `data-theme` removal.
- **Asset-resolution check (automated)**: a script asserts every `DemoEmbed src=` and every
  `/img/demos/...` reference in the mdx resolves to a file on disk (case-sensitive).
- **Screenshot standard (reproducible)**: Playwright, viewport 1920×1080, deviceScaleFactor 1,
  sidebar hidden via the `s` key, fragments revealed via the documented JS, light theme.
- **Secret/PII**: sanitize terminal output + screenshots in guide docs — no account IDs, ARNs,
  bucket names, tokens, or local user paths.
- **A1 scope**: "colors" = inline `style=`, CSS in `:::css`, SVG fill/stroke attrs, gradients,
  and chart/canvas color strings — but only OUTSIDE `:::script` (those go through A2).
- **i18n**: if an edited guide doc has a `docs/i18n/ko` counterpart, sync it or add a
  "translation needed" note; do not silently diverge.

## Order (revised — tractable first, highest-risk last)
**B (guide docs) → A (aiops migration) → C (verify).** aiops's `:::script` canvas migration
is the highest-risk item; do it after the guide docs with the refined A2 approach.

## Gates (multi-agent consensus)
- Plan gate (this doc): Kiro/Codex/Gemini panel → **GO-WITH-FIXES** (fixes above incorporated).
- Per-batch diff gate: after B and after A, fan the diff to the panel; validate citations,
  drop `unsupported` findings; fix CRITICAL/MAJOR (≤ 2 rounds).
- Final gate: cumulative diff review + `npm run build` green + asset-resolution check.

## Commit discipline
One commit per task group (B, A), explicit paths, on `main`. Never touch the user's
`decision-reconcile`/CLAUDE.md changes. AWS security mandates apply (no secrets, etc.).
