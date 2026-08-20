---
description: Add one atlas doc skeleton with pre-filled frontmatter under the wiki directory, then regenerate INDEX.md
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
argument-hint: Topic or filename for the new doc, e.g. "hybrid-gate" or "how the review pipeline works"
---

# atlas: add-doc

Add one new page to this repo's atlas wiki: a skeleton with fully pre-filled
frontmatter, then a regenerated `INDEX.md` so the page is immediately discoverable.

Resolve paths first:

```bash
SK="${CLAUDE_PLUGIN_ROOT}/skills/atlas/scripts"
ROOT="$(git rev-parse --show-toplevel)"
WIKI_REL="$(python3 "$SK/atlas_config.py" atlas-root --root "$ROOT")"
HEAD_SHA="$(git rev-parse --short HEAD)"
```

`--root` takes the REPOSITORY root, never the wiki directory — the scripts derive the
wiki directory from config themselves, and passing it to `--root` would double the
path up. Always pass `--root "$ROOT"`.

## Step 1: Name the doc and check for collisions

Derive a kebab-case filename from `$ARGUMENTS` (e.g. `review-pipeline.md`). List the
existing docs with `python3 "$SK/atlas_index.py" --list --root "$ROOT"` (one JSON
object per line): if the filename already exists, stop and ask whether to extend that
doc instead — two pages on one topic is worse than one longer page.

## Step 2: Draft the frontmatter

Copy the doc skeleton from
`${CLAUDE_PLUGIN_ROOT}/skills/atlas/references/atlas-templates.md` and fill every
field:

- `title` — the topic, phrased the way a teammate would say it.
- `description` — one sentence a reader can judge relevance by without opening the
  body; load-bearing words first (the INDEX truncates at 80 characters).
- `covers` — see the drafting rules below.
- `related` — relpaths of existing sibling docs where a real edge exists, else `[]`.
- `code_rev` — `$HEAD_SHA`. This anchors drift detection to the code the body
  actually describes.
- `updated` — today's date, `YYYY-MM-DD`.

### Drafting `covers`

`covers` decides both when this doc is flagged stale and which diff the fixer sees:

- **Derive globs from the module paths the doc describes.** Start from the concrete
  files you will cite in `## Code pointers` and generalize upward to the directory
  that owns them.
- **Prefer one directory-scoped `**` glob over enumerating files** — `plugins/x/**`
  keeps covering files added later; an enumerated list silently stops covering new
  files, which is the exact drift this plugin exists to catch. Remember `*` stops at
  `/`; write `dir/**` when you mean the whole tree.
- **Overlap needs a note.** Check the `covers` of the docs from Step 1: if two docs
  claim the same file, each doc's `## Overview` MUST say which one is authoritative
  for the shared territory. Without that note, one code change drags both docs into
  the fixer and they can be rewritten in opposite directions on the same push.

## Step 3: Write the doc

Write the file under `$ROOT/$WIKI_REL/` and fill the body sections (Overview, Key
decisions, Code pointers, Related) with real content — verify each code pointer
exists, and keep pointers inside the `covers` globs (a pointer outside them means the
globs are wrong). Update the frontmatter `related` of any existing doc that should
now link back, so the new page does not start life as an orphan.

## Step 4: Regenerate the INDEX and validate

```bash
python3 "$SK/atlas_index.py" --write --root "$ROOT"
python3 "$SK/atlas_index.py" --validate --root "$ROOT"
```

`--validate` exits 1 on any problem. Fix every `error:` line (schema break, broken
`related` link) before finishing; an `advisory:` orphan line for the new doc means no
sibling links to it yet — add a reciprocal `related` edge where one genuinely exists.

## Step 5: Report

Show the new doc's path, its frontmatter, any overlap notes added, and the INDEX
update. Remind the user the doc is drift-checked from `code_rev` onward: from the
next covered change, `/atlas:sync` (or the push hook, if enabled) will keep it
current.
