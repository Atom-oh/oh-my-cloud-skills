---
description: Create a new operational runbook from template in docs/runbooks/
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git log *), Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-bilingual.py *)
argument-hint: Runbook name (e.g. deploy-production, database-migration, incident-response)
---

# Add Runbook

Write a bilingual runbook at `docs/runbooks/<kebab-name>.md` that an operator can follow verbatim, often under pressure during an incident. Name: $ARGUMENTS (ask for one if it is empty). If that file already exists, offer to update it instead of creating a second runbook for the same task.

## Inputs

- The current conversation, root `CLAUDE.md`, `docs/architecture.md`, and the existing runbooks in `docs/runbooks/`.
- Where the real commands live: `scripts/`, `Makefile`, `package.json` scripts, CI workflows (for example `.github/workflows/`), IaC files (Dockerfile, `cdk.json`, `template.yaml`, `*.tf`), and `git log --oneline -20` for recent operational changes.
- Structure: the project's `docs/runbooks/.template.md` if it exists, because the team may have customized it; otherwise the `## Runbook Template` section of `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffolder/references/docs-templates.md`.
- Layout, tone, and formatting: `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffolder/references/writing-style-guide.md`. It applies even when the project's template is English-only; in that case mirror the template's sections in the Korean half.

If a plugin file cannot be read (for example because `${CLAUDE_PLUGIN_ROOT}` was not substituted), stop and say so instead of writing from memory; a document written from memory is the drift ADR-003 exists to prevent.

## Rules

- Derive every command from the repo. Where you cannot, write `# TODO(verify): <what is needed>` in its place instead of a plausible guess, because an operator will run these commands verbatim.
- Ask the user once, in one round (see Asking), only for what the repo cannot tell you, usually prerequisites such as permissions and access, and rollback details.
- Include only the phases the task needs; the template's phase count is an example, not a quota.

## Asking

Ask with the AskUserQuestion tool when it is available: its answers arrive in this turn, so the `allowed-tools` above still cover the writes and the check that follow, while a chat reply starts a new turn and the grant clears when the user sends it. Give each open item (the name when none was given, update or create when the file exists, each missing prerequisite or rollback detail) its own question, up to 4 questions per call; offer what the repo suggests as options, and let the user type anything else in the free-text "Other" answer. Without the tool, ask in one chat message.

## Output contract

- Every command is copy-paste ready, in a fenced block with a language tag. A placeholder is allowed only when it is named and explained next to the command (for example `<env>`: `staging` or `production`).
- Each step that changes state is followed by a command or observable result that shows it worked. The Verification section checks the end state.
- Rollback is executable at the command level. If a step cannot be undone, say so at that step, before the operator runs it.
- Notes records `Last verified: not yet run (written <today, YYYY-MM-DD>)` in the English half and `최종 검증일: 아직 실행 안 함 (<today, YYYY-MM-DD> 작성)` in the Korean half. Write a verified date only when the user says they ran the procedure, because an operator reads that line as proof the commands work.
- Also update, only when it applies:
  - Root `CLAUDE.md`, when it lists runbooks: add one line for this runbook.
  - `docs/architecture.md`, when it has an Operations section: link the runbook there in both halves.

## Check

Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-bilingual.py <new runbook file>` (add `docs/architecture.md` if you edited it) and fix what it reports until it exits 0. The script checks layout, not meaning, so also confirm that each Korean paragraph says what its English counterpart says and that both halves carry the same commands. If python3 or the script is unavailable, say "checker unavailable" in the report.

## Report

The file path, the other files you changed, which commands came from the user rather than from the repo, and every `TODO(verify)` left for the user to resolve.
