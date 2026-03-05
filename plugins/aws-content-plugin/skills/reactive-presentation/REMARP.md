m# Remarp — Reactive Markdown for Presentations

Remarp는 **reactive-presentation** 프레임워크를 위한 차세대 마크다운 포맷입니다. 사람이 읽고 편집할 수 있는 `.remarp.md` 파일 하나가 프레젠테이션의 **단일 소스**가 됩니다.

---

## 왜 Remarp인가?

| | Marp (기존) | JSON+Renderer | **Remarp (신규)** |
|---|---|---|---|
| 소스 포맷 | Markdown | JSON | **Markdown** |
| 사람이 읽기 | 쉬움 | 어려움 | **쉬움** |
| 프래그먼트 애니메이션 | 불가 | 수동 HTML | **`{.click}` 한 줄** |
| Canvas 애니메이션 | 불가 (수동 JS) | 별도 JS 모듈 | **`:::canvas` DSL** |
| 스피커 노트 | `<!-- notes: -->` | JSON 필드 | **`:::notes` + 타이밍/큐** |
| 컬럼 레이아웃 | 불가 | 수동 HTML | **`::: left`/`::: right`** |
| 슬라이드 전환 효과 | 불가 | 불가 | **`@transition fade`** |
| 키보드 커스텀 | 불가 | 불가 | **`keys:` frontmatter** |
| 블록별 증분 빌드 | 불가 | 해당 없음 | **`sync` 명령** |
| 하위 호환 | — | — | **`marp: true` 지원** |

> **한마디로**: Marp의 편집 편의성 + JSON 모드의 인터랙티브 기능 = Remarp

---

## 5분 퀵스타트

### 1. 파일 만들기

`my-talk.remarp.md` 파일을 생성합니다:

```markdown
---
remarp: true
title: "My First Remarp Presentation"
author: "Your Name"
audience: "Cloud Engineers"
lang: ko

theme:
  source: "./company-template.pptx"   # 또는 skip
  footer: "© 2026 My Company"

transition:
  type: fade
  duration: 350
---

# My First Remarp Presentation

Your Name | 2026

:::notes
{timing: 1min}
인사하고 자기소개.
:::

---

## 핵심 포인트

- 첫 번째 포인트{.click}
- 두 번째 포인트{.click}
- 세 번째 포인트{.click animation=fade-up}

:::notes
{timing: 3min}
**핵심**: 각 포인트를 클릭하며 설명.
{cue: question} "질문 있으신가요?"
:::

---
@type compare
@layout two-column

## 비교

::: left
### Option A
- 빠른 배포
- 간단한 구성
:::

::: right
### Option B
- 높은 확장성
- 세밀한 제어
:::

---
@type canvas
@canvas-id arch-flow

## 아키텍처

:::canvas width=960 height=400
box "API GW" at 50,170 size 130x60 color=accent
box "Lambda" at 260,170 size 130x60 color=green
box "DynamoDB" at 470,170 size 130x60 color=blue

arrow from "API GW" to "Lambda" at step=1 animate=draw
arrow from "Lambda" to "DynamoDB" at step=2 animate=draw

group "VPC" at 30,100 size 580x180 color=border
:::

:::notes
{timing: 5min}
{cue: demo} 아키텍처 흐름을 step별로 보여주기.
:::
```

### 2. HTML 빌드

```bash
python3 remarp_to_slides.py build my-talk.remarp.md
```

### 3. 브라우저에서 열기

생성된 HTML을 브라우저에서 열면 끝!

---

## 멀티파일 프로젝트 (긴 세션용)

30분 이상의 세션은 블록별로 파일을 분리합니다:

```
aws-scaling/
├── _presentation.remarp.md       # 글로벌 설정
├── 01-fundamentals.remarp.md     # Block 1 (25분)
├── 02-advanced.remarp.md         # Block 2 (30분)
└── build/                        # 생성된 HTML
    ├── index.html
    ├── 01-fundamentals.html
    └── 02-advanced.html
```

**`_presentation.remarp.md`** (글로벌 설정만):
```yaml
---
remarp: true
title: "AWS Auto Scaling Deep Dive"
author: "Cloud Architect"
event: "AWS Summit Seoul 2026"
lang: ko

blocks:
  - file: 01-fundamentals.remarp.md
    name: fundamentals
    title: "Block 1: Fundamentals"
    duration: 25
  - file: 02-advanced.remarp.md
    name: advanced
    title: "Block 2: Advanced Patterns"
    duration: 30

theme:
  source: "./company.pptx"
  footer: "© 2026, Amazon Web Services, Inc."
---
```

