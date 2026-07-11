# Upstream Sync (whchoi98/project-init)

> project-init은 upstream 플러그인에서 분기. **동기화할 때만** 이 문서를 참조하세요
> (CLAUDE.md는 출처 요약만 보유).

> **유지 정책 (2026-07 결정): 분기는 origin(이 레포)에서만 유지한다 — upstream으로
> PR을 보내지 않는다.** 아래 분기 목록의 "upstream 반영 권장" 표시는 upstream
> 관리자가 원하면 가져갈 수 있다는 기록일 뿐, 우리 쪽 작업 항목이 아니다.
> 동기화는 단방향(pull-only): upstream 변경 확인 → 제외 목록 적용 rsync.
> 마지막 점검: 2026-07-10, upstream HEAD `d43806e` — 가져올 변경 없음.

- **Source**: `git@github.com:whchoi98/project-init.git` (path: `plugins/project-init/`) · **Author**: whchoi98
- **Sync 정렬**: 마켓플레이스 추가 시 version 2.0.0 → 마켓플레이스 통일 버전으로 정렬, plugin.json에 agents/skills/commands 배열 보강

```bash
# Upstream 변경사항 확인
git clone --depth 1 https://github.com/whchoi98/project-init.git /tmp/project-init-upstream
diff -rq /tmp/project-init-upstream/plugins/project-init/ plugins/project-init/ \
  --exclude=plugin.json --exclude=CLAUDE.md --exclude=SKILL.md --exclude=readme-template.md \
  --exclude=doc-sync-checker.md --exclude=generate-readme.md --exclude=claude-md-template.md \
  --exclude=agents-templates.md --exclude=skills-templates.md \
  --exclude=add-adr.md --exclude=generate-changelog.md --exclude=sync-docs.md

# Upstream에서 업데이트 가져오기 — 로컬 분기 파일은 반드시 제외 (blanket rsync는 로컬 커스터마이징/4.8 수정/모델 티어를 덮어씀)
rsync -av \
  --exclude='.claude-plugin/plugin.json' \
  --exclude='CLAUDE.md' \
  --exclude='agents/doc-sync-checker.md' \
  --exclude='skills/project-scaffolder/SKILL.md' \
  --exclude='skills/project-scaffolder/references/readme-template.md' \
  --exclude='skills/project-scaffolder/references/claude-md-template.md' \
  --exclude='skills/project-scaffolder/references/agents-templates.md' \
  --exclude='skills/project-scaffolder/references/skills-templates.md' \
  --exclude='commands/generate-readme.md' \
  --exclude='commands/add-adr.md' \
  --exclude='commands/generate-changelog.md' \
  --exclude='commands/sync-docs.md' \
  /tmp/project-init-upstream/plugins/project-init/ plugins/project-init/
```

**로컬 분기 파일 (동기화 제외 대상):**
- `.claude-plugin/plugin.json` — agents/skills/commands 배열 + version 보강
- `CLAUDE.md` — 로컬 Upstream/version 섹션 보유
- `skills/project-scaffolder/SKILL.md` — 로컬 전용 `writing-style-guide.md` 참조 라인 +
  신형 모델 정렬(CLAUDE.md "몇 화면" 크기 가이드, 모듈 CLAUDE.md 블랭킷→조건부 생성)
- `skills/project-scaffolder/references/agents-templates.md` /
  `references/skills-templates.md` — 코드리뷰 recall 가이드 정렬(4.7+/Sonnet 5는
  "고신뢰만 보고" 지시를 문자 그대로 따라 recall이 떨어짐 — 발견은 전부 보고,
  75+ 임계는 상세도·verdict에만 적용; 공식 마이그레이션 가이드 권고). upstream 반영 권장.
- `skills/project-scaffolder/references/readme-template.md` — 로컬 `--`, upstream `—`
- `skills/project-scaffolder/references/claude-md-template.md` — 신형 모델(4.6+) 가이드 정렬:
  생성기용 작성 규칙 프리앰블(항상-로드 컨텍스트 세금 최소화, 강압 어휘·예시 패딩 금지,
  코드가 보여주는 것 서술 금지), Auto-Sync Rules를 단계 리스트에서 트리거→액션 표로 압축,
  모듈 CLAUDE.md를 블랭킷 필수에서 "비자명한 규칙이 있을 때만" 조건부 생성으로 완화.
  upstream 반영 권장.
- `commands/generate-readme.md` — 로컬 전용 GitHub-metrics fetch 단계(Step 2.5) + `Bash(gh:*)`/`Bash(python3:*)` 추가. upstream에는 없는 라이브 배지 기능이라 제외.
- `commands/add-adr.md` / `commands/generate-changelog.md` / `commands/sync-docs.md` —
  description frontmatter에 로컬 전용 superpowers 라이프사이클 라우팅 힌트
  (`superpowers:finishing-a-development-branch`) 추가. 2026-07 동기화 점검에서 미등록
  분기로 발견되어 등록 — rsync 시 이 힌트가 소실되면 루트 CLAUDE.md 라우팅 표와 어긋남.
- `skills/pr-autofix/**`, `commands/pr-autofix.md` — 로컬 전용(upstream 없음). 모델 ID Opus 4.8 로컬 고정
- `skills/decision-reconcile/**` — 로컬 전용(upstream 없음). ADR 모순 검출·번복 ADR 초안. 멀티 에이전트 패널(Claude 모델 티어 + 선택적 co-agent CLI)
- `agents/doc-sync-checker.md` — 모델 티어 로컬 `sonnet`(upstream `opus`). 기계적 doc 비교/채점이라 opus 과도 + `/sync-docs`마다 호출 비용. upstream 반영 권장. **tools**: bare `Bash`
  (agent frontmatter의 `tools` 필드는 bare 툴명만 유효 — `Bash(find:*)` 같은 스코프드
  표기는 지원되지 않으며, 명령 수준 제한은 PreToolUse 훅/settings 권한 소관. 과거 이
  항목이 스코프드 표기를 로컬 상태로 기술했으나 실제 파일과 불일치해 2026-07 정정)
