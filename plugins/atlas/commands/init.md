---
description: Bootstrap an atlas wiki — scan the repo, propose a doc set for approval, write frontmatter-filled skeletons, regenerate INDEX.md, then offer push-time auto-sync
allowed-tools: Read, Write, Glob, Grep, Bash, AskUserQuestion
---

# atlas: init

Bootstrap the per-topic doc wiki for this repository: a small set of frontmatter-filled
pages a future session can select from `INDEX.md` alone, each drift-checkable from day
one. Nothing is written until the user approves the proposed doc set in Step 2.

Resolve paths once, up front, and reuse them in every step:

```bash
SK="${CLAUDE_PLUGIN_ROOT}/skills/atlas/scripts"
ROOT="$(git rev-parse --show-toplevel)"
WIKI_REL="$(python3 "$SK/atlas_config.py" atlas-root --root "$ROOT")"
HEAD_SHA="$(git rev-parse --short HEAD)"
```

`--root` on every atlas script takes the REPOSITORY root, never the wiki directory —
the wiki directory is derived internally as `<repo>/<config value>`, so passing
`$ROOT/$WIKI_REL` would join the config value on twice and write every skeleton into a
nested wiki-inside-the-wiki. Always pass `--root "$ROOT"`.

## Step 1: Scan the repository

Build a picture of what needs documenting. Using Glob/Grep (read-only — no writes yet):

1. **Modules** — top-level source directories and any nested directory with its own
   manifest (`package.json`, `pyproject.toml`, `plugin.json`, `Cargo.toml`, ...).
2. **Languages** — file extensions per module, to phrase descriptions accurately.
3. **Existing `CLAUDE.md` files** — each one marks a module someone already considered
   worth explaining; its content seeds that module's doc description.
4. **Existing `docs/`** — material that can be referenced (not duplicated) by the wiki.
5. Check whether `$ROOT/$WIKI_REL` already has docs: run
   `python3 "$SK/atlas_index.py" --list --root "$ROOT"` and, if it prints any doc
   lines, propose only ADDITIONS — never overwrite an existing doc.

## Step 2: Propose a doc set and get approval

Draft one candidate entry per topic worth a page: a filename, a one-sentence
`description`, and 1-3 `covers` globs derived from the module paths that doc will
describe (prefer one directory-scoped `**` glob per module — see
`${CLAUDE_PLUGIN_ROOT}/skills/atlas/references/atlas-templates.md`, "How covers is
drafted"). Keep the set small enough that `INDEX.md` stays readable in one pass — a
page per genuine topic, not per file.

Present the full list via `AskUserQuestion` — filename, description, and covers globs
for every proposed doc — with options to approve all, trim the list, or cancel.
**Write nothing until the user has approved a set.**

## Step 3: Write the skeletons

For each approved doc, copy the doc skeleton from
`${CLAUDE_PLUGIN_ROOT}/skills/atlas/references/atlas-templates.md` and pre-fill the
frontmatter:

- `title` — the topic, phrased the way a teammate would say it.
- `description` — the drafted sentence from Step 2; load-bearing words first (the
  INDEX generator truncates long descriptions — `references/frontmatter-schema.md`).
- `covers` — the approved globs, repo-root-relative, block-list form.
- `related` — sibling filenames from this same batch where a real edge exists;
  otherwise `related: []`.
- `code_rev` — `$HEAD_SHA`, the sha the body is being written against.
- `updated` — today's date, `YYYY-MM-DD`.

Write each file under `$ROOT/$WIKI_REL/`, then fill the body sections (Overview, Key
decisions, Code pointers, Related) with real content from the Step 1 scan — a skeleton
with empty sections documents nothing.

## Step 4: Regenerate INDEX.md and validate

```bash
python3 "$SK/atlas_index.py" --write --root "$ROOT"
python3 "$SK/atlas_index.py" --validate --root "$ROOT"
```

`--validate` exits 1 on any problem. Fix `error:` lines (schema breaks, broken
`related` links) before finishing — a schema-broken doc is skipped by drift detection
forever. `advisory:` orphan lines are acceptable for a fresh wiki; mention them to the
user rather than forcing edges that do not exist.

## Step 5: Offer push-time auto-sync

State this plainly to the user BEFORE asking — the offer itself is the consent moment,
so do not bury it:

> Enabling `sync.on_push` means that just before every `git push`, the diff of the
> code files your atlas docs cover is sent to Anthropic through a headless `claude -p`
> call, so drifted docs can be auto-fixed and committed into that same push. It is off
> by default; enabling it is the consent for that per-push data egress.

Then ask via `AskUserQuestion` (enable / leave off). Only on an explicit yes:

```bash
python3 "$SK/atlas_config.py" set sync on_push on --root "$ROOT"
```

If declined, note that `/atlas:sync` runs the same fix on demand, and that
`sync.on_push` can be enabled later via `/atlas:configure`.

## Step 6: Report

Summarize: docs written (path + description), the INDEX location, validation outcome,
and whether push-time sync was enabled. Suggest committing the new wiki directory as
the natural next step (do not commit it yourself unless asked).
