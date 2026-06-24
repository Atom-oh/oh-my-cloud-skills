---
description: Distill CLAUDE.md into the per-AI context files the panel reads — AGENTS.md (Codex) and GEMINI.md (Gemini)
allowed-tools: Read, Write, Glob, Grep, Bash(python3:*)
argument-hint: "[project-dir]  (defaults to the repo root / cwd)"
---

# co-agent: sync-context

Give the external AI panel project context so it reviews with the repo's own
conventions. Each CLI auto-loads its own native file from the repo root:

| AI | Reads | generate? |
|----|-------|-----------|
| Kiro | `CLAUDE.md` (root + parents) directly | ❌ |
| Codex | `AGENTS.md` (~32 KiB cap) | ✅ |
| Gemini | `GEMINI.md` (kept lean) | ✅ |

**DISTILL — never copy `CLAUDE.md` verbatim.** All three CLIs degrade on a dumped copy
(Codex truncates at the cap, Gemini's context window degrades, Kiro favors ~2000 words).
Produce ONE lean, review-oriented core and write it to **both** `AGENTS.md` and `GEMINI.md`.

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
4. **Write** `<dir>/AGENTS.md` and `<dir>/GEMINI.md`, each as:
   `<marker>` → `> You are <Codex|Gemini>, an external reviewer — project context below.`
   → the distilled core.
   **Only overwrite a file that is missing or already carries the co-agent marker.** If a
   target exists WITHOUT the marker, it's hand-written (or Codex's `AGENTS.override.md`
   pattern) — leave it and report that you skipped it.
5. **Validate**:
   ```bash
   python3 "$H" <dir>
   ```
   This checks the marker, size caps, staleness (claude-md-sha vs current `CLAUDE.md`),
   and runs a secret scan. Fix anything it flags (e.g. distill further if over the cap).
6. **Report** which files were written/skipped and the validation result.

> A PostToolUse hook reminds you to re-run this when `CLAUDE.md` changes. This command is
> Mode 4 of the co-agent skill, surfaced as a standalone command for discoverability.
