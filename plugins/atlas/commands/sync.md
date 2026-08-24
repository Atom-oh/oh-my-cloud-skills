---
description: On-demand atlas drift check and auto-fix — detect docs whose covered code changed since their code_rev, preview what would be sent, then run the confined headless fix
allowed-tools: Read, Bash
argument-hint: Optional explicit diff range A..B (default — auto-resolved from upstream or trunk merge-base)
---

# atlas: sync

Run the push-time drift pipeline by hand: find atlas docs whose covered code changed
since their `code_rev`, then fix them with one confined headless `claude -p` call per
stale doc. Same machinery the pre-push hook uses, minus the push.

Resolve paths first:

```bash
SK="${CLAUDE_PLUGIN_ROOT}/skills/atlas/scripts"
ROOT="$(git rev-parse --show-toplevel)"
```

`--root` on both scripts below takes the REPOSITORY root, never the wiki directory
(the scripts derive the wiki directory from config themselves — passing the wiki
directory would make them look for docs nested one level too deep). Always pass
`--root "$ROOT"`.

## First run on an unsynced repo: `--dry-run`

**`--dry-run` should be the first thing you run on a repo you have not synced
before.** It spawns no `claude` process and writes nothing (it still runs a few
read-only `git` calls to compute the preview) — it is how you find out what WOULD be
sent (which docs, which matched files, which diff range) before anything is sent
anywhere:

```bash
python3 "$SK/atlas_sync.py" --dry-run --root "$ROOT"
```

Read the output with the user before proceeding. If a doc's matched-file list looks
wrong — files it should not cover, or a suspiciously huge range from a stale
`code_rev` — fix the doc's `covers` or `code_rev` first rather than syncing against
the wrong scope.

## Detect only

For the read-only view (no fixer involved at any point), use the drift detector
directly:

```bash
python3 "$SK/atlas_drift.py" --root "$ROOT"
python3 "$SK/atlas_drift.py" --range "$ARGUMENTS" --root "$ROOT"   # explicit range
python3 "$SK/atlas_drift.py" --json --root "$ROOT"                 # one packet per line
```

One `stale:` line per drifted doc. **Read stderr too**: a `skipping <doc> — ...`
advisory means that doc has a schema error, empty `covers`, or an unresolvable
`code_rev` — it can never be drift-checked until repaired, and staying silent about
that is how docs rot invisibly. Surface every advisory to the user.

## Fix

```bash
python3 "$SK/atlas_sync.py" --root "$ROOT"
python3 "$SK/atlas_sync.py" --range "$ARGUMENTS" --root "$ROOT"    # explicit range
```

Each stale doc gets its own headless call that may only edit that one doc — a
`PreToolUse` hook confines its `Edit` calls to the wiki directory by realpath, and a
post-hoc scan reverts anything that somehow still landed outside it. Afterwards the script — not
the model — advances `code_rev` to HEAD, regenerates `INDEX.md`, and creates a
`docs(atlas): sync ...` commit. Sending covered-file diff content to Anthropic is
inherent to the fix step; that is why the preview above comes first.

## Range semantics

`--range` overrides which ref counts as "now" for every doc's staleness check — only
the RIGHT-hand side of `A..B`/`A...B` is used. Each doc always uses its OWN `code_rev`
as the left bound, never a shared one: gating on a shared range used to mean a covered
file that changed during an earlier push the hook never saw (hook was off, or a
terminal push this `PreToolUse` hook can't see at all) could go permanently unreviewed
once some OTHER covered file later advanced the same doc's anchor to `HEAD`.

- No `--range`: literal `HEAD`. (An informational auto-resolution against
  `@{upstream}...HEAD` or a trunk merge-base still runs and prints an advisory if it
  can't resolve, but it is no longer load-bearing — every doc is checked against
  `HEAD` either way.)
- `$ARGUMENTS`, when given, is passed as the explicit `--range A..B`; only `B` is used.

## Report

Summarize per doc: synced, skipped (with the stderr reason), or failed. Both scripts
always exit 0 (fail-open, by design — they also run inside a push gate), so judge the
outcome from the output, never from the exit code. If the sync committed, show the
commit subject so the user knows a commit now precedes their next push.
