# ADR-006: project-init Plugin Introduction

## Status

Accepted (2026-04-20)

## Context

프로젝트 초기화(CLAUDE.md 생성, ADR 관리, 문서 동기화)를 위한 명령들이 루트 수준에 산재하여 재사용과 유지보수가 어려웠다. 여러 프로젝트에서 동일한 패턴(CLAUDE.md, docs/decisions/, CHANGELOG.md)을 반복 생성하고 있었다.

## Decision

`project-init` 플러그인을 독립 플러그인으로 분리한다:
- 1 agent (`doc-sync-checker`): 문서 동기화 분석 및 품질 점수 산정
- 1 skill (`project-scaffolder`): Claude Code 프로젝트 구조 패턴
- 8 commands: `/init-project`, `/sync-docs`, `/add-adr`, `/add-module`, `/add-runbook`, `/generate-readme`, `/generate-changelog`, `/health-check`

## Consequences

- 문서 동기화 상태를 100점 만점으로 정량화 가능
- `/sync-docs`로 누락 CLAUDE.md, 버전 불일치, ADR 누락을 자동 감지
- 다른 프로젝트에서도 플러그인으로 바로 사용 가능

## References

- Commit: 375ac6e
- Plugin path: `plugins/project-init/`
