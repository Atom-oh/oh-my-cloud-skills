---
sidebar_position: 3
title: "사용법 가이드"
---

# 사용법 가이드

co-agent로 다른 AI(Kiro CLI · Codex · Antigravity)와 협업해 리뷰·의사결정·ADR을 진행하고, Claude가 의장으로 종합하는 방법을 안내합니다.

## 빠른 시작

```
1. 설치        →  /plugin marketplace add https://github.com/Atom-oh/oh-my-cloud-skills
                   /plugin install co-agent@oh-my-cloud-skills
2. (선택) CLI  →  kiro-cli / codex / agy 중 설치·인증된 것이 패널이 됨
3. 프롬프트    →  "이 변경 다른 AI로 리뷰해줘"  /  "잘 모르겠어, 같이 결정해줘"
4. 결과물      →  합의/이견을 종합한 리뷰 보고서 · 의사결정표 · ADR 초안
```

설치된 AI가 하나도 없어도 동작합니다 — Claude가 단독으로 수행하고 그 사실을 명시합니다 (절대 hard-fail 안 함).

## 패널 확인

co-agent는 항상 먼저 패널을 감지합니다. 바이너리 존재만으로 감지하며(`kiro-cli`·`codex`·`agy`), 인증되지 않은 CLI는 호출 시점에 자동으로 스킵됩니다.

```
"지금 패널 어떤 AI가 잡혀?"
→ Panel: kiro-cli codex agy   (설치·인증된 것만 표시)
```

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

외부 AI가 **프로젝트 컨벤션을 알고** 리뷰하도록, 각 CLI가 자동 로드하는 컨텍스트 파일을 만듭니다.

```
/co-agent:sync-context
```

| AI | 읽는 파일 | 생성 |
|----|-----------|------|
| Kiro | `.kiro/steering/project-context.md` → `#[[file:AGENTS.md]]` (Codex와 동일 파일) | bridge 생성 |
| Codex | `AGENTS.md` (~32 KiB 캡) | ✅ |
| Agy | `AGENTS.md` (네이티브, Codex와 동일 컨벤션) | 별도 생성 불필요 — Codex와 공유 |

- `CLAUDE.md`를 **그대로 복사하지 않고 증류** — 리뷰에 필요한 핵심만(스택·빌드/테스트 명령·금지 패턴·아키텍처 경계·체크리스트). 시크릿은 포함하지 않음
- 생성 마커로 staleness를 추적하고, 마커 없는 수기 파일은 보호

## 패널 튜닝 (`/co-agent:configure`)

CLI가 헤드리스로 실제 받는 설정만 노출합니다.

```bash
/co-agent:configure show                  # 현재 설정 보기
/co-agent:configure set codex model gpt-5-codex
/co-agent:configure set codex effort high            # effort는 Codex 전용
/co-agent:configure set kiro  model claude-opus-4.8  # kiro-cli chat --list-models 참고
/co-agent:configure set agy enabled false            # 패널에서 제외
/co-agent:configure set timeout 300                  # CLI별 타임아웃(초)
/co-agent:configure set autosync on                  # CLAUDE.md 변경 시 자동 sync-context
```

설정은 `co-agent.defaults.json`(커밋) ← `.claude/co-agent.local.json`(gitignore) 레이어로 병합되며, 팬아웃이 실시간으로 읽습니다.

## 자동 동기화 (autosync)

`autosync on`이면 `CLAUDE.md`가 바뀌어 컨텍스트 파일이 stale해질 때 PostToolUse 훅이 Claude에게 `/co-agent:sync-context` 실행을 지시합니다 (기본 off = 알림만). 훅은 bash라 직접 증류할 수 없으므로, **자동이라도 Claude가 루프 안에서** 파일을 다시 씁니다 — 몰래 쓰기가 아닙니다.

## 동작 원리

```
프롬프트 → 패널 감지 → 동일 프롬프트 병렬 팬아웃(Kiro/Codex/Agy)
        → Claude 종합(합의/이견, 출처 표기) → 리뷰 보고서 / 의사결정 / ADR
```

## 의장 원칙

- 외부 AI는 **자문**, **Claude가 최종 결정·작성**
- 핵심 포인트는 **출처 표기**, **이견은 표면화**
- CLI 누락/에러 → 스킵·기록 후 진행 (단일 AI에 차단되지 않음)
- 패널 출력은 자문일 뿐 — Claude가 실제 코드/diff로 검증 (프롬프트 인젝션 방어)

## 다음 단계

- [co-agent 개요](/docs/co-agent/overview) — 모드·판정 기준·설정 표
- [co-agent 스킬](/docs/co-agent/skills/co-agent) — 모드별 상세 동작
