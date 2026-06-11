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
- **Source**: `git@github.com:whchoi98/project-init.git` (path: `plugins/project-init/`)
- **Author**: whchoi98
- **Sync**: 마켓플레이스 추가 시 version 2.0.0 → 1.3.0으로 정렬, plugin.json에 agents/skills/commands 배열 보강

```bash
# Upstream 변경사항 확인
git clone --depth 1 https://github.com/whchoi98/project-init.git /tmp/project-init-upstream
diff -rq /tmp/project-init-upstream/plugins/project-init/ plugins/project-init/ \
  --exclude=plugin.json --exclude=CLAUDE.md --exclude=SKILL.md --exclude=readme-template.md \
  --exclude=doc-sync-checker.md

# Upstream에서 업데이트 가져오기 — 로컬에서 분기한 파일은 반드시 제외할 것.
# (blanket rsync는 이들을 덮어써 로컬 커스터마이징/4.8 수정/모델 티어를 날림)
rsync -av \
  --exclude='.claude-plugin/plugin.json' \
  --exclude='CLAUDE.md' \
  --exclude='agents/doc-sync-checker.md' \
  --exclude='skills/project-scaffolder/SKILL.md' \
  --exclude='skills/project-scaffolder/references/readme-template.md' \
  /tmp/project-init-upstream/plugins/project-init/ plugins/project-init/
```

**로컬 분기 파일(동기화 제외 대상):**
- `.claude-plugin/plugin.json` — 로컬에서 agents/skills/commands 배열 + version 보강
- `CLAUDE.md` — 로컬 Upstream/version 섹션 보유
- `skills/project-scaffolder/SKILL.md` — 로컬 전용 `writing-style-guide.md` 참조 라인 보유
- `skills/project-scaffolder/references/readme-template.md` — 로컬은 `--`, upstream은 `—` 사용
- `skills/pr-autofix/**`, `commands/pr-autofix.md` — 로컬 전용 기능(upstream에 없음, rsync가 건드리지 않음). 모델 ID는 Opus 4.8로 로컬 고정.
- `skills/decision-reconcile/**` — 로컬 전용 기능(upstream에 없음, rsync가 건드리지 않음). ADR 모순 검출·번복 ADR 초안. 멀티 에이전트 패널(Claude 모델 티어 + 선택적 co-agent CLI)로 ADR-vs-ADR/ADR-vs-현실 모순 검토.
- `agents/doc-sync-checker.md` — **모델 티어를 로컬에서 `sonnet`으로 하향** (upstream은 `opus`). 기계적 doc 상태 비교/채점이라 opus는 과도하고 `/sync-docs`마다 호출되어 비용 큼. 가급적 upstream(whchoi98/project-init)에도 반영 권장. **tools**: read-only Bash 스코핑으로 제한 — `Bash(find:*), Bash(git log:*), Bash(ls:*), Bash(wc:*)`. upstream은 `wc`를 빠뜨려(본문 line 109 `wc -l`가 채점에 쓰임) 자기 불일치가 있으므로 로컬은 `Bash(wc:*)`를 추가함. upstream에도 `wc` 추가 권장.

## Rules
- All commands must have clear step-by-step instructions
- Reference templates contain code in fenced blocks for extraction
- The init-project command adapts based on detected project type
- Version in plugin.json must be updated for each release (마켓플레이스 통일 버전 유지)
- Bilingual support (Korean/English) in user-facing templates
- Upstream sync 시 plugin.json은 로컬 버전 유지 (agents/skills/commands 배열 + 마켓플레이스 버전)
