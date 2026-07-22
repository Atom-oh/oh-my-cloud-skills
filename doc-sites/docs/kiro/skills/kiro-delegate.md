---
sidebar_position: 1
title: "kiro-delegate"
---

# kiro-delegate Skill

Claude가 계획·검증하고, **Kiro CLI가 자기 구독의 정액 크레딧으로 구현**하는
비용 절감 위임 스킬. `co-agent`와 목적이 다릅니다 — 세컨드 오피니언이 아니라
순수 비용 절감입니다.

## 트리거

이 스킬은 **쓰기 가능**(Write/Edit/Bash — 계획 → 구현 → 커밋)이므로, 트리거 집합은
명시적인 **구현 위임** 문구만 포함합니다. 리뷰 문구는 절대 포함하지 않습니다 —
"kiro로 리뷰해줘"가 실수로 이 쓰기 가능한 스킬을 활성화하지 않도록, 읽기 전용
리뷰는 트리거 없이 직접 호출하는 `/kiro:review` 명령이 전담합니다.

- "kiro한테 시켜서 구현"
- "kiro로 구현"
- "kiro한테 구현 위임"
- "delegate implementation to kiro"
- "kiro implement this"

## "안전"의 의미와 한계

`co-agent:harness`는 Kiro를 구현자로 아예 거부합니다(`SANDBOX_IMPLEMENTERS = codex, agy`만
허용) — Kiro에 cwd로 격리되는 쓰기 샌드박스가 없기 때문입니다. 이 스킬은 샌드박스가
있는 척하지 않고 보장 범위를 좁게 정의합니다: **할당된 worktree 안에서 캡처되고,
plan의 선언 파일 집합 안에 있는 변경만 메인 트리에 도달할 수 있습니다** —
`worktree.py capture-diff` + `scope_guard.py`가 이를 강제합니다(scope_guard.py는
현재 태스크 하나가 아니라 plan 전체 태스크의 파일 합집합을 검사 — 웨이브 내
태스크별 경계는 파일 집합별로 구현자 실행을 직렬화하는 데서 나오지, scope_guard.py
자체에서 나오지 않습니다). 이는 자동 승인된 `execute_bash` 호출이 호스트의
나머지 부분에 하는 일(자격 증명 읽기, worktree 밖 파일 삭제)은 **전혀 제약하지
않습니다** — `execute_bash`를 신뢰하고 켜는 것은 이 파이프라인의 worktree/capture/
scope-guard 레이어와는 별개의, `kiro-cli` 자체에 대한 결정입니다. Kiro는 절대
커밋하지 않습니다.

## 명령

| 명령 | 설명 |
|------|------|
| `/kiro:setup` | kiro-cli 감지 + 실사용 프로브, 모델 목록, `.kiro/agents/{kiro-implementer,kiro-reviewer}.json` 생성, `default_delegate`/`review.on_commit` 설정 |
| `/kiro:delegate <요청>` | 계획 → 스펙 → 태스크별 Kiro 구현 → Claude 검증+커밋 → 위임률 리포트 |
| `/kiro:review [경로...]` | pre-commit 훅과 동일한 Kiro 리뷰를 온디맨드로 실행 (기본: staged 변경분) |
| `/kiro:configure` | `default_delegate`, delegate/review 모델, `parallel_tasks`, `max_fix_rounds`, `review.on_commit`, `review.block` 조회/변경 |

**위임 전에 먼저 태스크를 쪼개세요 — 여러 레이어에 걸친 태스크를 한 번에 넘기지
마세요.** 모델+레포지토리+서비스+핸들러+라우트+테스트에 걸친 태스크는 보통
`delegate.timeout`(기본 240초)을 넘겨 아무것도 캡처되지 않은 채 중간에 죽습니다 —
Kiro가 고장난 것처럼 보이지만 실은 태스크 크기 문제입니다.

## Pre-commit 리뷰 (opt-in)

`review.on_commit`은 **기본 off**입니다 — staged diff **내용**이 Kiro 백엔드로
전송되기 때문에, 켜는 것은 의도적인 선택이어야 합니다. `kiro-reviewer` 에이전트가
있으면 `fs_read`가 diff만 담긴 격리 임시 디렉터리로 제한됩니다(프롬프트 인젝션이
있어도 무관한 경로를 읽게 할 수 없음). 이 에이전트 파일이 없거나 변조됐으면
`kiro_review.py`는 **기본적으로 리뷰를 통째로 스킵**합니다 — 가드 없는 호출로
조용히 대체하지 않습니다(자동 훅과 수동 `/kiro:review` 모두 동일). 켜져 있을 때는
`PreToolUse(Bash)` 훅이 매 `git commit` 전에 실행되어 `review.block`(기본
`critical`) 이상 심각도의 발견에서만 커밋을 차단합니다(exit 2). Kiro
미인증/에러/타임아웃 시에는 fail-open — 커밋을 막지 않고 경고만 출력합니다.
한 커밋만 우회: `KIRO_REVIEW=off git commit ...`(인라인 접두사여야 함 — 이전
명령에서 `export`한 값은 셸 상태가 유지되지 않아 작동하지 않음).

## 구현 모델과 리뷰 모델을 다르게 유지하는 이유

- **구현(delegate) 모델** — 정액 크레딧이라 per-token 비용 트레이드오프가 없음.
  태스크를 제대로 끝내는 모델이면 무엇이든(fix-round가 적을수록 순수 시간 절약).
- **리뷰(review) 모델** — 구현 모델이 가벼워도 항상 Kiro의 **최강** 모델로 유지 —
  구현자가 만든 결과물의 안전망이므로 약한 링크가 되면 안 됨.

## Default-delegate 모드

`default_delegate`(기본 off)를 켜면 "kiro로 구현" 같은 트리거 문구 없이도 구현
요청이 자동으로 이 파이프라인으로 라우팅됩니다 — Kiro가 사용 불가능하거나 fix
loop가 소진되면 Claude가 코드를 직접 작성하는 폴백은 그대로 적용됩니다.
`/kiro:setup` 또는 `/kiro:configure set default_delegate on`으로 설정.

## 절대 하지 않는 것

- Kiro를 저장소 루트(할당된 worktree가 아닌 어떤 곳)를 cwd로 쓰기 모드 실행
- 캡처되지 않거나 scope 검증을 통과하지 않은 패치를 메인 트리에 적용
- Kiro가 `git commit`/`push`/`reset`을 실행하도록 허용
- 멈춘 태스크를 조용히 누락시키는 것 — 항상 Claude 폴백으로 보고됨

## 참고 파일

- `references/kiro-headless.md` — CLI 호출, 인증, 신뢰 경계, 모델 티어링
- `references/spec-format.md` — Kiro spec 구조, `tasks.md` 형식, 태스크 크기 조정 규칙
- `scripts/worktree.py`, `scripts/scope_guard.py`, `scripts/parse_plan.py` — co-agent에서
  그대로 복사(격리/스코핑 메커니즘 동일, 구현자 CLI만 다름)
- `scripts/kiro_config.py` — 레이어드 설정(`kiro.defaults.json` ← `.claude/kiro.local.json`)
- `scripts/kiro_review.py` — `/kiro:review`와 훅이 쓰는 리뷰 엔진
- `scripts/kiro_setup.py` — 프로브, 모델 목록, `.kiro/agents/*.json` 생성
