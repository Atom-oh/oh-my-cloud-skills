---
description: Synchronize all project documentation with current code state
allowed-tools: Read, Write, Edit, Glob, Grep, Agent, Bash(find *), Bash(ls *), Bash(git log *), Bash(git diff *), Bash(git tag *), Bash(git describe *), Bash(git remote *), Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-bilingual.py *)
---

# Sync Docs

Bring the project's documentation in line with the code as it is now: one audit finds what is missing or stale, you fix it per document type, run the bilingual check on what you wrote, and report quality before and after. The audit report is the single record of what is wrong in the documents it covers, which is all but README.md and CHANGELOG.md. Do not re-scan, re-score, or re-check what it covered, because a second pass doubles the cost and can score one file twice; reading a file to edit it is part of applying.

## Context

- Project structure: !`find . -not -path './.git/*' -not -path './node_modules/*' -not -path './__pycache__/*' -not -path './.venv/*' -type f | head -100`
- Recent commits: !`git log --oneline -20 2>/dev/null || echo "Not a git repository"`
- Latest tag: !`git describe --tags --abbrev=0 2>/dev/null || echo "no tags"`
- Existing CLAUDE.md files: !`find . -name "CLAUDE.md" -not -path './.git/*' -not -path '*/node_modules/*' 2>/dev/null`
- Documentation files: !`find . -maxdepth 4 -name '*.md' \( -path './docs/*' -o -path './README.md' -o -path './CHANGELOG.md' \) 2>/dev/null | head -100`
- Source roots: !`grep -h '^SOURCE_ROOTS=' .claude/hooks/check-doc-sync.sh 2>/dev/null || find . -maxdepth 1 -type d \( -name src -o -name app -o -name lib -o -name cmd -o -name pkg -o -name internal -o -name packages \) 2>/dev/null`

## Inputs

Read these before writing anything. If a file cannot be read, stop and say so instead of writing from memory.

- `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffolder/references/writing-style-guide.md`: every document you create or update follows it (ADR-003).
- `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffolder/SKILL.md`, sections `## CLAUDE.md Quality Criteria`, `## CLAUDE.md Anti-Patterns`, and `## Module CLAUDE.md Coverage`: the rules for CLAUDE.md content and for re-scoring the files you change.
- The template for each document type you touch, named in its Apply section below.

Ask the user at most once, before applying, and only for what the repo cannot answer (for a new README: maintainer name and GitHub username). Use the AskUserQuestion tool when it is available, because its answers arrive in this turn, where the `allowed-tools` above still apply; a chat reply starts a new turn without them. Give each field its own question (up to 4 per call), answered in the free-text "Other" field; without the tool, ask in one chat message. For a skipped field, write `<!-- TODO: ... -->` and list it under Remaining Gaps.

## Audit

Count the CLAUDE.md files and documentation files in Context. With roughly ten or fewer in total, audit inline: run the checks in `${CLAUDE_PLUGIN_ROOT}/agents/doc-sync-checker.md` yourself and produce its report format (its read-only rule covers the audit, not Apply). The Read tool shows that file's plugin-root placeholder unsubstituted; it stands for the plugin directory, the path above without `/agents/doc-sync-checker.md`. With more, launch the `project-init:doc-sync-checker` agent once.

The agent sees none of this conversation, so brief it in one message: the source roots, the documentation file list, the CLAUDE.md list, and the latest tag from Context, plus any focus the user asked for. Its `## Documentation Sync Report` is the audit. If the agent fails or a section of its report is missing, audit only that section inline and say so in the final report.

Show the user the report's Summary section, then apply.

## Apply

Work from the report's findings. For every document type:

- Change what a finding names and keep user-written content, because a sync fixes drift, not style.
- In a bilingual document, make every change in both language halves with the same structure.
- Do not invent content. When the repo does not show a value, write `<!-- TODO: ... -->` and list it under Remaining Gaps.
- CLAUDE.md content must pass `## CLAUDE.md Anti-Patterns`. Leave a finding marked `score only` unapplied and list it under Remaining Gaps, because a section added only for the score makes the file worse.

### Root CLAUDE.md

Fix each stale item in Overview, Tech Stack, Project Structure, Conventions, and Key Commands; every command must name a script, target, or file that exists. Keep the section structure of `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffolder/references/claude-md-template.md`, including Auto-Sync Rules.

### Module CLAUDE.md

For each directory the report names, create a CLAUDE.md only where `## Module CLAUDE.md Coverage` gives it one, from the `## Module CLAUDE.md Template` section of `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffolder/references/claude-md-template.md` with its headings as written, one screen at most. When a module has nothing to say beyond what its code shows, skip it and list it under Remaining Gaps with that reason. Update an existing module CLAUDE.md only for the findings that name it.

### docs/architecture.md

Follow `## Architecture Document` in `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffolder/references/docs-templates.md` and the style guide's Diagram Rules. For each finding:

