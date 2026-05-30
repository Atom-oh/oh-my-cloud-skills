---
description: Synchronize all project documentation with current code state
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(find:*), Bash(git log:*), Bash(git tag:*), Bash(git describe:*), Bash(git remote:*), Bash(ls:*), Agent
---

# Sync Docs

Synchronize project documentation with the current code state.

## Context

- Project structure: !`find . -not -path './.git/*' -not -path './node_modules/*' -not -path './__pycache__/*' -not -path './.venv/*' -type f | head -100`
- Recent commits: !`git log --oneline -20 2>/dev/null || echo "Not a git repository"`
- Existing CLAUDE.md files: !`find . -name "CLAUDE.md" -not -path './.git/*' 2>/dev/null`

## Phase 0: Read Shared Style Guide

Read the shared writing style guide that applies to all generated documents:

```
Read file: skills/project-scaffolder/references/writing-style-guide.md
```

All documents created or updated in this sync process must follow the bilingual structure, formatting, and style rules defined in the writing style guide.

## Phase 1: Gap Analysis (Subagent)

Launch the `doc-sync-checker` agent to analyze documentation gaps in parallel. This provides a structured report of:
- Missing module CLAUDE.md files
- Stale documents
- Suggested ADRs
- Quality scores for each CLAUDE.md

Use this report to prioritize updates in the following steps.

### Phase 1.5: Implementation References

Re-run the layer detection from `/init-project` Step 4.5 (signal matrix).
For each detected layer, check `docs/reference/{layer}.md`:

- **Missing file** for a detected layer → output:
  `❌ {layer}.md missing — run /add-reference-doc {layer}`

- **Existing file with Code Pointers** → for each path-like string under the
  `### 4. Code Pointers` section that matches the regex
  `[A-Za-z0-9_./-]+\.[A-Za-z0-9]+` with at least one `/`, verify the path
  exists on disk. Report:
  `⚠ {layer}.md: Code Pointer "<path>" not found in repo`

- **TODO marker count** → report only (no grade):
  `ℹ {layer}.md: 5 TODO markers remaining`

- **INDEX.md drift** → regenerate the table inside
  `<!-- AUTO-MANAGED:index -->` markers from the current
  `docs/reference/*.md` listing. If contents differed, report:
  `✓ INDEX.md auto-corrected (was out of sync)`

This block reports and may rewrite **only** the AUTO-MANAGED region in
INDEX.md. Layer files themselves are never modified by `/sync-docs`.

## Phase 2: CLAUDE.md Quality Assessment

For each CLAUDE.md file found, evaluate quality against these criteria:

| Criterion | Weight | Check |
|-----------|--------|-------|
| Commands/workflows documented | 20 | Are build/test/deploy commands present and correct? |
| Architecture clarity | 20 | Can Claude understand the codebase structure? |
| Non-obvious patterns | 15 | Are gotchas and quirks documented? |
| Conciseness | 15 | No verbose explanations or obvious info? |
| Currency | 15 | Does it reflect current codebase state? |
| Actionability | 15 | Are instructions executable, not vague? |

**Quality Grades:**
- **A (90-100)**: Comprehensive, current, actionable
- **B (70-89)**: Good coverage, minor gaps
- **C (50-69)**: Basic info, missing key sections
- **D (30-49)**: Sparse or outdated
- **F (0-29)**: Missing or severely outdated

Output a quality report before making changes:

```
## CLAUDE.md Quality Report

### Summary
- Files found: X
- Average score: XX/100
- Files needing update: X

### File-by-File Assessment

#### ./CLAUDE.md (Project Root)
**Score: XX/100 (Grade: X)**

| Criterion | Score | Notes |
|-----------|-------|-------|
| Commands/workflows | X/20 | ... |
| Architecture clarity | X/20 | ... |
| Non-obvious patterns | X/15 | ... |
| Conciseness | X/15 | ... |
| Currency | X/15 | ... |
| Actionability | X/15 | ... |
```

## Phase 3: Root CLAUDE.md Sync

Read the root `CLAUDE.md` and update:
- **Overview** - Match current project purpose
- **Tech Stack** - Match actual dependencies (package.json, pyproject.toml, go.mod, etc.)
- **Project Structure** - Match actual directory tree
- **Conventions** - Match observed code patterns
- **Key Commands** - Match actual build/test/deploy commands

Verify commands are copy-paste ready by checking they reference actual scripts/files.

## Phase 4: Architecture Doc Sync

Read `docs/architecture.md` and update all sections:

- **System Overview** - Reflect current system design and tech stack
- **Components (by Layer)** - Add new components, remove deleted ones. Organize by architectural layers (Ingestion, Storage, Processing, Query, Presentation, Observability, Security, AI/ML). Detect layers from source directories and IaC files.
- **Full Architecture Diagram** - Regenerate ASCII box diagram if components changed. Use `┌─┐│└─┘▶▼` characters. Verify all components in the diagram still exist in code.
- **Data Flow Summary** - Update the arrow-chain flow if data path changed
- **Infrastructure Tables** - If IaC files exist (terraform/, cdk/), update module/construct tables
- **Key Design Decisions** - Add new decisions from recent ADRs, flag decisions that may be outdated
- **Operations** - Update runbook cross-references

If `docs/architecture.md` uses bilingual format (Korean/English), update both sections consistently.

## Phase 5: Module CLAUDE.md Audit

Detect the main source directory (src/, app/, lib/, cmd/, etc.):

