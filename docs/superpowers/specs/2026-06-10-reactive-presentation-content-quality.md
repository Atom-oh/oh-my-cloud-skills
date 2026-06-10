# reactive-presentation Content-Quality Layer — Design Spec

- **Date**: 2026-06-10
- **Status**: Approved (direction) — pending implementation plan
- **Builds on**: `2026-06-10-reactive-presentation-design-system.md` (the token-driven, light-first **visual** overhaul, PR #53). This spec adds the **content/structure** layer.
- **Reference**: AWS Korea V-team's `aws-presentation` skill (a mature, production PPTX skill). Its design-token object + 24-check programmatic validator independently converged with our overhaul — confirming direction. The transferable gaps it exposes are content-layer conventions our skill lacks.
- **Target skill**: `plugins/aws-content-plugin/skills/reactive-presentation`

## Problem

The design-token overhaul fixed the **visual** layer (cohesion, light-first, tokens, lint). What still makes our output read as "AI-generated / amateur" is the **content layer**: free-form speaker notes, descriptive (encyclopedia-tone) slide titles, and scattered anti-patterns with no single sharp reference. The `aws-presentation` skill solves exactly these with structured notes, a headline title voice, and a consolidated "Forbidden AI-tells" list.

> **Output differs** (we emit Remarp/HTML, not PPTX), so PPTX mechanics (pptxgenjs anchors, `addStatBand`, fixed inches) do **not** transfer. Only the *principles* do, adapted to Remarp.

## Goal

Add the content-quality conventions to reactive-presentation, adapted to Remarp and to our **multi-level (100–400) multi-persona** audience (aws-presentation targets a single executive-briefing persona; we must differentiate by `level`).

## Decisions (locked)

- **Adapt, don't copy**: `[출처]` is conditional (claims/numbers only); `[변경이력]` is optional for us (git already tracks history) — include a lightweight form.
- **Level-differentiated title voice**: headline-with-edge is *recommended* for briefing/overview (level 100–200); clear topic titles are *allowed* for deep-dive (300–400). Not mandatory for every slide.
- **Mechanical where possible, qualitative where not**: note-structure + title-length are lint-enforced; title *voice/tone* is content-review-agent's qualitative call (not lint).

## Architecture

### 1. Structured speaker-note schema (`:::notes`)

Define a 5-layer `:::notes` structure that is a **superset** of today's free-form notes (keeps `{timing}`/`{cue}` markers, which aws lacks):

```
:::notes
{timing: Nmin}
[요약]            ← 3–5 one-line bullets (presenter scan / fold-above)
• …
<spoken script, 존댓말, with inline {cue: ...} markers>
[약어]            ← domain-specific abbreviations only (skip AWS/IT-common); omit block if none
• ABBR(Full): one-line
[출처]            ← conditional: required only when the slide cites numbers/benchmarks/vendor claims
• source — https://…
[변경이력]        ← optional, lightweight (git is canonical); bootstrap "• YYYY-MM-DD: 초기 작성"
:::
```

- `remarp_to_slides.py` already extracts `:::notes` verbatim and `presenter-view.js` renders it — the layers are plain text, so **no new parser** is required; only document the schema and (optionally) order `[요약]` to the top of the presenter fold.
- Documented in `references/remarp-format-guide.md` (notes section) + summarized in `SKILL.md`.

### 2. Slide title/subtitle voice

Add a "Slide Title Voice" section to `SKILL.md` + `references/slide-patterns.md`:
- Title = **headline with edge** (declarative / claim / question / reversal), ≤ ~28 KO chars; subtitle = **noun-ending (체언 종결)**, ≤ ~45 KO chars. Rich ✅/❌ examples (mirroring aws's, adapted).
- **Level gate**: recommend headline voice for `level` 100–200 (briefing/overview); allow clear descriptive titles for 300–400 (technical deep-dive). Reference the existing `level` frontmatter field.

### 3. Consolidated "Forbidden — AI-slide tells" section

Add one sharp anti-pattern section to `SKILL.md` that **consolidates** existing scattered STOP-checks + the transferable aws tells, each linked to its enforcing lint rule where mechanical:

| Anti-tell | Enforcement |
|-----------|-------------|
| hardcoded hex / inline color style / raw rgba | `RAW_HEX`/`INLINE_STYLE`/`RAW_RGBA` (lint) |
| magic-number type / off-scale spacing | `OFF_SCALE` + token system |
| dark-only / generic blue-teal default | dual-theme (light default) |
| text-wall bullets (8+) | `CONTENT_OVERFLOW` |
| gradient-text headings / decorative orbs / empty regions | guidance (+ candidate lint) |
| descriptive encyclopedia-tone titles | title-voice §2 (review-gated) |
| free-form / missing speaker notes | `NOTE_STRUCTURE` (new) |

### 4. New design-lint rules (`remarp_to_slides.py validate`)

- **`NOTE_STRUCTURE`** (WARNING): a content slide whose `:::notes` lacks a `[요약]` block; a claims/number slide lacking `[출처]`.
- **`TITLE_LENGTH`** (WARNING): slide title > 28 KO chars (or subtitle > 45) — the mechanical half of §2.
- Keep `--json` shape consistent with existing rules.

### 5. Source-omission cross-check (content-review-agent)

Add an explicit post-generation check to `content-review-agent`: list which source sections did **not** make it into the deck (architecture diagrams, domestic case studies, comparison tables, incident cases, timelines) — adapted from aws's "Cross-check After Generation".

## Components / files (anticipated)

- **Modify**: `SKILL.md` (note schema summary + title-voice + Forbidden section), `references/remarp-format-guide.md` (full note schema), `references/slide-patterns.md` (title-voice examples), `scripts/remarp_to_slides.py` (NOTE_STRUCTURE + TITLE_LENGTH lint), `agents/content-review-agent.md` (source-omission check).
- **Test**: extend `tests/structure/test-reactive-design-lint.sh` (NOTE_STRUCTURE/TITLE_LENGTH true+false positive).

## Compatibility / error handling

- Existing decks with free-form notes are **not invalidated** — `NOTE_STRUCTURE` is a WARNING (the rejection loop), not a hard fail; the schema is recommended, lint nudges.
- Title-length WARNING is advisory (some proper-noun titles legitimately run long).
- No change to rendering/runtime; notes remain plain text.

## Testing

- Lint rule tests (true-positive + false-positive fixtures) per the repo's secret-pattern test convention.
- A schema-conformant `:::notes` example builds and renders in presenter view (manual/Playwright spot-check).
- Full suite (`run-all.sh` + `test-plugins.py` + `test-codex-plugins.py`) stays green.

## Phasing (for the implementation plan)

1. **Note schema** — document in remarp-format-guide + SKILL.md; add `NOTE_STRUCTURE` lint + tests.
2. **Title voice** — SKILL.md + slide-patterns.md section (level-differentiated); add `TITLE_LENGTH` lint + tests.
3. **Forbidden AI-tells** — consolidated SKILL.md section linking each tell to its lint rule.
4. **Source-omission cross-check** — content-review-agent addition.

## Out of scope (future)

- PPTX-specific mechanics (anchors, stat-band, pptxgenjs) — different output format.
- A full PPTX export path mirroring aws-presentation (we already have html2canvas→PptxGenJS export).
- Auto-rewriting titles/notes of already-generated decks (forward-only guidance).
