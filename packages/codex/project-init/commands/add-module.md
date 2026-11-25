---
description: Add a new module directory with CLAUDE.md and update architecture docs
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(bash -n .claude/hooks/check-doc-sync.sh), Bash(bash .claude/hooks/check-doc-sync.sh *), Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-bilingual.py *)
argument-hint: Module path (e.g. src/auth, src/notifications)
---

# Add Module

Register the module at $ARGUMENTS: give it a `CLAUDE.md` when it needs one, and add it to `docs/architecture.md`, the root `CLAUDE.md`, and the doc-sync hook.

## Inputs

- The path, the conversation, and any code already in that directory.
- Root `CLAUDE.md`, `docs/architecture.md`, and `.claude/hooks/check-doc-sync.sh`.
- `## Module CLAUDE.md Template` in `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffolder/references/claude-md-template.md` (the format) and `## Module CLAUDE.md Coverage` in `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffolder/SKILL.md` (when a module needs its own file). If either file cannot be read, stop and say so instead of writing from memory.

## Rules

- The path belongs under a source root: one in the hook's `SOURCE_ROOTS`, or, without the hook, a fallback root from `## Module CLAUDE.md Coverage`. Otherwise confirm the location with the user before creating anything.
- Write `<module_path>/CLAUDE.md` when no CLAUDE.md covers the module, because a new module's role (what it owns and what it does not) is not in its code yet. When an ancestor covers it, write one only for conventions, invariants, or gotchas the ancestor does not describe; otherwise write none and name the covering file in the report.
- Write only what is true now, from the user or the code, and leave out sections you cannot fill, because an empty heading teaches nothing and still loads whenever Claude works there.
- Ask only what the path, the code, and the conversation leave unclear (the path when none was given, the location, the responsibility), in one round with the AskUserQuestion tool when it is available, so the `allowed-tools` above still cover the writes that follow. Offer what you found as options; without the tool, ask in one chat message.
- Do not create an empty directory: writing the CLAUDE.md creates it, and a module without one appears with its first file.

## Also update

- `docs/architecture.md`: add the module to the Components section under its layer, in both language halves. Add it to a diagram only where its connections are known, and name any guesses in the report.
- Root `CLAUDE.md`: add the module to the Project Structure section.
- `.claude/hooks/check-doc-sync.sh`: add the module path's first segment to the space-separated `SOURCE_ROOTS` if it is missing, because the hook checks only files under those roots.

## Check

Without `.claude/hooks/check-doc-sync.sh`, skip the hook checks and say so in the report.

- If you edited the hook, run `bash -n .claude/hooks/check-doc-sync.sh`.
- Run `bash .claude/hooks/check-doc-sync.sh <module_path>/probe.txt` (the hook takes the path as an argument; the file need not exist). It must not report a missing CLAUDE.md for the module; other reminders are fine. An ancestor's CLAUDE.md also silences it.
- If you edited `docs/architecture.md`, run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-bilingual.py docs/architecture.md` and fix what it reports. If python3 or the script is unavailable, say "checker unavailable" in the report.

## Report

One line per file created or changed, the covering CLAUDE.md if you wrote none, and anything left for the user.