**블록 파일** (`01-fundamentals.remarp.md`):
```markdown
---
remarp: true
block: fundamentals
title: "Block 1: Fundamentals"
---

# AWS Auto Scaling Fundamentals

Block 1: Fundamentals (25 min)

:::notes
{timing: 1min}
Welcome!
:::

---

## Why Auto Scaling?
...
```

### 빌드 명령어

```bash
# 전체 빌드
python3 remarp_to_slides.py build ./aws-scaling/

# 특정 블록만 빌드
python3 remarp_to_slides.py build ./aws-scaling/ --block 01-fundamentals

# 변경된 블록만 증분 빌드
python3 remarp_to_slides.py sync ./aws-scaling/
```

---

## 주요 문법 요약

### 슬라이드 구분

`---` 줄로 슬라이드를 구분합니다. `---` 다음에 `@directive`를 배치합니다.

### 디렉티브 (`@`)

```markdown
---
@type canvas
@layout two-column
@transition zoom
@background #1a1d2e
@timing 3min
```

| 디렉티브 | 설명 | 값 |
|-----------|------|-----|
| `@type` | 슬라이드 유형 | content, compare, canvas, quiz, tabs, timeline, checklist, slider, code |
| `@layout` | 레이아웃 | default, two-column, three-column, grid-2x2 |
| `@transition` | 전환 효과 | fade, slide, zoom, none |
| `@background` | 배경색 | CSS 색상 또는 `url(...)` |
| `@timing` | 발표 시간 | 3min, 90s |
| `@canvas-id` | Canvas ID | 식별자 |

### 프래그먼트 애니메이션 (`{.click}`)

Space/→ 키로 하나씩 나타나는 요소:

```markdown
- 첫 번째{.click}
- 두 번째{.click}
- 세 번째{.click animation=fade-up}
```

블록 단위도 가능:
```markdown
:::click animation=grow
### Phase 1
전체 블록이 클릭 시 나타남.
:::
```

12가지 애니메이션: `fade-in`, `fade-up`, `fade-down`, `fade-left`, `fade-right`, `grow`, `shrink`, `highlight`, `highlight-red`, `highlight-green`, `strike`, `fade-out`

### 컬럼 레이아웃

```markdown
@layout two-column

::: left
왼쪽 내용
:::

::: right
오른쪽 내용
:::
```

### Canvas DSL

```markdown
:::canvas width=960 height=400
box "서비스A" at 50,170 size 130x60 color=accent
arrow from "서비스A" to "서비스B" at step=1 animate=draw
:::
```

### 스피커 노트

```markdown
:::notes
{timing: 3min}
**핵심 포인트** 설명.
{cue: demo} 대시보드 보여주기.
{cue: question} "경험 있으신 분?"
:::
```

큐 유형: `demo` (데모), `pause` (멈춤), `question` (질문), `transition` (전환)

---

## 테마 통합

### PPTX/PDF 테마 소스

Frontmatter에서 PPTX 또는 PDF 파일을 테마 소스로 지정:

```yaml
---
remarp: true
title: "My Presentation"

theme:
  source: "./company-template.pptx"   # 또는 PDF 파일
  footer: auto                         # 자동으로 PPTX에서 추출
  pagination: true                     # 페이지 번호 표시
  logo: auto                           # 첫 번째 로고 자동 사용
---
```

- `source` — PPTX/PDF 파일 경로 또는 이미 추출된 테마 디렉토리
- `footer` — `auto`로 설정 시 PPTX에서 자동 추출, 또는 직접 문자열 지정
- `pagination` — `true`/`false` 페이지 번호 표시 여부
- `logo` — `auto`로 자동 추출 또는 직접 경로 지정

추출된 테마는 `_theme/` 디렉토리에 캐시됩니다.

### CSS 변수 자동 생성

PPTX 색상 스키마가 자동으로 CSS 변수로 변환됩니다:

```css
:root {
  --pptx-accent1: #FF9900;
  --pptx-accent2: #232F3E;
  --pptx-dk1: #000000;
  --pptx-lt1: #FFFFFF;
  /* ... */
}
```

---

## 프리셋 DSL

복잡한 Canvas 애니메이션을 위한 프리셋 시스템:

```markdown
:::canvas
preset eks-scaling {
  cluster "Production EKS" at 40,30
    node "node-1" pods=3 max=4
    node "node-2" pods=2 max=4

  step 1 scale-out node=0 "Pod 추가"
  step 2 scale-out node=0 "Pod 추가"
  step 3 add-node "Node 추가"
}
:::
```

지원 프리셋:
- `eks-scaling` — EKS 클러스터 스케일링 시각화
- `serverless-flow` — Lambda 이벤트 흐름
- `vpc-architecture` — VPC 네트워크 다이어그램
- `cicd-pipeline` — CI/CD 파이프라인
- `data-pipeline` — 데이터 처리 파이프라인

