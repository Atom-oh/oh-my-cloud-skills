# reactive-presentation Design-System Overhaul — Design Spec

- **Date**: 2026-06-10
- **Status**: Approved (direction) — pending implementation plan
- **Origin**: co-agent multi-AI design review (panel: Kiro claude-opus-4.8 / kimi-k2.5 / glm-5, Codex, Gemini). All findings below were verified by Claude against the actual files (no vote-counting).
- **Target skill**: `plugins/aws-content-plugin/skills/reactive-presentation`

## Problem

Modern AI presentation tools (Gamma, Tome, Presenton) produce visibly more polished, cohesive
decks than this skill. The 5-model panel converged on a **single root cause**:

> **Design lives in copy-paste inline-hardcoded literals, not a token system.**

The skill's most-promoted authoring pattern is "the LLM emits inline `style=` with hardcoded
hex." Color/spacing/typography decisions are delegated to per-slide model output, which
structurally guarantees drift — from the theme, between slides, and across sessions. Validator
heuristics (bullet-counting) cannot fix a design system that lives in copy-paste strings.

### Verified findings (severity · evidence)

| # | Sev | Finding | Evidence (verified) |
|---|-----|---------|---------------------|
| 1 | CRITICAL | **Palette split-brain** — SKILL.md templates hardcode cyan `#00d4ff` (9×) while `theme.css` `--accent` is purple `#6c5ce7`. Frame chrome renders violet, body renders cyan — every slide disagrees with its own frame. | `grep` SKILL hexes vs `--accent` |
| 2 | CRITICAL | **No design-token system** — no type/spacing/radius/shadow scales. font-size ad-hoc (.9/.82/.75/0.8rem + px), border-radius 10 values mixing px/rem. | `grep --space/--radius/--shadow` = 0 hits |
| 3 | CRITICAL | **Dark-only** — no `.theme-light`, no `prefers-color-scheme`; bg `#0f1117`. Modern AI PPT is light-first. | no light theme in `theme.css` |
| 4 | MAJOR | **Magic-number typography** — h1/h2/h3 = 2.4/1.8/1.3rem; inter-step ratios 1.33/1.38/1.24 → hierarchy reads as random. | `theme.css` |
| 5 | MAJOR | **Inline `style=` pollution** — templates use raw hex, not `var()`, so PPTX overrides are ignored by the most-used patterns. | SKILL.md templates |
| 6 | MAJOR | **PPTX/brand theming wired but not consumed** — `--pptx-*` tokens defined but never referenced; brand extraction is decorative. | **10 defs / 0 `var(--pptx*)` uses** |
| 7 | MAJOR | **No layout intelligence** — `validate` flags overflow but never rebalances; Gamma auto-adjusts density. | SKILL Phase 2.8 |
| 8 | MAJOR | **Inline px defeats responsive scaling** — `font-size:13px/20px` in templates sit outside the rem/clamp system → undersized at the 4K target the skill verifies. | SKILL templates vs `html{clamp}` |
| 9 | MINOR | **No tonal ramps / semantic on-colors** — each color is one hex + one fixed-alpha bg → scattered one-off `rgba()`. | `theme.css` |
| 10 | MINOR | **Fallback-hex drift** — `var(--yellow,#f1c40f)` ≠ root `--yellow:#fdcb6e`; `var(--text-muted,#8b8fa3)` ≠ root `#6b7194`. A second source of truth, already diverged. | `theme.css:29/609`, `20/588` |
| 11 | MINOR | **Violates project's own theming contract** — `AGENTS.md` mandates class-based `.theme-dark/.theme-light` (never `data-theme`); `theme.css` uses bare `:root`. | `AGENTS.md:29` |
| 12 | MINOR | **No a11y interaction states** — `:hover` only; missing `:focus-visible`/`:active`/`:disabled`. Plus z-index magic numbers, no motion tokens, render-blocking `@import` fonts. | `theme.css` |

## Goal

Transform the skill from "decorated inline HTML" to a **token-driven, light-first design system**
whose output is cohesive *by construction*. Consistency must come from the system, not from
per-slide LLM discipline.

## Decisions (locked)

- **Scope**: full remediation in one spec (tokens + palette unification + light-first dual theme +
  PPTX token wiring + design lint), implemented as ordered tasks.
- **Default theme**: **light-first** (Gamma-style). Dark becomes an intentional `.theme-dark`
  variant. Existing dark decks must still render via the dark class (no silent regression).
- **Single source of truth**: one token layer; templates and components consume tokens only.

## Architecture

### 1. Token layer — `assets/design-tokens.css` (new), imported first by `theme.css`

- **Type scale**: modular, ratio **1.25** (major third), 8 steps → `--text-xs … --text-5xl`,
  each paired with a line-height and weight role (display/title/subtitle/body/caption/eyebrow/
  metric/code). Headings/body map to roles, not raw rem.