- Components: add or remove them under their architectural layer.
- Diagrams: when components changed, regenerate the Mermaid `flowchart TB` (one `subgraph` per layer) and the Data Flow Summary `flowchart LR`. Replace any legacy ASCII box diagram with a Mermaid flowchart.
- Infrastructure tables: match the IaC.
- Key Design Decisions: add decisions from new ADRs and mark outdated ones.
- Operations: update the runbook links.

### ADRs

Suggest ADRs; do not create them, because an ADR records trade-offs the code does not show. For each suggestion, give the next number from the report, the source commit, and `/add-adr <title>`. Relay the freshness flags without editing the Status field, because a status change is a decision.

### Runbooks

Recommend each missing runbook with `/add-runbook <name>`, and list the runbooks whose referenced scripts or paths no longer exist. Do not rewrite runbook procedures: a guessed command in a runbook is worse than a flagged one.

### Implementation References

Consume the report's `### Implementation References` section without re-running the layer detection or the Code Pointer checks.

- `❌` missing layer file: do not create it; relay `run /add-reference-doc <layer>`, because `/add-reference-doc` owns the skeleton and asks before overwriting.
- `⚠` Code Pointer not found and the `ℹ` lines (TODO markers, declined layers): report them only. Do not modify the layer files in `docs/reference/`; they are hand-written guides.
- INDEX drift: regenerate only the table inside each `<!-- AUTO-MANAGED:index -->` ... `<!-- /AUTO-MANAGED -->` region of `docs/reference/INDEX.md` from the current `docs/reference/*.md` listing (excluding INDEX.md), as the `## INDEX.md` section of `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffolder/references/reference-doc-template.md` specifies, including its rule for `declined` rows. When a table changed, report `✓ INDEX.md auto-corrected (was out of sync)`. If INDEX.md or its markers are missing, report that instead of creating them.

### README.md

The audit does not cover this file; check it here against `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffolder/references/readme-template.md` (section order and conditions, badge format, `## Update Rules`).

- If README.md exists, apply `## Update Rules` and sync with the code: the version badge (latest tag or manifest version), the license badge, Overview (from CLAUDE.md), Features, Prerequisites (manifest `engines` or `.tool-versions`), Installation and Testing commands that exist, and the Project Structure tree.
- If it does not exist, generate it from the template with the detected information.

### CHANGELOG.md

The audit does not cover this file; check it here against `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffolder/references/changelog-template.md` (`## Update Rules`, `## Change Type Categories`, `## Entry Writing Guidelines`).

- If CHANGELOG.md exists, add `[Unreleased]` entries for the commits after the newest documented version (`git log --oneline <that tag>..HEAD`) that are not listed yet.
- If it does not exist, generate it from the full tag history (`git tag --sort=-v:refname`).

## Check

Run the bundled checker on every bilingual document you created or edited (README.md, CHANGELOG.md, docs/architecture.md, and any other document with `# English` and `# 한국어` halves) except `docs/reference/INDEX.md`, where you rewrote only the table:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-bilingual.py README.md CHANGELOG.md docs/architecture.md
```

It prints one `FILE:LINE: message` line per issue and exits 0 when clean, 1 when issues remain, and 2 on a usage or read error. Fix the issues and run it again. Leave an issue that predates this sync in user content (a released CHANGELOG section, the user's own README prose) and list it under Remaining Gaps as pre-existing. If python3 is unavailable, say in the report that the check did not run.

## Report

Take the Before scores from the audit report. For After, re-score only the files you changed, with the same SKILL.md rubric; an unchanged file shows its Before score once. Keep the report to these sections, one line per item; the values are illustrative.

```
## Sync Report

### Quality Scores (Before -> After)
- ./CLAUDE.md: D (35) -> B (78)
- ./src/api/CLAUDE.md: -- -> C (55) [NEW]
- ./src/auth/CLAUDE.md: C (52) (unchanged)

### Changes Made
- Created: src/api/CLAUDE.md
- Updated: CLAUDE.md, docs/architecture.md, README.md, CHANGELOG.md

### Implementation References
- ❌ api: docs/reference/api.md missing — run /add-reference-doc api
- ⚠ data: Code Pointer "src/db/schema.ts" not found
- ℹ infrastructure: 5 TODO markers
- ✓ INDEX.md auto-corrected (was out of sync)

### Suggested ADRs
- ADR-003: Adopt Redis for session caching (from commit abc1234) - run /add-adr "Adopt Redis for session caching"
- ADR-002-rest-api-design.md: Proposed for 90 days - accept or withdraw

### Runbooks
- Missing: deploy-production.md (Dockerfile present) - run /add-runbook deploy-production
- docs/runbooks/rollback.md: references scripts/rollback.sh, which no longer exists

### README.md
- Status: Created / Updated / No changes
- Sections synced: Overview, Project Structure
- Version badge: vX.Y.Z

### CHANGELOG.md
- Status: Created / Updated / No changes
- New entries added: X (Added: X, Changed: X, Fixed: X)
- Versions documented: X

### Bilingual Check
- README.md, CHANGELOG.md, docs/architecture.md: clean

### Remaining Gaps
- src/utils/ has no CLAUDE.md (helper functions only; nothing the code does not show)
- README.md: <!-- TODO: maintainer --> placeholder
```