---

## Mermaid 다이어그램

`:::canvas mermaid` 변형으로 Mermaid 다이어그램 지원:

```markdown
:::canvas mermaid
graph LR
    A[Client] --> B[API Gateway]
    B --> C[Lambda]
    C --> D[DynamoDB]
:::
```

Mermaid CDN이 자동으로 주입됩니다.

---

## 아이콘 사용

Canvas DSL에서 AWS 아이콘 사용:

```markdown
:::canvas
# 서비스 이름으로 참조 (자동 매핑)
icon gw "API-Gateway" at 100,150 size 48
icon fn "Lambda" at 250,150 size 48
icon db "DynamoDB" at 400,150 size 48

# 또는 전체 경로로 참조
icon custom "../common/aws-icons/services/Arch_Amazon-S3_48.svg" at 100,250 size 48
:::
```

지원되는 서비스 이름: `Lambda`, `EKS`, `API-Gateway`, `DynamoDB`, `S3`, `CloudWatch`, `EC2`, `VPC`, `RDS`, `SQS`, `SNS`, `CloudFront`, `Route53`, `Cognito`, `StepFunctions`, `Fargate`, `ECS`, `ALB`, `IAM`, `KMS`

---

## 참조 링크 (@ref)

슬라이드에 참조 링크 추가:

```markdown
---
@type content
@ref "https://docs.aws.amazon.com/lambda/" "Lambda Documentation"
@ref "https://aws.amazon.com/blogs/compute/" "AWS Compute Blog"

## Lambda Best Practices

Content here...
```

참조는 `data-refs` 속성으로 슬라이드에 저장되어 프레젠터 뷰에서 표시됩니다.

---

## PPTX 내보내기

프레젠테이션을 PPTX로 내보내기:

```javascript
// 브라우저에서
ExportUtils.exportPPTX({ title: 'My Presentation' });

// 또는 index.html의 Export PPTX 버튼 클릭
```

내보내기 옵션:
- **PDF** — 모든 슬라이드를 PDF로
- **ZIP** — HTML, CSS, JS를 포함한 전체 패키지
- **PPTX** — PowerPoint 형식으로 내보내기 (테마 색상 포함)

---

## 키보드 단축키

| 키 | 동작 |
|----|------|
| ← → | 이전/다음 슬라이드 |
| Space | 다음 프래그먼트 → 다음 슬라이드 |
| ↑ ↓ | 탭/비교 전환, 애니메이션 스텝 |
| F | 전체 화면 |
| N | 스피커 노트 패널 |
| P | 프레젠터 뷰 (새 창) |
| O | 슬라이드 오버뷰 (그리드) |
| B | 블랙아웃 |
| Esc | 전체 화면/오버뷰 종료 |

키보드 커스텀은 frontmatter의 `keys:` 섹션에서 설정합니다.

---

## Marp에서 마이그레이션

기존 Marp 파일을 Remarp로 자동 변환:

```bash
python3 remarp_to_slides.py migrate ./old-content.md -o ./my-presentation/
```

변환 내용:
| Marp | Remarp |
|------|--------|
| `marp: true` | `remarp: true` |
| `<!-- type: canvas -->` | `@type canvas` |
| `<!-- block: name -->` | 별도 블록 파일 |
| `<!-- notes: text -->` | `:::notes` 블록 |

하위 호환: `marp: true` 파일도 Remarp 파서가 그대로 처리합니다.

---

## VSCode 확장

`tools/remarp-vscode/` 에 VSCode 확장이 포함되어 있습니다:

- **구문 하이라이팅** — `@directive`, `:::block`, `{.click}`, Canvas DSL
- **라이브 프리뷰** — 사이드 패널에서 현재 슬라이드 미리보기
- **슬라이드 아웃라인** — 탐색기에서 슬라이드 목록 트리뷰
- **자동 완성** — `@type`, `@layout`, `@transition`, 애니메이션 타입 IntelliSense

---

## 더 알아보기

- [Remarp 포맷 전체 사양](references/remarp-format-guide.md) — 모든 문법의 상세 설명과 예제
- [슬라이드 패턴 가이드](references/slide-patterns.md) — 13개 슬라이드 유형별 HTML 패턴
- [프레임워크 가이드](references/framework-guide.md) — CSS/JS API 레퍼런스
- [PPTX 테마 가이드](references/pptx-theme-guide.md) — 기업 테마 추출 방법
- [AWS 아이콘 가이드](references/aws-icons-guide.md) — AWS 아키텍처 아이콘 사용법
