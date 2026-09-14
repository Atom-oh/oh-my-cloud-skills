---
sidebar_position: 1
title: "co-agent 명령어"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="co-agent-명령" />
<span id="push_gate--pr_autofix-설정-추가분" />


# co-agent 명령어

## /co-agent:configure {#co-agent}

병합된 설정과 출처를 표시합니다. 외부 AI 모델, 프로필, 어댑터가 지원하는 effort, 활성화 여부, 시간 제한, 컨텍스트 예산, autosync, harness 한도, PR 자동 수정 반복 횟수, 선택적 PR·푸시 게이트를 설정합니다.

```text
/co-agent:configure
/co-agent:configure set autosync on
/co-agent:configure set pr_autofix max_iterations 5
```

[기본 설정 및 정확한 키](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/skills/co-agent/co-agent.defaults.json)

선택적 훅 게이트는 기본적으로 꺼져 있으며 필수 CI와 브랜치 보호는 별도로 유지됩니다.
`pr_gate` 또는 `push_gate`를 켜면 검토할 diff를 외부 AI 서비스로 전송하는 데 동의합니다.
git이 추적하는 `.claude/co-agent.local.json`은 어느 게이트도 활성화할 수 없습니다.
[설정 계약](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/commands/configure.md)을 참고합니다.

## /co-agent:sync-context {#co-agent-1}

CLAUDE.md에서 생성 마커가 있는 AGENTS.md를 만들고 Kiro steering 브리지를 연결합니다. 소스 해시로 오래된 생성 컨텍스트를 식별하며, 마커 없는 수동 작성 파일은 보호합니다. Antigravity는 더 이상 co-agent의 외부 AI가 아닙니다.

## /co-agent:consensus {#co-agent-2}

문서 → 계획 → 구현 워크플로를 실행합니다. 호스트가 구현하고 외부 AI가 계획과 최종 diff를 검토합니다. READY 외부 AI가 반드시 필요하며 파이프라인은 설정된 라운드·호출 예산과 저장된 실행 상태를 사용합니다.

## /co-agent:harness {#co-agent-3}

호스트가 설계와 테스트를 책임지고 캡처된 변경을 검토한 뒤 커밋합니다. 자격을 갖춘
READY 외부 AI가 격리된 작업 트리에서 구현합니다. 사용할 수 있는 구현자가 없다면
`--allow-host-implementation`으로 승인된 호스트 계획을 명시적으로 선택합니다. 어느 모드든
활성화되어 있고 최신 READY 상태인 raw CLI 검토자가 반드시 필요합니다. 설정이나 준비 상태에
오류가 있으면 계획을 중단합니다. Kiro는 외부 구현자로 사용할 수 없습니다. 정확한 역할과 모드
규칙은 [harness 계약](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/commands/harness.md)을 따릅니다.

## /co-agent:setup {#co-agent-4}

플러그인과 CLI 접근 경로를 감지하고 실제 사용 가능 여부를 시험하여 준비 상태를 기록합니다. 인증이나 모델 호출 실패는 해결해야 할 설정 실패이며 성공한 검토로 계산하지 않습니다.

## /co-agent:pr-autofix {#co-agent-5}

검토 피드백을 주기적으로 확인하고 검증된 수정 계획을 세웁니다. 설정된 반복 한도 안에서 격리된 작업 트리에 수정을 적용하고 검증·커밋·푸시합니다. 새 HEAD의 검토와 CI를 다시 확인하고 저장소의 승인 및 병합 규칙을 따릅니다.

먼저 사용 프로젝트의 검토 워크플로와 대응하는 게이트 도우미를 설정합니다. 이 반복 절차는
`.github/workflows/*`를 수정하지 않습니다. [PR 자동 수정 설정과 경계](/docs/co-agent/skills/pr-autofix#limits-and-integration)를 참고합니다.

Codex에서는 이 명령 워크플로가 생성된 스킬 항목으로 제공됩니다. Claude 명령 등록이 공유된다고 가정하지 말고 대응하는 설치 항목을 선택합니다.
