---
sidebar_position: 3
title: "decision-reconcile"
---

# decision-reconcile Skill

시간이 지나며 누적된 ADR(Architecture Decision Record)은 서로 **모순**되기 시작합니다 — 두
개의 Accepted ADR이 상반된 것을 강제하거나, 새 결정이 옛 결정을 조용히 번복하거나, ADR이
더 이상 코드와 일치하지 않습니다. 이 스킬은 그런 모순을 **다양한 에이전트 패널**(여러 모델
티어 + 여러 리뷰 렌즈)로 탐지한 뒤, 결정을 번복/조정하는 **superseding ADR** 초안을
작성합니다.

> **로컬 전용** — upstream(whchoi98/project-init)에는 포함되지 않습니다.

## 왜 단일 패스가 아니라 패널인가

단일 모델 + 단일 프롬프트는 명백한 충돌만 찾습니다. **모델 티어**와 **리뷰 렌즈**(프레이밍)를
에이전트마다 달리하면 비명백한 모순이 드러납니다 — 그 다양성이 핵심입니다.

## 흐름

```
ADR 수집(스크립트) → 결정적 사전 체크 → 다양한 패널 팬아웃
  (Claude 모델 티어 ± 외부 CLI, 각 1개 렌즈) → 인용 검증 → 합의/이견 종합
  → 해소 방안 추천 → superseding ADR 초안 → 상태 업데이트
```

## 단계

| 단계 | 동작 |
|------|------|
| 1. 수집 + 사전 체크 | `collect_adrs.py docs/decisions`로 모든 ADR을 구조화하고 LLM이 필요 없는 상태/링크 불일치(C6)를 플래그. ADR이 2개 미만이면 중단 |
| 2. 범위 확인 | Claude 모델 티어 패널은 인-프로세스라 동의 불필요. **외부 CLI도 사용**한다면 ADR 텍스트가 제3자로 나가므로 `AskUserQuestion`으로 먼저 확인 |
| 3. 패널 팬아웃 | 에이전트마다 **1개 렌즈**(L1 논리 / L2 시간 / L3 현실 드리프트 / L4 가정) + **모델 티어 변경**. 각 발견은 ADR 번호·문장 인용 필수 (인용 불가 = 발견 아님) |
| 4. 종합 | 합의/이견을 정리하고 심각도 부여, 해소 방안 추천 |
| 5. superseding ADR | 번복/조정을 담은 새 ADR 초안 작성 + 기존 ADR 상태 업데이트 |

## 패널 구성 (예시 매핑)

| 에이전트 | 모델 | 렌즈 | 반환 |
|---------|------|------|------|
| 1 | opus | L1 논리 (C1) | 충돌하는 Accepted ADR 쌍 (인용) |
| 2 | sonnet | L2 시간 (C2/C6) | 조용한 supersession, 깨진 링크 |
| 3 | sonnet | L3 현실 드리프트 (C3) | ADR vs 코드/CLAUDE.md 괴리 (file:line) |
| 4 | haiku | L4 가정 (C4/C5) | 무효화된 가정, 범위 중첩 |

**외부 CLI는 다이제스트만 받습니다** — ADR 텍스트 간 논리 충돌(C1/C4/C5)만 찾을 수 있습니다.
**C3 현실 드리프트 탐지는 Claude 티어 전용**(L3)으로, 인-프로세스 서브에이전트만 실제
코드/`CLAUDE.md`/`plugin.json`을 읽습니다. 설치된 외부 CLI가 없으면 Claude 단독 패널로
완결되며 — 절대 hard-fail 하지 않습니다.

> 모순 카테고리, 에이전트별 렌즈, 심각도 루브릭, superseding ADR 초안 규칙은
> `references/contradiction-taxonomy.md`에 있습니다.

## 트리거

`의사결정 번복`, `ADR 모순`, `ADR 충돌`, `decision reversal`, `reconcile ADRs`,
`ADR contradiction`, `supersede ADR`
