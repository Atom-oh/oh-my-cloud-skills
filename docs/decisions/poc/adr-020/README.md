# ADR-020 PoC — Archify + official AWS icons + slide embed

Evidence for the two PoC gates in `../../ADR-020-archify-interactive-diagrams.md`.
Reproduce end to end (no repo changes required):

```bash
git clone --depth 1 https://github.com/tt-a1i/archify /tmp/archify
cd /tmp/archify/archify

# 1. Validate + render the AWS spec (the validator reports label overlaps with
#    concrete labelDy fixes — apply what it suggests).
node bin/archify.mjs validate architecture <this-dir>/aws-eks-web.architecture.json
node bin/archify.mjs render   architecture <this-dir>/aws-eks-web.architecture.json /tmp/poc-aws.html

# 2. Extract the official icons named in icon-map.json from the bundled set
#    (plugins/aws-content-plugin/skills/reactive-presentation/assets/aws-icons.zip,
#    Architecture-Service-Icons */64/*.svg) into a directory.

# 3. Inject official icons (keeps Archify unmodified) and re-check:
python3 <this-dir>/inject_aws_icons.py /tmp/poc-aws.html <this-dir>/icon-map.json <icons-dir> /tmp/poc-aws-icons.html
node bin/archify.mjs check /tmp/poc-aws-icons.html   # still passes on the modified artifact

# 4. Slide embed: poc-slide.html iframes the diagram at 1920x1080.
```

## Gate results (2026-09-01)

**Gate A — depend, do not fork.** Archify's native `brand` field cannot carry AWS
icons: the built-in catalog (107 marks, Simple Icons-based) has zero AWS entries
(Simple Icons removed AWS/Amazon marks), and the schema's only other form is a
digest-pinned network capture (`{url, sha256}`) — no local-vector form. Post-render
injection works instead, because the output carries stable hooks: every node group is
`<g id="node-<id>" data-node-id=...>` and its `<rect>` uses the spec's own
coordinates. Injection contract learned the hard way (both are load-bearing):

- insert **after the node's rects** — SVG paints in document order, so a first-child
  icon is covered by the opaque node body;
- position with `<g transform="translate() scale()">`, **not** a nested `<svg x= y=>`
  — the viewer's stylesheet can override nested-svg geometry, a transform attribute it
  cannot;
- namespace the icon's internal ids (gradients) per node.

This couples us to the output markup shape, so the dependency must be **version-pinned**
and guarded by a structure probe (assert `id="node-"` and spec-coordinate rects exist)
that fails loudly on an Archify upgrade.

**Gate B — iframe embed works.** With the diagram iframed into a 1920×1080 slide
(`poc-slide.html`): focus stays on the parent document at load (`document.activeElement
=== BODY`), two ArrowRight presses reach the parent's key handler (Remarp navigation
unaffected until the presenter clicks into the diagram), the artifact is ~716 KB
self-contained, and headless Playwright captures it cleanly (`evidence-slide.png`) —
the same capture path `export_pptx.py` uses.

Not yet exercised (implementation-phase items, not gate blockers): a full
`remarp_to_slides.py`-built deck with a real `:::archify` block, end-to-end
`export_pptx.py` run, and click-into-iframe-then-Escape focus return.
