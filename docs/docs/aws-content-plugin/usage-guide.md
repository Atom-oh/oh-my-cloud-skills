---
sidebar_position: 2
title: "사용법 가이드"
---

# 사용법 가이드

AWS Content Plugin으로 프레젠테이션, 다이어그램, 문서를 만드는 방법을 안내합니다.

## 빠른 시작

```
1. 설치         →  /plugin marketplace add aws-content-plugin
2. 프롬프트     →  "AWS 마이크로서비스 아키텍처 프레젠테이션 만들어줘"
3. 결과물       →  인터랙티브 HTML 슬라이드쇼 (.html)
```

설치 후 자연어 프롬프트만으로 콘텐츠를 생성할 수 있습니다. 키워드에 따라 적절한 에이전트가 자동으로 활성화됩니다.

---

## 에이전트 자동 호출

프롬프트에 특정 키워드가 포함되면 해당 에이전트가 자동으로 활성화됩니다.

| 키워드 | 에이전트 | 출력물 |
|--------|----------|--------|
| "프레젠테이션 만들어", "create slides", "training slides" | `presentation-agent` | HTML 슬라이드쇼 |
| "아키텍처 다이어그램", "infrastructure diagram", "draw.io" | `architecture-diagram-agent` | Draw.io XML |
| "애니메이션 다이어그램", "traffic flow", "SMIL animation" | `animated-diagram-agent` | SVG + SMIL HTML |
| "문서 작성", "write report", "technical report" | `document-agent` | Markdown 문서 |
| "gitbook", "documentation site" | `gitbook-agent` | GitBook 프로젝트 |
| "workshop", "hands-on guide", "랩 작성" | `workshop-agent` | Workshop Studio 콘텐츠 |
| "review content", "quality check" | `content-review-agent` | 리뷰 리포트 |

:::tip 한국어/영어 혼용
모든 에이전트는 한국어와 영어 키워드를 모두 지원합니다. "프레젠테이션 만들어줘"와 "create presentation"은 동일하게 동작합니다.
:::

---

## 프레젠테이션 만들기

프레젠테이션은 가장 핵심적인 워크플로우입니다. 단순한 프롬프트부터 상세한 프롬프트까지 다양하게 사용할 수 있습니다.

### 프롬프트 예시

**단순 프롬프트:**
```
AWS 서버리스 아키텍처 프레젠테이션 만들어줘
```

**상세 프롬프트:**
```
새로 프레젠테이션을 만들어줘 aiops에 관하여 90분간 세션을 진행할거야
고객은 300레벨 수준이야.
theme는 "example.pptx"를 가지고 사용하면 되고
스피커는 Junseok Oh, Sr. Solutions Architect, AWS
청중은 AnyCompany
```

### 에이전트 질문 항목

프롬프트에서 명시하지 않은 정보는 에이전트가 대화형으로 질문합니다:

| 항목 | 설명 | 예시 |
|------|------|------|
| 주제 | 프레젠테이션 주제 | AIOps, 서버리스, 컨테이너 |
| 시간 | 세션 총 시간 | 30분, 60분, 90분 |
| 블록 수 | 시간 기반 자동 분할 | 90분 → 3블록 (각 30분) |
| PPTX 테마 | 기업 브랜딩 템플릿 | `corporate.pptx` |
| 스피커 | 발표자 정보 | 이름, 직함, 소속 |
| 퀴즈 | 인터랙티브 퀴즈 포함 여부 | 블록별 3-5문제 |

### 워크플로우

```mermaid
flowchart TD
    A[프롬프트 입력] --> B[에이전트가 정보 수집]
    B --> C[Remarp 소스 작성]
    C --> D[HTML 빌드]
    D --> E[content-review-agent 리뷰]
    E --> F{판정}
    F -->|PASS ≥85점| G[완료 / 배포]
    F -->|REVIEW/FAIL| C
```

### PPTX 테마 적용

기업 PPTX 템플릿에서 색상과 폰트를 추출하여 프레젠테이션에 적용합니다:

```
프레젠테이션 만들어줘, theme는 "corporate.pptx"를 사용해줘
```

에이전트가 PPTX 파일에서 다음을 자동 추출합니다:
- 배경색, 텍스트 색상, 강조색
- 폰트 패밀리
- 로고 이미지 (있는 경우)

### Remarp → HTML 빌드

프레젠테이션 소스는 Remarp DSL(`.remarp.md`)로 작성되며, 빌드 스크립트로 HTML로 변환됩니다:

```bash
python3 remarp_to_slides.py build <project-dir>/
```

