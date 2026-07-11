# CLAUDE.md Template

Use this template when creating the root `CLAUDE.md` for a new project.

Replace placeholders (`<!-- ... -->`) with actual project information.

## Writing rules (for the generator — do NOT copy this section into the output)

`CLAUDE.md` is loaded into **every session** — and consumed by peer AIs too
(co-agent distills it into `AGENTS.md`) — so every line is a recurring context
tax. Modern Claude models (4.6+) follow instructions literally and need far
less scaffolding than the generations this format grew up with. When filling
the template:

- **Facts the model can't infer, not narration.** Record constraints, commands,
  and conventions. Never describe what the code already shows — the model will
  read the code.
- **Context, not commands.** State the constraint plainly ("API responses are
  snake_case"). Skip coercive framing (`CRITICAL`, `MUST`, `반드시`) and
  step-by-step lists where a goal plus a constraint suffices — current models
  over-trigger on both.
- **No example padding.** Few-shot examples in an always-loaded file cost every
  session and add little for current models.
- **Compact forms.** One-liners and tables over prose. When a section outgrows
  a screen, move the detail to `docs/` and link it — `CLAUDE.md` is the index,
  not the manual.
- **Right-sized.** The root file should fit in a few screens. If it can't,
  that's a signal to extract, not to compress the wording into fragments.

---

```markdown
# Project Context

## Overview
<!-- Project name and one-paragraph description — what it is and who it's for -->

## Tech Stack
<!-- Languages, frameworks, key libraries — one line each, versions only if pinned -->

## Project Structure
\```
docs/           - Architecture docs, ADRs, runbooks
.claude/        - Claude settings, hooks, skills
tools/          - Scripts, prompts
src/            - Application source code
  api/          - API layer
  persistence/  - Data persistence layer
\```

## Conventions
<!-- Only conventions the code doesn't make obvious: naming, error handling, commit style -->

## Key Commands
<!-- Build, test, deploy — the exact commands, one line each -->

---

## Auto-Sync Rules

Applied after Plan mode exit and on major code changes.

| Trigger | Action |
|---------|--------|
| Architecture decision made (plan exit) | Update `docs/architecture.md` |
| Technical choice / trade-off made (plan exit) | Create `docs/decisions/ADR-NNN-title.md` — NNN = highest existing + 1 |
| Operational procedure defined | Create runbook in `docs/runbooks/` |
| New module with non-obvious rules or context | Create `CLAUDE.md` in that module directory |
| API endpoint added/changed | Update `src/api/CLAUDE.md` |
| DB schema/model changed | Update `src/persistence/CLAUDE.md` |
| Infrastructure changed | Update `docs/architecture.md` (Infrastructure section) |
| Sections above drift from reality | Update this file |
```

---

## Module CLAUDE.md Template

Use this for `src/<module>/CLAUDE.md` files. Create one **only when the module
has rules or context the code doesn't show** — a module file that would merely
restate the directory name is context tax with no payload; skip pure
pass-through directories.

```markdown
# <Module Name> Module

## Role
<!-- One or two sentences: responsibility and boundary -->

## Key Files
<!-- Only files whose purpose isn't obvious from their name -->

## Rules
<!-- Module-specific constraints the code doesn't enforce by itself -->
```

## API Module CLAUDE.md

```markdown
# API Module

## Role
<!-- API layer responsibility and boundary -->

## Endpoints
<!-- Major endpoints — path and one-line purpose -->

## Rules
<!-- API-specific constraints: auth, versioning, response shape -->
```

## Persistence Module CLAUDE.md

```markdown
# Persistence Module

## Role
<!-- Data persistence layer responsibility and boundary -->

## Data Model
<!-- Key entities and relationships — names and links, not full schemas -->

## Rules
<!-- Persistence-specific constraints: migrations, transactions, access patterns -->
```
