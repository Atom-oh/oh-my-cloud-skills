# Remarp Slides - VSCode 확장

Remarp 마크다운 포맷(`.remarp.md` 파일)을 사용하여 리액티브 프레젠테이션을 작성하기 위한 VSCode 확장입니다.

## 기능

### 구문 하이라이팅

Remarp 전용 TextMate 문법으로 종합적인 하이라이팅을 제공합니다:

- **디렉티브**: `@type`, `@layout`, `@transition`, `@background`, `@class`, `@timing`, `@animation` 등
- **블록 태그**: `:::notes`, `:::canvas`, `:::click`, `:::left`, `:::right`, `:::col`, `:::cell` 등
- **클릭 속성**: `{.click}`, `{.click animation=fade-up order=2}`
- **Canvas DSL**: 캔버스 도형, 위치, 스타일, 애니메이션 전체 하이라이팅
- **YAML Frontmatter**: 프레젠테이션 메타데이터 하이라이팅

### 라이브 프리뷰

- 현재 슬라이드를 보여주는 사이드 패널 프리뷰
- **사이드바 레이아웃**: 오른쪽 패널에 Speaker Notes + 이슈 배지 표시
- 타이핑하면 자동 업데이트 (디바운스 적용)
- VSCode 테마에 맞는 다크 모드
- 이전/다음 버튼으로 네비게이션
- 키보드 네비게이션 (화살표 키, Space, PageUp/PageDown)
- 커서 위치에 따라 해당 슬라이드로 동기화 (`remarp.scrollSync` 설정)
- 슬라이드 타입 렌더링: cover, compare, tabs, agenda, timeline, quiz, checklist, cards, code, steps, title, section, thankyou
- `@background` / `@badge` 디렉티브를 배경 이미지 및 배지 오버레이로 렌더링

### 문서 아웃라인

- 탐색기 사이드바에 모든 슬라이드 트리뷰 표시
- 각 슬라이드: 번호, 제목 (첫 번째 헤딩), @type 표시
- 클릭하면 에디터에서 해당 슬라이드로 이동
- 편집 시 자동 새로고침

### IntelliSense

스마트 자동완성 제공:

- **@ 디렉티브**: 모든 지원 디렉티브와 설명
- **디렉티브 값**: 타입별 값 (예: `@type content|compare|canvas|quiz|...`)
- **레이아웃 값**: 모든 레이아웃 옵션
- **전환 효과 값**: 모든 전환 효과
- **애니메이션 값**: 24가지 애니메이션 타입
- **::: 블록**: 모든 블록 타입과 스니펫 템플릿
- **{.click} 속성**: 클릭 애니메이션과 order
- **Canvas DSL**: 도형, 위치, 스타일, 애니메이션

### 이슈 어노테이션 & AI 리뷰

슬라이드에 개선 제안을 기록하면 Claude Code가 자동으로 수정합니다:

- **프롬프트 바**: 사이드바의 입력 필드에서 현재 슬라이드에 `<!-- issue: 텍스트 -->` 어노테이션 추가
- **이슈 배지**: 사이드바에 노란색 배지로 어노테이션 표시
- **슬라이드 수정 안내**: 어노테이션 개수를 표시하고 Claude Code에서 `/slide-fix` 실행 안내
- 이슈는 소스 `.md`에 HTML 주석으로 저장 — 포맷 영향 없음

### 슬라이드 네비게이션

- `Cmd+Shift+Right` (Mac) / `Ctrl+Shift+Right` (Win/Linux): 다음 슬라이드
- `Cmd+Shift+Left` (Mac) / `Ctrl+Shift+Left` (Win/Linux): 이전 슬라이드

## 설치

### VS Code Marketplace에서 설치

Extensions 뷰(`Ctrl+Shift+X`)에서 **"Remarp Slides"**를 검색하고 Install을 클릭합니다.

### VSIX에서 설치 (로컬)

```bash
code --install-extension remarp-vscode-0.1.0.vsix
```

### 개발

```bash
cd tools/remarp-vscode
npm install
npm run compile
```

그 다음 VSCode에서 F5를 눌러 Extension Development Host를 실행합니다.

## VS Code Marketplace에 배포

### 사전 준비

```bash
# vsce (Visual Studio Code Extension CLI) 설치
npm install -g @vscode/vsce
```

### 1. Publisher 생성

1. https://dev.azure.com 에 로그인하여 조직을 생성합니다 (없는 경우)
2. **User Settings** (우상단) → **Personal Access Tokens** → **New Token**으로 이동
   - Scopes: **Marketplace > Manage** 선택
   - 생성된 토큰을 복사 (한 번만 표시됨)
3. https://marketplace.visualstudio.com/manage → **Create publisher**로 이동
   - Publisher ID는 `package.json`의 `"publisher"`와 일치해야 함 (현재 `aws-cloud-skills`)

### 2. 패키지 & 배포

```bash
cd tools/remarp-vscode

# PAT로 로그인
vsce login aws-cloud-skills

# .vsix로 패키지 (선택사항, 테스트용)
vsce package

# Marketplace에 배포
vsce publish
```

### 3. 버전 업데이트

```bash
# 패치/마이너/메이저 버전 올리고 배포를 한 번에
vsce publish patch   # 0.1.0 → 0.1.1
vsce publish minor   # 0.1.0 → 0.2.0
vsce publish major   # 0.1.0 → 1.0.0
```

### 배포 전 체크리스트

- [ ] `media/icon.png` 존재 (128x128 PNG, Marketplace 요구사항)
- [ ] `package.json`의 `publisher`가 Azure DevOps Publisher ID와 일치
- [ ] `npm run compile` 에러 없이 성공
- [ ] F5로 Extension Development Host에서 로컬 테스트 완료

## 사용법

1. `.remarp.md` 확장자로 파일 생성
2. Remarp 문법으로 프레젠테이션 작성
3. 에디터 제목 표시줄의 미리보기 아이콘 클릭 (또는 "Remarp: Preview" 명령 실행)
4. 탐색기의 아웃라인 뷰에서 슬라이드 탐색

### 예제

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

## 명령어

| 명령어 | 설명 |
|--------|------|
| `Remarp: Preview` | 슬라이드 미리보기 패널 열기 |
| `Remarp: Next Slide` | 다음 슬라이드로 이동 |
| `Remarp: Previous Slide` | 이전 슬라이드로 이동 |
| `Remarp: Build HTML` | 현재 Remarp 파일에서 HTML 빌드 |
| `Remarp: Show Slide Fix Guide` | `<!-- issue: -->` 어노테이션 개수를 표시하고 `/slide-fix` 실행 안내 |

## 요구 사항

- VSCode 1.85.0 이상

## 알려진 제한 사항

- 프리뷰는 단순화된 마크다운 렌더링 사용 (전체 Remarp HTML 빌더 아님)
- Canvas DSL 프리뷰는 소스를 `<pre>` 블록으로 표시 (그래픽 렌더링 아님)
- 일부 복잡한 중첩 블록은 하이라이팅이 완벽하지 않을 수 있음
- Claude CLI 연동을 위해 `claude`가 PATH 또는 `~/.local/bin/`에 설치되어 있어야 함

## 기여

이 확장은 oh-my-cloud-skills 프로젝트의 일부입니다. 기여를 환영합니다!

## 라이선스

MIT
