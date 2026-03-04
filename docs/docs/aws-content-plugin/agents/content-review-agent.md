---
sidebar_position: 7
title: "Content Review Agent"
---

# Content Review Agent

모든 콘텐츠 타입에 대한 포괄적인 품질 검토를 수행하는 에이전트입니다. 레이아웃, 용어, 환각 탐지, 언어, PII/민감 데이터, 가독성, 접근성, 구조적 완전성을 검사합니다.

## 기본 정보

| 항목 | 값 |
|------|-----|
| **모델** | sonnet |
| **도구** | Read, Write, Glob, Grep, Bash, AskUserQuestion |

## 트리거 키워드

다음 키워드가 감지되면 자동으로 활성화됩니다:

| 키워드 | 설명 |
|--------|------|
| "review content", "quality check" | 콘텐츠 검토 |
| "review document", "review presentation" | 문서/프레젠테이션 검토 |
| "review workshop" | 워크샵 검토 |

## 지원 콘텐츠 타입

| 타입 | 소스 에이전트 | 검토 중점 |
|------|---------------|-----------|
| HTML Presentations | presentation-agent | 슬라이드 구조, Canvas 애니메이션, 프레임워크 참조 |
| Marp Markdown | presentation-agent | 콘텐츠 품질, 슬라이드 구성 |
| Architecture Diagrams | architecture-diagram-agent | 다이어그램 완전성, 라벨, 계층 구조 |
| Animated SVG | animated-diagram-agent | 애니메이션 정확성, 색상 코딩 |
| Markdown Documents | document-agent | 구조, 콘텐츠, 참조 |
| GitBook Pages | gitbook-agent | 네비게이션, 컴포넌트, 상호 참조 |
| Workshop Content | workshop-agent | 디렉티브, 구조, 이중언어 일관성 |

## 16개 검사 카테고리

### 1. Layout Inspection (레이아웃 검사)

- 제목 계층 정확성 (H1 → H2 → H3)
- 슬라이드 구분자 / 섹션 일관성
- 테이블 정렬과 포맷
- 코드 블록 언어 지정
- 이미지 위치와 크기

### 2. Terminology Appropriateness (용어 적절성)

- 모호한 표현 금지: "etc.", "various", "and so on"
- 근거 없는 과장 금지: "perfect", "best", "innovative"
- 동일 개념에 일관된 용어 사용

### 3. Hallucination Detection (환각 탐지)

- AWS 서비스명 정확성 (예: "Lamda" → "Lambda")
- 존재하지 않는 AWS 서비스/기능 언급 금지
- 서비스 제한 및 리전 가용성 정확성
- 통계에 출처 인용

### 4. Language Check (언어 검사)

- 한국어: 기술 용어는 영어, 설명은 한국어
- 영어: 일관된 시제, 첫 등장 시 약어 확장
- 어색한 직역 금지

### 5. PII/Sensitive Data Inspection (민감 데이터 검사)

탐지 패턴:

| 심각도 | 타입 | 조치 |
|--------|------|------|
| Critical | AWS 키, 비밀번호 | 즉시 삭제 |
| High | PII (주민번호, 전화번호) | 마스킹 또는 삭제 |
| Medium | 내부 IP, 이메일 | 필요시 마스킹 |

### 6. Content-Type-Specific Quality (타입별 품질)

**Presentations (HTML):**
- SlideFramework 올바르게 초기화
- Canvas 애니메이션에 setupCanvas() 호출
- Quiz data-quiz/data-correct 속성 유효

**GitBook:**
- SUMMARY.md 네비게이션과 실제 페이지 일치
- GitBook 컴포넌트 올바른 문법
- 상호 참조가 존재하는 페이지로 연결

**Workshop:**
- Workshop Studio 디렉티브 (Hugo shortcode 아님)
- front matter에 `chapter: true` 없음
- 이중언어 파일 쌍 존재

### 7-16. 추가 검사

- **Icon Inspection**: 깨진 아이콘 참조 없음
- **Readability Analysis**: 1-7-7 Rule
- **Accessibility Check**: WCAG 2.1 (색상 대비 4.5:1 이상)
- **Structural Completeness**: TOC와 섹션 일치
- **Data Accuracy**: 숫자/단위/날짜 형식 일관성
- **Legal/Regulatory Compliance**: 저작권, 상표 표기
- **Message Clarity**: 섹션당 1개 핵심 메시지
- **Duplication & Gap Detection**: 중복/누락 탐지
- **External Reference Validation**: 이미지/URL 유효성
- **Quality Gate**: 자동 Pass/Fail 판정

