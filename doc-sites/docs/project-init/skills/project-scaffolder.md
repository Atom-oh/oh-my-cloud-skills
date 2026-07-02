---
sidebar_position: 1
title: "project-scaffolder"
---

# project-scaffolder Skill

Claude Code 프로젝트 구조 패턴과 컨벤션을 제공하는 스킬입니다.

## 제공 리소스

### references/ (12개 템플릿)

| 문서 | 설명 |
|------|------|
| `claude-md-template.md` | CLAUDE.md 생성 템플릿 |
| `settings-json-template.md` | `.claude/settings.json` 훅 등록 템플릿 |
| `hook-scripts.md` | 4개 훅 스크립트 (doc-sync, secret-scan, session-context, notify) |
| `skills-templates.md` | 4개 기본 스킬 + 3개 슬래시 명령 템플릿 |
| `agents-templates.md` | code-reviewer, security-auditor 에이전트 템플릿 |
| `docs-templates.md` | architecture.md, ADR, runbook, onboarding, API reference 템플릿 |
| `readme-template.md` | 이중 언어 README.md 생성 규칙 |
| `changelog-template.md` | 이중 언어 CHANGELOG.md 생성 규칙 |
| `writing-style-guide.md` | 이중 언어 작성 스타일 가이드 (공유) |
| `scripts-templates.md` | setup.sh, install-hooks.sh 스크립트 템플릿 |
| `tests-templates.md` | run-all.sh, 훅 테스트, 구조 테스트, fixture 템플릿 |
| `mcp-json-template.md` | .mcp.json 설정 템플릿 |

## 프로젝트 타입 감지

| 감지 파일 | 프로젝트 타입 | 소스 디렉토리 |
|----------|-------------|-------------|
| `package.json` | Node.js | src/, app/, lib/, components/ |
| `pyproject.toml` | Python | src/, app/, lib/ |
| `go.mod` | Go | cmd/, pkg/, internal/ |
| `Cargo.toml` | Rust | src/ |
| `pom.xml` / `build.gradle` | Java/Kotlin | src/main/, src/test/ |
| 없음 | New project | src/api/, src/persistence/ |
