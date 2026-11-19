---
name: sketch-diagram
description: "Create a light, hand-drawn animated concept diagram (wobbly ink lines, soft washes, doodle icons, dots flowing along the real topology) as inline SVG for a slide opener or a friendly explainer. Use for 'sketch diagram', 'hand-drawn diagram', 'doodle diagram', 'animated sketch', 'light opener diagram for a slide', '손그림 다이어그램', '스케치 다이어그램', '가볍게 시작하는 도식'. Not for AWS architecture accuracy (use architecture-diagram or animated-diagram), and not for step-by-step deep dives (use Remarp `:::archify` or canvas)."
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - AskUserQuestion
---

# Sketch Diagram

A one-screen concept diagram that looks like an engineer's notebook sketch: wobbly ink
lines, pale colour washes, doodle icons, numbered stamps, and small dots that travel along
the connections. It is the **light** diagram: it opens a topic, it does not document an
architecture. Style and motion ideas were studied from the MIT-licensed `animated-sketch-diagram`
skill (OLDyade); nothing is copied, and everything here is written for this plugin and
for deck theme tokens.

## When to use it, and when not

| Situation | Use |
|---|---|
| First content slide after the cover, a "here is the whole idea" picture | **sketch-diagram** |
| Friendly explainer of a loop, pipeline, hub, comparison or timeline | **sketch-diagram** |
| Exact AWS services, VPC and account boundaries, official icons | `architecture-diagram` / `animated-diagram` |
| Step-by-step walkthrough or explorable diagram | Remarp `:::archify` / canvas in `reactive-presentation` |
| Several slides of dense diagrams | not this skill; sketch style loses legibility past about 8 nodes |

## Workflow

1. **Find the real shape of the topic** before drawing. Pick the layout archetype in
   `references/layouts.md` that matches it (bands, layers, hub and spokes, comparison,
   single path, timeline). Do not default to a left to right row of boxes.
2. **Write the flow story in one sentence**: what flows (data, requests, memory, tasks),
   where it starts, where it forks or merges, where it loops, where it ends. Every path
   that carries that flow gets dots. A loop in the topic must be a loop in the picture.
3. **Pick icon sourcing.** Default: draw simple doodle icons inline (recipes in
   `references/recipes.md`). Ask once with `AskUserQuestion` only when the user may want
   generated or downloaded art; in headless or subagent runs use the default without asking.
4. **Assemble from `templates/sketch-opener.html`**: copy it, replace labels and geometry,
   keep the shared filter, tokens and animation rules. Use only role tokens, never hex.
5. **Verify** (see Checks below), then embed per `references/slide-embedding.md`.

```bash
python3 skills/reactive-presentation/scripts/remarp_to_slides.py validate deck.remarp.md
```

## Hard rules

- **Tokens only.** Ink is `currentColor` (the deck's `--on-surface`), paper is
  `--surface-1`, cards `--surface-2`, washes `color-mix()` of a role colour into the paper.
  The result must read in both `.theme-light` and `.theme-dark`. No raw hex or rgba.
- **Hand-drawn feel comes from one shared SVG filter** (`feTurbulence` plus
  `feDisplacementMap`) on ink strokes, plus gently bowed paths. No ruler-straight lines.
  Do not put the filter on text.
- **Motion is meaning.** Dots move at readable speed (roughly 80 to 150 px per second in
  slide space), follow the actual curves, and appear on loops and merges too. One slow
  loop (about 3 s base) drives everything through `--sk-loop`.
- **Respect reduced motion**: animations off, dots hidden, static picture still complete.
- **Short labels** (about 12 Korean characters at most), one doodle icon per card, 3 to 6
  cards per band, at most 3 to 6 sparkles in the whole picture.
- **Content comes from the user's topic.** Never keep the template's wording or topology
  by default.
- Copy style from the deck applies: no em dashes or middle dots in labels.

## Output

One self-contained block: a `<style>` with the `sk-*` rules and an inline `<svg>` with
`viewBox="0 0 960 450"`, an `aria-label` that tells the flow in one sentence, and no
external files. A flow dot is one circle whose motion path repeats a visible edge:

```html
<path d="M265 170 Q310 158 372 170"/>
<circle class="sk-dot a" style="offset-path:path('M265 170 Q310 158 372 170')"/>
```

## Common problems

| Symptom | Cause | Fix |
|---|---|---|
| Everything renders as black blobs in a deck | rules put in a `:::css` block, which drops ordinary CSS | move the `<style>` inside the `:::html` block |
| A spinning icon jumps away from its card | animated element also positioned with `transform=` | position on an outer `<g>`, animate an inner `<g>` |
| Dots drift off the lines | `offset-path` differs from the visible edge | paste the same path string into both |
| Diagram looks washed out in dark mode | a raw colour or fixed paper colour was used | use role tokens and `color-mix()` washes only |

## Checks before showing

1. Open the file in a browser at deck size and in both themes; screenshot both.
2. Squint test: ink should be evenly distributed; an empty zone means a missing element
   or a band that is too big.
3. Every label is readable at projector distance (>= 16 px in a 960 wide viewBox).
4. Flow dots visibly move within two seconds and cover every flow-bearing path.
5. With `prefers-reduced-motion: reduce` the diagram is still understandable.
6. Inside a deck: `remarp_to_slides.py validate` shows no `RAW_HEX`, `INLINE_STYLE`
   or `EM_DASH` findings from the pasted block (see `references/slide-embedding.md`).

## References

- `references/layouts.md`: archetypes and how to pick one
- `references/recipes.md`: filter, panels, cards, icons, arrows, dots, sparkles, motion timing
- `references/slide-embedding.md`: putting it in a Remarp slide, fonts, sizing, notes
- `templates/sketch-opener.html`: working three-band example with a feedback loop
