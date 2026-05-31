---
sidebar_position: 1
title: "co-agent"
---

# co-agent Skill

다른 AI(Kiro CLI, Codex, Gemini)와 협업해 second opinion을 받고 **Claude가 의장으로 종합**하는 3-모드 스킬.

## 트리거

- `/co-agent`
- "second opinion", "다른 AI", "AI 협업", "코드/아키텍처 리뷰"
- "잘 모르겠어", "의사결정", "decide", "help me decide"
- "ADR 협업", "adr"

## Step 0: 패널 감지 (항상 먼저)

```bash
PANEL=""
command -v kiro-cli >/dev/null 2>&1 && [ -n "$KIRO_API_KEY" ] && PANEL="$PANEL kiro"
command -v codex    >/dev/null 2>&1 && PANEL="$PANEL codex"
command -v gemini   >/dev/null 2>&1 && PANEL="$PANEL gemini"
echo "Panel: ${PANEL:-none (Claude solo)}"
```

설치된 AI CLI만 패널로 사용합니다. 없으면 Claude 단독 수행.

## AI CLI 어댑터 (read-only 자문)

| AI | 명령 |
|----|------|
| Kiro | `kiro-cli chat "<P>" --no-interactive --trust-tools=read,grep --wrap never` |
| Codex | `codex exec -s read-only "<P>"` |
| Gemini | `gemini -p "<P>" -o text` |

패널은 **병렬 실행**(`&` + `wait`), 각자 파일로 캡처. 빈 출력/에러 = 해당 AI 스킵.

## 모드 1 — Review

1. `git diff`로 변경 캡처(빈 diff/잘못된 base ref 가드).
2. 같은 리뷰 프롬프트를 패널에 팬아웃.
3. **Claude 종합**: 합의(≥2 AI) vs 이견(단일 AI, 출처 표기) + Well-Architected → PASS/REVIEW/FAIL.

## 모드 2 — Decide ("잘 모르겠어" / 의사결정)

1. 결정 + 옵션 확정(없으면 Claude가 2~4개 옵션 제시).
2. "이 옵션 중 하나 추천 + 근거 2~3개 + 핵심 트레이드오프"를 패널에 팬아웃.
3. **Claude 종합**: 비교표(옵션 × 각 AI 선택/근거) → 단일 추천 + 결정 트레이드오프. 의견 갈리면 그 사실을 명시.

## 모드 3 — ADR 협업

1. 컨텍스트 + 기록할 결정 확정.
2. "현실적 대안 + 트레이드오프 + 리스크"를 패널에 팬아웃.
3. **Claude가 Nygard ADR 초안** 작성(Considered Alternatives / Consequences를 패널 입력으로 보강, 출처 표기). project-init `/add-adr`과 연동해 `docs/decisions/ADR-NNN.md`에 저장.

## 의장 원칙

외부 AI는 자문, Claude가 최종 결정·작성. 출처 표기 + 이견 표면화. 단일 AI에 차단 금지.

> 상세 어댑터·팬아웃·폴백: 스킬의 `references/ai-cli-adapters.md`.