수정 후 증분 빌드:
```
"remarp 반영해줘" 또는 "rebuild"
```

---

## 아키텍처 다이어그램

AWS 서비스 구성도를 Draw.io XML 형식으로 생성합니다.

**프롬프트 예시:**
```
3-tier 웹 애플리케이션 아키텍처 다이어그램 그려줘
VPC, ALB, ECS Fargate, Aurora PostgreSQL 포함
```

**출력:** `.drawio` XML 파일 → Draw.io에서 열어 PNG/SVG로 내보내기

---

## 애니메이션 다이어그램

트래픽 흐름이나 서비스 간 상호작용을 SMIL 애니메이션으로 시각화합니다.

**프롬프트 예시:**
```
API Gateway → Lambda → DynamoDB 트래픽 흐름 애니메이션 다이어그램 만들어줘
```

**출력:** 자체 포함 HTML 파일 (SVG + SMIL 애니메이션, 인터랙티브 범례)

---

## 문서 생성

기술 문서, 비교 분석 리포트, 솔루션 가이드를 마크다운으로 생성합니다.

**프롬프트 예시:**
```
ECS vs EKS 비교 문서 작성해줘. 운영 복잡도, 비용, 유연성 관점에서 비교
```

**출력:** 전문적인 마크다운 문서 (`.md`)

---

## GitBook / Workshop

### GitBook 문서 사이트

```
GitBook 문서 사이트 만들어줘 - AWS Well-Architected Framework 가이드
```

구조화된 GitBook 프로젝트를 생성합니다 (SUMMARY.md, 챕터별 페이지, 컴포넌트).

### AWS Workshop Studio

```
EKS 핸즈온 워크샵 만들어줘, 3개 모듈 구성
```

Workshop Studio 형식의 콘텐츠를 생성합니다 (디렉티브, 다국어 지원, CloudFormation 인프라).

---

## Quality Gate

모든 콘텐츠는 배포 전 `content-review-agent`의 품질 검토를 거칩니다.

| 판정 | 점수 | 조건 | 결과 |
|------|------|------|------|
| **PASS** | 85점 이상 | Critical 0, Warning ≤3 | 승인 — 배포 가능 |
| **REVIEW** | 70-84점 | Critical 0, Warning 4-10 | 수정 후 재리뷰 |
| **FAIL** | 70점 미만 | Critical ≥1 또는 Warning >10 | 진행 불가 — 재작성 |

리뷰 항목: 레이아웃, 용어 정확도, 할루시네이션, 언어 일관성, PII/민감 정보, 가독성, 접근성, 구조 완성도

:::warning 필수 규칙
Quality Gate를 통과하지 않고 배포/완료를 선언할 수 없습니다. 최대 3회 리뷰 사이클 후에도 PASS 미달 시 사용자에게 판단을 요청합니다.
:::

---

## 키보드 단축키

생성된 HTML 프레젠테이션에서 사용할 수 있는 키보드 단축키입니다.

| 키 | 동작 |
|----|------|
| `←` `→` | 이전/다음 슬라이드 |
| `Space` | 다음 Fragment 또는 다음 슬라이드 |
| `F` | 전체 화면 토글 |
| `P` | 프레젠터 뷰 (노트 + 타이밍) |
| `O` | 개요 모드 (슬라이드 그리드) |
| `Esc` | 모드 종료 |
| `Home` / `End` | 처음/마지막 슬라이드 |

---

## 팁 & 트릭

### 블록 편집

이미 생성된 프레젠테이션의 특정 블록만 수정할 수 있습니다:

```
Block 2의 슬라이드 5에 "비용 최적화 사례" 추가해줘
```

### 증분 빌드

전체를 다시 만들지 않고 수정된 부분만 반영합니다:

```
"remarp 반영해줘" 또는 "다시 빌드해줘"
```

### 한국어/영어 혼용 규칙

- 프롬프트: 한국어와 영어 모두 사용 가능
- 콘텐츠: 프롬프트 언어에 맞춰 자동 생성
- 기술 용어: 원문 영어를 유지하되 설명은 요청 언어로 작성

### 다이어그램 에이전트 선택

| 필요 사항 | 에이전트 |
|-----------|----------|
| 정적 AWS 아키텍처 | `architecture-diagram-agent` |
| 애니메이션 트래픽 흐름 | `animated-diagram-agent` |
| Workshop 인라인 다이어그램 | `workshop-agent` (Mermaid) |
| 프레젠테이션 Canvas 애니메이션 | `presentation-agent` |
