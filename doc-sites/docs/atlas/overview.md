---
sidebar_position: 1
title: "Atlas"
---
# Atlas

Maintain a per-topic repository wiki with git-based drift detection and optional push-time synchronization.

## Wiki model {#wiki-model}

Pages under the configured wiki root (default `docs/atlas/`) declare `description`, `covers`, `related`, `code_rev`, and `updated`. `INDEX.md` helps the host select relevant topics without loading every document.

Drift detection compares each page's own `code_rev` with HEAD for files matching its `covers` globs. `*` stops at a path separator; `**` spans directories. Invalid schema, empty coverage, and unresolved revisions produce advisories rather than false “fresh” results.

## Synchronization {#synchronization}

`atlas_drift.py --json` lists stale pages and their covered-file ranges without a
model call or Claude CLI. The optional `atlas_sync.py --dry-run` repair preview
requires `claude` on PATH even though it invokes no model and writes no files;
see [Local checks](commands.md#local-checks). On-demand repair can use the current host. The optional push-time path uses a confined Claude CLI fixer, advances revision anchors, regenerates the index, and commits repaired wiki pages.

`sync.on_push` defaults off. Enabling it authorizes sending covered-file diffs to the configured Claude service. The hook observes supported shell-tool push calls; it does not intercept pushes typed directly in a terminal. Hook failures are advisory and fail open. `atlas_index.py --validate` is the explicit schema/graph validation gate.

[Atlas contract](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/atlas/skills/atlas/SKILL.md) · [Defaults](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/atlas/skills/atlas/atlas.defaults.json)
