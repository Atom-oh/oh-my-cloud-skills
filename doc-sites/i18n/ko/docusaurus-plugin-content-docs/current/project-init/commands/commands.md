---
sidebar_position: 1
title: "프로젝트 초기화 명령어"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="project-init-명령" />


# 프로젝트 초기화 명령어

Claude Code에서는 슬래시 명령으로 사용합니다. Codex에서는 대응하는 생성 스킬을 사용합니다. `source-command-health-check`는 프로젝트 설정 점검을 AWS 상태 점검과 구분하는 이름입니다.

## /init-project {#init-project}

저장소의 언어, 프레임워크, 명령, 기존 구조를 감지합니다. 수동 작성 내용을 덮어쓰지 않고 누락된 지침, 문서, 스킬, 지원되는 호스트 연동 파일을 생성합니다.

## /sync-docs {#sync-docs}

관리되는 문서를 소스와 설정에 대조해 점검하고 오래된 명령, 수치, 경로, 아키텍처 설명을 갱신합니다. 자주 바뀌는 세부 사항은 하나의 기준 설명으로 관리합니다.

## /add-adr {#add-adr}

배경, 대안, 결정, 결과를 포함하는 번호가 있는 의사결정 기록을 작성합니다. 필요한 경우 대체된 기록을 연결합니다.

## /add-module {#add-module}

모듈 디렉터리와 해당 범위의 지침을 추가한 뒤 아키텍처 문서에 역할과 의존성을 반영합니다.

## /add-runbook {#add-runbook}

사전 조건, 작업, 예상 출력, 검증, 복구 단계를 포함한 운영 절차서를 작성합니다.

## /add-reference-doc {#add-reference-doc}

선택한 계층의 구현 참조 자료를 `docs/reference/` 아래에 추가하고 담당 지침에서 연결합니다.

## /generate-readme {#generate-readme}

프로젝트의 실제 목적, 설치, 사용법, 개발 명령, 기여 절차를 설명합니다. 요청한 언어를 따릅니다.

## /generate-changelog {#generate-changelog}

프로젝트의 버전 및 변경 기록 규칙에 따라 릴리스 변경을 기록합니다. 실제 출시된 동작을 설명하고 릴리스 날짜를 만들어 내지 않습니다.

## /health-check {#health-check}

파일, 훅, 권한, 지침 품질, 설정을 검증합니다. 평가 기준, 근거, 수정안을 보고합니다. 상태 점수는 필수 테스트 모음을 대체하지 않습니다.
