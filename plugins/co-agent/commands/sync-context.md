---
description: Distill CLAUDE.md into AGENTS.md and wire Kiro steering to the same file (Codex and Agy auto-load it natively; the fan-out also folds it into Agy's context as defense-in-depth)
allowed-tools: Read, Write, Glob, Grep, Bash(python3:*)
argument-hint: "[project-dir]  (defaults to the repo root / cwd)"
---

# co-agent: sync-context

Give the external AI panel project context so it reviews with the repo's own
conventions. Keep `CLAUDE.md` canonical, distill it once into `AGENTS.md`, and have
**Kiro, Codex, and Agy all draw from that one distilled file** instead of each peer
seeing a different (or no) view of the project:

| AI | Reads | sync-context action |
|----|-------|---------------------|
| Kiro | `.kiro/steering/project-context.md` → `#[[file:AGENTS.md]]` | create/update bridge |
| Codex | `AGENTS.md` (~32 KiB cap) | distill + validate |
| Agy | `AGENTS.md` (native, same convention as Codex) | shared with Codex — no separate generation; `ai-cli-adapters.md`'s fan-out also prepends it to Agy's context at call time as defense-in-depth |

**DISTILL — never copy `CLAUDE.md` verbatim.** These context channels degrade on a dumped copy
(Codex truncates at the cap). Produce one lean, review-oriented core and write it to
**`AGENTS.md` only** — Kiro's steering points at this same file rather than the full
`CLAUDE.md`, trading Kiro's previously more-complete view for one that's *consistent*
with what Codex and Agy see.

## Steps

Target dir: `$ARGUMENTS` (default: repo root / cwd). Let `H` be the validator:

```bash
H="${CLAUDE_PLUGIN_ROOT}/skills/co-agent/scripts/check_ai_context.py"
```

1. **Read** `<dir>/CLAUDE.md`. If absent, tell the user there's nothing to sync from and stop.
2. **Distill** a lean core covering only what helps an external reviewer judge a diff:
   - language / stack / runtime
   - build · test · lint commands (copy-paste ready)
   - naming conventions + **banned patterns** (e.g. the global AWS security mandates)
   - architectural boundaries (what may import what; where logic belongs)
   - PR/review expectations: test-coverage bar, error-handling style, security rules
   - a short review checklist + known false-positives to suppress

   Omit: transient project state, version-bump/release mechanics, tool internals, and
   exhaustive file inventories. **Never include secrets** — these files go to third-party AIs.
3. **Marker**: get the generation marker for the current `CLAUDE.md`:
   ```bash
   python3 "$H" <dir> --emit-marker
   ```
4. **Write** `<dir>/AGENTS.md` as:
   `<marker>` → `> You are an external reviewer for this repo — project context below,
   distilled from CLAUDE.md. This file is shared verbatim by Kiro, Codex, and Agy
   (not a per-AI copy).` → the distilled core.
   **Only overwrite a file that is missing or already carries the co-agent marker.** If a
   target exists WITHOUT the marker, it's hand-written (or Codex's `AGENTS.override.md`
   pattern) — leave it and report that you skipped it.
5. **Write Kiro steering bridge** at `<dir>/.kiro/steering/project-context.md`:
   ```markdown
   ---
   name: project-context
   inclusion: always
   ---

   # Project Context

   #[[file:AGENTS.md]]
   ```
   If the file already exists with other hand-written content and does not already contain
   `#[[file:AGENTS.md]]`, leave it and report that it needs manual merge.
6. **Validate**:
   ```bash
   python3 "$H" <dir>
   ```
   This checks the `AGENTS.md` marker, size cap, staleness (claude-md-sha vs current
   `CLAUDE.md`), and runs a secret scan. Fix anything it flags (e.g. distill further if
   over the cap).
7. **Report** which files were written/skipped and the validation result.

> A PostToolUse hook reminds you to re-run this when `CLAUDE.md` changes. This command is
> Mode 4 of the co-agent skill, surfaced as a standalone command for discoverability.
