---
sidebar_position: 1
title: "Doc Sync Checker"
---

# Doc Sync Checker Agent

프로젝트 문서가 현재 코드 상태와 동기화되어 있는지 분석하고, 누락되거나 오래된 문서를 품질 점수와 함께 보고하는 에이전트입니다.

## 기능

1. **소스 디렉토리 감지** — `src/`, `app/`, `lib/`, `cmd/` 등 주요 소스 디렉토리 탐색
2. **누락 CLAUDE.md 감지** — 각 소스 디렉토리에 모듈 CLAUDE.md 존재 여부 확인
3. **아키텍처 문서 검증** — `docs/architecture.md`의 컴포넌트, 다이어그램, 레이어 커버리지 확인
4. **ADR 커버리지** — git log에서 아키텍처 결정을 시사하는 커밋과 ADR 매칭
5. **이중 언어 일관성** — 한국어/영어 섹션 구조 일치 확인
6. **CLAUDE.md 품질 평가** — 500줄 이하, 기술 스택, 핵심 명령, 프로젝트 구조 섹션 존재 여부

## 사용 방법

```
"/sync-docs"
```

또는 doc-sync-checker 에이전트가 자동으로 활성화됩니다.

## 출력 형식

```markdown
## Documentation Sync Report

### Missing Module CLAUDE.md
- src/api/ — MISSING
- src/persistence/ — OK

### Architecture Doc Freshness
- Component Sync: 3/5 match
- Diagram Accuracy: OK
- Layer Coverage: 80%

### CLAUDE.md Quality: 85/100 (Grade: A)
- ✓ Under 500 lines
- ✓ Has Tech Stack section
- ✗ Missing Key Commands section

### Recommendations
1. Add CLAUDE.md to src/api/
2. Update architecture diagram with new components
```