- **Spacing scale**: 8px grid → `--space-1:.25rem … --space-8:4rem`. One slide-padding token,
  one default content-gap token.
- **Radius**: `--radius-sm/md/lg/pill` (single unit).
- **Shadow/elevation**: `--shadow-1/2/3` + `--shadow-glow`. Inline shadow literals forbidden.
- **Color roles** (semantic, theme-agnostic): `--surface-1/2/3`, `--on-surface`, `--on-surface-muted`,
  `--accent`, `--accent-subtle`, `--accent-on`, plus semantic `--info/--success/--warning/--danger`
  each with `-subtle`/`-on` variants. Per-hue tonal handling via `color-mix()` (stdlib CSS, no build).
- **Motion**: `--duration-fast/normal/slow` + named easings. **Z-index**: `--z-base/nav/overlay/modal/toast`.

### 2. Theme scoping — class-based `.theme-light` / `.theme-dark`

- Move all themeable values out of bare `:root` into `.theme-light` and `.theme-dark` scopes
  (honoring the `AGENTS.md` contract). `:root` holds only non-theme primitives (scales).
- **`.theme-light` is the default** (applied on the deck root when no class is set). Author a real
  light palette (clean surfaces, restrained contrast) — not an inversion of the dark one.
- Keep a curated `.theme-dark` that reproduces today's look closely enough that existing decks
  don't regress when switched to the dark class.

### 3. Template detox — `SKILL.md` + `references/*` + JS asset components

- Remove every hardcoded hex / inline `style=` from the promoted tab/card/flow templates and the
  copy-paste palette table. Replace with **class-based primitives** backed by tokens:
  `.tab-set`, `.card-grid`, `.metric-card`, `.flow-group`, `.callout`, `.comparison`.
- Behavior (tab switching, fragment reveal) stays self-contained but references token vars and
  rem units only — never raw px or hex.
- Remove inline `var(--x, #hex)` fallbacks (the drifted second source of truth).

### 4. Brand/PPTX wiring — make extraction drive core tokens

- `extract_pptx_theme.py` output maps brand colors **into the core token layer** (e.g.
  `--accent: var(--pptx-accent1)` consumed everywhere), so a customer's PPTX re-brands the whole
  deck — including the interactive tab/card components — instead of populating unused vars.

### 5. Design lint — extend `remarp_to_slides.py validate`

- New rules (rejection loop, mechanical): raw hex / inline `style=` in `:::html`, off-scale
  spacing (values not in the spacing scale), non-token font-size, raw `rgba()` literals, and
  treat slide-body overflow as a hard layout failure (not silently scrollable).
- Add `--fix`-able guidance where deterministic; flag otherwise.

## Components / files (anticipated)

- **New**: `assets/design-tokens.css`, lint rules in `scripts/remarp_to_slides.py`,
  tests under `tests/structure/`.
- **Modify**: `assets/theme.css` (tokenize + dual-theme scopes), `SKILL.md` (template detox +
  light-first guidance + slide-type color guidance), `references/colors-reference.md`,
  `references/framework-guide.md`, `references/slide-patterns.md` (token-based examples),
  `scripts/extract_pptx_theme.py` (token mapping), `assets/theme-override-template.css`.

## Error handling / compatibility

- **No silent regression of existing decks**: dark look preserved under `.theme-dark`; a deck that
  set no theme class now defaults to light — document this and provide a one-line opt-back-to-dark.
- PPTX override path must keep working (now driving tokens).
- Generated HTML for prior presentations is not rewritten by this change (forward-only); the
  framework `common/theme.css` they copy is what upgrades.

## Testing

- Token presence + scale unit tests (`tests/structure/`): tokens defined; no raw hex in SKILL
  templates; spacing/radius values drawn from the scale; light + dark scopes both present.
- `validate` design-lint rule tests (true-positive + false-positive fixtures), per the repo's
  secret-pattern test convention.
- Build a representative deck and screenshot-verify (Playwright) light + dark at FHD/4K
  (existing Phase 8 procedure).
- Full suite (`run-all.sh` + `test-plugins.py` + `test-codex-plugins.py`) stays green.

## Phasing (for the implementation plan — bite-sized TDD tasks)

1. **Token foundation** — `design-tokens.css` (type/spacing/radius/shadow/color-role/motion/z) + tests.
2. **Palette unification** — SKILL templates → token classes; remove hardcoded hex + inline fallbacks.
3. **Dual theme** — `.theme-light` (default) / `.theme-dark` scopes; tokenize `theme.css`.
4. **PPTX token wiring** — extraction maps brand → core tokens; verify a themed deck inherits brand.
5. **Design lint** — `validate` rules + tests; overflow = hard fail.

## Out of scope (future specs)

- A full slide-AST / layout solver (auto-layout intelligence) — large; follow-up.
- Image generation / stock imagery integration.
- Component-kit expansion beyond the primitives needed to detox current templates.
- Rewriting already-generated presentation HTML in user repos.
