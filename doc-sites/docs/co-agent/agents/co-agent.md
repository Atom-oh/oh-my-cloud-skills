---
sidebar_position: 1
title: "co-agent"
---

# co-agent Agent

**외부 AI 에이전트(Kiro CLI, Codex, Agy)로 구성된 패널의 의장**입니다. second opinion을 모아 **Claude가 최종 종합**합니다. 외부 AI는 항상 자문 역할이고, 결정·작성은 Claude가 합니다. 설치된 AI CLI만 사용하며 없으면 우아하게 단독 수행으로 강등됩니다.

## 트리거 키워드

멀티-AI 의도가 명확할 때만 발동합니다 — 일반 "코드 리뷰"/"decide"/"adr"은 다른 스킬과 충돌하므로 트리거가 아닙니다.

- "co-agent", "second opinion"
- "다른 AI", "다른 AI로 리뷰", "AI 협업", "AI 패널", "멀티 AI"
- "잘 모르겠어" (의사결정 도움), "ADR 협업"

## 핵심 역량

1. **Multi-AI Review** — 코드/아키텍처 리뷰 프롬프트를 사용 가능한 AI CLI에 팬아웃, 각 의견을 수집해 합의/이견 + AWS Well-Architected로 종합
2. **Decision Support** — 사용자가 확신이 없을 때("잘 모르겠어") 결정+옵션을 패널에 붙여 비교표를 만들고 종합 추천을 제시
3. **ADR Co-authoring** — 패널에서 대안/트레이드오프/리스크를 모아 Nygard 형식 ADR 초안 작성. project-init `/add-adr`과 연동

Claude가 항상 의장입니다: 각 AI의 포인트를 출처 표기하고, 이견을 표면화하며, 최종 판정은 Claude가 소유합니다.

## 모드 라우팅

```mermaid
graph TD
    A[요청] --> P[Step 0: 패널 감지<br/>kiro-cli / codex / agy 중 설치된 것]
    P --> B{의도?}
    B -->|코드/아키텍처 리뷰| R[Review: diff 팬아웃 → 종합 → PASS/REVIEW/FAIL]
    B -->|"잘 모르겠어" / 의사결정| D[Decide: 옵션 팬아웃 → 비교표 → 추천]
    B -->|ADR 작성| ADR[ADR: 대안·트레이드오프 팬아웃 → ADR 초안]
    R --> S[Claude 종합 + 출처 표기]
    D --> S
    ADR --> S
    P -->|패널 없음| SOLO[Claude 단독 수행 + 그 사실 명시]
```

`/co-agent:consensus`(host가 직접 구현, 패널은 리뷰만)와 `/co-agent:harness`(peer가 격리 worktree에서 구현), `/co-agent:setup`(패널 readiness preflight)은 별도 슬래시 명령으로 제공되며, 세부 흐름은 스킬의 `SKILL.md`에 있습니다.

## 패널 감지 (항상 Step 0)

```bash
PANEL=""
# 바이너리 존재만으로 감지 — kiro-cli는 인터랙티브 로그인 OR $KIRO_API_KEY로 헤드리스 인증됨.
# 미인증 CLI는 호출 시점에 에러 → 스킵.
command -v kiro-cli >/dev/null 2>&1 && PANEL="$PANEL kiro-cli"
command -v codex    >/dev/null 2>&1 && PANEL="$PANEL codex"
command -v agy      >/dev/null 2>&1 && PANEL="$PANEL agy"
echo "Panel: ${PANEL:-none (Claude solo)}"
```

패널 멤버는 **병렬 실행**(`&` + `wait`)하며 각자 파일로 캡처합니다. 빈 출력이나 에러는 해당 AI가 이번 실행에서 스킵됐다는 뜻 — 기록하고 계속 진행합니다.

## 의장 원칙 (Chair Principle, non-negotiable)

- 외부 AI는 **자문**; **Claude가 최종 결정·작성**.
- **출처 표기**("Agy가 지적함") — **이견은 숨기지 않고 표면화**.
- CLI 누락/에러 → 스킵, 기록, 진행. 단일 AI에 절대 차단되지 않음.
- 모든 AI에 **동일 프롬프트**를 사용해 답변을 비교 가능하게 유지.

## 다른 에이전트와의 연계

| 상황 | 연계 | 역할 분담 |
|------|------|-----------|
| 코드/PR 리뷰 | `project-init:pr-autofix` | co-agent가 멀티-AI 리뷰, pr-autofix가 피드백 반영 |
| 설계 의사결정 | `project-init:/add-adr` | co-agent가 패널 협업 + ADR 초안, add-adr이 번호 부여/저장 |
| AWS 인프라 변경 | `aws-ops-plugin` 에이전트 | co-agent가 다중 AI 설계 검증, ops가 실행 진단 |

## 참고 파일

- `references/ai-cli-adapters.md` — Kiro/Claude/Codex/Agy CLI 명령, 감지, 팬아웃, 폴백, ADR 연동
- `references/architecture-review-framework.md` — 리뷰 루브릭, 심각도, PASS/REVIEW/FAIL
- `references/aws-well-architected.md` — Review 모드용 6-필러 체크리스트
