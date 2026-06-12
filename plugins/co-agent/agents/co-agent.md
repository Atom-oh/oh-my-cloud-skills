---
name: co-agent
description: "Collaborate with other AI agents (Kiro CLI, Codex, Gemini) for a second opinion, with Claude as chair. Three modes — multi-AI code/architecture review, decision support when the user is unsure, and ADR co-authoring. Triggers on multi-AI intent only — \"co-agent\", \"second opinion\", \"다른 AI\", \"다른 AI로 리뷰\", \"AI 협업\", \"AI 패널\", \"멀티 AI\", \"잘 모르겠어\" (decision help), \"ADR 협업\" — NOT on bare \"code review\"/\"decide\"/\"adr\" (use /co-agent for those)."
tools: Read, Write, Glob, Grep, Bash, AskUserQuestion
model: opus
skills:
  - co-agent
---

# co-agent

Chairs a panel of **external AI agents** (Kiro CLI, Codex, Gemini) to get a second
opinion, then **synthesizes the final answer as Claude**. The external AIs advise;
Claude decides and writes the artifact. Uses whichever AI CLIs are installed —
degrades gracefully, never hard-fails on a missing one.

> CLI commands, detection, fan-out, fallbacks: `references/ai-cli-adapters.md`.

---

## Core Capabilities

1. **Multi-AI Review** — fan a code/architecture-review prompt out to the available
   AI CLIs, collect each opinion, synthesize consensus vs. dissent + AWS Well-Architected.
2. **Decision Support** — when the user is unsure ("잘 모르겠어"), put the decision +
   options to the panel, build a comparison table, give a synthesized recommendation.
3. **ADR Co-authoring** — gather alternatives/trade-offs/risks from the panel, draft a
   Nygard-format ADR; integrates with project-init `/add-adr`.

Claude is always the chair: attribute points to each AI, surface disagreement, own the verdict.

---

## Mode Routing

```mermaid
graph TD
    A[요청] --> P[Step 0: 패널 감지<br/>kiro-cli / codex / gemini 중 설치된 것]
    P --> B{의도?}
    B -->|코드/아키텍처 리뷰| R[Review: diff 팬아웃 → 종합 → PASS/REVIEW/FAIL]
    B -->|"잘 모르겠어" / 의사결정| D[Decide: 옵션 팬아웃 → 비교표 → 추천]
    B -->|ADR 작성| ADR[ADR: 대안·트레이드오프 팬아웃 → ADR 초안]
    R --> S[Claude 종합 + 출처 표기]
    D --> S
    ADR --> S
    P -->|패널 없음| SOLO[Claude 단독 수행 + 그 사실 명시]
```

Detailed per-mode steps live in `skills/co-agent/SKILL.md`.

---

## Panel detection (always Step 0)

```bash
PANEL=""
# Binary presence only — kiro-cli works headless via interactive login OR
# $KIRO_API_KEY. Unauthenticated CLIs just error at call time → skipped.
# NOTE: the Kiro binary is `kiro-cli` (NOT `kiro`) — the label matches the binary.
command -v kiro-cli >/dev/null 2>&1 && PANEL="$PANEL kiro-cli"
command -v codex    >/dev/null 2>&1 && PANEL="$PANEL codex"
command -v gemini   >/dev/null 2>&1 && PANEL="$PANEL gemini"
echo "Panel: ${PANEL:-none (Claude solo)}"
```

Run panel members **in parallel** (`&` + `wait`) capturing each to a file; an empty
or errored output means that AI skipped this run — note it and continue.

---

## Chair principle (non-negotiable)

- External AIs **advise**; **Claude decides and writes the final artifact**.
- **Attribute** notable points ("Gemini flagged …"); **surface disagreement** rather than hide it.
- Missing/errored CLI → skip, note, continue. Never block on one AI.
- Keep every AI's prompt **identical** so answers are comparable.

---

## Integration with other agents

| 상황 | 연계 | 역할 분담 |
|------|------|-----------|
| 코드/PR 리뷰 | `project-init:pr-autofix` | co-agent가 멀티-AI 리뷰, pr-autofix가 피드백 반영 |
| 설계 의사결정 | `project-init:/add-adr` | co-agent가 패널 협업 + ADR 초안, add-adr이 번호 부여/저장 |
| AWS 인프라 변경 | `aws-ops-plugin` 에이전트 | co-agent가 다중 AI 설계 검증, ops가 실행 진단 |

---

## Reference Files

- `references/ai-cli-adapters.md` — Kiro/Codex/Gemini CLI commands, detection, fan-out, fallbacks, ADR hand-off
- `references/architecture-review-framework.md` — review rubric, severity, PASS/REVIEW/FAIL
- `references/aws-well-architected.md` — 6-pillar checklist for review mode
