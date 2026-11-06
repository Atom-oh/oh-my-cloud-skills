---
description: Generate or update a bilingual (English/Korean) README.md following GitHub open-source best practices
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git remote get-url *), Bash(git describe --tags *), Bash(git tag --list *), Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-bilingual.py *)
argument-hint: "Optional: path to target directory (default: project root)"
---

# Generate README

Create or update the bilingual (English first, then Korean) `README.md` in $ARGUMENTS, or in the project root when no path is given, so a newcomer learns what the project does, how to install and use it, and where to go next.

## Inputs

- `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffolder/references/readme-template.md`: the top layout and badges, the Section Structure table (order and conditions), the Section Guidelines, the Auto-Detection Sources table (where each field comes from), and the Update Rules.
- `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffolder/references/writing-style-guide.md`: bilingual layout, tone, formatting, and Mermaid diagram rules.
- The project: the sources listed in Auto-Detection Sources, root `CLAUDE.md`, `LICENSE`, `.env.example`, CI config, test directories, `docs/architecture.md`, `git remote get-url origin`, `git describe --tags --abbrev=0`, and the existing README.

If a plugin file cannot be read (for example because `${CLAUDE_PLUGIN_ROOT}` was not substituted), stop and say so instead of writing from memory; a document written from memory is the drift ADR-003 exists to prevent.

## Rules

- Detect before asking. Ask once, in one round, only for what detection cannot give, usually the Korean one-line description, the maintainer name and GitHub handle, and an optional demo image. Use the AskUserQuestion tool when it is available: its answers arrive in this turn, so the `allowed-tools` above still cover the write and the check that follow, while a chat reply starts a new turn and the grant clears when the user sends it. Give each field its own question (up to 4 per call), offer detected candidates or "Leave a TODO" as options, and let the user type the value in the free-text "Other" answer. Without the tool, ask in one chat message. Anything left unanswered becomes `<!-- TODO: ... -->`.
- Section content follows the template's Section Guidelines. Two of them depend on the project: the Architecture flowchart comes from `docs/architecture.md` when it exists, and Contributing describes the fork flow only for a public GitHub repository.
- Updating an existing README: follow the template's Update Rules. The user's own prose is the reason to update rather than regenerate, so keep it unless the code shows it is wrong, and say what you changed.
- Length: write what a newcomer needs to install and use the project, and stop. Omit optional sections whose condition is not met instead of filling them with generic text.

## Output contract

- Every section the Section Structure table marks Required is present, in that order, in both halves; conditional sections appear only when their condition holds.
- License and version badges carry the project's real values (template Top Layout); the language badges, anchors, and separators follow the writing-style-guide layout.

## Check

Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-bilingual.py <target>/README.md` and fix what it reports in the text this run wrote until the only remaining issues, if any, are in the user's own prose that existed before this run. Leave such an issue as it is and list it in the report as pre-existing, with its line, because rewriting the user's prose to satisfy a layout check is not what an update is for. The script checks layout, not meaning, so also confirm that each Korean paragraph says what its English counterpart says. If python3 or the script is unavailable, say "checker unavailable" in the report.

## Report

The path, whether it was created or updated, which fields were detected and which the user supplied, what an update changed in existing prose, every TODO left in the file, and each pre-existing checker issue left in place (or "checker unavailable").
