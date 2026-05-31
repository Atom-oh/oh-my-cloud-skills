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
  ├── Step 0: 패널 감지 (kiro / codex / gemini 중 설치된 것)
  ├── Review   : git diff → 동일 프롬프트 팬아웃 → 합의/이견 종합 → PASS/REVIEW/FAIL
  ├── Decide   : 결정+옵션 팬아웃 → 비교표 → Claude 추천 (의장)
  └── ADR      : 대안·트레이드오프·리스크 팬아웃 → Nygard ADR 초안 → /add-adr 연동
```

## AI CLI Adapters (read-only advisory)

| AI | Command |
|----|---------|
| Kiro | `kiro-cli chat "<P>" --no-interactive --trust-tools=read,grep --wrap never` |
| Codex | `codex exec -s read-only "<P>"` |
| Gemini | `gemini -p "<P>" -o text` |

> 상세: `skills/co-agent/references/ai-cli-adapters.md`. 패널은 병렬 실행, 누락/에러 시 스킵.

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
