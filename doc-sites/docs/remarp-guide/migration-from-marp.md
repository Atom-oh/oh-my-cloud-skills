---
sidebar_position: 12
title: Marp에서 마이그레이션
---

# Marp에서 마이그레이션

기존 Marp 프레젠테이션을 Remarp로 마이그레이션하는 방법을 설명합니다.

## 자동 변환

`migrate` 명령으로 Marp 파일을 Remarp로 자동 변환합니다:

```bash
python3 remarp_to_slides.py migrate ./old-content.md -o ./my-presentation/
```

## 변환 테이블

| Marp | Remarp | 비고 |
|------|--------|------|
| `marp: true` | `remarp: true` | frontmatter 헤더 |
| `footer: "text"` | `footer: "text"` (또는 `theme.footer`) | 그대로 사용 가능 |
| `paginate: true` | `paginate: true` (또는 `theme.pagination`) | 그대로 사용 가능 |
| `backgroundColor: "#xxx"` | `backgroundColor: "#xxx"` | 글로벌 배경색 |
| `backgroundImage: url(...)` | `backgroundImage: url(...)` | 글로벌 배경이미지 |
| `header: "text"` | `header: "text"` | 글로벌 헤더 |
| `color: "#fff"` | `color: "#fff"` | 글로벌 텍스트 색상 |
| `<!-- type: canvas -->` | `@type canvas` | 디렉티브 문법 |
| `<!-- block: name -->` | 별도 블록 파일 | 멀티파일 구조 |
| `<!-- notes: text -->` | `:::notes ... :::` | 블록 문법 |
| HTML 주석 전체 | `@` 디렉티브 또는 `:::` 블록 | 선언적 문법 |

## 하위 호환성

Remarp 파서는 `marp: true` 파일도 그대로 처리합니다. 기존 Marp 파일을 변환하지 않고도 사용할 수 있습니다.

또한 Marp 표준 frontmatter 디렉티브(`footer`, `paginate`, `backgroundColor`, `backgroundImage`, `header`, `color`)를 top-level에서 그대로 사용할 수 있습니다. 이 디렉티브들은 자동으로 Remarp 내부 구조로 매핑되므로, 기존 Marp 파일의 frontmatter를 수정하지 않아도 동작합니다.

## 상세 변환 예제

### Frontmatter

**Marp:**
```yaml
---
marp: true
title: My Presentation
blocks:
  - name: intro
    title: "Introduction"
    duration: 20
---
```

**Remarp:**
```yaml
---
remarp: true
version: 1
title: My Presentation
blocks:
  - name: intro
    title: "Introduction"
    duration: 20
---
```

### 블록 지정

**Marp:**
```markdown
<!-- block: intro -->

# Welcome
Introduction content
```

**Remarp (별도 파일 `01-intro.remarp.md`):**
```markdown
---
remarp: true
block: intro
---

# Welcome
Introduction content
```

### 슬라이드 타입

**Marp:**
```markdown
---
<!-- type: compare -->
## Options

### Option A
Content A

### Option B
Content B
```

**Remarp:**
```markdown
---
@type: compare

## Options

::: left
### Option A
Content A
:::

::: right
### Option B
Content B
:::
```

### 스피커 노트

**Marp:**
```markdown
## Slide Title

Content here

<!-- notes: Remember to explain both options -->
```

**Remarp:**
```markdown
## Slide Title

Content here

:::notes
Remember to explain both options
:::
```

### Canvas 슬라이드

**Marp:**
```markdown
---
<!-- type: canvas -->
<!-- canvas-id: arch-diagram -->

## Architecture

<!-- Canvas content is defined in JavaScript -->
```

**Remarp:**
```markdown
---
@type: canvas
@canvas-id: arch-diagram

## Architecture

:::canvas
box api "API Gateway" at 100,150 size 120,60 color #FF9900
box lambda "Lambda" at 300,150 size 120,60 color #4CAF50
arrow api -> lambda "invoke"
:::
```

## 무엇이 바뀌나요?

### 바뀌는 것

| 항목 | Marp | Remarp |
|------|------|--------|
| 파일 확장자 | `.md` | `.remarp.md` (권장) |
| 타입 지정 | HTML 주석 | `@` 디렉티브 |
| 스피커 노트 | HTML 주석 | `:::notes` 블록 |
| 레이아웃 | 수동 HTML | `::: left/right/col` |
| 프래그먼트 | 불가 | `{.click}` |
| Canvas | 별도 JS | `:::canvas` DSL |

### 그대로 유지되는 것

- 마크다운 문법 (헤딩, 리스트, 볼드, 코드 등)
- 슬라이드 구분자 `---`
- 이미지 임베딩
- 코드 블록
- frontmatter 기본 구조

## 마이그레이션 체크리스트

### 1. Frontmatter 업데이트

- [ ] `marp: true` → `remarp: true`
- [ ] `version: 1` 추가 (선택사항)

### 2. 블록 분리 (선택사항)

- [ ] `<!-- block: name -->` 주석 제거
- [ ] 각 블록을 별도 파일로 분리
- [ ] 블록 파일에 로컬 frontmatter 추가

### 3. 디렉티브 변환

- [ ] `<!-- type: X -->` → `@type: X`
- [ ] `<!-- layout: X -->` → `@layout: X`
- [ ] `<!-- transition: X -->` → `@transition: X`

### 4. 스피커 노트 변환

- [ ] `<!-- notes: ... -->` → `:::notes ... :::`
- [ ] 타이밍 마커 추가: `{timing: 3min}`
- [ ] 큐 마커 추가: `{cue: demo}`

### 5. 레이아웃 변환

- [ ] 수동 HTML 레이아웃 → `@layout` 디렉티브
- [ ] 컬럼 → `::: left/right` 또는 `::: col`
- [ ] 그리드 → `::: cell`

### 6. 인터랙티브 기능 추가 (선택사항)

- [ ] 순차 표시 → `{.click}` 프래그먼트
- [ ] 다이어그램 → `:::canvas` DSL
- [ ] 퀴즈 → `@type: quiz` + 체크박스

## 점진적 마이그레이션

모든 것을 한 번에 변환할 필요는 없습니다:

1. **Phase 1**: `marp: true` → `remarp: true` 변경만
2. **Phase 2**: HTML 주석을 `@` 디렉티브로 변환
3. **Phase 3**: 스피커 노트를 `:::notes` 블록으로 변환
4. **Phase 4**: 레이아웃을 `:::` 블록으로 변환
5. **Phase 5**: 프래그먼트, Canvas 등 새 기능 추가

각 단계 후에 프레젠테이션이 정상 동작하는지 확인하세요.
