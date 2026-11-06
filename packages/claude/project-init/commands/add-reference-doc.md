---
description: Add an implementation reference doc skeleton for one or more layers under docs/reference/
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-bilingual.py *)
argument-hint: One or more layer names — infrastructure, data, api, iac, frontend, ui, security, agent-llm
---

# Add Implementation Reference Doc

Create `docs/reference/<layer>.md` for each requested layer, then update `docs/reference/INDEX.md` and the `## Implementation References` block in the root `CLAUDE.md`. /init-project and /sync-docs write and parse the same files, so follow the template's formats exactly.

Layers: $ARGUMENTS

## Inputs

- `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffolder/references/reference-doc-template.md`, read in full: its header says how to fill the placeholders, and its `## Layer: <layer>`, `## INDEX.md`, and `## Root CLAUDE.md Block` sections hold the output formats. If the file cannot be read, stop and say so instead of writing from memory.
- The repo, for the paths that fill `{{COMPONENTS_TABLE}}` and `{{CODE_POINTERS_AUTO}}`.

## Asking

Ask with the AskUserQuestion tool when it is available, so the `allowed-tools` above still cover the writes and the check that follow. Each call holds at most 4 questions of 4 options:
- Layer choice (no argument): `multiSelect` questions of at most four layers each, covering all eight.
- Conflicts: one question per existing file, with the options `overwrite`, `skip`, and `abort`.

Without the tool, ask everything in one chat message.

## Steps

Write nothing until every argument is valid and every conflict is resolved.

1. **Validate.** Valid layers: `infrastructure`, `data`, `api`, `iac`, `frontend`, `ui`, `security`, `agent-llm`. If any argument is not one of them, stop with exactly: `Unknown layer "<name>". Valid: infrastructure, data, api, iac, frontend, ui, security, agent-llm`.
2. **Resolve conflicts.** Ask about every requested layer whose `docs/reference/<layer>.md` exists, all in one round. `skip` keeps the file; `abort` ends the command with nothing written.
3. **Write the layer files.** For each remaining layer, write the fenced block under `## Layer: <layer>` (without the fence) to `docs/reference/<layer>.md`, with the placeholders replaced as the template header specifies. Write creates `docs/reference/` if it is missing.
4. **Refresh `docs/reference/INDEX.md`** from the `## INDEX.md` section: one row per layer, from the layer files that exist now, keeping each `declined` (`제외`) row whose layer still has no file. If the file has an `<!-- AUTO-MANAGED:index -->` region in both language halves, replace only those regions; otherwise write the whole file from the template and carry over any user text outside the markers.
5. **Refresh the root `CLAUDE.md`** from the `## Root CLAUDE.md Block` section: replace the lines between `<!-- AUTO-MANAGED:references -->` and `<!-- /AUTO-MANAGED -->`, or append the section near the end of the file if the markers are absent.

## Check

Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-bilingual.py docs/reference/INDEX.md docs/reference/<layer>.md` on every file you wrote and fix what it reports until it exits 0. If python3 or the script is unavailable, say "checker unavailable" in the report.

## Report

```text
Added reference docs:
  ✓ docs/reference/<layer>.md  (skeleton)
  - docs/reference/<layer>.md  (existing, kept)
Updated:
  - docs/reference/INDEX.md
  - CLAUDE.md (## Implementation References)

Next: fill in the TODO sections in each new file.
```
