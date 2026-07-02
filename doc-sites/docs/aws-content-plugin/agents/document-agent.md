---
sidebar_position: 4
title: "Document Agent"
---

# Document Agent

기술 문서와 리포트를 생성하는 전문 에이전트입니다. 마크다운 형식의 전문적인 기술 문서, 리포트, 솔루션 비교, 아키텍처 문서를 만듭니다.

## 기본 정보

| 항목 | 값 |
|------|-----|
| **도구** | Read, Write, Glob, Grep, Bash, AskUserQuestion |

## 트리거 키워드

다음 키워드가 감지되면 자동으로 활성화됩니다:

| 키워드 | 설명 |
|--------|------|
| "create document", "write report" | 문서/리포트 생성 |
| "technical report", "comparison document" | 기술 리포트, 비교 문서 |
| "guide document", "write guide" | 가이드 문서 |

## 핵심 기능

1. **Document Structure Planning** — 논리적 계층 구조, TOC, 섹션 흐름
2. **Technical Content Generation** — 리포트, 비교, 아키텍처 문서
3. **Architecture Diagram Integration** — architecture-diagram-agent와 연계한 Draw.io 다이어그램
4. **Table Formatting** — 정렬된 마크다운 테이블

## 워크플로우

### Step 1: Requirements Analysis

- 문서 타입 결정 (리포트, 비교, 가이드, 아키텍처 문서)
- 대상 청중 식별
- 핵심 메시지와 목표 정의
- 필요한 섹션과 다이어그램 목록 작성

### Step 2: Structure Planning

- 논리적 흐름의 아웃라인 생성
- 시각적 요소 계획 (테이블, 다이어그램)
- 섹션별 콘텐츠 볼륨 추정

### Step 3: Content Creation

각 섹션마다:
- **Title**: 명확하고 행동 지향적 (최대 8단어)
- **Key Message**: 하나의 주요 테이크어웨이
- **Supporting Points**: 증거, 데이터, 예시
- **Visual Elements**: 테이블, 다이어그램, 코드 블록

### Step 4: Diagram Integration

다이어그램이 필요할 때:
1. architecture-diagram-agent를 호출하여 Draw.io 다이어그램 생성
2. .drawio를 .png로 내보내기: `drawio -x -f png -s 2 -o output.png input.drawio`
3. 이미지 참조 추가: `![Description](path/to/diagram.png)`

## 문서 템플릿

### Technical Report

```markdown
# [Document Title]

## Executive Summary
간략한 개요 (2-3 단락)

## 1. Introduction
### 1.1 Background
### 1.2 Purpose

## 2. Current State Analysis
| Category | Status | Notes |
|----------|--------|-------|

## 3. Proposed Solution
### 3.1 Architecture Overview
![Architecture Diagram](./assets/architecture.png)
### 3.2 Component Details

## 4. Implementation Plan
### 4.1 Phase 1
### 4.2 Phase 2

## 5. Conclusion

## Appendix
### A. References
### B. Glossary
```

### Solution Comparison

```markdown
# Solution Comparison: [Topic]

## Overview
| Aspect | Solution A | Solution B |
|--------|------------|------------|

## Detailed Comparison
### Category 1
| Aspect | Solution A | Solution B |
|--------|------------|------------|
| Strengths | ... | ... |
| Weaknesses | ... | ... |

## Recommendation
```

## 콘텐츠 품질 규칙

### 가독성

- **1-7-7 Rule**: 섹션당 1개 핵심 메시지, 7줄 이하, 제목 7단어 이하
- 문장 길이: 한국어 40자 이하, 영어 20단어 이하

### 데이터 인용

```
Source: [Organization], [Year]
Example: Source: Gartner, 2024
```

### 약어

- 첫 등장: "Amazon Elastic Compute Cloud (EC2)"
- 이후: "EC2"

### 이미지 Alt Text (WCAG 2.1)

```markdown
![AWS Lambda function triggering S3 event and saving to DynamoDB](arch.png)
```

## 콘텐츠 제외 규칙

**절대 포함하지 않음:**
- 인사말 ("안녕하세요", "Dear Team")
- Next Steps 섹션
- 맺음말 ("감사합니다")
- 서명 또는 날짜 스탬프
- 타임라인 추정

**문서는:**
- 제목과 목적으로 바로 시작
- 마지막 콘텐츠 섹션으로 종료
- 기술 콘텐츠에만 집중

## 출력물

| 산출물 | 형식 | 위치 |
|--------|------|------|
| Technical Document | .md | `[project]/results/[Name]_Report.md` |
| Diagrams | .drawio, .png | `[project]/diagrams/` |
| Comparison Guide | .md | `[project]/results/[Name]_Comparison.md` |

## 사용 예시

```
사용자: "EKS vs ECS 비교 문서 작성해줘"

에이전트:
1. 요구사항 분석 (비교 기준, 대상 청중)
2. 구조 계획
3. 콘텐츠 작성 (기능 비교, 장단점, 권장사항)
4. content-review-agent로 품질 검토
```

## 협업 워크플로우

```mermaid
flowchart LR
    A[document-agent] --> B[content-review-agent]
    B --> C[Final .md File]
```
