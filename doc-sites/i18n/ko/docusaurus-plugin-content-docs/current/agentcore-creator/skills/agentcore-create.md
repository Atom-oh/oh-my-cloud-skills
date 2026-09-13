---
sidebar_position: 1
title: "AgentCore 생성 스킬"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="트리거" />
<span id="제공-리소스" />
<span id="scripts" />
<span id="references" />
<span id="워크플로우" />
<span id="phase-1-discovery" />
<span id="phase-2-design" />
<span id="phase-3-skill-first-build" />
<span id="phase-4-agentcore-convert" />
<span id="phase-5-deploy--verify" />


# AgentCore 생성 스킬

새 에이전트에는 `agentcore-create`를, 기존 플러그인에는 `convert <plugin-path>`를 사용합니다. 로컬, GitHub, 마켓플레이스 입력을 지원하며 변환 전에 의도한 플러그인을 반드시 식별해야 합니다.

## 설계 및 로컬 개발 {#design-and-local-build}

목적, 사용자, 도구, 지식, 대상, 성공 기준을 정리하고 구체적인 파일 계획을 작성합니다. 클라우드 변환 전에 스킬·플러그인을 로컬에서 개발하고 대표 요청과 예외 사례를 테스트합니다. Codex 테스트에는 에이전트 지침을 불러오는 노출된 `.agents/skills/` 항목이 필요합니다. Claude 에이전트 파일 이름만으로 Codex 작업자가 등록되지는 않습니다.

## 변환 경로 {#conversion-paths}

Harness는 모델, 지침, 도구, 스킬, 지원되는 관리형 기능의 설정을 생성합니다. Runtime은 AgentCore용으로 래핑한 Strands 애플리케이션을 생성합니다. 필요한 오케스트레이션, 스트리밍, 프레임워크, 도구 동작을 기준으로 선택합니다. 모델별 요청 호환성과 ID는 변환기의 매핑 및 참조 파일을 따릅니다.

## 배포 검증 {#deployment-verification}

리소스 계획, 계정·리전, 실행 주체(ID/역할), 도구 인증, 메모리 요구 사항, 의존성을 검토합니다. 승인된 리소스 생성만 수행하고 배포된 에이전트를 호출하여 관찰한 출력을 기록합니다. 설정이 생성되었다는 사실만으로 배포 성공을 입증할 수는 없습니다.

[전체 단계 및 명령어](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/agentcore-creator/skills/agentcore-create/SKILL.md)
