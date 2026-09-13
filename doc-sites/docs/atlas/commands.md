---
sidebar_position: 1
title: "Atlas commands"
---
# Atlas commands

| Workflow | Purpose |
| --- | --- |
| `/atlas:init` | Propose the topic set, write approved pages, and build INDEX.md |
| `/atlas:add-doc` | Add one topic with coverage metadata and refresh the index |
| `/atlas:sync` | Detect drift and repair selected stale pages |
| `/atlas:graph` | Show related-page edges, orphans, and broken references |
| `/atlas:configure` | Inspect wiki root and synchronization settings |

Codex exposes corresponding generated skills. The unattended Claude fixer is a separate option from host-native repair.

## Local checks {#local-checks}

Run from the repository root containing the wiki; script paths below refer to this marketplace checkout:

```bash
python3 plugins/atlas/skills/atlas/scripts/atlas_drift.py --json --root .
python3 plugins/atlas/skills/atlas/scripts/atlas_index.py --validate --root .
```

These checks do not require Claude CLI. The optional fixer checks for `claude` on
PATH before parsing arguments, even with `--dry-run`. With Claude CLI installed,
preview its repair plan without invoking a model or writing files:

```bash
python3 plugins/atlas/skills/atlas/scripts/atlas_sync.py --dry-run --root .
```

For these scripts, `--root` means the repository root, not the wiki directory. Each document retains its own revision anchor. An explicit range changes the comparison's right-hand revision rather than replacing every document's left-hand anchor.

Schema errors, unresolved revisions, local edits, timeouts, or confinement failures must be reported. Do not mistake the push hook's fail-open behavior for validated documentation freshness.
