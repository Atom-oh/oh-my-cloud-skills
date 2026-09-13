---
sidebar_position: 1
title: "AgentCore 생성 에이전트"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="트리거-키워드" />
<span id="기능" />
<span id="사용-예시" />
<span id="새-에이전트-설계-및-배포" />
<span id="기존-플러그인-변환" />
<span id="출력물" />


# AgentCore 생성 에이전트

아이디어나 기존 플러그인에서 시작해 로컬로 검증한 설계와 AgentCore 배포 후보를 준비하도록 안내합니다.

## 역할 {#responsibilities}

요구 사항을 파악하고 스킬, 참조 자료, 도구, 상태를 설계합니다. harness 설정 또는 Runtime 생성을 선택하고 로컬에서 빌드·테스트한 뒤 변환합니다. 이후 사용자 승인 범위 안에서 배포하고 스모크 테스트를 수행합니다. 파일·리소스 계획을 구체적으로 유지하고 각 단계의 결과를 기록합니다.

기존 플러그인은 매니페스트, 스킬, 에이전트 지침, MCP 도구, 참조 자료, 훅을 확인합니다. 호스트 전용 훅이 관리형 harness 동작으로 자동 전환된다고 설명하지 않습니다. 선택한 harness 경로로 필요한 사용자 정의 오케스트레이션을 표현할 수 없으면 Runtime을 선택합니다.

## 결과물 {#output}

생성된 설정·코드, 의존성, 도구와 메모리 매핑, 로컬 테스트 결과, 제안하는 배포 명령을 제공합니다. 승인된 배포 후에는 자격 증명을 노출하지 않고 리소스 식별자와 실제 호출 결과를 보고합니다.

[에이전트 정의](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/agentcore-creator/agents/agentcore-creator-agent.md)