```bash
ls -d src/ app/ lib/ cmd/ pkg/ internal/ components/ pages/ 2>/dev/null
```

Scan all directories under the source root:

```bash
find <source_dir> -type d -not -path './.git/*' 2>/dev/null
```

For each directory:
- If `CLAUDE.md` is missing, create one with module name, role, and key files
- If `CLAUDE.md` exists, verify it matches current files and update if needed
- Score each module CLAUDE.md using the quality criteria

## Phase 6: ADR Audit

Review recent commits for architecture-relevant changes:

```bash
git log --oneline -20 2>/dev/null
```

Check if significant decisions are documented:
- New dependencies added (check git diff for package.json/pyproject.toml changes)
- API design changes
- Database schema changes
- Infrastructure changes

If undocumented decisions found, suggest creating new ADRs. Determine the next ADR number:

```bash
find docs/decisions -name 'ADR-*.md' -not -name '.template.md' 2>/dev/null | sort -t'-' -k2 -n | tail -1
```

Review existing ADRs for freshness:
- Flag ADRs in "Proposed" status older than 30 days -> suggest accepting or withdrawing
- Flag ADRs referencing technologies no longer in use -> suggest deprecating
- Score: count of current ADRs vs estimated decisions from git history

## Phase 7: Runbook Audit

Check runbook coverage against project characteristics:

```bash
ls docs/runbooks/*.md 2>/dev/null
find docs/runbooks -name '*.md' -not -name '.template.md' 2>/dev/null
```

Assess operational coverage:
- **Deployment**: Does the project have deployment config (Dockerfile, CDK, SAM, Terraform, CI/CD)? If yes, check for a deployment runbook.
- **Database**: Does the project have migrations or database config? If yes, check for a database migration runbook.
- **Incident Response**: Does the project have monitoring/alerting? If yes, check for an incident response runbook.
- **Environment Setup**: Does the project have multiple environments? If yes, check for environment setup runbook.

For each existing runbook:
- Verify commands are still copy-paste ready (check referenced scripts/paths exist)
- Check last modified date vs recent code changes
- Flag runbooks referencing removed files or changed paths

## Phase 8: README.md Sync

Read [references/readme-template.md](../skills/project-scaffolder/references/readme-template.md) for structure and generation rules.

If `README.md` exists, read it and update the following:

1. **Badges** - Update version badge to match current manifest version, verify license badge
2. **Overview** - Sync with current `CLAUDE.md` project description
3. **Features** - Add newly detected features, remove references to removed functionality
4. **Prerequisites** - Update runtime versions from manifest `engines` or `.tool-versions`
5. **Installation** - Verify install commands are still correct
6. **Project Structure** - Regenerate directory tree to match actual layout
7. **Testing** - Update test commands if build system changed
8. **Language sync** - Ensure English and Korean sections contain identical information

```bash
# Detect current version
ls package.json pyproject.toml Cargo.toml go.mod 2>/dev/null
git describe --tags --abbrev=0 2>/dev/null
```

If `README.md` does not exist, generate a new bilingual README following the template. Auto-detect project information and ask the user for missing required fields.

**Validation checklist:**
- [ ] Language toggle uses HTML `<a><img></a>` with `#english` and `#korean` anchors
- [ ] Explicit `<a id="english">` and `<a id="korean">` tags before each language heading
- [ ] Both language sections have identical structure
- [ ] Code blocks specify the language
- [ ] No emojis in the document
- [ ] Version and license badges reflect current values

## Phase 9: CHANGELOG.md Sync

Read [references/changelog-template.md](../skills/project-scaffolder/references/changelog-template.md) for structure and generation rules.

If `CHANGELOG.md` exists, read it and update:

1. **Unreleased section** - Analyze commits since the last documented version and add new entries

```bash
# Find last documented version
git tag --sort=-v:refname 2>/dev/null | head -5

# Get commits since last tag
git log --oneline $(git describe --tags --abbrev=0 2>/dev/null)...HEAD 2>/dev/null
```

2. **Categorize** new commits into standard types (Added, Changed, Fixed, etc.)
3. **Write** bilingual entries (English imperative, Korean 명사형 종결)
4. **Preserve** all existing released version entries unchanged
5. **Language sync** - Ensure both language sections have identical version entries

If `CHANGELOG.md` does not exist, generate a new bilingual CHANGELOG from full git tag history following the template.

**Validation checklist:**
- [ ] `[Unreleased]` section present in both language sections
- [ ] Versions in reverse chronological order
- [ ] Category headings in English in both sections
- [ ] Reference links correctly formatted
- [ ] Previously released versions unchanged

## Phase 10: Report

Present a comprehensive summary:

```
## Sync Report

### Quality Scores (Before -> After)
- ./CLAUDE.md: D (35) -> B (78)
- ./src/api/CLAUDE.md: F (0) -> C (55) [NEW]
- ./src/auth/CLAUDE.md: C (52) -> B (72)

### Changes Made
- Files created: X
- Files updated: X

### Suggested ADRs
- ADR-003: Adopted Redis for session caching (from commit abc1234)

### README.md
- Status: Created / Updated / No changes
- Sections synced: X
- Version badge: vX.Y.Z

### CHANGELOG.md
- Status: Created / Updated / No changes
- New entries added: X (Added: X, Changed: X, Fixed: X)
- Versions documented: X

### Remaining Gaps
- src/utils/ has no CLAUDE.md (directory contains only helper functions)
```
