# ADR-020: Archify as the Interactive-Diagram Path, with Official AWS Icons, Embedded in Reactive-Presentation

## Status

Accepted (2026-09-01) — PoC complete, both gates resolved (see below and
`poc/adr-020/`).

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

## PoC results (2026-09-01 — evidence and repro in `poc/adr-020/`)

- **Vendor vs. depend → depend, version-pinned, no fork.** Archify's native `brand`
  field cannot carry AWS icons (its Simple Icons-based catalog has zero AWS marks —
  Simple Icons removed them — and the only other schema form is a network-captured
  `{url, sha256}`). Post-render injection works instead: the output HTML gives every
  node a stable `id="node-<id>"` hook with spec-coordinate rects, so a small script
  (`poc/adr-020/inject_aws_icons.py`) places official icons without touching the
  renderer, and Archify's own `check` still passes on the modified artifact. Two
  injection rules are load-bearing (paint order; `<g transform>` not nested-svg
  geometry) — recorded in the PoC README. Cost of this path: we depend on the output
  markup shape, so the Archify version is pinned and a structure probe test must fail
  loudly on upgrade.
- **Iframe interaction budget → fits.** 6-node EKS reference diagram, official icons
  on all 6 nodes, iframed into a 1920×1080 slide: focus stays with the deck on load,
  arrow keys reach the deck's handler, the artifact is ~716 KB self-contained, and
  headless Playwright (the `export_pptx.py` capture path) screenshots it cleanly.
  Deferred to implementation: a real `:::archify` build in `remarp_to_slides.py`,
  an end-to-end `export_pptx.py` run, and click-in/Escape-out focus return.

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

## References

- Pin: [tt-a1i/archify](https://github.com/tt-a1i/archify) 2.16.0, commit
  `199360cc6687a7857b54dd188d4922b09e466a4b` (canonical constant:
  `reactive-presentation/scripts/archify_icons.py`)
- PoC evidence and repro: `poc/adr-020/`
- Implementation: `archify_icons.py` (icon injection), `ARCH_STEMS` in
  `architecture-diagram/scripts/layout_aws.py` (shared vocabulary), `:::archify` in
  `remarp_to_slides.py`, `--base-url` notes in `export_pptx.py`,
  `tests/structure/test-archify-structure-probe.sh` (upgrade guard)
