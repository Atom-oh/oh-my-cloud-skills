---
description: Create a new Architecture Decision Record with auto-numbering
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git log *), Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-bilingual.py *)
argument-hint: ADR title (e.g. "use-postgresql", "adopt-rest-api", "switch-to-typescript")
---

# Add ADR

Record one architecture decision as a bilingual ADR at `docs/decisions/ADR-NNN-<kebab-title>.md`, so a later reader can see what was decided, what else was considered, and what the choice costs. Title: $ARGUMENTS (ask for one if it is empty).

## Inputs

- The current conversation. ADRs usually follow a plan-mode discussion, which often already holds the context, the options, and the reasoning.
- Root `CLAUDE.md`, `docs/architecture.md`, and `git log --oneline -10`.
- Structure: the project's `docs/decisions/.template.md` if it exists, because the team may have customized it; otherwise the `## ADR Template` section of `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffolder/references/docs-templates.md`.
- Layout, tone, and formatting: `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffolder/references/writing-style-guide.md`. It applies even when the project's template is English-only; in that case mirror the template's sections in the Korean half.

If a plugin file cannot be read (for example because `${CLAUDE_PLUGIN_ROOT}` was not substituted), stop and say so instead of writing from memory; a document written from memory is the drift ADR-003 exists to prevent.

## Rules

- Number: the highest existing `docs/decisions/ADR-NNN-*.md` plus one, zero-padded to three digits, or `001` when there is none. The slug is the title in kebab-case.
- Draft from the inputs first. Ask the user once, in one round (see Asking), only for what you cannot find, usually the rejected alternatives and why they lost. Do not invent options or consequences to fill the template, because a fabricated alternative misleads every later reader. Anything still unknown becomes `<!-- TODO: ... -->` in the file.
- Status is Accepted unless the user says the decision is still open (Proposed). Use the template's Korean status names in the Korean half.
- If the decision replaces an earlier ADR, set that ADR's status to Superseded with a link to the new one, in both halves.
- Length: what a later reader needs to follow the trade-off, usually a few short paragraphs or bullets per section.

## Asking

Ask with the AskUserQuestion tool when it is available: its answers arrive in this turn, so the `allowed-tools` above still cover the writes and the check that follow, while a chat reply starts a new turn and the grant clears when the user sends it. Give each open item (the title when none was given, the rejected alternatives, Proposed or Accepted) its own question, up to 4 questions per call; offer what the inputs suggest as options, and let the user type anything else in the free-text "Other" answer. Without the tool, ask in one chat message.

## Output contract

- Context states the problem and the forces behind it, not the chosen solution.
- Options Considered has at least two options, the chosen one included, each with pros and cons.
- Decision names the chosen option and why it won over the others.
- Consequences lists both positive and negative effects; a decision with no downside has not been examined yet.
- References link the issues, PRs, commits, or docs the decision came from, when there are any.
- Also update, only when it applies:
  - `docs/architecture.md`, when the decision changes a component it describes: update that description in both halves and link the ADR.
  - Root `CLAUDE.md`, when it already lists ADRs: add one line naming the ADR and the rule it sets.

## Check

Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-bilingual.py <new ADR file>` (add `docs/architecture.md` if you edited it) and fix what it reports until it exits 0. The script checks layout, not meaning, so also confirm that each Korean paragraph says what its English counterpart says. If python3 or the script is unavailable, say "checker unavailable" in the report.

## Report

The file path and status, the other files you changed, and anything you inferred rather than were told, including each TODO left in the file.
