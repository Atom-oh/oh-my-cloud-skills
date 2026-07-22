---
sidebar_position: 3
title: "사용법 가이드"
---

# 사용법 가이드

Claude가 계획을 세워 태스크를 쪼개면, 각 태스크를 Kiro CLI가 격리된 git worktree
안에서 구현합니다. 결과 diff는 capture → scope guard(계획에 선언된 파일만 통과)
검증을 거쳐 Claude가 메인 트리에 적용하고 테스트로 검증합니다. Kiro가 태스크를 못
끝내면 Claude가 직접 구현으로 폴백하고, 커밋은 항상 Claude만 합니다.

## 빠른 시작

```
1. 설치     →  /plugin marketplace add https://github.com/Atom-oh/oh-my-cloud-skills
                /plugin install kiro@oh-my-cloud-skills
2. 셋업     →  /kiro:setup     (프로브 → 모델 선택 → 신뢰 결정 → 에이전트 파일 생성)
3. 위임 실행 →  /kiro:delegate <구현 요청>
4. 결과물   →  구현 diff · 테스트 통과 확인 · 위임률 리포트(몇 %를 Kiro 크레딧으로 처리했는지)
```

## `/kiro:delegate` — 구현 위임 파이프라인

```
/kiro:delegate 이 함수에 재시도 로직을 추가해줘
```

1. **Plan** — Claude가 `.kiro/specs/<name>/{requirements,design,tasks}.md`를
   Kiro-native 스펙 형식으로 작성
2. **Wave-plan + execute** — 태스크(또는 파일이 겹치지 않는 태스크 묶음, 최대
   `delegate.parallel_tasks`개)별로: 격리 worktree 생성 → Kiro 구현 →
   capture-diff → scope_guard 검증
3. **Verify + bounded retry** — `delegate.max_fix_rounds`만큼 재시도 후,
   소진되면 **Claude 직접 구현으로 폴백** (조용히 스킵하지 않음)
4. **Commit** — Claude만 커밋 + `tasks.md` 체크 + 위임률 리포트(Kiro가 끝낸
   태스크 수 vs. Claude가 넘겨받은 태스크 수)

kiro-cli가 `READY` 상태가 아니면(`/kiro:setup` 미실행 등) `/kiro:delegate`는 파이프라인
중간에 조용히 폴백하는 대신, 먼저 `/kiro:setup`을 실행하라고 안내합니다.

## `/kiro:review` — 온디맨드 리뷰

pre-commit 훅과 동일한 리뷰 엔진을 수동으로 실행합니다.

```bash
/kiro:review              # staged diff 리뷰 (기본)
/kiro:review src/foo.py src/bar.py   # 특정 경로의 전체 working-tree diff (staged+unstaged)
```

- `kiro-reviewer` 에이전트 파일이 있으면 `fs_read`가 격리된 diff 임시 디렉터리로만
  제한됩니다 — 신뢰할 수 없는 diff에 프롬프트 인젝션이 있어도 무관한 파일(예:
  자격 증명)을 읽도록 유도할 수 없습니다
- 에이전트 파일이 없거나 검증에 실패하면 **기본적으로 리뷰를 통째로 스킵**합니다
  (fail-open, 가드 없는 호출로 조용히 대체하지 않음). 이때는 `/kiro:setup`을 다시
  실행하는 것이 정상적인 해결책이고, 정말 가드 없이 리뷰하고 싶다면
  `AskUserQuestion` 확인 후에만 `--allow-unguarded`를 사용
- `review.on_commit`이 off여도 이 명령은 항상 실행됩니다 — on_commit은 자동
  pre-commit 훅만 제어

### pre-commit 훅 (opt-in, 기본 off)

`/kiro:configure set review on_commit on`으로 켜면 `git commit` 실행 전에
staged diff가 자동으로 Kiro 리뷰를 받습니다. **staged diff 내용이 Kiro 백엔드로
전송된다는 점**을 먼저 인지해야 합니다. Kiro/에러/미인증 시 fail-open(커밋을
막지 않음)이며, `review.block`(기본 `critical`) 이상 심각도의 발견만 커밋을
차단합니다. 한 번만 우회하려면:

```bash
KIRO_REVIEW=off git commit -m "..."
```

## `/kiro:configure` — 설정 조정

| 명령 | 효과 | 기본값 |
|------|------|--------|
| `set default_delegate on\|off` | 트리거 문구 없이도 구현 요청을 자동으로 Kiro로 라우팅 | off |
| `set delegate model <m>` | 구현자 모델 (정액 크레딧 — per-token 비용 트레이드오프 없음, 태스크를 제대로 끝내는 모델이면 무엇이든 OK) | CLI 기본 |
| `set review model <m>` | 리뷰어 모델 — 구현 모델이 가벼워도 Kiro의 최신/최강 모델로 유지 권장 | CLI 기본 |
| `set delegate parallel_tasks <n>` | 웨이브당 최대 동시 태스크 수 (`1` = 순차) | 3 |
| `set delegate max_fix_rounds <n>` | Claude 폴백 전 재시도 횟수 | 2 |
| `set review on_commit on\|off` | pre-commit 리뷰 훅 활성화 | off |
| `set review block critical\|warning\|none` | 커밋을 막는 최소 심각도 (`warning`은 warning+critical 차단, `suggestion`은 어느 레벨에서도 차단 안 함) | critical |
| `set review timeout <s>` / `set delegate timeout <s>` | 호출당 wall-clock 예산(초) | 240 |

```bash
/kiro:configure                              # 현재 유효 설정 보기
/kiro:configure set delegate parallel_tasks 5
/kiro:configure set review model "gpt-5.6-sol"
```

설정은 `kiro.defaults.json`(커밋) ← `.claude/kiro.local.json`(레포 로컬,
gitignore) 레이어로 병합되며, `set`은 항상 로컬 오버라이드에 씁니다.

:::warning
`review.on_commit`과 `default_delegate`는 **동의 게이팅 설정**입니다 — 커밋된
`.claude/kiro.local.json`에 이 두 값이 있어도 무시되고 셸 기본값(둘 다 off)이
적용됩니다. 개인 오버라이드 파일이 실수로(혹은 악의적으로) 커밋되어도 설치한
사용자의 동의 없이 자동으로 켜지는 일이 없도록 하는 방어입니다.
:::

## 동작 원리

```
프롬프트 → Claude 계획(Kiro-native spec) → 태스크별 격리 worktree
        → Kiro 구현 → capture-diff → scope_guard → Claude 적용+테스트
        → 실패 시 재시도 → 소진 시 Claude 폴백 → Claude만 커밋 → 위임률 리포트
git commit → pre-commit 훅(opt-in) → kiro_review.py (fail-open, critical만 차단)
```

## 다음 단계

- [kiro 개요](/docs/kiro/overview) — 비용 절감 컨셉, 신뢰 경계
- [kiro-delegate-agent](/docs/kiro/agents/kiro-delegate-agent) — 오케스트레이터 상세
- [kiro-delegate 스킬](/docs/kiro/skills/kiro-delegate) — 트리거·파이프라인 상세
- [명령 목록](/docs/kiro/commands/) — 4개 슬래시 명령 상세
