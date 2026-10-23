---
sidebar_position: 1
title: "co-agent 역할"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="트리거-키워드" />
<span id="핵심-역량" />
<span id="모드-라우팅" />
<span id="패널-감지-항상-step-0" />
<span id="의장-원칙-chair-principle-non-negotiable" />
<span id="다른-에이전트와의-연계" />
<span id="참고-파일" />
<span id="co-agent-agent" />
<span id="co-agent-에이전트" />


# co-agent 역할

기준 `/co-agent` 스킬은 현재 호스트에서 작업을 조정합니다. 명시적으로 요청된
다중 AI 검토, 의사결정 지원, ADR 협업을 처리하고, 컨텍스트 동기화, consensus,
harness를 해당 절차로 배정합니다. Setup은 별도의 준비 상태 점검 명령입니다.
호스트가 결과를 종합하고 최종 결정을 책임지며, 별도의 `co-agent` 조정 에이전트는
없습니다. 기존 링크를 위해 이 페이지의 이전 주소를 유지합니다.

## 작업 배정 및 근거 {#routing-and-evidence}

외부 AI 감지와 해당 모드의 준비 상태 규칙부터 확인합니다. 일반적인 review/decide/ADR는 사용 가능한 외부 AI를 활용하거나 안내 후 단독으로 진행할 수 있습니다. consensus와 harness는 필요한 READY 검토 범위를 충족해야 합니다. 비교가 중요한 경우 동일한 검토 컨텍스트를 사용하고 오류를 기록하며, 주요 발견 사항을 저장소와 대조해 검증합니다.

호스트는 의견 차이를 드러내고 유용한 관찰의 출처를 표시합니다. 투표 수로 기술적 검증을 대신하지 않습니다. 외부 AI로 보내는 컨텍스트는 워크플로의 최신성 및 비밀 정보 검사를 반드시 통과해야 합니다.

## 관련 작업자 {#related-workers}

권한이 서로 다른 다음 세 에이전트는 유지합니다.

| 에이전트 | 책임과 경계 |
| --- | --- |
| `gate-chair` | 발견 사항을 검증하고 정리된 요약을 작성하며 검증 라운드를 판정합니다. 외부 AI 병렬 호출, 커밋, 설정 변경은 하지 않습니다. |
| `pr-autofix-planner` | 준비된 피드백과 제약을 읽기 전용 도구로 구조화된 수정 계획으로 변환합니다. 직접 편집하지 않습니다. |
| `pr-autofix-implementer` | 격리된 작업 트리에서 승인된 계획 항목을 편집 전용 도구로 적용합니다. Bash/network 권한이 없으며 검증과 통합은 호스트가 담당합니다. |

계획자와 구현자에는 일반적인 사용자 요청이 아니라 PR 자동 수정이 준비한 입력이
필요합니다. Codex에서는 이러한 진입점이 네이티브 역할이나 권한 부여가 아닌 절차를
제공하므로 실제 호스트 기능으로 경계를 적용해야 합니다. 의사결정 조정의 동적 검토
관점 네 가지는 변경되지 않으며 별도로 등록된 에이전트에 추가하지 않습니다.
Project-init은 결과 ADR을 작성할 수 있으며, 주제상 필요한 경우 AWS 전문가가
영역별 근거를 제공합니다.

## 폐지된 에이전트에서 마이그레이션 {#retired-agent-migration}

| 폐지된 호출 | 대체 방법 |
| --- | --- |
| 네이티브 `co-agent:co-agent` 에이전트 | 현재 호스트의 `/co-agent` 스킬을 사용합니다. 기존 Codex `co-agent` 진입점은 유지됩니다. |
| `harness-analyst` 에이전트 또는 진입점 | `/co-agent:configure analyze [session-dir]` |

분석은 harness/consensus 기록을 읽고 설정 변경을 제안하지만 직접 적용하지
않습니다. 기록된 실행이 세 번 미만이면 관찰 결과만 보고합니다. 실행 횟수는 개별
단계 행이 아니라 plan-gate 기록을 기준으로 셉니다. 모든 제안의 적용은 별도로
승인이 필요한 작업입니다.

스킬 사용 시 폐지된 래퍼의 `opus`/`xhigh` 설정을 강제하거나 해당 래퍼의 사용자
범위 에이전트 메모리를 생성하지 않습니다. 현재 호스트의 모델과 추론 설정으로
실행하며 유지되는 작업자는 각자의 설정을 계속 사용합니다. 기존 폐지 에이전트의
메모리를 이동·삭제하지 않으며 대체 절차가 자동으로 불러오지도 않습니다. 필요한
경우 검토를 거친 관련 요약 관찰만 옮기고, 메모리를 공유 컨텍스트로 그대로 복사하지
않습니다.

[기준 스킬](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/skills/co-agent/SKILL.md) · [설정 절차](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/commands/configure.md) · [Codex 진입점](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/.codex-plugin/skills/co-agent/SKILL.md)
