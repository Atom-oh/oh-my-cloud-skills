---
sidebar_position: 1
title: "co-agent"
---

# co-agent Skill

다른 AI(Kiro CLI, peer host CLI, Agy 우선/Gemini fallback)와 협업해 second opinion을 받고 **현재 host가 의장으로 종합**하는 4-모드 스킬.

## 트리거

멀티-AI 의도가 명확할 때만 발동합니다 (일반 "코드 리뷰"/"decide"/"adr"은 다른 스킬과 충돌하므로 트리거가 아닙니다 — 그럴 땐 `/co-agent`를 직접 사용).

- `/co-agent`
- "second opinion", "다른 AI", "다른 AI로 리뷰", "AI 협업", "AI 패널", "멀티 AI"
- "잘 모르겠어", "의사결정 도와", "협업해서 결정"
- "ADR 협업"
- "AI 컨텍스트 동기화" (`/co-agent:sync-context`)

## Step 0: 패널 감지 (항상 먼저)

```bash
PANEL=""
# 바이너리 존재만으로 감지 — kiro-cli는 인터랙티브 로그인 OR $KIRO_API_KEY로
# 헤드리스 인증됨. KIRO_API_KEY로 사전 게이트하지 않음(미인증이면 호출 시 에러→스킵).
command -v kiro-cli >/dev/null 2>&1 && PANEL="$PANEL kiro-cli"
HOST="${CO_AGENT_HOST:-claude}"
python3 "$CLAUDE_PLUGIN_ROOT/skills/co-agent/scripts/co_agent_config.py" panel --host "$HOST"
```

설치된 AI CLI만 패널로 사용합니다. 없으면 현재 host 단독 수행. 패널은 `/co-agent:configure` 설정을 따릅니다 (비활성 AI 제외, model/effort/timeout 주입). Claude Code host는 Codex를 peer로 쓰고, Codex host는 Claude를 peer로 씁니다. Agy가 우선이며 없을 때만 Gemini를 fallback으로 씁니다.

## AI CLI 어댑터 (read-only 자문)

| AI | 명령 |
|----|------|
| Kiro | `kiro-cli chat "<P>" --no-interactive --trust-tools=read,grep --wrap never` |
| Claude | `claude -p "<P>" --permission-mode plan --tools Read,Grep,Glob --output-format text` |
| Codex | `codex exec -s read-only "<P>"` |
| Agy | `agy -p "<P>" --sandbox` |
| Gemini fallback | `gemini -p "<P>" -o text` |

패널은 **병렬 실행**(`&` + `wait`), 각자 파일로 캡처. 빈 출력/에러 = 해당 AI 스킵.

## 모드 1 — Review

1. `git diff`로 변경 캡처(빈 diff/잘못된 base ref 가드).
2. 같은 리뷰 프롬프트를 패널에 팬아웃.
3. **Host 종합**: 합의(≥2 AI) vs 이견(단일 AI, 출처 표기) + Well-Architected → PASS/REVIEW/FAIL.

## 모드 2 — Decide ("잘 모르겠어" / 의사결정)

1. 결정 + 옵션 확정(없으면 host가 2~4개 옵션 제시).
2. "이 옵션 중 하나 추천 + 근거 2~3개 + 핵심 트레이드오프"를 패널에 팬아웃.
3. **Host 종합**: 비교표(옵션 × 각 AI 선택/근거) → 단일 추천 + 결정 트레이드오프. 의견 갈리면 그 사실을 명시.

## 모드 3 — ADR 협업

1. 컨텍스트 + 기록할 결정 확정.
2. "현실적 대안 + 트레이드오프 + 리스크"를 패널에 팬아웃.
3. **Host가 Nygard ADR 초안** 작성(Considered Alternatives / Consequences를 패널 입력으로 보강, 출처 표기). project-init `/add-adr`과 연동해 `docs/decisions/ADR-NNN.md`에 저장.

## 모드 4 — sync-context (AI 컨텍스트 동기화)

`/co-agent:sync-context` 명령으로도 실행. 외부 AI가 프로젝트 컨벤션으로 리뷰하도록 `CLAUDE.md`를 **증류**해 각 CLI의 컨텍스트 파일 생성:

1. `CLAUDE.md` 읽기 → 리뷰에 필요한 핵심만(스택·빌드/테스트 명령·금지 패턴·아키텍처 경계·리뷰 체크리스트) **증류** (그대로 복사 ❌, 시크릿 ❌).
2. 생성 마커(`check_ai_context.py --emit-marker`)를 붙여 `AGENTS.md`(Codex)·`GEMINI.md`(Gemini fallback)에 기록. Kiro는 `CLAUDE.md` 직접 사용.
3. 마커 없는 수기 파일/`AGENTS.override.md`는 건드리지 않음.
4. `check_ai_context.py`로 검증(마커·크기 캡·staleness·시크릿 스캔).

## 의장 원칙

외부 AI는 자문, 현재 host가 최종 결정·작성. 출처 표기 + 이견 표면화. 단일 AI에 차단 금지.

> 상세 어댑터·팬아웃·폴백: 스킬의 `references/ai-cli-adapters.md`. 패널 설정: `/co-agent:configure`.
