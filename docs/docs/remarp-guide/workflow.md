---
sidebar_position: 3
title: 사용 워크플로우
---

# 사용 워크플로우

Remarp 파일을 편집하고 Claude Code 프롬프트로 빌드하는 실전 워크플로우입니다.

## 전체 흐름

```
.remarp.md 편집 → "반영해줘" 프롬프트 → HTML 자동 빌드 → 브라우저 프리뷰
                                                         ↕ (VSCode에서 HTML 직접 편집도 가능)
```

## 1단계: 프레젠테이션 생성

Claude Code에 프롬프트를 입력하면 `.remarp.md` 파일이 자동으로 생성됩니다.

```
"AWS AIOps 마스터클래스 프레젠테이션 만들어줘.
3블록 구성 (각 30분), 인터랙티브 슬라이드 포함."
```

생성되는 파일 구조:

```
aiops-masterclass/
├── _presentation.remarp.md     ← 글로벌 설정 (테마, 블록 목록)
├── 01-fundamentals.remarp.md   ← Block 1 슬라이드
├── 02-detection.remarp.md      ← Block 2 슬라이드
└── 03-automation.remarp.md     ← Block 3 슬라이드
```

:::caution 확장자는 반드시 `.remarp.md`
빌드 도구가 `*.remarp.md` 패턴으로 파일을 검색합니다. 일반 `.md` 확장자로는 파일을 인식하지 못합니다.
:::

## 2단계: VSCode에서 편집

생성된 `.remarp.md` 파일을 VSCode(code-server)에서 직접 편집합니다. Remarp VSCode 확장이 설치되어 있으면 구문 강조와 프리뷰를 사용할 수 있습니다.

### 편집 예시 — 슬라이드 내용 수정

```markdown
## AIOps란 무엇인가?

**Artificial Intelligence for IT Operations**

> "AIOps 플랫폼은 빅데이터, 현대적 머신러닝 및 기타 고급 분석 기술을
> 결합하여 가시성을 향상시키고, 노이즈를 줄이며,
> IT 운영 관리의 문제를 자동으로 해결합니다."

**Gartner 정의** {.click}
**핵심 목표** {.click}
**주요 기술** {.click}
```

### 편집 예시 — 퀴즈 추가

```markdown
@type: quiz

## 확인 퀴즈

**CloudWatch Anomaly Detection의 주요 장점은?**

- [ ] 고정 임계값 설정이 쉽다
- [x] ML 기반으로 동적 기준선을 자동 생성한다
- [ ] 알림을 완전히 제거한다
- [ ] 로그 수집이 불필요하다
```

### 편집 예시 — Canvas 다이어그램 추가

```markdown
@type: canvas

## AWS Observability 서비스 맵

:::canvas
icon cw "CloudWatch" at 80,120 size 48 step 1
box collect "Collect" at 55,180 size 100,35 color #41B3FF step 1
icon guru "DevOpsGuru" at 272,120 size 48 step 2
box analyze "Analyze" at 247,180 size 100,35 color #AD5CFF step 2
arrow collect -> analyze "metrics" step 3
:::
```

## 3단계: 프롬프트로 반영

편집이 끝나면 Claude Code에 반영 프롬프트를 입력합니다.

### 반영 프롬프트

다음 중 아무 표현이나 사용할 수 있습니다:

| 프롬프트 | 설명 |
|----------|------|
| `반영해주세요` | 변경사항을 HTML로 빌드 |
| `remarp 반영` | 동일 |
| `다시 빌드` | 동일 |
| `rebuild` | 영어 키워드 |

### 예시

```
01-fundamentals.remarp.md 에서 퀴즈 문제를 3개에서 4개로 늘렸어. 반영해줘.
```

```
Canvas 슬라이드에서 Detect 단계 아이콘을 추가했어. 다시 빌드해줘.
```

Claude가 자동으로 `remarp_to_slides.py build` 또는 `sync`를 실행하여 변경된 블록만 다시 빌드합니다.

## 4단계: 브라우저 프리뷰

빌드된 HTML 파일을 브라우저에서 엽니다.

### 키보드 조작

| 키 | 동작 |
|----|------|
| `←` `→` | 이전/다음 슬라이드 |
| `Space` | 다음 Fragment 또는 다음 슬라이드 |
| `F` | 전체 화면 |
| `O` | 개요 모드 (전체 슬라이드 그리드) |
| `P` | 프레젠터 뷰 (노트/타이밍 표시) |
| `N` | 스피커 노트 패널 |

### 인터랙티브 슬라이드 조작

| 슬라이드 타입 | 조작 |
|---------------|------|
| Compare | `↑` `↓` 로 좌/우 옵션 전환 |
| Tabs | `↑` `↓` 로 탭 전환 |
| Quiz | 선택지 클릭으로 정답 확인 |
| Canvas | `Space` 로 step별 요소 등장 |
| Checklist | 체크박스 클릭으로 항목 완료 |

## 5단계: HTML 직접 편집 (선택)

빌드된 HTML 파일을 VSCode에서 열면 Remarp 확장이 자동으로 인식합니다.

### 확인 방법

에디터 타이틀 바에 👁(Preview), ✏️(Edit), ▶(Build) 아이콘이 표시되면 Remarp HTML로 인식된 것입니다.

### Visual Edit 모드

1. ✏️ 아이콘을 클릭하여 Edit 모드 활성화
2. 슬라이드 요소를 드래그하여 위치/크기 조정
3. 변경사항이 소스 `.remarp.md`의 `:::css` 블록에 자동 반영
4. 소스 저장 시 HTML 자동 재빌드

이 기능으로 **HTML 결과물을 보면서 소스를 간접 편집**하는 양방향 워크플로우가 가능합니다.

## 반복 편집 사이클

실제 작업은 아래 사이클을 반복합니다:

```
┌─────────────────────────────────────────────────┐
│  1. VSCode에서 .remarp.md 편집                  │
│  2. Claude에 "반영해줘" 프롬프트                │
│  3. 브라우저 또는 VSCode에서 결과 확인          │
│  3b. (선택) HTML에서 Visual Edit → 소스 자동반영│
│  4. 필요하면 1로 돌아가서 수정                  │
└─────────────────────────────────────────────────┘
```

### 증분 빌드

멀티파일 프로젝트에서는 변경된 블록만 빌드하므로 빠르게 반복할 수 있습니다. `sync` 명령은 `.remarp.md` 파일의 수정 시각(mtime)을 `.html` 파일과 비교하여 변경된 블록만 다시 빌드합니다.

## 슬라이드 타입 빠른 참조

| 타입 | 디렉티브 | 용도 |
|------|----------|------|
| 기본 | (없음) | 제목 + 본문 + 리스트 |
| Compare | `@type: compare` | A vs B 좌우 비교 |
| Tabs | `@type: tabs` | 탭으로 구분된 콘텐츠 |
| Canvas | `@type: canvas` | 아키텍처 다이어그램 애니메이션 |
| Quiz | `@type: quiz` | 자동 채점 퀴즈 |
| Timeline | `@type: timeline` | 시간순 흐름 |
| Cards | `@type: cards` | 카드 그리드 |
| Checklist | `@type: checklist` | 체크리스트 |
| Thank You | `@type: thankyou` | 마무리 슬라이드 |

## 다음 단계

- [슬라이드 타입별 문법](./slide-types/content.md) 상세 가이드
- [Canvas DSL](./syntax/canvas-dsl.md) 다이어그램 작성법
- [프래그먼트](./syntax/fragments.md) 클릭 애니메이션 상세
- [테마 설정](./themes/pptx-extraction.md) PPTX 테마 추출
