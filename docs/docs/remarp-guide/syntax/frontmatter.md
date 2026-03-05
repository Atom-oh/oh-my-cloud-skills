---
sidebar_position: 1
title: Frontmatter
---

# Frontmatter

Frontmatter는 프레젠테이션의 전역 설정을 정의하는 YAML 블록입니다. 파일 최상단에 `---`로 감싸서 작성합니다.

## 글로벌 Frontmatter

단일 파일 프레젠테이션에서는 파일 최상단에, 멀티파일 프로젝트에서는 `_presentation.remarp.md` 파일에 작성합니다.

```yaml
---
remarp: true
version: 1
title: "AWS Architecture Deep Dive"
author: "Cloud Team"
audience: "클라우드 엔지니어 (중급)"
date: 2025-01-15
event: "AWS Summit 2025"
lang: ko

blocks:
  - name: fundamentals
    title: "Block 1: Fundamentals"
    duration: 30
  - name: advanced
    title: "Block 2: Advanced Patterns"
    duration: 25
  - name: hands-on
    title: "Block 3: Hands-On Lab"
    duration: 45

theme:
  primary: "#232F3E"
  accent: "#FF9900"
  font: "Amazon Ember"
  codeTheme: "github-dark"

transition:
  default: slide
  duration: 400

keys:
  next: ["ArrowRight", "Space", "n"]
  prev: ["ArrowLeft", "Backspace", "p"]
  overview: ["o", "Escape"]
  presenter: ["s"]
---
```

## 필드 레퍼런스

### 기본 필드

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `remarp` | boolean | Yes | `true`로 설정하여 Remarp 처리 활성화 |
| `version` | number | No | 포맷 버전 (기본값: 1) |
| `title` | string | Yes | 프레젠테이션 제목 (HTML `<title>`에 사용) |
| `author` | string | No | 발표자 이름 |
| `audience` | string | No | 대상 청중 (기술 수준/역할) |
| `date` | date | No | 프레젠테이션 날짜 (YYYY-MM-DD) |
| `event` | string | No | 이벤트 또는 컨퍼런스 이름 |
| `lang` | string | No | 언어 코드 (`ko`, `en`, `ja`) |

### blocks 배열

멀티파일 프로젝트에서 블록(섹션)을 정의합니다:

```yaml
blocks:
  - name: architecture     # URL-safe 슬러그 (파일명에 사용)
    title: "Architecture"  # 사람이 읽는 제목
    duration: 30           # 소요 시간 (분)
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `name` | string | URL-safe 식별자 (파일명 매칭용) |
| `title` | string | 블록 제목 |
| `duration` | number | 예상 소요 시간 (분) |

### theme 객체

테마 설정을 정의합니다:

```yaml
theme:
  source: "./company-template.pptx"  # PPTX/PDF 파일 또는 추출된 디렉토리
  primary: "#232F3E"       # 기본 색상 (헤더, 배경)
  accent: "#FF9900"        # 강조 색상 (하이라이트, 링크)
  font: "Amazon Ember"     # 본문 폰트
  codeTheme: "github-dark" # 코드 구문 강조 테마
  footer: auto             # 자동 추출 또는 직접 지정
  pagination: true         # 페이지 번호 표시
  logo: auto               # 자동 추출 또는 경로 지정
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `source` | string | PPTX/PDF 파일 경로 또는 추출된 테마 디렉토리 |
| `primary` | string | 기본 색상 (CSS 색상값) |
| `accent` | string | 강조 색상 (CSS 색상값) |
| `font` | string | 본문 폰트 패밀리 |
| `codeTheme` | string | 코드 구문 강조 테마 |
| `footer` | string | `auto` 또는 직접 문자열 지정 |
| `pagination` | boolean | 페이지 번호 표시 여부 |
| `logo` | string | `auto` 또는 로고 파일 경로 |

### transition 객체

슬라이드 전환 효과를 정의합니다:

```yaml
transition:
  default: slide           # 기본 전환 타입
  duration: 400            # 전환 시간 (ms)
```

사용 가능한 전환 타입: `none`, `fade`, `slide`, `convex`, `concave`, `zoom`

### keys 객체

키보드 단축키를 커스터마이즈합니다:

```yaml
keys:
  next: ["ArrowRight", "Space", "n"]
  prev: ["ArrowLeft", "Backspace", "p"]
  overview: ["o", "Escape"]
  presenter: ["s"]
```

## 블록 파일 Frontmatter

멀티파일 프로젝트에서 각 블록 파일(`01-fundamentals.remarp.md` 등)은 로컬 frontmatter를 가집니다:

```yaml
---
remarp: true
block: fundamentals
title: "Block 1: Fundamentals"
---
```

### 로컬 Frontmatter 필드

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `remarp` | boolean | Yes | Remarp 파일 식별자 |
| `block` | string | Yes | 블록 이름 (글로벌 `blocks[].name`과 매칭) |
| `title` | string | No | 블록 제목 (글로벌 설정 오버라이드) |

## PPTX 테마 소스

PPTX 파일을 테마 소스로 지정하면 색상, 폰트, 로고가 자동으로 추출됩니다:

```yaml
theme:
  source: "./company-template.pptx"
  footer: auto
  logo: auto
```

| 소스 타입 | 예시 | 동작 |
|----------|------|------|
| PPTX 파일 | `./template.pptx` | `_theme/` 디렉토리로 테마 추출 |
| PDF 파일 | `./template.pdf` | 색상과 이미지 추출 |
| 디렉토리 | `./_theme/template/` | 이미 추출된 테마 사용 |

## 예제: 완전한 글로벌 Frontmatter

```yaml
---
remarp: true
version: 1
title: "AWS Serverless Architecture"
author: "Cloud Team"
audience: "서버리스 개발자"
date: 2025-03-01
event: "AWS Tech Talk"
lang: ko

blocks:
  - name: fundamentals
    title: "Block 1: Serverless Fundamentals"
    duration: 25
  - name: patterns
    title: "Block 2: Architecture Patterns"
    duration: 30
  - name: hands-on
    title: "Block 3: Hands-On Lab"
    duration: 35

theme:
  source: "./aws-template.pptx"
  footer: "© 2025, Amazon Web Services"
  pagination: true
  logo: auto

transition:
  default: slide
  duration: 400

keys:
  next: ["ArrowRight", "Space"]
  prev: ["ArrowLeft"]
  presenter: ["p"]
---
```
