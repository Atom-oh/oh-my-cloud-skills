---
sidebar_position: 11
title: VSCode 확장
---

# VSCode 확장

Remarp Slides VSCode 확장은 `.remarp.md` 파일과 Remarp가 생성한 HTML 파일 모두를 위한 편집 환경을 제공합니다.

## 기능

### 구문 하이라이팅

Remarp 전용 TextMate 문법으로 다음 요소를 하이라이팅합니다:

- **디렉티브**: `@type`, `@layout`, `@transition`, `@background`, `@class`, `@timing`, `@animation` 등
- **블록 태그**: `:::notes`, `:::canvas`, `:::click`, `:::left`, `:::right`, `:::col`, `:::cell` 등
- **클릭 속성**: `{.click}`, `{.click animation=fade-up order=2}`
- **Canvas DSL**: 도형, 위치, 스타일, 애니메이션 문법
- **YAML Frontmatter**: 프레젠테이션 메타데이터

### 라이브 프리뷰

- 사이드 패널에서 현재 슬라이드 미리보기
- 타이핑하면 자동 업데이트 (디바운스 적용)
- VSCode 테마에 맞는 다크 모드
- 이전/다음 버튼으로 네비게이션
- 키보드 네비게이션 (화살표 키, Space, PageUp/Down)
- 커서 위치에 따라 해당 슬라이드로 동기화
- Remarp가 생성한 HTML 파일 직접 프리뷰 (메타태그로 자동 인식)
- HTML 파일에서도 동일한 Preview/Edit/Build 아이콘 표시

### HTML 파일 지원

Remarp가 생성한 HTML 파일을 자동으로 인식하여 `.remarp.md`와 동일한 편집 환경을 제공합니다.

**인식 조건**: HTML `<head>`에 `<meta name="generator" content="remarp">` 태그가 있는 파일

**지원 기능**:
- 에디터 타이틀 바에 Preview(👁), Edit(✏️), Build(▶) 아이콘 표시
- Preview: HTML 내용을 그대로 webview에서 렌더링
- Visual Edit: 요소 드래그/리사이즈 시 소스 `.remarp.md`의 `:::css` 블록에 자동 반영
- Build: 소스 `.remarp.md`를 찾아서 재빌드

**소스 추적**: `<meta name="remarp-source" content="파일명.remarp.md">` 태그로 소스 파일을 자동 탐색합니다. HTML 파일 기준 상위 3단계까지 검색합니다.

:::tip 일반 HTML 파일에는 영향 없음
Remarp 메타태그가 없는 일반 `.html` 파일에서는 아이콘이 표시되지 않습니다.
:::

### 문서 아웃라인

- 탐색기 사이드바에 모든 슬라이드 트리뷰 표시
- 각 슬라이드: 번호, 제목 (첫 번째 헤딩), @type 표시
- 클릭하면 해당 슬라이드로 에디터 이동
- 편집 시 자동 새로고침

### IntelliSense

스마트 자동완성 제공:

- **@ 디렉티브**: 모든 지원 디렉티브와 설명
- **디렉티브 값**: 타입별 값 (`@type content|compare|canvas|quiz|...`)
- **레이아웃 값**: 모든 레이아웃 옵션
- **전환 효과 값**: 모든 전환 효과
- **애니메이션 값**: 12가지 애니메이션 타입
- **::: 블록**: 모든 블록 타입과 스니펫 템플릿
- **`{.click}` 속성**: 클릭 애니메이션과 order
- **Canvas DSL**: 도형, 위치, 스타일, 애니메이션

## 설치 방법

### VS Code Marketplace에서 설치

Extensions 뷰(`Ctrl+Shift+X`)에서 "**Remarp Slides**"를 검색하고 Install을 클릭합니다.

### VSIX에서 설치 (로컬)

```bash
code --install-extension remarp-vscode-0.1.0.vsix
```

### 개발 모드

