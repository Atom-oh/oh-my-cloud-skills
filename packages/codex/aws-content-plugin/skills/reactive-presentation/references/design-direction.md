# Design Direction — Slide Visual Design Principles

> This document distills the principles of Anthropic's **frontend-design** skill for the
> reactive-presentation framework. Read it **before starting Phase 2 (Content Authoring) and
> during Phase 8 (Screenshot verification) self-critique**. For token/class details see
> [colors-reference.md](colors-reference.md); for writing rules see
> [authoring-rules.md](authoring-rules.md).

---

## 1. Core Principles (frontend-design summary)

1. **Ground it in the subject** — design choices come from the world of the presentation's
   subject matter. For an AWS technical deck, the starting point is AWS's actual design
   material (Cloudscape, Squid Ink `#232F3E`, Smile Orange, console UI, terminal/mono
   typography). If a customer-brand PPTX exists, **that brand always takes priority** (Phase 1
   extraction → `--pptx-*` tokens flow through the whole theme).
2. **Typography is personality** — deliberately pair a display typeface (headings) with a body
   typeface, and be deliberate about letter-spacing, weight, and scale. A title isn't just a
   content-delivery vehicle — it's a memorable design element.
3. **Structure is information** — number markers (01/02/03), eyebrows, and dividers should only
   be used when they encode the content's **real structure** (a process where order carries
   meaning, module numbers). Decorative numbering is forbidden.
4. **Motion is restrained orchestration** — one deliberate moment beats several scattered
   effects. Fragments should be used only to encode "speaking order." Excessive animation
   actually makes content look more AI-generated.
5. **Boldness lives in one place only (signature element)** — one element is enough to make a
   deck memorable; everything else should stay quiet and disciplined. "Take off one accessory
   before you leave the house" (Chanel).

## 2. Anti-default calibration — 3 "AI default looks" to avoid

Template looks that frontend-design flags as recurring regardless of subject matter:

| # | Look | Characteristics |
|---|-----|------|
| 1 | Warm cream + serif + terracotta | Background near `#F4F1EA`, high-contrast serif headings, terracotta accents |
| 2 | Near-black background + one neon solid accent | Near-black plus a single acid green/vermilion accent |
| 3 | Newspaper typesetting | Hairline rules, border-radius 0, dense multi-column layout |

> This framework's **old light default fell into look #1's family** (warm cream background +
> terracotta accent — though the typeface was Pretendard, not serif). The current default theme
> has replaced it with an AWS-subject-grounded identity (console-gray canvas + Squid Ink text +
> Smile Orange accent + Cloudscape blue text accent). If a brief explicitly requests a specific
> look, the brief wins — otherwise, don't "waste your creative freedom" on the three looks above.
> A deck that genuinely needs the old warm look should opt into it deliberately via
> `theme: { preset: paper }`.

## 3. Per-deck design plan (before entering Phase 2, 2-pass)

**Pass 1 — write the plan** (alongside the answer to the planning question's "Design refs",
concisely, in your own thinking):

- **Subject**: one sentence covering the topic, audience, and this deck's single purpose.
- **Palette**: 4–6 named hex values. If using the default theme tokens, this step only needs to
  declare "adopting the default palette + keeping/changing the accent." When extracting from a
  PPTX, the manifest's colors are the palette.
- **Type**: 2+ roles (display / body / mono-utility). Defaults: Space Grotesk (Latin display,
  Pretendard fallback for Korean) / Pretendard / JetBrains Mono. State explicitly if the subject
  gives a reason to change this.
- **Layout**: one sentence each on the layout concept for 1–2 representative slides.
- **Signature**: the single element that will make this deck memorable. The framework's default
  signature is the **beam rule** (an accent-gradient hairline below the slide header). If adding
  a deck-specific signature, add only one via `:::css` — don't let it compete with the default
  signature.

**Pass 2 — self-critique**: check whether the plan would look "the same as what you'd have
produced for a similar brief." If so, revise that part and leave a one-line note on what changed
and why. Only start writing Remarp content after this passes.

## 4. Framework theme system

| Choice | frontmatter | Result |
|------|-------------|------|
| Default (light) | (none) | Console-gray canvas `#eaedee` + white cards + Squid Ink text + Smile Orange accent |
| Dark | `theme: { mode: dark }` | Squid-ink night (`#0f1b2a` family) + `#ff9900` accent |
| Warm paper (old default) | `theme: { preset: paper }` | Warm cream + terracotta (only when deliberately chosen) |
| Brand PPTX | Phase 1 extraction | `--pptx-*` takes priority over every preset |

- Per-slide contrast: the `@theme: dark` directive can switch only a cover/section slide to
  dark. **Caution**: this switch applies to DOM/CSS content. `:::canvas` diagram colors
  (`Colors`) and the Mermaid theme are resolved **relative to the deck root theme**, so don't
  place canvas/Mermaid content on an `@theme` slide that differs from the deck theme (use
  text/CSS slides for cover/section emphasis instead). Custom code that switches theme at
  runtime must call `refreshThemeColors()` and then redraw the canvas upon receiving the
  `remarp:theme-colors` event.
- All markup should use only role tokens (`var(--accent)`, etc.) — hardcoded hex is forbidden
  (colors-reference.md). That's what lets theme/brand switching propagate everywhere at once.

## 5. Typography rules

- `h1`/`h2` = `--font-display` + `--tracking-tight`. Korean titles fall back to Pretendard
  safely. `h3` = `--text-accent` (light mode: Cloudscape blue) — kept role-separate from the
  accent orange.
- **Eyebrow** (`.eyebrow`): mono, uppercase, `--tracking-wide`, accent color. Use only for
  **real structure**, such as module numbers ("MODULE 02") or section categories ("HANDS-ON") —
  don't repeat it as decoration on every slide.
- Gradient text is a template answer — don't use it (already removed from the old
  `.title-slide h1`).

## 6. Restraint checklist (during Phase 8 screenshot self-critique)

- [ ] Is there exactly **one** signature element? (If a deck-specific decoration was added
      beyond the beam rule, is it only that one?)
- [ ] Is accent orange used in 1–2 places per slide at most? (Progress bar/active tab/marker/beam
      are the framework's own responsibility.)
- [ ] Do numbers/eyebrows encode real structure?
- [ ] Does fragment order match speaking order? Are there unnecessary fades?
- [ ] Is body text contrast at least 4.5:1, and do cards visually separate from the canvas?
- [ ] Is there one accessory that could be removed? If so, remove it.

## 7. Slide copy (summary — see authoring-rules.md §2/§3 for detail)

Copy is also design material: use active voice, and assertion-style titles (Title Voice) rather
than imperative titles, naming things the way the audience perceives them rather than as system
implementation details. Filler phrases and AI-tell expressions follow the forbidden list in
authoring-rules §2.
