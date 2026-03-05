---
sidebar_position: 1
title: "Presentation Agent"
---

# Presentation Agent

Interactive HTML 슬라이드쇼를 생성하는 전문 에이전트입니다. reactive-presentation 프레임워크를 사용하여 Canvas 애니메이션, 퀴즈, 키보드 네비게이션이 포함된 프레젠테이션을 만듭니다.

## 기본 정보

| 항목 | 값 |
|------|-----|
| **도구** | Read, Write, Glob, Grep, Bash, AskUserQuestion |

## 트리거 키워드

다음 키워드가 감지되면 자동으로 활성화됩니다:

| 키워드 | 설명 |
|--------|------|
| "create presentation", "create slides", "make slideshow" | 프레젠테이션 생성 |
| "training slides", "interactive presentation" | 교육용 슬라이드 |
| "reactive presentation", "remarp" | Remarp 포맷 프레젠테이션 |
| "PPTX theme", "extract theme", "corporate branding" | PPTX 테마 추출 |
| "반영해주세요", "rebuild", "다시 빌드" | Remarp에서 HTML 증분 빌드 |

## 핵심 기능

1. **Remarp Markdown Authoring** — 프래그먼트 애니메이션, Canvas DSL, 스피커 노트, 슬라이드 전환을 지원하는 차세대 포맷
2. **HTML Slide Generation** — Remarp/Marp를 Canvas 애니메이션과 프래그먼트 효과가 포함된 인터랙티브 HTML로 변환
3. **PPTX/PDF Theme Extraction** — .pptx 또는 .pdf 템플릿에서 기업 브랜딩 추출 (선택사항)
4. **Quiz Integration** — 교육 세션을 위한 자동 채점 퀴즈 컴포넌트
5. **Presenter View** — 타이밍 가이드와 큐 마커가 포함된 스피커 노트 (P 키)
6. **AWS Icon Integration** — AWS Architecture Icons를 사용한 아키텍처 다이어그램
7. **Per-block Editing** — 개별 `.remarp.md` 블록 편집, 변경된 HTML만 재빌드

## 워크플로우

### Phase 1: Planning

사용자에게 다음을 질문합니다:
- **Topic & audience** (필수) — 주제 + 대상 청중 (기술 수준/역할) → `audience` 필드
- **Duration** — 블록 수와 슬라이드 수 결정
- **Blocks** — 20-35분 블록으로 분할, 5분 휴식
- **Target repo** — 배포용 GitHub 저장소
- **Language** — 한국어 또는 영어 (기술 용어는 항상 영어)
- **PPTX/PDF template** (필수, 스킵 가능) — 디자인 참고용 파일
- **Speaker info** (필수, 스킵 가능) → `author` 필드
- **Footer text** (필수, 스킵 가능) → `theme.footer` 필드
- **Logo** (필수, 스킵 가능) → `theme.logo` 필드
- **Quiz inclusion** (필수 — 건너뛰기 금지)

### Phase 2: Theme Setup (선택사항)

PPTX 템플릿이 제공되면 테마를 추출합니다:

```bash
python3 {plugin-dir}/skills/reactive-presentation/scripts/extract_pptx_theme.py <pptx_path> -o {repo}/common/pptx-theme/
```

### Phase 3: Content Authoring

Remarp 포맷으로 콘텐츠를 작성합니다:

```
{slug}/
├── _presentation.remarp.md       # 글로벌 설정 (title, theme, blocks, keys)
├── 01-fundamentals.remarp.md     # Block 1 소스
├── 02-advanced.remarp.md         # Block 2 소스
└── build/                        # 생성된 HTML (gitignored)
```

### Phase 4: HTML Generation

```bash
# 전체 빌드
python3 {plugin-dir}/skills/reactive-presentation/scripts/remarp_to_slides.py build {repo}/{slug}/

# 특정 블록만 빌드
python3 {plugin-dir}/skills/reactive-presentation/scripts/remarp_to_slides.py build {repo}/{slug}/ --block 01-fundamentals

# 변경된 블록만 증분 빌드
python3 {plugin-dir}/skills/reactive-presentation/scripts/remarp_to_slides.py sync {repo}/{slug}/
```

## 슬라이드 타입 가이드

| 콘텐츠 타입 | 슬라이드 패턴 | 인터랙티브 요소 |
|-------------|---------------|-----------------|
| 아키텍처 개요 | Canvas Animation | 컴포넌트 흐름 + Play 버튼 |
| A vs B 비교 | Compare Toggle | `.compare-toggle` 버튼 |
| 설정 변형 | Tab Content | `.tab-bar` + YAML 코드 블록 |
| 단계별 프로세스 | Timeline | `.timeline` + 애니메이션 단계 |
| 모니터링/대시보드 | Canvas Animation | 노드 그리드 + 이벤트 로그 |
| 파라미터 탐색 | Slider | `input[type=range]` + 라이브 출력 |
| 베스트 프랙티스 | Checklist | `.checklist` + 클릭 토글 |
| YAML/코드 예제 | Code Block | `.code-block` + 구문 강조 |
| 블록 요약 | Quiz | `data-quiz` + 3-4개 질문 |
| 블록 종료 | Thank You | 그라데이션 제목 + TOC 링크 |

## 키보드 단축키

| 키 | 동작 |
|----|------|
| ← → | 이전/다음 슬라이드 |
| Space | 다음 슬라이드 |
| ↑ ↓ | 탭/비교 옵션 순환, 애니메이션 단계 |
| F | 전체 화면 토글 |
| N | 스피커 노트 패널 토글 |
| P | 프레젠터 뷰 열기 |
| O | 개요 모드 토글 |
| B | 화면 블랙아웃 |
| 1-9 | 슬라이드 번호로 이동 |

## 출력물

| 산출물 | 형식 | 위치 |
|--------|------|------|
| Remarp Source | .remarp.md | `{repo}/{slug}/_presentation.remarp.md` + `{repo}/{slug}/0N-block.remarp.md` |
| HTML Slides | .html | `{repo}/{slug}/build/0N-block.html` |
| Hub Page | .html | `{repo}/index.html` |
| Theme Override | .css | `{repo}/common/theme-override.css` |

## 사용 예시

```
사용자: "EKS 교육 프레젠테이션 만들어줘"

에이전트:
1. 주제, 청중, 시간, 언어 등을 질문
2. Remarp 콘텐츠 작성
3. 사용자 검토 요청
4. HTML 빌드
5. content-review-agent로 품질 검토
6. GitHub Pages 배포
```

## 협업 워크플로우

```mermaid
flowchart LR
    A[presentation-agent] --> B[content-review-agent]
    B --> C[Deploy to GitHub Pages]
```
