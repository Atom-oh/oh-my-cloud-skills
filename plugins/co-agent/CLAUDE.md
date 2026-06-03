# co-agent Plugin — Claude Code Configuration

다른 AI 에이전트(Kiro CLI, Codex, Gemini)와 협업해 **second opinion**을 받고, **Claude가 의장으로 종합**하는 플러그인. 세 가지 모드: 멀티-AI 리뷰, 의사결정 보조, ADR 협업.

**Prerequisites (선택적 — 있는 것만 사용)**: `kiro-cli`(+`KIRO_API_KEY`), `codex`, `gemini` CLI 중 설치된 것을 패널로 활용. 하나도 없으면 Claude 단독 수행 + 그 사실을 명시. 절대 hard-fail 하지 않음.

---

## Agent

| Agent | Purpose |
|-------|---------|
| `co-agent` | 멀티-AI 패널 의장 — 리뷰/의사결정/ADR을 외부 AI에 팬아웃하고 Claude가 종합 |

## Skill

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `co-agent` | "co-agent", "second opinion", "다른 AI", "AI 협업", "코드/아키텍처 리뷰", "잘 모르겠어", "의사결정", "decide", "adr" | 3-모드 멀티-AI 협업 |

## Three Modes

```
co-agent
  ├── Step 0: 패널 감지 (kiro-cli / codex / gemini 중 설치된 것; Kiro 바이너리는 `kiro-cli`, NOT `kiro`)
  ├── Review       : git diff → 동일 프롬프트 팬아웃 → 합의/이견 종합 → PASS/REVIEW/FAIL
  ├── Decide       : 결정+옵션 팬아웃 → 비교표 → Claude 추천 (의장)
  ├── ADR          : 대안·트레이드오프·리스크 팬아웃 → Nygard ADR 초안 → /add-adr 연동
  └── sync-context : CLAUDE.md 증류 → AGENTS.md(Codex)·GEMINI.md(Gemini) 생성 (Kiro는 CLAUDE.md 직접 사용)
```

## AI Context Files (per-AI project docs)

각 AI CLI가 리포 루트에서 자동 로드하는 컨텍스트 파일. co-agent가 **CLAUDE.md를 증류(distill)** 해 생성 — 복사 ❌.

| AI | 파일 | 생성? |
|----|------|-------|
| Kiro | `CLAUDE.md` (직접 읽음) | ❌ |
| Codex | `AGENTS.md` (~32 KiB cap) | ✅ |
| Gemini | `GEMINI.md` (lean 유지) | ✅ |

생성 마커(`generated-by: co-agent · claude-md-sha:`)로 staleness/수기파일 보호. `scripts/check_ai_context.py`가 검증(크기·마커·동기화·시크릿 스캔). CLAUDE.md 편집 시 PostToolUse 훅이 동기화 알림.

## AI CLI Adapters (read-only advisory)

| AI | Command |
|----|---------|
| Kiro | `kiro-cli chat "<P>" --no-interactive --trust-tools=read,grep --wrap never` |
| Codex | `codex exec -s read-only "<P>"` |
| Gemini | `gemini -p "<P>" -o text` |

> 상세: `skills/co-agent/references/ai-cli-adapters.md`. 패널은 병렬 실행, 누락/에러 시 스킵.

## Configure (`/co-agent:configure`)

패널 설정을 레이어드(`co-agent.defaults.json` ← `.claude/co-agent.local.json`)로 관리. **CLI가 헤드리스로 실제 받는 것만** 노출:

| 설정 | kiro | codex | gemini |
|------|------|-------|--------|
| model | `--model` | `-m` | `-m` |
| effort | — | `-c model_reasoning_effort` | — |
| enabled / timeout | ✅ | ✅ | ✅ |
| context_limit (토큰) | 1,000,000 | 272,000 | 1,000,000 |
| autosync (global) | `set autosync on` → CLAUDE.md 변경 시 `/co-agent:sync-context` 자동 실행 (옵트인, 기본 off) |

> effort는 **Codex 전용** (Gemini/Kiro는 헤드리스 effort 플래그 없음 — dead 설정 미노출). 팬아웃이 `co_agent_config.py`의 `panel`/`flags`/`timeout`/`fits`을 호출해 설정이 **실시간 반영**됨. `context_limit` 초과 AI는 하드 실패 대신 **스킵**(예: 거대 diff에서 Codex 272K 초과 → Kiro/Gemini만). model 값은 charset 검증으로 팬아웃 주입 차단.

## Sync-context (`/co-agent:sync-context`)

`CLAUDE.md`를 **증류**해 외부 AI가 읽는 컨텍스트 파일 생성 (스킬 Mode 4를 독립 명령으로 노출). Codex→`AGENTS.md`, Gemini→`GEMINI.md`, Kiro→`CLAUDE.md` 직접. 생성 마커로 staleness 추적·수기파일 보호. `CLAUDE.md` PostToolUse 훅이 drift 알림 — `autosync on`이면 Claude에게 재동기화 지시.

## Chair Principle

외부 AI는 **자문**, **Claude가 최종 결정·작성**. 출처 표기 + 이견 명시. 단일 AI에 의존/차단 금지.

## Auto-Invocation Keywords

| 한국어 | English |
|--------|---------|
| 다른 AI 협업 | collaborate with other AI |
| 코드 리뷰 | code review |
| 잘 모르겠어 / 의사결정 | help me decide |
| ADR 협업 | co-author ADR |
| second opinion | second opinion |
