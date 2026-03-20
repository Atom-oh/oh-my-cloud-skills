---
sidebar_position: 10
title: 빌드 & CLI
---

# 빌드 & CLI

Remarp 파일을 HTML 프레젠테이션으로 빌드하는 방법을 설명합니다.

## 기본 명령어

### build - HTML 생성

단일 파일 또는 프로젝트를 HTML로 빌드합니다:

```bash
# 단일 파일 빌드
python3 remarp_to_slides.py build my-talk.md

# 프로젝트 디렉토리 빌드
python3 remarp_to_slides.py build ./my-presentation/

# 출력 디렉토리 지정
python3 remarp_to_slides.py build my-talk.md -o ./output/
```

### sync - 증분 빌드

변경된 블록만 다시 빌드합니다 (멀티파일 프로젝트용):

```bash
# 변경된 블록만 빌드
python3 remarp_to_slides.py sync ./my-presentation/
```

### migrate - Marp 변환

기존 Marp 파일을 Remarp 형식으로 변환합니다:

```bash
# 단일 파일 변환
python3 remarp_to_slides.py migrate ./old-content.md -o ./my-presentation/
```

## 빌드 옵션

| 옵션 | 설명 |
|------|------|
| `-o, --output` | 출력 디렉토리 |
| `--block` | 특정 블록만 빌드 (멀티파일 프로젝트) |
| `--watch` | 파일 변경 감시 모드 |
| `--format` | 출력 형식 (`html`, `pdf`) |

## 멀티파일 프로젝트 구조

30분 이상의 긴 세션은 블록별로 파일을 분리하여 관리합니다:

```
my-presentation/
├── _presentation.md          # 글로벌 설정 (필수)
├── 01-fundamentals.md        # Block 1
├── 02-advanced.md            # Block 2
├── 03-hands-on.md            # Block 3
├── assets/                   # 이미지, 다이어그램
│   └── architecture.png
└── build/                    # 생성된 HTML
    ├── index.html            # TOC 페이지
    ├── 01-fundamentals.html
    ├── 02-advanced.html
    └── 03-hands-on.html
```

:::tip 파일 확장자
`.md` 확장자를 사용하고 frontmatter에 `remarp: true`를 추가합니다. `.remarp.md` 확장자도 하위호환 지원됩니다.
:::

### _presentation.md

글로벌 설정만 포함하는 메인 파일:

```yaml
---
remarp: true
title: "AWS Auto Scaling Deep Dive"
author: "Cloud Architect"
event: "AWS Summit Seoul 2026"
lang: ko

blocks:
  - file: 01-fundamentals.md
    name: fundamentals
    title: "Block 1: Fundamentals"
    duration: 25
  - file: 02-advanced.md
    name: advanced
    title: "Block 2: Advanced Patterns"
    duration: 30
  - file: 03-hands-on.md
    name: hands-on
    title: "Block 3: Hands-On Lab"
    duration: 35

theme:
  source: "./company.pptx"
  footer: "© 2026, Amazon Web Services, Inc."
---
```

### 블록 파일

각 블록 파일은 로컬 frontmatter와 슬라이드를 포함합니다:

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

## 빌드 명령어 예제

```bash
# 전체 프로젝트 빌드
python3 remarp_to_slides.py build ./my-presentation/

# 특정 블록만 빌드
python3 remarp_to_slides.py build ./my-presentation/ --block 01-fundamentals

# 변경된 블록만 증분 빌드
python3 remarp_to_slides.py sync ./my-presentation/

# 파일 변경 감시 모드
python3 remarp_to_slides.py build ./my-presentation/ --watch
```

## 내보내기 옵션

### PDF 내보내기

```bash
python3 remarp_to_slides.py build my-talk.md --format pdf
```

또는 브라우저에서 HTML을 열고 `ExportUtils.exportPDF()` 사용:

```javascript
// 브라우저 콘솔에서
ExportUtils.exportPDF({ title: 'My Presentation' });
```

### ZIP 내보내기

오프라인 뷰어용 전체 패키지:

```javascript
// 브라우저에서
ExportUtils.downloadZIP({ slug: 'my-presentation' });
```

포함 내용:
- HTML 파일들
- CSS/JS 프레임워크 파일
- 이미지, 아이콘
- 테마 파일

### PPTX 내보내기

```javascript
// 브라우저에서
ExportUtils.exportPPTX({ title: 'My Presentation' });
```

:::warning
PPTX 내보내기는 정적 슬라이드로 변환됩니다. Canvas 애니메이션, 인터랙티브 요소는 정적 이미지로 대체됩니다.
:::

## TOC 페이지

멀티파일 프로젝트를 빌드하면 자동으로 TOC(목차) 페이지가 생성됩니다:

```html
<!-- build/index.html -->
<div class="block-cards">
  <a href="01-fundamentals.html" class="block-card">
    <div class="block-number">Block 1</div>
    <div class="block-title">Fundamentals</div>
    <div class="block-duration">25 min</div>
  </a>
  <a href="02-advanced.html" class="block-card">
    <div class="block-number">Block 2</div>
    <div class="block-title">Advanced Patterns</div>
    <div class="block-duration">30 min</div>
  </a>
</div>

<div class="export-toolbar">
  <button onclick="ExportUtils.exportPDF({...})">Export PDF</button>
  <button onclick="ExportUtils.downloadZIP()">Download ZIP</button>
</div>
```

## GitHub Pages 배포

```bash
# build/ 디렉토리를 gh-pages 브랜치로 배포
git subtree push --prefix build origin gh-pages

# 또는 GitHub Actions 사용
```

빌드된 HTML은 정적 파일이므로 GitHub Pages, Netlify, S3 등 어디에서나 호스팅할 수 있습니다.
