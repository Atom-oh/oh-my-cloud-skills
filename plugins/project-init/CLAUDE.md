# project-init Plugin

## Role
Core plugin providing project structure initialization, documentation quality scoring, and auto-sync workflows. This is the primary plugin in the marketplace.

## Key Files
- `.claude-plugin/plugin.json` - Plugin manifest (name, version, description)
- `commands/init-project.md` - Main initialization command (project scaffolding, all generated files)
- `commands/add-reference-doc.md` - Implementation reference doc skeleton generator (per-layer)
- `commands/sync-docs.md` - Documentation synchronization
- `commands/add-adr.md` - ADR creation
- `commands/add-module.md` - Module scaffolding
- `commands/add-runbook.md` - Runbook creation
- `commands/generate-readme.md` - Bilingual README.md generation/update
- `commands/generate-changelog.md` - Bilingual CHANGELOG.md generation/update
- `commands/health-check.md` - Project validation
- `commands/pr-autofix.md` - PR review feedback auto-fix (AI + human review polling)
- `agents/doc-sync-checker.md` - Documentation sync analysis agent
- `skills/project-scaffolder/SKILL.md` - Scaffolding skill definition
- `skills/project-scaffolder/references/` - 12 template files for code generation (includes shared writing-style-guide)
- `skills/pr-autofix/SKILL.md` - PR auto-fix skill (AI review + human review loop)
- `skills/pr-autofix/references/pr-review-workflow.yml` - Reference CI workflow for AI code review
- `skills/decision-reconcile/SKILL.md` - ADR contradiction detection + superseding-ADR drafting (diverse multi-agent panel)
- `skills/decision-reconcile/scripts/collect_adrs.py` - Parse `docs/decisions/ADR-*.md` → JSON + deterministic inconsistency pre-checks
- `skills/decision-reconcile/references/contradiction-taxonomy.md` - C1–C6 contradiction categories, per-agent review lenses, severity, resolution patterns

## Upstream
- **Source**: `git@github.com:whchoi98/project-init.git` · **Author**: whchoi98 · 마켓플레이스 통일 버전으로 정렬.
- 로컬 분기 파일(plugin.json·CLAUDE.md·doc-sync-checker[sonnet 티어]·pr-autofix·decision-reconcile 등)은 rsync 동기화에서 **반드시 제외**.

> **동기화 명령·제외 목록·로컬 분기 사유 상세**: **`references/upstream-sync.md`** — upstream sync 수행 시 참조.

## Rules
- All commands must have clear step-by-step instructions
- Reference templates contain code in fenced blocks for extraction
- The init-project command adapts based on detected project type
- Version in plugin.json must be updated for each release (마켓플레이스 통일 버전 유지)
- Bilingual support (Korean/English) in user-facing templates
- Upstream sync 시 plugin.json은 로컬 버전 유지 (agents/skills/commands 배열 + 마켓플레이스 버전)
