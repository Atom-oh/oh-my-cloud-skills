---
sidebar_position: 1
title: "명령 목록"
---

# Project Init 명령

10개의 슬래시 명령으로 프로젝트 설정부터 문서 관리, 구현 참조 문서, PR 자동 수정까지 지원합니다.

## /init-project

Claude Code 프로젝트 구조를 초기화합니다. 기존 프로젝트에서는 언어/프레임워크를 자동 감지하고, 누락된 파일만 생성합니다.

```bash
/init-project              # 현재 디렉토리
/init-project /path/to/dir # 특정 디렉토리
```

생성 항목: CLAUDE.md, settings.json, hooks, skills, commands, agents, docs, scripts, tests, README, CHANGELOG

## /sync-docs

문서와 코드를 동기화합니다. doc-sync-checker 에이전트를 실행하여 누락/오래된 문서를 감지하고 품질 점수를 보고합니다.

```bash
/sync-docs
```

## /add-adr

Architecture Decision Record를 생성합니다.

```bash
/add-adr "Use PostgreSQL for user data"
```

`docs/decisions/ADR-NNN.md` 파일이 번호 자동 부여와 함께 생성됩니다.

## /add-module

모듈 디렉토리와 CLAUDE.md를 추가합니다.

```bash
/add-module src/auth
```

디렉토리가 없으면 생성하고, 모듈 역할에 맞는 CLAUDE.md를 작성합니다.

## /add-runbook

운영 런북을 생성합니다.

```bash
/add-runbook "Database failover procedure"
```

`docs/runbooks/` 디렉토리에 표준 런북 템플릿으로 생성됩니다.

## /generate-readme

이중 언어 (영어/한국어) README.md를 생성하거나 업데이트합니다.

```bash
/generate-readme
```

프로젝트 매니페스트, git remote, 빌드 시스템에서 정보를 자동 감지합니다.

## /generate-changelog

이중 언어 (영어/한국어) CHANGELOG.md를 생성하거나 업데이트합니다.

```bash
/generate-changelog
```

git 태그와 커밋 히스토리를 분석하여 변경사항을 자동 분류합니다.

## /health-check

프로젝트 설정을 200점 척도로 검증합니다.

```bash
/health-check
```

검증 항목: 코어 파일, 훅 설정, 스킬, 문서 커버리지, 보안, CLAUDE.md 품질, 테스트 구조

## /add-reference-doc

레이어별 구현 참조 문서 스켈레톤을 `docs/reference/`에 생성합니다. (upstream implementation-reference-docs 기능)

```bash
/add-reference-doc api              # 단일 레이어
/add-reference-doc infrastructure data security  # 다중 레이어
```

유효 레이어(enum): `infrastructure`, `data`, `api`, `iac`, `frontend`, `ui`, `security`, `agent-llm`. `/init-project`의 Step 4.5(레이어 자동 감지)와 `/sync-docs`의 Phase 1.5(참조 문서 검증)가 이 기능과 연동됩니다.

## /pr-autofix

PR 생성 후 AI 리뷰와 사람 리뷰 피드백을 자동으로 읽고 코드를 수정합니다. 최대 5회 반복합니다.

```bash
/pr-autofix
```

**워크플로우:**
1. 현재 브랜치의 PR을 자동 감지
2. AI 리뷰 코멘트(`<!-- bedrock-pr-review -->`)와 사람 리뷰(`CHANGES_REQUESTED`) 동시 polling
3. 이슈 발견 시 CRITICAL → MAJOR → MINOR 순으로 수정
4. 빌드 검증 후 커밋 & push
5. 3회 반복 후에도 통과 못하면 사용자에게 수동 리뷰 요청

**제약:**
- `.github/workflows/*` 파일 수정 금지
- 리뷰에서 언급된 이슈만 수정 (추가 리팩토링 금지)
- AI 리뷰를 사용하려면 프로젝트에 `pr-review.yml` CI 워크플로우 설정 필요
