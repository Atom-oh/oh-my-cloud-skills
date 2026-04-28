# project-init Plugin

## Role
Core plugin providing project structure initialization, documentation quality scoring, and auto-sync workflows. This is the primary plugin in the marketplace.

## Key Files
- `.claude-plugin/plugin.json` - Plugin manifest (name, version, description)
- `commands/init-project.md` - Main initialization command (10K+ lines)
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

## Upstream
- **Source**: `git@github.com:whchoi98/project-init.git` (path: `plugins/project-init/`)
- **Author**: whchoi98
- **Sync**: 마켓플레이스 추가 시 version 2.0.0 → 1.3.0으로 정렬, plugin.json에 agents/skills/commands 배열 보강

```bash
# Upstream 변경사항 확인
git clone --depth 1 git@github.com:whchoi98/project-init.git /tmp/project-init-upstream
diff -rq /tmp/project-init-upstream/plugins/project-init/ plugins/project-init/ \
  --exclude=plugin.json  # plugin.json은 로컬에서 보강했으므로 제외

# Upstream에서 업데이트 가져오기 (plugin.json 제외)
rsync -av --exclude='.claude-plugin/plugin.json' \
  /tmp/project-init-upstream/plugins/project-init/ plugins/project-init/
```

## Rules
- All commands must have clear step-by-step instructions
- Reference templates contain code in fenced blocks for extraction
- The init-project command adapts based on detected project type
- Version in plugin.json must be updated for each release (마켓플레이스 통일 버전 유지)
- Bilingual support (Korean/English) in user-facing templates
- Upstream sync 시 plugin.json은 로컬 버전 유지 (agents/skills/commands 배열 + 마켓플레이스 버전)
