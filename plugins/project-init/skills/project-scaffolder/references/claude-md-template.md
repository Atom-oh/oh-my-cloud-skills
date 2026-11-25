# CLAUDE.md Template

Templates for the root and module `CLAUDE.md`. Replace each `<!-- ... -->` placeholder from detection or the user's answers; one you cannot fill becomes `<!-- TODO: ... -->` and goes in the init summary.

Every line must pass the prune test and `## CLAUDE.md Anti-Patterns` in `SKILL.md`. Keep the root file short enough to read at a glance, because it loads in every session.

Keep all six root `##` headings (`Overview`, `Tech Stack`, `Project Structure`, `Conventions`, `Key Commands`, `Auto-Sync Rules`) even when a section is short, because the generated structure tests and `/sync-docs` look for them.

---

## Root CLAUDE.md Template

Path: `CLAUDE.md`

Keep the first-line HTML comment for later editors; Claude Code strips it before loading CLAUDE.md, so it costs no context.

````markdown
<!-- Prune test: keep a line only if removing it would cause Claude to make a mistake. Leave out what Claude can read from the code or config. -->

# Project Context

## Overview
<!-- One or two sentences: what the project does and for whom. -->

## Tech Stack
<!-- Languages, frameworks, and tools that change how code is written here. Skip what the manifest already makes obvious. -->

## Project Structure
```text
<!-- Top-level directories whose purpose is not obvious from the name, a few words each. -->
```

## Conventions
<!-- Rules that differ from the language or framework defaults, each with its reason. -->

## Key Commands
```bash
<!-- build, test, lint/typecheck, and run commands, copy-paste ready -->
```

Verify a change: `<!-- the fastest command that proves a change works: unit tests, lint, or typecheck -->`
Run it before reporting a change done. A syntax-only check, or a command that failed to start, does not count; if it cannot run here, say which check you skipped and why.

---

## Auto-Sync Rules

Claude applies these while working; nothing runs automatically. Docs change in the same commit as the code they describe, so a reviewer sees both.

- Update `docs/architecture.md` when components or data flows change.
- Add an ADR (`/add-adr`) when a choice would be expensive to reverse or a future reader would ask why it was made.
- Add a module `CLAUDE.md` (`/add-module`) only for a module with rules or gotchas the code does not show.
- Write a runbook (`/add-runbook`) for a procedure someone will repeat under pressure: a deploy, a rollback, a migration.
- Update this file when a command, convention, or structure it describes changes.

### ADR Numbering
Find the highest number in `docs/decisions/ADR-*.md` and increment by 1.
Format: `ADR-NNN-concise-title.md`
````

The `## Implementation References` section between `<!-- AUTO-MANAGED:references -->` markers comes from `/init-project` and `/add-reference-doc`, not from this template.

---

## Module CLAUDE.md Template

Path: `<module>/CLAUDE.md`

When to create one: `## Module CLAUDE.md Coverage` in `SKILL.md`.

```markdown
# <Module Name>

## Role
<!-- One or two lines: what this module owns, and what it deliberately does not. -->

## Invariants and gotchas
<!-- Rules the code does not make obvious, each with its reason, e.g. "Handlers never query the DB directly; go through repo/ so every write runs in one transaction." -->

## Entry point
<!-- The one file to read first, if it is not obvious from the names. -->
```
