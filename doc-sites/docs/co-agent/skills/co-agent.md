---
sidebar_position: 1
title: "co-agent"
---

# co-agent Skill

다른 AI(Kiro CLI, Codex, Agy)와 협업해 second opinion을 받고 **Claude가 의장으로 종합**하는 7-모드 스킬.

## 트리거

멀티-AI 의도가 명확할 때만 발동합니다 (일반 "코드 리뷰"/"decide"/"adr"은 다른 스킬과 충돌하므로 트리거가 아닙니다 — 그럴 땐 `/co-agent`를 직접 사용).

- `/co-agent`
- "second opinion", "다른 AI", "다른 AI로 리뷰", "AI 협업", "AI 패널", "멀티 AI"
- "잘 모르겠어", "의사결정 도와", "협업해서 결정"
- "ADR 협업"
- `/co-agent:sync-context`, `/co-agent:consensus`, `/co-agent:harness`, `/co-agent:setup`

## Step 0: 패널 감지 (항상 먼저)

```bash
PANEL=""
# 바이너리 존재만으로 감지 — kiro-cli는 인터랙티브 로그인 OR $KIRO_API_KEY로
# 헤드리스 인증됨. KIRO_API_KEY로 사전 게이트하지 않음(미인증이면 호출 시 에러→스킵).
command -v kiro-cli >/dev/null 2>&1 && PANEL="$PANEL kiro-cli"
command -v codex    >/dev/null 2>&1 && PANEL="$PANEL codex"
command -v agy      >/dev/null 2>&1 && PANEL="$PANEL agy"
echo "Panel: ${PANEL:-none (Claude solo)}"
```

설치된 AI CLI만 패널로 사용합니다. 없으면 Claude 단독 수행(단, consensus/harness는 예외 — 아래 참조). 패널은 `/co-agent:configure` 설정을 따릅니다 (비활성 AI 제외, model/effort/timeout 주입). `/co-agent:setup`을 먼저 실행하면 `.claude/co-agent-panel.local.json`의 실사용 readiness(READY/AUTH/TIMEOUT/ERROR/ABSENT)를 우선 참조합니다.

## AI CLI 어댑터 (read-only 자문)

| AI | 명령 | 비고 |
|----|------|------|
| Kiro | `kiro-cli chat "<P>\n\nRead the review context with fs_read from: <CTX_FILE>" --no-interactive --trust-tools=fs_read --wrap never` | `chat`은 stdin을 무시 — 컨텍스트는 임시 파일 + `fs_read` 지시로 전달 |
| Codex | `codex exec -s read-only "<P>"` | read-only 샌드박스 |
| Agy | `agy -p "<P>" --sandbox` | 3순위 피어. `-p` print 모드가 read-only 보장 |

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

## 모드 4 — sync-context (AI 컨텍스트 동기화)

`/co-agent:sync-context` 명령으로도 실행. 외부 AI가 프로젝트 컨벤션으로 리뷰하도록 `CLAUDE.md`를 **한 번만 증류**해 Kiro·Codex·Agy가 공통 참조하는 `AGENTS.md`를 생성:

1. `CLAUDE.md` 읽기 → 리뷰에 필요한 핵심만(스택·빌드/테스트 명령·금지 패턴·아키텍처 경계·리뷰 체크리스트) **증류** (그대로 복사 안 함, 시크릿 제외).
2. 생성 마커(`check_ai_context.py --emit-marker`)를 붙여 `AGENTS.md`에 기록. Kiro는 `.kiro/steering/project-context.md` → `#[[file:AGENTS.md]]` 브릿지로 같은 파일 참조.
3. Agy는 자동로드가 없어 fan-out 시점에 `AGENTS.md`를 컨텍스트로 fold-in — `check_ai_context.py --verify`로 marker/freshness/secret을 통과해야만 전송(실패 시 diff-only로 조용히 fallback).
4. 마커 없는 수기 파일/`AGENTS.override.md`는 건드리지 않음.
5. `check_ai_context.py`로 검증(마커·크기 캡·staleness·시크릿 스캔).

## 모드 5 — consensus (자율 doc→plan→구현 파이프라인)

`/co-agent:consensus`로도 실행. **host(Claude/Codex) 자신이 TDD로 구현**하고, 패널은 plan(P2)과 구현 diff(P4)를 리뷰만 합니다.

1. **Stage A (P0–P2)**: 입력 문서 감지(plan 있으면 로드, ADR/spec만 있으면 plan 생성) → 패널 합의 게이트 반복(CRITICAL/MAJOR 없을 때까지).
2. **Stage B (P3)**: task별 checkpoint → TDD → `scope_guard.py`로 plan 파일셋 검증 → 보안 mandate veto → 테스트 게이트 → 멀티모델 게이트 → 단일 커밋.
3. **Stage C (P4/P5)**: 누적 diff에 최종 게이트 → `.claude/co-agent-consensus/report.md` 리포트.
4. 로컬 커밋만. 세션 상태(`consensus_state.py`) 기반으로 재실행 시 이어서 진행(resumable).

## 모드 6 — harness (host 설계 / peer 구현 / 패널 리뷰)

`/co-agent:harness`로도 실행. **크로스벤더 peer(Codex 또는 Agy)가 격리 git worktree에서 구현**하고, host가 설계·실패 테스트·검증·**유일한 커밋 주체**입니다.

1. host가 설계 + 실패하는 테스트 작성.
2. peer가 workspace-write 샌드박스(worktree cwd로 제한)에서만 코드 작성.
3. host가 peer worktree에서 `git add -A && git diff --cached`로 캡처한 diff만 적용 — worktree 밖 쓰기는 메인 트리에 절대 반영 안 됨. 각 경로는 `scope_guard.py` 통과 필요.
4. 패널이 캡처된 diff를 리뷰(consensus 게이트 재사용) → host가 검증 후 커밋.
5. Opt-in, 로컬 커밋만. 상세 신뢰 경계: `references/delegated-implement.md`.

## 모드 7 — setup (패널 준비도 preflight)

`/co-agent:setup`으로도 실행. 각 peer의 접근경로(`plugin`→`raw`→`none`)를 감지하고 실제 프로브(짧은 프롬프트 전송)로 READY/AUTH/NO_INGEST/TIMEOUT/ERROR/ABSENT를 분류, `.claude/co-agent-panel.local.json`에 기록. review/decide/adr은 결과 없어도 solo 강등하지만, **consensus/harness는 gate-eligible peer가 0이면 solo 강등 대신 멈추고 이 명령을 안내**합니다.

## 의장 원칙

외부 AI는 자문, Claude가 최종 결정·작성. 출처 표기 + 이견 표면화. 단일 AI에 차단 금지.

> 상세 어댑터·팬아웃·폴백: 스킬의 `references/ai-cli-adapters.md`. consensus/harness 상세: `references/consensus-pipeline.md`, `references/delegated-implement.md`. 패널 설정: `/co-agent:configure`.
