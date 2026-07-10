# Upstream Sync (whchoi98/project-init)

> project-init은 upstream 플러그인에서 분기. **동기화할 때만** 이 문서를 참조하세요
> (CLAUDE.md는 출처 요약만 보유).

- **Source**: `git@github.com:whchoi98/project-init.git` (path: `plugins/project-init/`) · **Author**: whchoi98
- **Sync 정렬**: 마켓플레이스 추가 시 version 2.0.0 → 마켓플레이스 통일 버전으로 정렬, plugin.json에 agents/skills/commands 배열 보강

```bash
# Upstream 변경사항 확인
git clone --depth 1 https://github.com/whchoi98/project-init.git /tmp/project-init-upstream
diff -rq /tmp/project-init-upstream/plugins/project-init/ plugins/project-init/ \
  --exclude=plugin.json --exclude=CLAUDE.md --exclude=SKILL.md --exclude=readme-template.md \
  --exclude=doc-sync-checker.md --exclude=generate-readme.md --exclude=claude-md-template.md

# Upstream에서 업데이트 가져오기 — 로컬 분기 파일은 반드시 제외 (blanket rsync는 로컬 커스터마이징/4.8 수정/모델 티어를 덮어씀)
rsync -av \
  --exclude='.claude-plugin/plugin.json' \
  --exclude='CLAUDE.md' \
  --exclude='agents/doc-sync-checker.md' \
  --exclude='skills/project-scaffolder/SKILL.md' \
  --exclude='skills/project-scaffolder/references/readme-template.md' \
  --exclude='skills/project-scaffolder/references/claude-md-template.md' \
  --exclude='commands/generate-readme.md' \
  /tmp/project-init-upstream/plugins/project-init/ plugins/project-init/
```

**로컬 분기 파일 (동기화 제외 대상):**
- `.claude-plugin/plugin.json` — agents/skills/commands 배열 + version 보강
- `CLAUDE.md` — 로컬 Upstream/version 섹션 보유
- `skills/project-scaffolder/SKILL.md` — 로컬 전용 `writing-style-guide.md` 참조 라인
- `skills/project-scaffolder/references/readme-template.md` — 로컬 `--`, upstream `—`
- `skills/project-scaffolder/references/claude-md-template.md` — 신형 모델(4.6+) 가이드 정렬:
  생성기용 작성 규칙 프리앰블(항상-로드 컨텍스트 세금 최소화, 강압 어휘·예시 패딩 금지,
  코드가 보여주는 것 서술 금지), Auto-Sync Rules를 단계 리스트에서 트리거→액션 표로 압축,
  모듈 CLAUDE.md를 블랭킷 필수에서 "비자명한 규칙이 있을 때만" 조건부 생성으로 완화.
  upstream 반영 권장.
- `commands/generate-readme.md` — 로컬 전용 GitHub-metrics fetch 단계(Step 2.5) + `Bash(gh:*)`/`Bash(python3:*)` 추가. upstream에는 없는 라이브 배지 기능이라 제외.
- `skills/pr-autofix/**`, `commands/pr-autofix.md` — 로컬 전용(upstream 없음). 모델 ID Opus 4.8 로컬 고정
- `skills/decision-reconcile/**` — 로컬 전용(upstream 없음). ADR 모순 검출·번복 ADR 초안. 멀티 에이전트 패널(Claude 모델 티어 + 선택적 co-agent CLI)
- `agents/doc-sync-checker.md` — 모델 티어 로컬 `sonnet`(upstream `opus`). 기계적 doc 비교/채점이라 opus 과도 + `/sync-docs`마다 호출 비용. upstream 반영 권장. **tools**: read-only Bash 스코핑 `Bash(find:*), Bash(git log:*), Bash(ls:*), Bash(wc:*)`. upstream은 `wc` 누락(본문 `wc -l`가 채점에 쓰임) — 로컬은 `Bash(wc:*)` 추가, upstream에도 권장
