# Atlas frontmatter schema

Every doc under the atlas root (default `docs/atlas/`) opens with a YAML frontmatter
block. The parser (`atlas_index.py`) is stdlib-only — no pyyaml — and accepts exactly
three value shapes: `key: scalar`, an inline flow list (`["a", "b"]` or the unquoted
`[a, b]`), and a block list of `  - item` lines. Matching surrounding single or double
quotes are stripped from every scalar and every list item. Anything fancier — anchors,
multi-line strings, nested maps — is not parsed. Keep the frontmatter flat.

The canonical example:

```yaml
---
title: co-agent hybrid gate
description: How the hybrid gate fans out finders, triages, and closes verify rounds.
covers: ["plugins/co-agent/skills/co-agent/references/hybrid-gate.md", "plugins/co-agent/**/scripts/gate_*.py"]
related: [consensus-pipeline.md, pr-autofix-loop.md]
code_rev: 566db30
updated: 2026-08-19
---
```

The block-list form is equivalent for `covers` and `related`:

```yaml
covers:
  - plugins/co-agent/**/scripts/gate_*.py
  - "plugins/co-agent/skills/co-agent/references/hybrid-gate.md"
```

One failure mode dominates everything below, so name it up front: a doc with any schema
error is **skipped** by drift detection with a one-line stderr advisory — never silently
treated as fresh, and never handed to the fixer unanchored. Get a required field wrong
and the doc does not break loudly; it becomes permanently uncheckable, and the advisory
in the hook's stderr is the only symptom. Read that stderr.

## title

String. **Required.** The doc's human name; the INDEX table and `/atlas:graph` use it.
If missing: the doc lands in `errors`, drift detection skips it (advisory on stderr),
and `atlas_index.py --validate` exits 1 — which also blocks the sync commit, because
`atlas_sync.py` refuses to commit while validation reports problems.

## description

String. **Required.** This is the field a consuming session judges relevance by
*without reading the body* — the SessionStart hook tells the host to pick docs from
`INDEX.md` by `description` and `covers` alone. If missing, same skip-and-block behavior
as `title`. If merely vague ("misc notes"), nothing mechanical breaks, but the doc is
never selected and might as well not exist. Descriptions over 80 characters are
truncated with `...` in the INDEX table, so put the load-bearing words first.

## covers

List of repo-root-relative glob strings. **Required, and must be non-empty.** This is
the doc's territory: a doc is stale iff a file matching one of these globs changed
between its `code_rev` and `HEAD`. If missing, empty, or not a list: schema error, skip
with advisory — the doc can never be checked. If too narrow: covered code changes
without the glob matching, and the doc drifts silently, which is the exact disease this
plugin exists to cure. If too broad, or overlapping another doc's globs: unrelated
changes drag the doc into the fixer, and two docs claiming one file can be rewritten in
opposite directions on the same push. See `atlas-templates.md` for drafting guidance.

## related

List of sibling doc relpaths (e.g. `consensus-pipeline.md`, relative to the atlas root).
**Optional** — but if present it must be a list, or the doc gets a schema error. A
`related` entry that does not resolve to another doc under the same root is reported by
`atlas_index.py --validate` (exit 1) and blocks the sync commit, so a broken link cannot
quietly ship. A doc no other doc points at is reported as an orphan advisory — the graph
is only navigable if the edges are real.

## code_rev

String, a resolvable git rev (short sha is fine). **Required.** The drift anchor and the
whole mechanic — see the last section. If empty or unresolvable (rebased away, garbage
collected, typo): the doc is skipped with a stderr advisory, never treated as fresh, and
never sent to the fixer unanchored — an unanchored fix has no diff to work from. The
**sync script rewrites this field itself** after a successful fix; do not hand-maintain
it beyond the initial value at doc creation.

## updated

ISO date string (`YYYY-MM-DD`). **Optional.** Purely informational for humans scanning
the INDEX; the sync script rewrites it alongside `code_rev`. A wrong value misleads a
reader about freshness but has no mechanical effect — staleness is computed from
`code_rev`, never from this date.

## Glob semantics

`covers` globs are matched by a hand-rolled matcher, deliberately not `fnmatch`:
`fnmatch`'s `*` crosses `/`, so `docs/atlas/*.md` would match `docs/atlas/sub/deep.md`
and a doc would claim territory it does not cover. Here, `*` stops at a path separator
and `**` spans them (`**/` also matches zero directories). All globs are anchored: they
must match the whole repo-relative path, not a substring.

The rows below are **verified** — they were executed against the real matcher (15/15
cases passed) before this doc was written:

| Glob | Path | Matches |
|---|---|---|
| `docs/atlas/*.md` | `docs/atlas/x.md` | yes |
| `docs/atlas/*.md` | `docs/atlas/sub/deep.md` | **no** — `*` does not cross `/` |
| `plugins/co-agent/**/scripts/gate_*.py` | `plugins/co-agent/scripts/gate_x.py` | yes — `**` matches zero directories |
| `plugins/co-agent/**/scripts/gate_*.py` | `plugins/co-agent/a/b/scripts/gate_deep.py` | yes |
| `plugins/co-agent/**/scripts/gate_*.py` | `plugins/co-agent/skills/co-agent/scripts/other.py` | no |
| `src/한글/**` | `src/한글/mod.py` | yes — the matcher itself handles non-ASCII bytes fine; the regression this row guards against is upstream, in how the changed-file list reaches the matcher (see below) |

Regression guard: `atlas_drift.py:changed_files()` calls `git diff` with `-c
core.quotePath=false -z`, not a bare `--name-only`. Git's default
`core.quotePath=true` octal-escapes and double-quotes any path byte outside
printable ASCII (`src/한글/mod.py` comes back as `"src/\355\225\234\352\270\200/mod.py"`),
which the matcher's literal-escaping (`re.escape`) then never matches — a covered
non-ASCII path would silently never be flagged stale, even though `glob_match` itself
is fine (row above). If this file's changed-file computation is ever reworked, keep
`core.quotePath=false` (or use `-z` with NUL-split output some other way).

## Why code_rev is the anchor

Staleness is a purely mechanical predicate: a doc is stale iff a file matching one of
its `covers` globs changed between its `code_rev` and `HEAD`. That definition buys two
properties the rest of the design leans on:

- **Detection is cheap.** It is O(changed files × docs) glob matching over
  `git diff --name-only` output — **no LLM pass at all**. That is what makes running it
  on every push tolerable; an LLM reading the wiki to guess what is stale would be slow,
  metered, and wrong in both directions.
- **The fix is idempotent.** After a successful, confined edit, the sync writes
  `code_rev: HEAD` (and `updated:`) into the doc's frontmatter. The next push resolves
  `code_rev == HEAD`, finds no covered change in that empty range, and does nothing.
  Without that write there would be no fixed point, and every push would re-fix the
  same doc forever.

The **script** writes that value, never the model. The headless fixer is explicitly told
not to touch the frontmatter, and `atlas_sync.py` performs the `code_rev`/`updated`
rewrite itself by line-wise substitution inside the frontmatter block. Idempotence must
not depend on a language model transcribing a sha correctly — hash transcription is
exactly the kind of detail models get subtly wrong, and a mistranscribed anchor either
re-flags the doc every push or points it at a rev that never existed.