```bash
cd tools/remarp-vscode
npm install
npm run compile
```

그 다음 VSCode에서 F5를 눌러 Extension Development Host를 실행합니다.

## 사용법

1. `.remarp.md` 확장자로 파일 생성
2. Remarp 문법으로 프레젠테이션 작성
3. 에디터 제목 표시줄의 미리보기 아이콘 클릭 (또는 "Remarp: Open Preview" 명령 실행)
4. 탐색기의 아웃라인 뷰에서 슬라이드 탐색
5. Remarp가 생성한 `.html` 파일을 열면 동일한 Preview/Edit/Build 아이콘 자동 표시
6. HTML에서 Visual Edit 모드로 편집하면 소스 `.remarp.md`에 자동 반영

## 키보드 단축키

### 슬라이드 네비게이션

| 단축키 (Mac) | 단축키 (Win/Linux) | 동작 |
|-------------|-------------------|------|
| `Cmd+Shift+Right` | `Ctrl+Shift+Right` | 다음 슬라이드 |
| `Cmd+Shift+Left` | `Ctrl+Shift+Left` | 이전 슬라이드 |

## 명령어

| 명령어 | 설명 |
|--------|------|
| `Remarp: Open Preview` | 슬라이드 미리보기 패널 열기 |
| `Remarp: Next Slide` | 다음 슬라이드로 이동 |
| `Remarp: Previous Slide` | 이전 슬라이드로 이동 |
| `Remarp: Toggle Visual Edit Mode` | 비주얼 편집 모드 전환 |
| `Remarp: Build HTML` | HTML 빌드 (HTML 파일에서는 소스 자동 탐색) |

## 예제

```markdown
---
title: My Presentation
author: Your Name
theme: dark
---

# Welcome

This is the first slide.

---

@type compare
@layout two-column

# Comparison Slide

::: left
## Option A
- Feature 1
- Feature 2
:::

::: right
## Option B
- Feature 3
- Feature 4
:::

---

@type canvas

# Architecture

:::canvas
box "Frontend" at 100 100 size 150 80 color="#4CAF50"
box "Backend" at 100 250 size 150 80 color="#2196F3"
arrow from 175 180 to 175 250
:::

---

# Click to Reveal

- First point {.click}
- Second point {.click animation=fade-up order=2}
- Third point {.click animation=zoom-in order=3}

:::notes
Speaker notes go here - not visible during presentation
:::
```

## 요구 사항

- VSCode 1.85.0 이상

## 알려진 제한 사항

- 미리보기는 단순화된 마크다운 렌더링 사용 (전체 Remarp 렌더러 아님)
- Canvas DSL 미리보기는 소스 코드를 `<pre>` 블록으로 표시 (그래픽 렌더링 아님)
- 일부 복잡한 중첩 블록은 하이라이팅이 완벽하지 않을 수 있음

## Marketplace 배포

### 사전 준비

```bash
# vsce (Visual Studio Code Extension CLI) 설치
npm install -g @vscode/vsce
```

### 1. Publisher 생성

1. https://dev.azure.com 에서 조직 생성
2. **User Settings** > **Personal Access Tokens** > **New Token**
   - Scopes: **Marketplace > Manage** 선택
3. https://marketplace.visualstudio.com/manage 에서 **Create publisher**
   - Publisher ID는 `package.json`의 `"publisher"`와 일치해야 함

### 2. 패키지 & 배포

```bash
cd tools/remarp-vscode

# PAT로 로그인
vsce login aws-cloud-skills

# .vsix로 패키지 (테스트용)
vsce package

# Marketplace에 배포
vsce publish
```

### 3. 버전 업데이트

```bash
# 버전 올리고 배포
vsce publish patch   # 0.1.0 → 0.1.1
vsce publish minor   # 0.1.0 → 0.2.0
vsce publish major   # 0.1.0 → 1.0.0
```
