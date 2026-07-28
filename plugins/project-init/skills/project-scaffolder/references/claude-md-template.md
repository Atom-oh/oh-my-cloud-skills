# CLAUDE.md Template

Use this template when creating the root `CLAUDE.md` for a new project.

Replace placeholders (`<!-- ... -->`) with actual project information.

---

```markdown
# Project Context

## Overview
<!-- Project name and brief description -->

## Tech Stack
<!-- List languages, frameworks, libraries, and tools -->

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
<!-- Coding conventions, naming rules, etc. -->

## Key Commands
<!-- Build, test, deploy commands -->

---

## Auto-Sync Rules

Rules below are applied automatically after Plan mode exit and on major code changes.

### Post-Plan Mode Actions
After exiting Plan mode (`/plan`), before starting implementation:

1. **Architecture decision made** -> Update `docs/architecture.md`
2. **Technical choice/trade-off made** -> Create `docs/decisions/ADR-NNN-title.md`
3. **New module added** -> Create `CLAUDE.md` in that module directory
4. **Operational procedure defined** -> Create runbook in `docs/runbooks/`
5. **Changes needed in this file** -> Update relevant sections above

### Code Change Sync Rules
- New directory under `src/` -> Must create `CLAUDE.md` alongside
- API endpoint added/changed -> Update `src/api/CLAUDE.md`
- DB schema/model changed -> Update `src/persistence/CLAUDE.md`
- Infrastructure changed -> Update `docs/architecture.md` Infrastructure section

### ADR Numbering
Find the highest number in `docs/decisions/ADR-*.md` and increment by 1.
Format: `ADR-NNN-concise-title.md`
```

---

## Module CLAUDE.md Template

Use this for `src/<module>/CLAUDE.md` files:

```markdown
# <Module Name> Module

## Role
<!-- Module responsibilities and scope -->

## Key Files
<!-- List important files in this module -->

## Rules
<!-- Module-specific rules and conventions -->
```

## API Module CLAUDE.md

```markdown
# API Module

## Role
<!-- API layer responsibilities and scope -->

## Endpoints
<!-- List major API endpoints -->

## Rules
<!-- API-specific rules and conventions -->
```

## Persistence Module CLAUDE.md

```markdown
# Persistence Module

## Role
<!-- Data persistence layer responsibilities and scope -->

## Data Model
<!-- Key entities and relationships -->

## Rules
<!-- Persistence-specific rules and conventions -->
```
