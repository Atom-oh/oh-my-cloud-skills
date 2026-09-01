# ADR-020: Archify as the Interactive-Diagram Path, with Official AWS Icons, Embedded in Reactive-Presentation

## Status

Proposed (2026-09-01) — draft; two open questions below are gated on a PoC.

## Context

The marketplace already ships four diagram paths, each with a settled seat:

| Path | Produces | Seat |
|------|----------|------|
| `architecture-diagram-agent` (`layout_aws.py`) | .drawio → PNG/SVG | static, editable-in-drawio architecture artifacts |
| `animated-diagram-agent` | SVG + SMIL HTML | linear animated flows as standalone pages |
| Remarp `:::canvas` DSL (reactive-presentation) | in-slide SVG with step animation | diagrams that live inside a deck and step with the talk |
| `aws-diagram` (user-level skill) | self-contained SVG | quick one-shot diagrams outside the plugin flow |

What none of them provide is an **explorable** diagram: progressive detail the audience
can zoom through (overview → region → component), path-aware highlighting ("follow this
request"), and a semantic camera — the presentation move where an architecture is
revealed by navigation rather than by a fixed animation order.

[Archify](https://github.com/tt-a1i/archify) (tt-a1i/archify, MIT, 20k+ stars) is an
open-source Claude skill that does exactly this: natural language or Mermaid in → a
typed, schema-validated JSON spec → a **single self-contained HTML file with inline
SVG**, with MAP→READ→FULL progressive detail, path-aware stories, dark/light theming,
and PNG/SVG/WebM export. Three properties make it a natural fit here rather than a
fifth redundant path:

1. **Same artifact contract.** Self-contained HTML with no external dependencies is
   already this repo's convention (Remarp decks, brochure, gh-home), so Archify output
   can be hosted, reviewed, and embedded the way every other content artifact is.
2. **The icon asset already exists.** `aws-content-plugin` bundles the official
   811-icon AWS library (`reactive-presentation/assets/aws-icons.zip`, shared with
   `aws-light-fcd` via `kit.icon()`), and `layout_aws.py` already maintains a
   service-name → icon mapping. Injecting official icons into Archify nodes is a
   mapping layer, not new asset work — and MIT licensing permits the modification if
   the renderer needs one.
3. **The presentation grammar matches.** MAP→READ→FULL and path stories are the same
   move as `:::canvas` step animation (ArrowDown reveals); an Archify diagram inside a
   Remarp deck extends a pattern presenters already use, instead of introducing a
   foreign interaction model.

## Decision

1. **Adopt Archify as the fifth diagram path with a scoped seat: exploratory /
   interactive diagrams** — anything the audience or reader is meant to navigate
   (zoom, trace a path, toggle detail). The four existing paths keep their seats;
   routing keywords that imply a static artifact (.drawio, PNG, "다이어그램 파일") or a
   linear animation (SMIL) do not route to Archify. Routing tables in
   `aws-content-plugin/CLAUDE.md` and the root inventory gain one line each.

2. **AWS icon layer at the spec level.** When the diagram depicts AWS services, node
   visuals come from the bundled official 811-icon library (referenced in place, same
   rule as `kit.icon()` — never duplicated). The mapping (service name/alias → icon
   asset) reuses `layout_aws.py`'s table as the vocabulary source so the two paths
   name services identically.

3. **Embedding in reactive-presentation via an `:::archify` block.** The block carries
   the Archify JSON spec (or a pointer to it); `remarp_to_slides.py` renders the
   Archify HTML and embeds it in the slide inside an **iframe** — isolation is what
   keeps Archify's keyboard/camera interaction from fighting Remarp's arrow-key slide
   navigation (focus stays with the deck until the presenter clicks into the diagram;
   Esc or clicking outside returns it).

4. **PPTX export flattens deliberately.** `export_pptx.py` captures the diagram's MAP
   state as the slide image and appends the hosted interactive URL to the speaker
   notes. An interactive artifact cannot survive a PPTX round-trip; pretending
   otherwise would break the export contract, so the flattening is the documented
   behavior, not a bug.

5. **Quality gate unchanged.** Archify-bearing artifacts go through
   `content-review-agent` like every other content artifact; the icon rule (official
   icons for AWS services, scored in category 7) applies to Archify nodes the same as
   to slides.

## Open questions (PoC gates — resolve before Accepted)

- **Vendor vs. depend.** If Archify's spec supports custom node icons/brand marks
  natively, we depend on the upstream skill and inject icons purely at spec level (no
  fork). If icon injection requires touching the renderer, we vendor a pinned copy
  under the project-init-style mirror rule (byte-identical + documented local delta).
  The PoC answers which.
- **Iframe interaction budget.** Verify on a real deck: focus hand-off both directions,
  1920×1080 canvas fit, capture behavior in `export_pptx.py`, and that a deck carrying
  2-3 Archify iframes stays within acceptable size/load for GitHub Pages hosting.

## Consequences

- One new seat to maintain in the routing tables and `docs/reference/review-routing.md`
  (mixed-changeset gate precedence gains an "interactive diagram" row).
- An upstream dependency (or pinned vendor copy) enters the content plugin — sync
  cadence and the local-delta rule must be stated in the plugin `CLAUDE.md` either way.
- The `:::archify` block adds a build path to `remarp_to_slides.py` and a capture case
  to `export_pptx.py`; both need structure tests alongside the implementation.
- Presenters get an AWS-branded explorable diagram inside the deck they already build,
  with zero change to how the rest of the deck is authored.

## Alternatives considered

- **Extend `:::canvas` to cover zoom/story natively** — keeps everything in-house but
  re-implements Archify's hardest features (semantic camera, progressive LOD) inside a
  DSL whose writeback editor (VSCode extension) would also need to grow; rejected as
  building a worse Archify.
- **Convert Archify specs into `:::canvas` DSL** (compile-away) — preserves export and
  editor compatibility but discards exactly the interactive features that motivate
  adoption; kept in reserve as a degradation path for PPTX-first decks.
- **Iframe-embed without the icon layer** — works immediately but produces generically
  styled nodes, which fails the official-icon convention and the review gate's
  category 7; rejected as not meeting the repo's own bar.
