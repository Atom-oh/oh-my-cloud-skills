---
sidebar_position: 3
title: "사용법 가이드"
---

# 사용법 가이드

co-agent로 다른 AI(Kiro CLI · Codex · Agy)와 협업해 리뷰·의사결정·ADR·자율 구현을 진행하고, Claude가 의장으로 종합하는 방법을 안내합니다.

## 빠른 시작

```
1. 설치        →  /plugin marketplace add https://github.com/Atom-oh/oh-my-cloud-skills
                   /plugin install co-agent@oh-my-cloud-skills
2. (선택) CLI  →  kiro-cli / codex / agy 중 설치·인증된 것이 패널이 됨
3. 준비도 확인 →  /co-agent:setup   (readiness 요약 기록, 이후 흐름이 참조)
4. 프롬프트    →  "이 변경 다른 AI로 리뷰해줘"  /  "잘 모르겠어, 같이 결정해줘"
5. 결과물      →  합의/이견을 종합한 리뷰 보고서 · 의사결정표 · ADR 초안 · (opt-in) 자율 구현
```

설치된 AI가 하나도 없어도 review/decide/adr/sync-context는 동작합니다 — Claude가 단독으로 수행하고 그 사실을 명시합니다. **단, `consensus`/`harness`는 non-degraded 모드**라 gate-eligible peer가 없으면 solo 강등 대신 멈추고 `/co-agent:setup`을 안내합니다.

## 패널 확인

```
"지금 패널 어떤 AI가 잡혀?"
→ Panel: kiro-cli codex agy   (설치·인증된 것만 표시)
```

`/co-agent:setup`을 먼저 실행하면 `.claude/co-agent-panel.local.json`에 각 peer의 실제 사용가능 여부(READY/AUTH/TIMEOUT/ERROR/ABSENT)가 기록되고, 이후 모든 흐름이 이 readiness를 먼저 참조합니다 — `command -v`만으로는 인증/실사용 가능 여부를 알 수 없기 때문입니다.

## 모드별 사용 예시

### 1. Review — 멀티-AI 코드/아키텍처 리뷰

```
"이 PR 변경분을 다른 AI들로 리뷰해줘"
"멀티 AI로 second opinion 받아줘"
```

- 같은 리뷰 프롬프트를 패널에 **병렬 팬아웃** → 각 AI 의견 수집
- Claude가 **합의(≥2 AI 일치)** vs **이견(단일 AI, 출처 표기)** 으로 종합 + AWS Well-Architected
- 판정: **PASS** (Critical 0, High ≤2) / **REVIEW** / **FAIL**

### 2. Decide — 의사결정 보조

```
"RDS로 갈지 DynamoDB로 갈지 잘 모르겠어, 같이 결정해줘"
"이 두 방안 중에 협업해서 결정해줘"
```

- 옵션을 패널에 질의 → **비교표(옵션 × 각 AI 선택/근거)**
- Claude가 단일 추천 + 결정을 가른 트레이드오프를 명시. 의견이 갈리면 그 사실을 숨기지 않음

### 3. ADR — 의사결정 기록 협업

```
"이 아키텍처 결정을 ADR로 남기자, 다른 AI랑 같이"
```

- 패널에서 대안·트레이드오프·리스크 수집 → Claude가 **Nygard 형식 ADR 초안**
- project-init `/add-adr`과 연동해 `docs/decisions/ADR-NNN.md`에 저장

### 4. sync-context — AI 컨텍스트 동기화

외부 AI가 **프로젝트 컨벤션을 알고** 리뷰하도록, `CLAUDE.md`를 증류해 **Kiro·Codex·Agy가 공통 참조하는 하나의 `AGENTS.md`**를 만듭니다.

```
/co-agent:sync-context
```

| AI | 참조 방식 | 생성 |
|----|-----------|------|
| Kiro | `.kiro/steering/project-context.md` → `#[[file:AGENTS.md]]` | steering bridge |
| Codex | `AGENTS.md` (~32 KiB 캡) 네이티브 로드 | 증류 생성 |
| Agy | fan-out 시점에 컨텍스트로 fold-in (검증 통과 시만) | — |

- `CLAUDE.md`를 **그대로 복사하지 않고 증류** — 리뷰에 필요한 핵심만(스택·빌드/테스트 명령·금지 패턴·아키텍처 경계·체크리스트). 시크릿은 포함하지 않음
- 생성 마커로 staleness를 추적하고, 마커 없는 수기 파일은 보호
- Agy에게 fold-in되기 전 `check_ai_context.py --verify`로 marker/freshness/secret을 재확인 — stale하거나 수기 파일이면 diff-only 컨텍스트로 조용히 fallback

### 5. consensus — 자율 doc→plan→구현 파이프라인

**host(Claude/Codex) 자신이 TDD로 코드를 작성**하고, 멀티모델 패널은 계획(P2)과 구현 diff(P4)를 **리뷰만** 합니다.

```
/co-agent:consensus plan docs/decisions/ADR-011-example.md
/co-agent:consensus implement docs/superpowers/plans/2026-07-01-example.md
/co-agent:consensus review                # 팬아웃 리뷰 게이트만 단독 실행
/co-agent:consensus                       # 전체 P0→P5 파이프라인 (재실행 시 자동 이어서 진행)
```

