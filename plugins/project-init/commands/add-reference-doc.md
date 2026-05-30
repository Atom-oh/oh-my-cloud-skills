---
description: Add an implementation reference doc skeleton for one or more layers under docs/reference/
allowed-tools: Read, Write, Edit, Bash(ls:*), Bash(find:*), Bash(grep:*), Bash(git config:*), Bash(date:*), Glob
argument-hint: One or more layer names — infrastructure, data, api, iac, frontend, ui, security, agent-llm
---

# Add Implementation Reference Doc

Append a skeleton implementation reference document for the given layer(s) under `docs/reference/`.

## Step 1: Validate Layer Names

Target layers: $ARGUMENTS

Valid layers (enum):
- `infrastructure`
- `data`
- `api`
- `iac`
- `frontend`
- `ui`
- `security`
- `agent-llm`

If any argument is not in the enum, abort with: `Unknown layer "<name>". Valid: infrastructure, data, api, iac, frontend, ui, security, agent-llm`.

## Step 2: Ensure Target Directory

```bash
mkdir -p docs/reference
```

## Step 3: For Each Layer — Generate Skeleton

For every requested layer:

1. **Check existence** at `docs/reference/{layer}.md`:
   - If exists: prompt the user `overwrite / skip / abort`. On `skip` skip this layer; on `abort` abort the whole command.
2. **Extract skeleton** from `plugins/project-init/skills/project-scaffolder/references/reference-doc-template.md` — read the fenced block under `## Layer: {layer}`.
3. **Substitute variables**:
   - `{{COMPONENTS_TABLE}}` → empty table row `| <!-- TODO: component --> | <!-- path --> | <!-- purpose --> |`
   - `{{CODE_POINTERS_AUTO}}` → `<!-- TODO: add 3-7 code pointers -->`
4. **Write** to `docs/reference/{layer}.md`.

## Step 4: Regenerate `docs/reference/INDEX.md`

Read the current directory listing of `docs/reference/*.md` (excluding INDEX.md itself).
Rewrite the file with this structure:

```markdown
# Implementation Reference Index / 구현 참조 인덱스

[![English](https://img.shields.io/badge/Language-English-blue)](#english)
[![한국어](https://img.shields.io/badge/Language-한국어-red)](#korean)

<a id="english"></a>
## English

Layer-by-layer implementation guides. Each file follows the same 5-section
structure (Overview / Components / Key Decisions / Code Pointers / Cross-references).

<!-- AUTO-MANAGED:index -->
| Layer | File | Status |
|---|---|---|
| Infrastructure | [infrastructure.md](infrastructure.md) | present |
| Data | — | not applicable |
| API | — | not applicable |
| IaC | — | not applicable |
| Frontend | — | not applicable |
| UI | — | not applicable |
| Security | — | not applicable |
| Agent · LLM | — | not applicable |
<!-- /AUTO-MANAGED -->

Last updated: <today's date in YYYY-MM-DD> (managed by /init-project, /add-reference-doc, /sync-docs)

<a id="korean"></a>
## 한국어
(same structure, Korean section headings)
```

The table cells reflect actual file presence. Files outside the AUTO-MANAGED region must be preserved if the file already existed.

## Step 5: Update Root CLAUDE.md AUTO-MANAGED Region

Locate the block between `<!-- AUTO-MANAGED:references -->` and `<!-- /AUTO-MANAGED -->` in the root `CLAUDE.md`. If absent, append a new `## Implementation References` section near the end:

```markdown
## Implementation References
<!-- AUTO-MANAGED:references -->
Layer-by-layer implementation guides in `docs/reference/`. See [INDEX](docs/reference/INDEX.md).
- <link line per present layer>
<!-- /AUTO-MANAGED -->
```

Rewrite the content between the markers based on the current INDEX status.

## Step 6: Report

Output a summary:
```
Added reference docs:
  ✓ docs/reference/<layer>.md  (skeleton)
  ...
Updated:
  - docs/reference/INDEX.md
  - CLAUDE.md (## Implementation References)

Next: fill in the TODO sections in each new file.
```
