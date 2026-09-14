---
sidebar_position: 1
title: "co-agent"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="co-agent-개요" />
<span id="구성-요소" />
<span id="에이전트-5개" />
<span id="스킬-3개" />
<span id="명령-6개" />
<span id="사전-요구사항-선택적--있는-것만-사용" />
<span id="일곱-가지-모드" />
<span id="의장-원칙-chair-principle" />
<span id="판정-기준-review-모드" />
<span id="패널-설정-co-agentconfigure" />
<span id="현재-기본값-co-agentdefaultsjson" />
<span id="ai-컨텍스트-동기화-co-agentsync-context" />
<span id="auto-invocation-키워드" />


# co-agent

외부 AI 검토를 통해 추가 의견, 의사결정, ADR, 구현 파이프라인을 지원합니다. 현재 호스트가 작업을 주도합니다.

## 6가지 스킬 모드 {#six-skill-modes}

| 모드 | 결과 | 실행 조건 |
| --- | --- | --- |
| `review` | 근거로 검증한 발견 사항과 의견 차이 | 사용 가능한 외부 AI 활용, 안내 후 단독 진행 허용 |
| `decide` | 대안 비교와 호스트의 권고 | 사용 가능한 외부 AI 활용, 안내 후 단독 진행 허용 |
| `adr` | 대안, 절충점, ADR 초안 | 사용 가능한 외부 AI 활용, 안내 후 단독 진행 허용 |
| `sync-context` | 공유 AGENTS.md와 Kiro steering 브리지 | 로컬 컨텍스트 검증 |
| `consensus` | 계획·최종 검토 게이트를 거치는 호스트 구현 | READY 외부 AI 필수 |
| `harness` | 자격을 갖춘 외부 AI 또는 명시적으로 선택한 호스트 모드의 작업 트리 구현 | 최신 READY 상태의 raw CLI 검토자 필수, 호스트가 검증과 커밋 담당 |

자격을 갖춘 READY 구현자가 없으면 harness에서 `--allow-host-implementation`으로
승인된 호스트 모드를 명시적으로 선택해야 합니다. 먼저 설정과 준비 상태의 오류를
해결해야 합니다. 두 모드 모두 최신 상태이며 게이트 참여 자격을 갖춘 검토자가 필요합니다.
[harness 계약](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/commands/harness.md)을 참고합니다.

`/co-agent:setup`은 게이트가 있는 워크플로 실행 전에 설치·인증된 외부 AI CLI를 시험하고 준비 상태를 기록하는 별도 명령입니다.

Claude Code 세션은 Claude가, Codex 세션은 Codex가 주도합니다. 호스트는 자신을 외부 AI로 호출하지 않습니다. 외부 응답은 참고 의견입니다. 호스트가 근거를 확인하고 발견 사항의 출처를 표시하며 의미 있는 의견 차이를 보고합니다.

활성 CLI 후보는 Kiro와 반대편 호스트 CLI입니다. Claude가 호스트이면 Codex를,
Codex가 호스트이면 Claude를 사용합니다. Antigravity(`agy`)와 기존 Gemini CLI는
지원이 종료되었습니다. 기존 제공자 설정을 옮긴 뒤 준비 상태를 다시 확인합니다.
지원되는 외부 AI와 구현 방식은 [v2.0.0 마이그레이션 가이드](/docs/releases/v2.0.0#co-agent-migration)에서
설명합니다.

## 구성 요소 {#components}

Claude 패키지는 `co-agent`, `gate-chair`, `harness-analyst`, `pr-autofix-planner`, `pr-autofix-implementer`를 선언하며 스킬은 `co-agent`, `pr-autofix`, `decision-reconcile`입니다. 계획자와 구현자는 준비된 입력이 필요한 내부 PR 작업자입니다. Codex는 명령 래퍼를 포함한 생성 오버레이로 이 워크플로를 제공합니다.

## 설정 및 게이트 {#configuration-and-gates}

`/co-agent:configure`로 병합된 설정, 출처, 호스트별 외부 AI 가용성을 확인합니다. 기본 설정 파일은 프로필, 모델 목록, effort, 시간 제한, 컨텍스트 한도, 호출 예산, 재시도 한도를 정의합니다. deep 프로필은 외부 AI별 여러 모델을 사용할 수 있고 default 프로필은 단일 모델 설정을 사용합니다. 설정 문자열만으로 제공자가 지원하는 모델 목록을 추정하지 않습니다.

[기준 기본 설정](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/skills/co-agent/co-agent.defaults.json)

`pr_gate.enabled`와 `push_gate.enabled`는 기본적으로 꺼져 있습니다. 이 선택적 로컬 훅은 필수 CI 및 브랜치 보호와 별개입니다. 필수 검토 범위가 누락되거나 검토가 실패했거나 오래된 결과만 있다면 성공한 검토로 간주하지 않습니다.

## 컨텍스트 동기화 {#context-synchronization}

`/co-agent:sync-context`는 `CLAUDE.md`를 생성 마커가 있는 `AGENTS.md`로 요약하고 `.kiro/steering/project-context.md` 브리지를 만듭니다. 소스 해시로 변경 불일치를 감지하며 마커 없는 수동 작성 파일은 보호합니다. 자동 동기화 안내를 사용하려면 `/co-agent:configure set autosync on`을 실행합니다.

## 관련 워크플로 {#related-workflows}

[PR 자동 수정](/docs/co-agent/skills/pr-autofix)은 검토 피드백을 반영합니다. [의사결정 조정](/docs/co-agent/skills/decision-reconcile)은 ADR 간 또는 ADR과 현재 코드 사이의 모순을 찾습니다. 일반적인 코드 검토나 단순한 “decide” 요청만으로 다중 AI 패널을 호출하지 않습니다. 외부 AI 의견이 필요하면 co-agent를 명시적으로 호출합니다.
