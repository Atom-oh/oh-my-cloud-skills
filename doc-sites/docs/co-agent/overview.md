---
sidebar_position: 1
title: "개요"
---

# co-agent 개요

co-agent는 **다른 AI 에이전트(Kiro CLI, Codex, Antigravity)와 협업**해 second opinion을 받고, **Claude가 의장(chair)으로 최종 종합**하는 플러그인입니다. 네 가지 모드를 제공합니다: 멀티-AI 리뷰, 의사결정 보조, ADR 협업, AI 컨텍스트 동기화.

## 구성 요소

### 에이전트 (1개)

| 에이전트 | 설명 | 출력물 |
|----------|------|--------|
| `co-agent` | 멀티-AI 패널 의장 — 리뷰/의사결정/ADR 프롬프트를 외부 AI에 팬아웃하고 Claude가 종합 | 리뷰 보고서 / 의사결정표 / ADR |

### 스킬 (1개)

| 스킬 | 설명 |
|------|------|
| `co-agent` | 4-모드 멀티-AI 협업 (review · decide · adr · sync-context) |

### 명령 (5개)

| 명령 | 설명 |
|------|------|
| `/co-agent:configure` | 패널 설정 — AI별 `model`, Codex `effort`, `enabled`, `timeout`, `autosync` 토글 |
| `/co-agent:sync-context` | `CLAUDE.md` 증류 → `AGENTS.md` 생성 (Kiro·Codex·Agy 공용) |
| `/co-agent:consensus` | doc→plan→구현 자율 파이프라인 + 멀티모델 합의 게이트 (P0–P5, resumable) |
| `/co-agent:harness` | host 설계 / 단일 구현자 병렬 태스크 서브에이전트 / 하이브리드 게이트 리뷰 |
| `/co-agent:setup` | 패널 준비도 프리플라이트 — peer별 감지·프로브 후 readiness 요약 기록 |

## 사전 요구사항 (선택적 — 있는 것만 사용)

외부 AI CLI 중 **설치된 것만** 패널로 활용합니다. 하나도 없으면 Claude 단독 수행 + 그 사실을 명시 (절대 hard-fail 안 함).

| AI | CLI | 비고 |
|----|-----|------|
| Kiro | `kiro-cli` | 인터랙티브 로그인 **또는** `KIRO_API_KEY`로 헤드리스 인증 (둘 중 하나). 미인증 시 호출 시점에 에러→스킵 |
| Codex | `codex` | `codex exec -s read-only` (read-only 샌드박스) |
| Agy | `agy` | `agy -p … --sandbox` |

## 네 가지 모드

```mermaid
flowchart LR
    A["/co-agent"] --> P["Step 0: 패널 감지<br/>(kiro-cli/codex/agy)"]
    P --> R["Review: diff 팬아웃 → 합의/이견 종합 → PASS/REVIEW/FAIL"]
    P --> D["Decide: 옵션 팬아웃 → 비교표 → Claude 추천"]
    P --> ADR["ADR: 대안·트레이드오프 팬아웃 → Nygard ADR 초안"]
    P --> S["sync-context: CLAUDE.md 증류 → AGENTS.md"]
```

| 모드 | 트리거 | 동작 |
|------|--------|------|
| **Review** | "다른 AI로 리뷰", "second opinion", "멀티 AI" | 같은 리뷰 프롬프트를 패널에 병렬 팬아웃 → Claude가 합의/이견 종합 + Well-Architected → PASS/REVIEW/FAIL |
| **Decide** | "잘 모르겠어", "의사결정 도와", "협업해서 결정" | 결정+옵션을 패널에 질의 → 비교표(옵션×AI) → Claude 단일 추천 + 결정 트레이드오프 |
| **ADR** | "ADR 협업" | 패널에서 대안·트레이드오프·리스크 수집 → Claude가 Nygard ADR 초안 (project-init `/add-adr` 연동) |
| **sync-context** | `/co-agent:sync-context`, "AI 컨텍스트 동기화" | `CLAUDE.md`를 증류해 `AGENTS.md` 생성 (Codex 네이티브 로드, Kiro는 steering bridge, Agy는 팬아웃 fold-in) |

## 의장 원칙 (Chair Principle)

- 외부 AI는 **자문**, **Claude가 최종 결정·작성**.
- 핵심 포인트는 **출처 표기**("Agy가 지적함"), **이견은 숨기지 않고 표면화**.
- CLI 누락/에러 → 해당 AI 스킵·기록 후 진행. 단일 AI에 차단되지 않음.
- 모든 AI에 **동일 프롬프트** → 답변 비교 가능.

## 판정 기준 (Review 모드)

| 판정 | 조건 | 결과 |
|------|------|------|
| **PASS** | CRITICAL 0개, HIGH ≤ 2개 | 통과 |
| **REVIEW** | CRITICAL 0개, HIGH ≥ 3개 | 수동 승인 필요 |
| **FAIL** | CRITICAL ≥ 1개 | 머지 차단 + 수정 권고 |

## 패널 설정 (`/co-agent:configure`)

패널을 레이어드 설정으로 튜닝합니다 — `co-agent.defaults.json`(커밋) ← `.claude/co-agent.local.json`(gitignore). **CLI가 헤드리스로 실제 받는 것만** 노출합니다 (죽은 설정 없음).

| 설정 | kiro | codex | agy |
|------|------|-------|--------|
| `model` | `--model` | `-m` | `-m` |
| `effort` (`minimal\|low\|medium\|high`) | — | `-c model_reasoning_effort` | — |
| `enabled` / `timeout` | ✅ | ✅ | ✅ |
| `autosync` (글로벌, on/off) | `CLAUDE.md` 변경 시 `/co-agent:sync-context` 자동 실행 (옵트인, 기본 off) |

> `effort`는 **Codex 전용** — Agy/Kiro는 헤드리스 effort 플래그가 없습니다. 팬아웃이 설정값을 실시간으로 읽어 `enabled false`는 패널에서 제외되고 model/effort 플래그가 주입됩니다.

## AI 컨텍스트 동기화 (`/co-agent:sync-context`)

외부 AI가 프로젝트 컨벤션으로 리뷰하도록, `CLAUDE.md`를 **증류**해 각 CLI가 자동 로드하는 컨텍스트 파일을 생성합니다 (그대로 복사 ❌).

| AI | 파일 | 생성 |
|----|------|------|
| Kiro | `CLAUDE.md` 직접 | — |
| Codex | `AGENTS.md` (~32 KiB 캡) | ✅ |
| Agy | *(리포 컨텍스트 파일 없음 — 팬아웃 시 `AGENTS.md` fold-in)* | ❌ |

생성 마커(`claude-md-sha`)로 staleness를 추적하고, 마커 없는 수기 파일은 보호합니다. `CLAUDE.md` 편집 시 PostToolUse 훅이 drift를 알리며, `autosync on`이면 재동기화를 지시합니다.

## Auto-Invocation 키워드

| 한국어 | English |
|--------|---------|
| 다른 AI / 다른 AI로 리뷰 | second opinion / multi-AI review |
| AI 협업 / AI 패널 / 멀티 AI | collaborate with other AI |
| 잘 모르겠어 / 의사결정 도와 | help me decide |
| ADR 협업 | co-author ADR |
| AI 컨텍스트 동기화 | sync-context |
