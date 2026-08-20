# Atlas templates

The skeletons `/atlas:init` and `/atlas:add-doc` write. Copy these shapes exactly rather
than inventing a variant: `atlas_index.py`'s parser accepts a deliberately small YAML
subset (flat keys, inline or block lists — see `frontmatter-schema.md`), and a doc that
drifts from these shapes gets schema errors, which means drift detection skips it with a
stderr advisory and it becomes permanently uncheckable.

## Doc skeleton

Paste, replace every angle-bracketed value, delete the guidance comments. All six
frontmatter fields are present so nothing has to be retrofitted later; `related: []` is
a valid empty list and better than omitting the key, because it makes the "no edges yet"
state explicit rather than ambiguous.

````markdown
---
title: <topic, phrased the way a teammate would say it>
description: <one sentence stating what this doc knows — a reader must be able to decide relevance from this line alone, without opening the body>
covers:
  - <repo-root-relative glob, e.g. plugins/example/skills/example/**>
related: []
code_rev: <output of `git rev-parse --short HEAD` at creation time>
updated: <YYYY-MM-DD>
---

## Overview

<What this area of the code does and why it exists. Two or three paragraphs. Write for
a session that has read only the description so far.>

## Key decisions

<The non-obvious choices and their reasons — the things a reader would otherwise
re-litigate. Link an ADR where one exists instead of restating it.>

## Code pointers

<Entry points, the files that matter, and what each is responsible for. Paths here
should fall inside this doc's `covers` globs — a pointer outside them is a sign the
globs are wrong.>

## Related

<One line per `related` entry saying why a reader would jump there. Keep this section
and the frontmatter `related` list in step: the frontmatter is what /atlas:graph and
the validator read; this section is for humans.>
````

Set `code_rev` to the sha of the commit whose code the body actually describes. Setting
it to an older sha makes the very next push flag the doc as stale and send it to the
fixer over changes the body already covers — harmless, but a wasted headless call.

## INDEX.md skeleton

`/atlas:init` writes this file, and `atlas_index.py --write` regenerates the table on
every sync. The generated table lives between two AUTO-MANAGED markers. **Content
outside the markers is preserved byte-for-byte on regeneration; content inside them is
overwritten wholesale.** Put anything you hand-write — intro prose, reading order,
house rules — outside the block, or the next regeneration will silently discard it.

````markdown
# Atlas Index

Per-topic documentation for this repository. Pick docs by `description` and `covers`,
then read only those bodies.

<!-- AUTO-MANAGED:index -->
| Doc | Description | Covers | Related | Synced |
|---|---|---|---|---|
| [hybrid-gate.md](hybrid-gate.md) | How the hybrid gate fans out finders... | 2 globs | consensus-pipeline.md | 566db30 |
<!-- /AUTO-MANAGED -->

Last updated: 2026-08-19 (managed by /atlas:init, /atlas:add-doc, /atlas:sync)
````

Do not edit the table by hand — your edit survives exactly until the next regeneration.
If `INDEX.md` exists but has lost its markers, `atlas_index.py --write` appends a fresh
block rather than overwriting the file, and says so; restore the markers rather than
accumulating stale blocks. Cell content is pipe-escaped and descriptions are truncated
at 80 characters by the generator, so a long or pipe-containing description cannot break
the table — but it will read badly, which is a `description` problem, not a table one.

## How covers is drafted

`covers` decides both when a doc is flagged stale and which diff the fixer is shown, so
draft it deliberately:

- **Derive globs from the module paths the doc describes.** Start from the paths in
  `## Code pointers` and generalize upward to the directory that owns them. A doc about
  a skill covers that skill's directory, not the three files it happens to mention
  today.
- **Prefer one directory-scoped `**` glob over enumerating files.** `plugins/x/**` keeps
  working when files are added to the module; a hand-enumerated file list silently stops
  covering new files, and changes to those files never flag the doc — the exact silent
  drift this plugin exists to prevent. Enumerate individual files only when the doc
  genuinely covers a slice of a directory that another doc owns the rest of.
- **Never let two docs claim the same file without a note saying which one is
  authoritative.** Overlap is not detected mechanically, and it is not always wrong —
  an overview doc and a deep-dive doc may legitimately share territory. But one code
  change then drags both docs into the fixer, each headless call sees only its own doc,
  and the two can be rewritten in opposite directions on the same push. If globs must
  overlap, add a line to each doc's `## Overview` naming which doc is authoritative for
  the shared files, so the fixer (which reads the body it is editing) and any human
  reviewer can resolve the conflict in the same direction.

Remember the matcher's semantics when drafting: `*` stops at `/`, `**` spans directories
(including zero of them). `docs/atlas/*.md` does not cover `docs/atlas/sub/deep.md`; if
you meant the whole tree, write `docs/atlas/**`. The verified examples are in
`frontmatter-schema.md`.
