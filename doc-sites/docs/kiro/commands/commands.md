---
sidebar_position: 1
title: "명령 목록"
---

# kiro 명령

4개의 슬래시 명령으로 kiro-cli 셋업, 구현 위임, 온디맨드 리뷰, 설정 조정을
지원합니다.

## /kiro:setup

kiro-cli를 감지하고 실사용 여부를 프로브한 뒤, 모델을 선택하고 구현/리뷰용
커스텀 에이전트 파일을 생성합니다. **다른 명령을 쓰기 전에 반드시 먼저
실행해야 합니다.**

```bash
/kiro:setup
```

1. **감지 + 프로브** — `kiro_setup.py probe`가 PATH 확인 + 실제 짧은 프롬프트
   전송으로 `READY`/`AUTH`/`NO_INGEST`/`TIMEOUT`/`ERROR`/`ABSENT` 분류
2. **모델 선택** — 구현(delegate) 모델과 리뷰(review) 모델을 각각 선택
   (리뷰 모델은 목록 중 최신/최강을 권장)
3. **신뢰 결정** — `execute_bash`를 구현자에게 허용할지 명시적으로 확인
   (기본: 허용 안 함)
4. **에이전트 파일 작성** — `.kiro/agents/kiro-implementer.json`,
   `.kiro/agents/kiro-reviewer.json`
5. **default delegation 여부** 확인 (기본 off)
6. **pre-commit 리뷰 훅 여부** 확인 (기본 off — staged diff 내용이 Kiro
   백엔드로 전송됨을 먼저 설명)

## /kiro:delegate

Kiro-native 스펙을 계획한 뒤, 격리 worktree 안에서 Kiro CLI에 구현을 위임하고,
호스트 측에서 검증·커밋합니다. 태스크의 fix loop가 소진되면 Claude가 직접
코드를 작성하는 것으로 폴백합니다.

```bash
/kiro:delegate 이 함수에 재시도 로직을 추가해줘
```

1. **Plan** — `.kiro/specs/<name>/{requirements,design,tasks.md}` 작성
2. **Wave-plan + execute** — 태스크(또는 파일이 겹치지 않는 웨이브, 최대
   `delegate.parallel_tasks`)별로 격리 worktree → Kiro 구현 → capture-diff →
   scope_guard
3. **Verify + bounded retry**(`delegate.max_fix_rounds`) → 소진 시 **Claude 폴백**
4. **Commit**(호스트만) + `tasks.md` 체크 + 위임률 리포트

kiro-cli가 `READY`가 아니면 파이프라인을 시도하는 대신 `/kiro:setup`을 먼저
안내합니다.

## /kiro:review

pre-commit 훅과 동일한 Kiro 리뷰 엔진을 온디맨드로 실행합니다.

```bash
/kiro:review                          # staged diff 리뷰 (기본)
/kiro:review src/foo.py src/bar.py    # 지정 경로의 전체 working-tree diff
```

`kiro-reviewer` 에이전트 파일이 있으면 `fs_read`가 격리된 diff 임시 디렉터리로
제한됩니다. 파일이 없거나 검증에 실패하면 기본적으로 리뷰를 스킵합니다
(fail-open) — 가드 없이 리뷰하려면 `AskUserQuestion` 확인 후에만
`--allow-unguarded`를 사용합니다. `review.on_commit`이 off여도 이 명령은
항상 실행됩니다.

## /kiro:configure

kiro 플러그인 설정을 조회/변경합니다. 설정은 `kiro.defaults.json`(커밋) ←
`.claude/kiro.local.json`(레포 로컬, gitignore) 레이어로 병합됩니다.

```bash
/kiro:configure                                   # 현재 설정 보기
/kiro:configure set default_delegate on
/kiro:configure set delegate model <m>
/kiro:configure set review model "gpt-5.6-sol"    # 리뷰는 항상 최신/최강 모델 권장
/kiro:configure set delegate parallel_tasks 5     # 기본 3, 1=순차
/kiro:configure set delegate max_fix_rounds 3     # 기본 2
/kiro:configure set review on_commit on           # 기본 off
/kiro:configure set review block warning          # 기본 critical
/kiro:configure set delegate timeout 300          # 기본 240초
```

`review.on_commit`/`default_delegate`는 동의 게이팅 설정이라, 커밋된
`.claude/kiro.local.json`에 값이 있어도 무시되고 셸 기본값(off)이 적용됩니다.
