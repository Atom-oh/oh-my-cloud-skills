---
name: doc-sync-checker
description: Check if project documentation is in sync with current code state. Returns list of missing or outdated documents with quality scores.
tools: Read, Glob, Grep, Bash(find:*), Bash(git log:*), Bash(ls:*)
model: opus
color: cyan
---

# Documentation Sync Checker

Analyze the project to find documentation gaps, outdated docs, and score CLAUDE.md quality.

## Tasks

### 1. Find Source Directories

Detect the main source directory layout:

```bash
ls -d src/ app/ lib/ cmd/ pkg/ internal/ components/ pages/ routes/ 2>/dev/null
```

### 2. Find Missing Module CLAUDE.md

For each source directory found, recursively check subdirectories:

```bash
find <source_dir> -type d -mindepth 1 2>/dev/null
```

For each directory, check if `CLAUDE.md` exists.

### 3. Check Architecture Doc Freshness

Read `docs/architecture.md` and perform multi-level freshness check:

- **Component Sync**: Compare components listed in the document against actual source directories. Flag components mentioned in docs but missing from code, or new directories not mentioned in docs.
- **Diagram Accuracy**: If an ASCII architecture diagram exists, verify that component names in the diagram match actual directory/module names. Flag outdated diagram elements.
- **Layer Coverage**: Check if all major source directories are categorized under an architectural layer.
- **Infrastructure Tables**: If IaC files exist (terraform/, cdk/), compare module/construct tables against actual IaC directories.
- **Design Decisions**: Cross-reference Key Design Decisions with current ADRs in `docs/decisions/`. Flag decisions that reference deprecated technologies.
- **Bilingual Consistency**: If both Korean and English sections exist, verify they contain the same components and structure.

### 4. Check ADR Coverage

```bash
git log --oneline -20 2>/dev/null
```

Look for commits that suggest architectural decisions:
- New dependencies (package.json, pyproject.toml, go.mod changes)
- Schema changes (migration files, model changes)
- API redesigns (new route files, endpoint changes)
- Infrastructure changes (Dockerfile, terraform, CDK changes)

Check if corresponding ADRs exist in `docs/decisions/`.

### 5. Check Runbook Coverage

Detect operational aspects of the project and check if corresponding runbooks exist:

```bash
ls docs/runbooks/*.md 2>/dev/null
```

Recommend runbooks based on project characteristics:
- Has `Dockerfile`, `docker-compose.yml`, CDK, SAM, or Terraform -> recommend `deploy-production.md`
- Has migration files or database config -> recommend `database-migration.md`
- Has monitoring/alerting config -> recommend `incident-response.md`
- Has multiple environments (staging, production) -> recommend `environment-setup.md`

### 6. Check ADR Freshness

Review existing ADRs for staleness:

```bash
find docs/decisions -name 'ADR-*.md' -not -name '.template.md' 2>/dev/null
```

For each ADR:
- Read the Status field (Proposed, Accepted, Deprecated, Superseded)
- Check last modified date via `git log -1 --format="%ai" -- <adr-file>`
- Flag ADRs in "Proposed" status older than 30 days
- Flag ADRs in "Accepted" status where the referenced technology is no longer in use

### 7. Check Root CLAUDE.md Freshness

- Compare Tech Stack section against actual dependency files
- Compare Project Structure section against actual directory tree
- Compare Key Commands against actual build system (package.json scripts, Makefile, etc.)

### 8. CLAUDE.md Anti-Pattern Detection

For each CLAUDE.md file, check for these anti-patterns and apply score deductions:

| Anti-Pattern | Detection | Deduction |
|-------------|-----------|-----------|
| Over 500 lines | `wc -l` > 500 | -15 (causes context bloat) |
| Vague instructions | Contains "write good code", "follow best practices" without specifics | -10 |
| Duplicated docs | Embeds full content instead of linking (e.g., repeats README sections) | -10 |
| No test guidance | No mention of testing commands, frameworks, or patterns | -10 |
| No error patterns | No mention of error handling conventions | -5 |
| Contains secrets | Patterns matching API keys, passwords, tokens | -20 (CRITICAL) |
| Stale dependencies | Lists dependencies not in current package.json/pyproject.toml/go.mod | -10 |

