---
sidebar_position: 1
title: "프로젝트 구조 설계"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="project-scaffolder-skill" />
<span id="제공-리소스" />
<span id="references-12개-템플릿" />
<span id="프로젝트-타입-감지" />


# 프로젝트 구조 설계

이 지식 스킬은 프로젝트 구조, 범위별 지침, 문서, 호스트 연동을 설명합니다. 실제 의존성·빌드 파일에서 언어와 프레임워크를 감지하고 템플릿을 기존 저장소에 맞춥니다.

## 파일 배치 {#placement}

간결한 저장소 지침은 루트에, 모듈별 컨텍스트는 해당 모듈 옆에 둡니다. 아키텍처 가이드, ADR, 운영 절차서, 온보딩, 구현 참조는 docs 아래에 배치합니다. 스킬, 명령, 에이전트, 훅, MCP 설정은 현재 호스트가 지원하는 디렉터리와 형식을 사용합니다.

Claude 소스 템플릿은 CLAUDE.md와 `.claude/`를 설명합니다. Codex 오버레이는 적용 가능한 워크플로를 AGENTS.md와 `.agents/skills/`에 맞춥니다. Claude 전용 훅이 자동으로 호환되지는 않습니다.

## 템플릿 선택 {#template-selection}

참조 자료는 지침 품질, 설정과 훅, 스킬과 에이전트, 문서, MCP, 설정 스크립트, 테스트, 편집기 설정을 다룹니다. 프로젝트에 필요한 파일만 생성합니다. 사용자 내용을 보존하고 실행 가능한 프로젝트 명령을 사용하며 비밀 정보를 제외하고 요청한 언어를 일관되게 유지합니다.

[템플릿 디렉터리](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/project-init/skills/project-scaffolder/references/)
