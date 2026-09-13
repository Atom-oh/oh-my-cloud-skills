---
sidebar_position: 1
title: "프로젝트 초기화"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="project-init-개요" />
<span id="구성-요소" />
<span id="에이전트-1개" />
<span id="스킬-1개" />
<span id="명령-9개" />
<span id="워크플로우" />
<span id="프로젝트-초기화" />
<span id="문서-동기화" />
<span id="생성되는-구조" />
<span id="health-check-점수" />


# 프로젝트 초기화

두 호스트용 프로젝트 지침과 구조를 초기화하고 문서를 동기화하며 ADR, 운영 절차서, 참조 가이드를 작성합니다.

## 호스트별 설정 {#host-specific-setup}

Claude Code는 소스 플러그인의 명령, project-scaffolder 지식 스킬, doc-sync-checker 에이전트를 사용합니다. Codex는 초기화 절차를 AGENTS.md, `.agents/skills/`, 사용 가능한 호스트 도구에 맞춘 생성 오버레이를 사용합니다. Claude 훅 JSON을 Codex 설정처럼 설치하지 않습니다.

## 워크플로 {#workflows}

| 항목 | 결과 |
| --- | --- |
| `init-project` | 기술 스택을 감지하고 누락된 프로젝트 구조를 추가합니다. |
| `sync-docs` | 관리되는 문서를 코드와 설정에 대조합니다. |
| `add-adr` | 아키텍처 의사결정에 번호를 매기고 초안을 작성합니다. |
| `add-module` | 모듈 지침을 추가하고 아키텍처 참조를 갱신합니다. |
| `add-runbook` | 운영 절차서를 작성합니다. |
| `add-reference-doc` | docs/reference 아래에 구현 참조 자료를 작성합니다. |
| `generate-readme` | 사용자용 README를 작성하거나 갱신합니다. |
| `generate-changelog` | 릴리스 기록을 갱신합니다. |
| `health-check` | 프로젝트 설정과 문서 품질을 점검합니다. |

## 프로젝트 적응 및 품질 {#adaptation-and-quality}

기존 프로젝트는 감지된 언어, 프레임워크, 소스 구조, 사용자가 작성한 지침을 유지합니다. 생성 파일은 실제 명령과 경계를 설명해야 합니다. 사용자의 언어 요구 사항을 따릅니다. 이중 언어 템플릿은 선택적 결과물 기능이며 모든 문서를 중복 작성하라는 요구가 아닙니다.

상태 점검은 누락된 설정, 지침 품질, 아키텍처 설명 범위, 실행 가능한 수정안을 보고합니다. 수치 점수를 해석하기 전에 해당 명령의 실제 평가 기준을 읽습니다. PR 자동 수정과 의사결정 조정은 co-agent가 담당합니다.

[Codex 패키지](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/project-init/.codex-plugin/plugin.json) · [소스 구조 참조](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/project-init/skills/project-scaffolder/SKILL.md)