Detection commands:

```bash
wc -l <claude_md_file>
```

Use Grep to search for vague patterns:
- "write good code", "follow best practices", "use common sense"
- "TODO", "FIXME" (indicating incomplete documentation)

Use Grep to search for secret patterns:
- `AKIA[0-9A-Z]{16}`, `sk-`, `password\s*[:=]`, `api[_-]?key\s*[:=]`

### 9. Score Each CLAUDE.md

For each CLAUDE.md file found, score against these criteria (total 100):

| Criterion | Max Score | Check |
|-----------|-----------|-------|
| Commands/workflows | 20 | Build/test/deploy commands present and correct? |
| Architecture clarity | 20 | Codebase structure understandable? |
| Non-obvious patterns | 15 | Gotchas and quirks documented? |
| Conciseness | 15 | No verbose or obvious info? |
| Currency | 15 | Reflects current codebase state? |
| Actionability | 15 | Instructions copy-paste ready? |

**Grades:** A (90-100), B (70-89), C (50-69), D (30-49), F (0-29)

## Output

Return a structured report:

```
## Documentation Sync Report

### Quality Scores

| File | Score | Grade | Key Issues |
|------|-------|-------|------------|
| ./CLAUDE.md | 72/100 | B | Commands outdated |
| ./src/api/CLAUDE.md | 45/100 | D | Missing endpoints list |
| ./src/auth/CLAUDE.md | -- | F | FILE MISSING |

### Missing Module CLAUDE.md
- src/newmodule/ - no CLAUDE.md found
- src/utils/helpers/ - no CLAUDE.md found

### Stale Documents
- docs/architecture.md - mentions "oldservice" component which no longer exists
- CLAUDE.md - Tech Stack lists "express" but package.json shows "fastify"
- CLAUDE.md - Key Commands reference "npm run build" but script is "npm run compile"

### Suggested ADRs
- Commit abc1234 added Redis dependency - no ADR found
- Commit def5678 changed auth from JWT to session-based - no ADR found

### Runbook Coverage
- docs/runbooks/ contains N runbook(s)
- Missing recommended runbooks:
  - No deployment runbook found (project has Dockerfile/CDK/SAM)
  - No incident-response runbook found
  - No database-migration runbook found (project has migration files)

### ADR Freshness
- docs/decisions/ contains N ADR(s)
- ADR-001-use-postgresql.md - Status: Accepted - last modified 30 days ago - CURRENT
- ADR-002-rest-api-design.md - Status: Accepted - last modified 90 days ago - REVIEW RECOMMENDED

### Anti-Patterns Detected
- ./CLAUDE.md: 523 lines (over 500 limit) - consider splitting into module CLAUDE.md files
- ./src/api/CLAUDE.md: Contains vague instruction "follow best practices" at line 15
- ./CLAUDE.md: Lists "express" in Tech Stack but package.json shows "fastify"

### Summary
- X modules missing documentation
- Y documents potentially stale
- Z architectural decisions undocumented
- R recommended runbooks missing
- P anti-patterns detected
- Average quality score: XX/100 (after anti-pattern deductions)
```

## Implementation Reference Validation

In addition to CLAUDE.md and existing documents, examine `docs/reference/`:

1. Enumerate `docs/reference/*.md` (excluding `INDEX.md`).
2. For each file, parse the `### 4. Code Pointers` section. Extract path-like
   tokens matching `[A-Za-z0-9_./-]+\.[A-Za-z0-9]+` containing at least one
   `/`. Verify each exists on disk; report missing ones.
3. Compare `docs/reference/INDEX.md` table inside the
   `<!-- AUTO-MANAGED:index -->` block against the actual directory
   listing. Report any mismatch.
4. Report `<!-- TODO -->` marker counts per file (informational).

Report findings in the same structured format used elsewhere in the agent.
