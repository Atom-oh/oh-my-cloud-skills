---
description: Distill CLAUDE.md into AGENTS.md for Codex and wire Kiro steering to CLAUDE.md
allowed-tools: Read, Write, Glob, Grep, Bash(python3:*)
argument-hint: "[project-dir]  (defaults to the repo root / cwd)"
---

# co-agent: sync-context

Give the external AI panel project context so it reviews with the repo's own
conventions. Keep `CLAUDE.md` canonical, distill only the Codex context file, and
connect Kiro to the same canonical file through steering:

| AI | Reads | sync-context action |
|----|-------|---------------------|
| Kiro | `.kiro/steering/project-context.md` → `#[[file:CLAUDE.md]]` | create/update bridge |
| Codex | `AGENTS.md` (~32 KiB cap) | distill + validate |
| Agy / legacy Gemini fallback | prompt-supplied context during fan-out | no repo context file |

**DISTILL — never copy `CLAUDE.md` verbatim.** These context channels degrade on a dumped copy
(Codex truncates at the cap, and Kiro steering should point at the canonical file instead
of maintaining a second copy). Produce one lean, review-oriented core and write it to
**`AGENTS.md` only**.

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
   `<marker>` → `> You are Codex, an external reviewer — project context below.`
   → the distilled core.
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

   #[[file:CLAUDE.md]]
   ```
   If the file already exists with other hand-written content and does not already contain
   `#[[file:CLAUDE.md]]`, leave it and report that it needs manual merge.
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
