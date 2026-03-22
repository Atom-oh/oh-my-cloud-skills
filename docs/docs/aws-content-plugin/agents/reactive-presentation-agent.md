---
sidebar_position: 2
title: "Reactive Presentation Agent"
---

# Reactive Presentation Agent

Remarp(reactive-presentation) 프레임워크를 사용하여 인터랙티브 HTML 슬라이드쇼를 생성하는 전문 에이전트입니다. Canvas 애니메이션, 프래그먼트 전환, 퀴즈, 키보드 네비게이션이 포함된 웹 프레젠테이션을 만듭니다.

## 기본 정보

| 항목 | 값 |
|------|-----|
| **도구** | Read, Write, Glob, Grep, Bash, AskUserQuestion |
| **연결 스킬** | reactive-presentation |

## 트리거 키워드

다음 키워드가 감지되면 자동으로 활성화됩니다:

| 키워드 | 설명 |
|--------|------|
| "reactive presentation", "remarp" | Remarp 포맷 프레젠테이션 |
| "web presentation", "interactive presentation" | 웹 기반 인터랙티브 프레젠테이션 |
| "web slides", "HTML slides" | HTML 슬라이드 |
| "인터랙티브 프레젠테이션", "웹 프레젠테이션", "리마프" | 한국어 트리거 |

## 핵심 기능

1. **Remarp Markdown Authoring** — 프래그먼트 애니메이션, Canvas DSL, 스피커 노트, 슬라이드 전환을 지원하는 차세대 포맷
2. **HTML Slide Generation** — Remarp를 Canvas 애니메이션과 프래그먼트 효과가 포함된 인터랙티브 HTML로 변환
3. **PPTX/PDF Theme Extraction** — .pptx 또는 .pdf 템플릿에서 기업 브랜딩 추출 (선택사항)
4. **Quiz Integration** — 교육 세션을 위한 자동 채점 퀴즈 컴포넌트
5. **Presenter View** — 타이밍 가이드와 큐 마커가 포함된 스피커 노트 (P 키)
6. **AWS Icon Integration** — AWS Architecture Icons를 사용한 아키텍처 다이어그램
7. **Per-block Editing** — 개별 `.remarp.md` 블록 편집, 변경된 HTML만 재빌드

## Presentation Agent와의 관계

`presentation-agent`는 포맷 디스패처 역할을 합니다. 웹/HTML 프레젠테이션 요청이 들어오면 `reactive-presentation-agent`로 라우팅됩니다.

```mermaid
flowchart LR
    A[사용자 요청] --> B[presentation-agent]
    B -->|웹/HTML| C[reactive-presentation-agent]
    B -->|PPTX| D[PPTX 가이드]
```

## 워크플로우

### Phase 1: Planning + Theme Setup

사용자에게 다음을 질문합니다:
- **Topic & audience** (필수) — 주제 + 대상 청중
- **PPTX/PDF source** (선택) — 테마 추출 또는 콘텐츠 변환
- **Duration** — 블록 수와 슬라이드 수 결정
- **Language** — 한국어 또는 영어
- **Speaker info** (선택) — 발표자 정보
- **Quiz inclusion** (필수) — 복습 퀴즈 포함 여부

### Phase 2: Content Authoring (Remarp)

Remarp 포맷으로 콘텐츠를 작성합니다:

```
{slug}/
├── _presentation.remarp.md       # 글로벌 설정
├── 01-fundamentals.remarp.md     # Block 1 소스
├── 02-advanced.remarp.md         # Block 2 소스
└── build/                        # 생성된 HTML
```

### Phase 3: Review & Build

1. 사용자에게 Remarp 콘텐츠 검토 요청
2. 승인 후 `remarp_to_slides.py build`로 HTML 생성
3. `content-review-agent`로 품질 검토 (PASS >= 85점)

## 슬라이드 타입

| 콘텐츠 타입 | 슬라이드 패턴 | 인터랙티브 요소 |
|-------------|---------------|-----------------|
| 단순 흐름 (박스 4개 이하) | Canvas Animation | `:::canvas` DSL, step 내비게이션 |
| 복잡 아키텍처 (박스 5개 이상) | HTML Architecture | `:::html` + `:::css` (flow-h, flow-group) |
| A vs B 비교 | Compare Toggle | `.compare-toggle` 버튼 |
| 설정 변형 | Tab Content | `.tab-bar` + YAML 코드 블록 |
| 단계별 프로세스 | Timeline | `.timeline` + 애니메이션 단계 |
| 베스트 프랙티스 | Checklist | `.checklist` + 클릭 토글 |
| 블록 요약 | Quiz | `data-quiz` + 3-4개 질문 |

### Canvas vs HTML 선택 기준 (v1.2.3)

:::warning STOP Gate - Canvas 사용 전 필수 확인
슬라이드에 들어갈 박스/아이콘의 총 개수를 세시오:
- **4개 이하**: `:::canvas` 사용 가능
- **5개 이상**: `:::canvas` 금지 → `:::html` + `:::css` 필수
- **인터랙션 필요**: `:::html` + `:::script` 사용
:::

| 복잡도 | 방식 | 예시 |
|--------|------|------|
| 단순 (박스 ≤4) | `:::canvas` DSL | A→B→C 직선 흐름 |
| 중간 (박스 5+, 다계층) | `:::html` + `:::css` 필수 (canvas 금지) | 3-tier 아키텍처, 서비스 맵, 에코시스템 |
| 복잡 (인터랙션 + 계산) | `:::html` + `:::script` 필수 | 슬라이더, 계산기, 시뮬레이터, 대시보드 |
| 정적 아키텍처 | `@img:` + draw.io | AWS 전체 아키텍처, VPC 네트워크 |

### HTML Architecture 패턴 (박스 5+ 필수)

박스 5개 이상의 아키텍처/파이프라인은 반드시 이 패턴을 사용합니다:

```markdown
:::html
<div class="flow-h">
  <div class="flow-group bg-blue" data-fragment-index="1">
    <div class="flow-group-label">수집</div>
    <div class="icon-item"><img src="common/aws-icons/..."><span>CloudWatch</span></div>
  </div>
  <div class="flow-arrow">→</div>
  <div class="flow-group bg-orange" data-fragment-index="2">
    <div class="flow-group-label">분석</div>
    <div class="flow-box">DevOps Guru</div>
  </div>
</div>
:::
```

- `flow-h` / `flow-group` / `flow-box` / `flow-arrow`: theme.css 제공 유틸리티
- `bg-blue`, `bg-orange`, `bg-pink`: 색상 유틸리티
- `data-fragment-index="N"`: 그룹별 순차 등장 (canvas step 대체)

## 키보드 단축키

| 키 | 동작 |
|----|------|
| ← → | 이전/다음 슬라이드 |
| Space | 다음 슬라이드 |
| ↑ ↓ | 탭/비교 옵션 순환, 애니메이션 단계 |
| F | 전체 화면 토글 |
| P | 프레젠터 뷰 열기 |
| O | 개요 모드 토글 |

## 출력물

| 산출물 | 형식 | 위치 |
|--------|------|------|
| Remarp Source | .remarp.md | `{repo}/{slug}/` |
| HTML Slides | .html | `{repo}/{slug}/build/` |
| Hub Page | .html | `{repo}/index.html` |
| Theme Override | .css | `{repo}/common/theme-override.css` |

## 협업 워크플로우

```mermaid
flowchart LR
    A[reactive-presentation-agent] --> B[content-review-agent]
    B --> C[Deploy to GitHub Pages]
```

콘텐츠 생성 후 `content-review-agent`를 호출하여 품질 검토를 수행합니다.
