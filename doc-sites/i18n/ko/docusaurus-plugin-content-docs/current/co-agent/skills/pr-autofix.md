---
sidebar_position: 2
title: "PR 자동 수정"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="pr-autofix-skill" />
<span id="리뷰-소스" />
<span id="워크플로우" />
<span id="판정-기준" />
<span id="제약-사항" />
<span id="레퍼런스" />
<span id="pr-review-workflowyml" />


# PR 자동 수정

PR 자동 수정은 AI와 사람의 검토 피드백을 모아 발견 사항을 코드와 대조하고, 분리된 계획·구현 작업자로 범위가 제한된 수정을 적용합니다.

## 피드백 반복 절차 {#feedback-loop}

1. PR의 현재 HEAD, 검토 요약, 인라인 댓글, 미해결 스레드, 검사 결과를 확인합니다.
2. 오래되었거나 근거 없는 발견 사항은 제외하고 확인된 문제의 구체적인 수정 계획을 준비합니다.
3. 격리된 작업 트리에 계획을 적용하고 관련 테스트와 필수 검사를 실행한 뒤 커밋하고 푸시합니다.
4. 새 HEAD의 검토를 기다린 뒤 `pr_autofix.max_iterations` 한도 안에서 반복합니다.
5. 남은 발견 사항, 검토 범위, 검사 결과, 최종 PR 상태를 보고합니다.

검토 실패, 응답 누락, 이전 커밋의 검토는 현재 변경에 문제가 없다는 근거가 아닙니다. 영향받는 런타임 경로와 대조해 심각도를 검증하고 모든 제안을 자동으로 구현하지 않습니다.

## 제한 및 연동 {#limits-and-integration}

[기준 반복 횟수 설정](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/skills/co-agent/co-agent.defaults.json)

AI 검토를 사용하려면 사용 프로젝트에 예제 워크플로와 대응하는 게이트 도우미를
설치해야 합니다. [CI 워크플로 설정](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/skills/pr-autofix/SKILL.md#ci-workflow-setup)을 따릅니다.
자동 수정 반복 절차는 `.github/workflows/*`를 수정하지 않습니다. 해당 자동화는 별도로 설정합니다.

이 스킬 자체가 병합 권한을 부여하거나 보호 규칙을 우회하지는 않습니다. 저장소의 명시적인 검토 및 병합 정책을 따릅니다. 선택적 로컬 검토 훅과 CI 검토 워크플로는 별개의 통제입니다.

[스킬 계약](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/skills/pr-autofix/SKILL.md) · [검토 워크플로 예제](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/skills/pr-autofix/references/pr-review-workflow.yml)
