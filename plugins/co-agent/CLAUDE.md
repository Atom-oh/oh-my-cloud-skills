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

패널 설정(per-AI `model`, Codex `effort`, `enabled`/`timeout`, `context_limit`, `autosync`)을 레이어드 관리: `co-agent.defaults.json` ← `.claude/co-agent.local.json`. 팬아웃이 `scripts/co_agent_config.py`(`panel`/`flags`/`timeout`/`fits`)를 **실시간** 호출 — `context_limit` 초과 AI는 하드실패 대신 **스킵**. effort는 **Codex 전용**. `autosync on` 시 CLAUDE.md 변경 → `/co-agent:sync-context` 자동.

> 설정 표·플래그 매핑 상세: **`/co-agent:configure`** 명령 + `scripts/co_agent_config.py`. (Sync-context = 스킬 Mode 4, 독립 명령 `/co-agent:sync-context` — AI Context Files 위 참조.)

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
