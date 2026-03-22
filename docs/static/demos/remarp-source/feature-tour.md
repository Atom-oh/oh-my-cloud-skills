---
remarp: true
block: feature-tour
---

@type: cover
@background: linear-gradient(135deg, #161D26 0%, #0d1117 50%, #1a2332 100%)

# Remarp Feature Tour
인터랙티브 프레젠테이션 프레임워크의 모든 기능

@speaker: Remarp Demo
@speaker-title: Interactive Presentation Framework

---
@type: title

# Remarp 주요 기능
마크다운으로 작성하고 HTML 슬라이드쇼로 변환

---

## Fragment 순차 표시 ({.click})

Remarp에서는 `{.click}` 문법으로 요소를 순차적으로 표시합니다:

- **Step 1**: 콘텐츠 기획 및 구조 설계 {.click}
- **Step 2**: Remarp 마크다운 소스 작성 {.click}
- **Step 3**: HTML 슬라이드쇼 빌드 {.click}
- **Step 4**: 프레젠테이션 전달 {.click}

> 스페이스바를 눌러 하나씩 나타나는 것을 확인하세요

---
@type: compare

## Compare 슬라이드

### Before: 기존 도구

- PowerPoint/Keynote로 수작업
- 디자인에 시간 소모
- 버전 관리 어려움
- 인터랙티브 요소 제한

### After: Remarp

- 마크다운으로 빠른 작성
- 자동 레이아웃 & 테마
- Git 기반 버전 관리
- Canvas, Quiz, Tabs 내장

---
@type: canvas
@canvas-id: remarp-workflow

## Remarp 워크플로우

:::canvas
box md "Markdown Source" at 60,150 size 150,40 color #41B3FF step 1
box build "remarp_to_slides.py" at 280,150 size 170,40 color #FF9900 step 2
box html "HTML Slideshow" at 520,150 size 150,40 color #00E500 step 3
box theme "Theme CSS" at 280,60 size 170,40 color #AD5CFF step 4
box js "JS Framework" at 280,240 size 170,40 color #AD5CFF step 4

arrow md -> build "input" step 5
arrow build -> html "output" step 5
arrow theme -> build "styling" step 6
arrow js -> build "interactivity" step 6
:::

---

## Code 하이라이팅

Remarp는 코드 블록을 자동으로 하이라이팅합니다:

```python
# remarp_to_slides.py 빌드 명령
import remarp

project = remarp.load("./my-presentation/")
project.build(output="./dist/", lang="ko")
```

```yaml
# _presentation.md 메타데이터
remarp: true
title: "My Presentation"
theme:
  primary: "#232F3E"
  accent: "#FF9900"
```

---
@type: quiz

## Remarp 확인 퀴즈

**Q1: Remarp 소스 파일의 확장자는?**

- [ ] .pptx
- [x] .md (마크다운)
- [ ] .html
- [ ] .json

**Q2: Canvas DSL에서 요소를 순차적으로 표시하는 키워드는?**

- [ ] order
- [ ] sequence
- [x] step
- [ ] animate

---

## Summary

| 기능 | 문법 | 설명 |
|------|------|------|
| Cover | `@type: cover` | 타이틀 슬라이드 |
| Fragment | `{.click}` | 순차 표시 |
| Compare | `@type: compare` | 좌우 비교 |
| Canvas | `@type: canvas` + `:::canvas` | 단계별 다이어그램 |
| Tabs | `@type: tabs` | 탭 전환 |
| Quiz | `@type: quiz` + `[x]` | 인터랙티브 퀴즈 |
| Code | 코드 블록 | 구문 강조 |

> Remarp: **Re**active **Ma**rkdown **R**e**p**resentation