## Visual Testing (HTML 콘텐츠)

HTML 기반 콘텐츠에 대해 Playwright MCP 도구로 브라우저 검증:

| 테스트 | Playwright 명령 | 통과 기준 |
|--------|----------------|-----------|
| 페이지 로드 | `browser_navigate` → `browser_console_messages` | JS 콘솔 에러 없음 |
| 슬라이드 전환 | `browser_press_key` (ArrowRight) x N | 모든 슬라이드 이동 확인 |
| 탭 전환 | `browser_click` (`.tab-btn`) | 탭 콘텐츠 변경 확인 |
| 반응형 FHD | `browser_resize` (1920x1080) | 오버플로우 없음 |
| 반응형 4K | `browser_resize` (3840x2160) | 오버플로우 없음 |

## Quality Gate

### 점수 체계 (100점 만점)

**기본 검사 (55점):**

| 항목 | 배점 | 감점 |
|------|------|------|
| Layout | 8 | 오류당 -2 |
| Terminology | 8 | 오류당 -1 |
| No Hallucination | 12 | 발견당 -4 |
| Language Consistency | 8 | 오류당 -2 |
| No Sensitive Data | 12 | Critical: -12 |
| Content-Type Quality | 4 | 오류당 -2 |
| Icon Appropriateness | 3 | Null: -3 |

**Visual Testing (10점 — HTML 콘텐츠만):**

| 항목 | 배점 | 감점 |
|------|------|------|
| 렌더링 정상 | 5 | JS 에러: 자동 FAIL |
| 인터랙션 정상 | 5 | 깨진 인터랙션당 -1 |

**확장 검사 (35점):**

| 항목 | 배점 | 감점 |
|------|------|------|
| Readability | 5 | 1-7-7 위반당 -1 |
| Accessibility | 5 | 대비 실패당 -2 |
| Structural Completeness | 5 | 누락 섹션당 -2 |
| Data Accuracy | 5 | 형식 오류당 -1 |
| Legal Compliance | 5 | 저작권 누락 -3 |
| Message Clarity | 5 | 다중 메시지당 -1 |
| Duplication/Gaps | 5 | 중복당 -1 |

### 판정

| 판정 | 점수 | Critical | Warning |
|------|------|----------|---------|
| **PASS** | 85점 이상 | 0 | 3개 이하 |
| **REVIEW** | 70-84점 | 0 | 4-10개 |
| **FAIL** | 70점 미만 | 1개 이상 | 10개 초과 |

### 자동 FAIL

- 민감 데이터 노출
- 심각한 환각 (존재하지 않는 서비스)
- 법적 위험 (저작권 침해)

## 리뷰 리포트 형식

```markdown
# Content Review Report

## Review Metadata
| Field | Value |
|-------|-------|
| **Review Type** | [Content Type] |
| **Iteration** | #[N] |
| **Current Score** | [Y] |
| **Verdict** | PASS / REVIEW / FAIL |

## Quality Gate Result
### Verdict: [PASS/REVIEW/FAIL]

| Category | Critical | Warning | Info |
|----------|----------|---------|------|
| ... | ... | ... | ... |
| **Total** | **X** | **Y** | **Z** |

## Critical Issues (Must Fix)
...

## Warning Issues (Should Fix)
...

## Revision Checklist
...

## Next Steps
[PASS: proceed / REVIEW: fix and re-review / FAIL: fix critical issues]
```

## 리뷰 프로세스

### Step 1: File Collection

Glob 도구로 리뷰 대상 파일 수집.

### Step 2: Type-Specific Inspection

콘텐츠 타입에 따른 검사 수행.

### Step 3: Visual Testing (HTML만)

Playwright MCP로 브라우저 검증.

### Step 4: Report Generation

`[ProjectName]_Review_Report.md`로 저장.

## 리비전 루프

1. 에이전트가 콘텐츠 생성
2. content-review-agent가 검토하고 리포트 생성
3. REVIEW/FAIL 시 에이전트가 이슈 수정
4. PASS까지 재검토 (최대 3회)
5. 3회 후에도 PASS 미달 시 사용자에게 문의

## 출력물

| 산출물 | 형식 | 위치 |
|--------|------|------|
| Review Report | .md | `[project]/results/[Name]_Review_Report.md` |
