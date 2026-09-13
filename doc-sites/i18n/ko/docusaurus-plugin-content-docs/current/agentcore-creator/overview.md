---
sidebar_position: 1
title: "AgentCore 생성 도구"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="agentcore-creator-개요" />
<span id="구성-요소" />
<span id="에이전트-1개" />
<span id="스킬-1개" />
<span id="사전-요구사항" />
<span id="워크플로우" />
<span id="5-phase-상세" />
<span id="agentcore-구성-요소" />
<span id="auto-invocation-키워드" />


# AgentCore 생성 도구

에이전트를 로컬에서 설계·테스트한 뒤 AgentCore harness 설정 또는 생성된 Runtime 애플리케이션을 준비합니다.

## 5단계 과정 {#five-phases}

| 단계 | 결과 |
| --- | --- |
| 요구 사항 탐색 | 목적, 사용자, 기능, 도구, 지식, 성공 기준 |
| 설계 | 승인된 구성 요소 계획과 harness/Runtime 대상 |
| 스킬 우선 개발 | 로컬에서 테스트한 플러그인 또는 호스트가 접근할 수 있는 스킬 |
| 변환 | harness 설정 또는 생성된 Strands/Runtime 코드 |
| 배포 및 검증 | 승인된 리소스 생성과 스모크 테스트 근거 |

기존 플러그인 경로는 변환 단계부터 시작하고 새 아이디어는 요구 사항 탐색부터 시작합니다. harness 설정은 관리형 루프에 스킬과 도구를 연결합니다. 설계에 사용자 정의 오케스트레이션이나 런타임 동작이 필요하면 Runtime 생성으로 Strands 애플리케이션을 제공합니다.

## 구성 요소 및 연동 {#components-and-integration}

이 패키지는 agentcore-creator-agent와 agentcore-create를 제공합니다. 워크플로는 Gateway를 통해 도구를 매핑하고 필요한 경우 Memory를 계획할 수 있습니다. 어느 호스트에서도 변환 입력은 `.claude-plugin/plugin.json`을 사용합니다. Codex 로컬 테스트에는 관련 지침을 불러오는 호스트 노출 스킬이 추가로 필요합니다.

모델 매핑과 호환성 규칙은 변환기와 참조 자료에 정의되어 있습니다. 만들어 낸 모델 ID나 오래된 ID를 복사하지 말고 실제 배포에서 사용할 수 있는 모델을 확인합니다. 리소스 생성은 후보를 검토할 수 있는 상태로 만든 뒤 별도로 승인받아 진행하는 단계입니다.

[워크플로 계약](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/agentcore-creator/skills/agentcore-create/SKILL.md) · [변환기 및 모델 매핑](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/agentcore-creator/skills/agentcore-create/scripts/convert_plugin_to_agentcore.py)
