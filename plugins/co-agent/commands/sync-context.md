---
description: Draft and cross-review one concise shared AGENTS.md
allowed-tools: Read, Write, Glob, Grep, Bash(python3:*)
argument-hint: "[project-dir]  (defaults to the repo root / cwd)"
---

# co-agent: sync-context

Maintain one concise, reviewed `AGENTS.md` as the shared project context.

1. Collect the current `AGENTS.md`, applicable repository policies, and verified
   build and test commands. Use legacy `CLAUDE.md` as migration evidence. Preserve
   user-authored rules, and flag unresolved policy conflicts for the user.
2. Have the host and each available opposite-host reviewer independently draft
   a compact replacement from the same secret-free evidence. Use the configured
   CLI defaults and read-only peer adapters. Context drafting is outside Kiro's
   AWS task scope. Use only peers authorized to receive the supplied context.
3. Share the drafts among the participating agents for cross-review. Ask each
   to identify missing rules, unsupported claims, duplicate guidance, and text
   better kept in scoped files. Each agent may propose a shorter replacement.
   If independent review is unavailable, report the blocker and retain the
   current file.
4. The host reconciles evidence-backed feedback into one candidate. Keep the
   complete file, including metadata, at or below 200 lines and 10 KiB (10,240
   UTF-8 bytes). Keep repository-wide constraints and short links to scoped
   guidance. If the candidate exceeds either limit, shorten it before publication.
   Use the first line
   `<!-- generated-by: co-agent · source: reviewed AGENTS.md -->`.
5. Validate the candidate before replacing `AGENTS.md`. Run
   `python3 "${CLAUDE_PLUGIN_ROOT}/skills/co-agent/scripts/check_ai_context.py" <project-dir> --check-candidate <candidate-path>`.
   After publishing, run the same script with only `<project-dir>` to repeat those
   checks and the residual context-file secret audit. Preserve `AGENTS.override.md` and require
   approval before replacing a hand-written `AGENTS.md`. Report reviewers, size,
   material changes and unresolved feedback.
6. Keep Claude's project instructions pointing at the shared `AGENTS.md` and
   keep Kiro's existing `.kiro/steering/project-context.md` bridge using
   `#[[file:AGENTS.md]]`. Preserve hand-written instructions and report any
   bridge that needs a manual merge.
