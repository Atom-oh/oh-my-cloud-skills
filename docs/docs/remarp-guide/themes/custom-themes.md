---
sidebar_position: 3
title: 커스텀 테마
---

# 커스텀 테마

PPTX 추출 외에도 직접 커스텀 테마를 만들 수 있습니다.

## Frontmatter에서 테마 정의

```yaml
---
remarp: true
title: "My Presentation"

theme:
  primary: "#232F3E"       # 기본 색상
  accent: "#FF9900"        # 강조 색상
  font: "Amazon Ember"     # 본문 폰트
  codeTheme: "github-dark" # 코드 구문 강조 테마
---
```

## 테마 필드

| 필드 | 설명 | 예시 |
|------|------|------|
| `primary` | 기본 색상 (헤더, 배경) | `#232F3E` |
| `accent` | 강조 색상 (버튼, 링크) | `#FF9900` |
| `font` | 본문 폰트 패밀리 | `"Amazon Ember"` |
| `codeTheme` | 코드 구문 강조 테마 | `"github-dark"` |

## CSS 오버라이드 파일 생성

프레젠테이션 디렉토리에 `theme-override.css` 파일을 생성합니다:

```css
/* theme-override.css */
:root {
  /* 색상 오버라이드 */
  --bg-primary: #0a0e14;
  --bg-secondary: #151a22;
  --accent: #ff6b35;
  --accent-light: #ff8f66;

  /* 폰트 오버라이드 */
  --font-main: "Inter", sans-serif;
  --font-mono: "Fira Code", monospace;
}

/* 웹 폰트 로드 */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Fira+Code&display=swap');
```

## 컴포넌트별 스타일링

### 타이틀 슬라이드

```css
.title-slide {
  background: linear-gradient(135deg, #1a1f35 0%, #0d1117 50%, #161b2e 100%);
}

.title-slide h1 {
  background: linear-gradient(135deg, var(--accent-light), var(--cyan));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
```

### 카드 컴포넌트

```css
.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.5rem;
}

.card.highlight {
  border-color: var(--accent);
  box-shadow: 0 0 30px var(--accent-glow);
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}
```

### 버튼 스타일

```css
.btn {
  background: var(--bg-secondary);
  color: var(--text-primary);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.5rem 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary {
  background: var(--accent);
  border-color: var(--accent);
}

.btn:hover {
  background: var(--accent-light);
  border-color: var(--accent-light);
}
```

### 코드 블록

```css
.code-block {
  background: #0d1117;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1rem;
  font-family: var(--font-mono);
  font-size: 0.875rem;
  overflow-x: auto;
}

.code-block .comment { color: #6a737d; }
.code-block .keyword { color: #ff7b72; }
.code-block .string { color: #a5d6ff; }
.code-block .key { color: #7ee787; }
.code-block .value { color: #79c0ff; }
.code-block .number { color: #f2cc60; }
```

## 로고 위치 조정

```css
.slide-logo {
  position: fixed;
  bottom: 16px;
  left: 20px;
  height: 32px;
  opacity: 0.8;
}

/* 타이틀 슬라이드에서 다른 위치/크기 */
.title-slide .slide-logo {
  bottom: 24px;
  height: 48px;
}
```

## 애니메이션 커스터마이징

### 슬라이드 전환

```css
.slide {
  transition: opacity 0.4s ease, transform 0.4s ease;
}

/* Fade 전환 */
.slide[data-transition="fade"] {
  opacity: 0;
}

.slide[data-transition="fade"].active {
  opacity: 1;
}

/* Slide 전환 */
.slide[data-transition="slide"] {
  transform: translateX(100%);
}

.slide[data-transition="slide"].active {
  transform: translateX(0);
}
```

### 프래그먼트 애니메이션

```css
/* 커스텀 애니메이션 추가 */
.fragment.custom-bounce {
  opacity: 0;
  transform: scale(0);
}

.fragment.custom-bounce.visible {
  opacity: 1;
  transform: scale(1);
  animation: bounce 0.5s ease;
}

@keyframes bounce {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}
```

## 반응형 조정

```css
/* 4K 디스플레이 */
@media (min-width: 2560px) {
  html {
    font-size: clamp(14px, 2.2vh, 52px);
  }

  .slide-logo {
    height: 48px;
  }
}

/* FHD 디스플레이 */
@media (max-width: 1920px) {
  html {
    font-size: clamp(14px, 2.2vh, 32px);
  }
}
```

## 테마 프리셋

### AWS 스타일

```css
:root {
  --accent: #ff9900;
  --accent-light: #ffb84d;
  --bg-primary: #232f3e;
  --bg-secondary: #1b2838;
}
```

### Modern Dark

```css
:root {
  --accent: #6c5ce7;
  --accent-light: #a29bfe;
  --bg-primary: #0f1117;
  --bg-secondary: #1a1d2e;
}
```

### Corporate Blue

```css
:root {
  --accent: #0066cc;
  --accent-light: #3399ff;
  --bg-primary: #1a1a2e;
  --bg-secondary: #16213e;
}
```

## 테마 적용 순서

1. `common/theme.css` - 기본 테마 (프레임워크 제공)
2. `theme-override.css` - PPTX 추출 또는 커스텀 오버라이드
3. 인라인 스타일 - 슬라이드별 스타일

나중에 로드된 스타일이 우선 적용됩니다.