- **Stage A (P0–P2)**: 입력 문서 감지 → plan 로드/생성 → 패널 합의 게이트(CRITICAL/MAJOR 없을 때까지 반복)
- **Stage B (P3)**: task별 checkpoint → TDD → scope 검증 → 보안 mandate veto → 테스트 게이트 → 멀티모델 게이트 → 커밋
- **Stage C (P4/P5)**: 누적 diff에 최종 게이트 → 리포트(`.claude/co-agent-consensus/report.md`)
- 로컬 커밋만 수행(push/reset/rebase 없음). 세션 상태 기반으로 **재실행 시 이어서 진행**.

### 6. harness — host 설계 / peer 구현 / 패널 리뷰

**크로스벤더 peer(Codex 또는 Agy)가 격리된 git worktree에서 코드를 작성**하고, host는 설계·실패하는 테스트 작성·검증·**모든 커밋의 유일한 주체**입니다.

```
/co-agent:harness docs/decisions/ADR-011-example.md --implementer codex
```

- peer는 workspace-write 샌드박스(worktree cwd로 제한) 안에서만 쓰기
- host는 peer의 worktree에서 `git add -A && git diff --cached`로 캡처한 diff만 적용 — worktree 밖 쓰기는 절대 메인 트리에 반영되지 않음
- 캡처된 각 경로는 `scope_guard.py`로 plan 범위 검증 후에만 적용
- opt-in, 로컬 커밋만. 상세 신뢰 경계: 스킬의 `references/delegated-implement.md`

> **consensus vs harness 선택 기준**: host가 직접 쓰는 코드에 만족하고 독립적인 멀티모델 검증만 원하면 **consensus**. 서로 다른 모델 계열이 실제로 구현을 작성하게 하고 싶으면(진짜 구현 다양성) **harness** — 어느 쪽이든 커밋 권한은 host에만 있습니다.

### 7. setup — 패널 준비도 preflight

```
/co-agent:setup
```

- 각 peer의 접근경로를 `plugin` → `raw CLI` → `none` 순으로 감지
- 접근 가능한 peer는 실제로 짧은 프롬프트를 보내 프로브(READY/AUTH/NO_INGEST/TIMEOUT/ERROR/ABSENT 분류)
- 결과를 `.claude/co-agent-panel.local.json`에 기록 — review/decide/adr은 이 결과가 없어도 solo 강등, **consensus/harness는 gate-eligible peer가 0이면 반드시 이 명령을 먼저 안내**

## 패널 튜닝 (`/co-agent:configure`)

CLI가 헤드리스로 실제 받는 설정만 노출합니다.

```bash
/co-agent:configure show                  # 현재 설정 보기
/co-agent:configure set codex model gpt-5-codex
/co-agent:configure set codex effort high            # effort는 Codex 전용
/co-agent:configure set kiro-cli model claude-opus-4.8  # kiro-cli chat --list-models 참고
/co-agent:configure set agy enabled false            # 패널에서 제외
/co-agent:configure set timeout 300                  # CLI별 타임아웃(초)
/co-agent:configure set autosync on                  # CLAUDE.md 변경 시 자동 sync-context
/co-agent:configure set codex model openai.gpt-5.6-sol --scope user  # 모든 레포에 적용
```

설정은 `co-agent.defaults.json`(커밋) ← `~/.claude/co-agent.user.json`(유저) ← `.claude/co-agent.local.json`(레포 로컬, gitignore) 레이어로 병합되며, 팬아웃이 실시간으로 읽습니다.

## 자동 동기화 (autosync)

`autosync on`이면 `CLAUDE.md`가 바뀌어 컨텍스트 파일이 stale해질 때 PostToolUse 훅이 Claude에게 `/co-agent:sync-context` 실행을 지시합니다 (기본 off = 알림만). 훅은 bash라 직접 증류할 수 없으므로, **자동이라도 Claude가 루프 안에서** 파일을 다시 씁니다 — 몰래 쓰기가 아닙니다.

## 동작 원리

```
프롬프트 → 패널 감지(readiness 우선 참조) → 동일 프롬프트 병렬 팬아웃(Kiro/Codex/Agy)
        → Claude 종합(합의/이견, 출처 표기) → 리뷰 보고서 / 의사결정 / ADR / (opt-in) 자율 구현
```

## 의장 원칙

- 외부 AI는 **자문**, **Claude가 최종 결정·작성**
- 핵심 포인트는 **출처 표기**, **이견은 표면화**
- CLI 누락/에러 → 스킵·기록 후 진행 (단일 AI에 차단되지 않음)
- 패널 출력은 자문일 뿐 — Claude가 실제 코드/diff로 검증 (프롬프트 인젝션 방어)

## 다음 단계

- [co-agent 개요](/docs/co-agent/overview) — 모드·판정 기준·설정 표
- [co-agent 스킬](/docs/co-agent/skills/co-agent) — 모드별 상세 동작
- [명령 목록](/docs/co-agent/commands/) — 5개 슬래시 명령 상세
