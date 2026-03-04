---
sidebar_position: 2
title: CSS 변수
---

# CSS 변수

PPTX 테마를 추출하면 색상 스키마가 자동으로 CSS 변수로 변환됩니다. 이 변수들을 사용하여 프레젠테이션의 스타일을 일관되게 유지할 수 있습니다.

## 자동 생성 변수

PPTX에서 테마를 추출하면 `theme-override.css` 파일이 생성됩니다:

```css
:root {
  --pptx-accent1: #FF9900;
  --pptx-accent2: #232F3E;
  --pptx-accent3: #146EB4;
  --pptx-accent4: #4CAF50;
  --pptx-accent5: #f44336;
  --pptx-accent6: #9C27B0;
  --pptx-dk1: #000000;
  --pptx-lt1: #FFFFFF;
  --pptx-dk2: #1A1A1A;
  --pptx-lt2: #F5F5F5;
}
```

## 기본 테마 변수

reactive-presentation 프레임워크의 기본 테마 변수:

### 배경 색상

```css
--bg-primary: #0f1117    /* 메인 배경 */
--bg-secondary: #1a1d2e  /* 보조 배경 */
--bg-tertiary: #232740   /* 3차 배경 */
--bg-card: #1e2235       /* 카드 배경 */
--surface: #282d45       /* 표면 색상 */
--border: #2d3250        /* 테두리 색상 */
```

### 강조 색상

```css
--accent: #6c5ce7        /* 기본 강조색 */
--accent-light: #a29bfe  /* 밝은 강조색 */
--accent-glow: rgba(108,92,231,.3)  /* 글로우 효과 */
```

### 상태 색상

```css
--green: #00b894   /* 성공 */
--yellow: #fdcb6e  /* 경고 */
--red: #e17055     /* 오류 */
--blue: #74b9ff    /* 정보 */
--cyan: #00cec9    /* 링크 */
--orange: #f39c12  /* 주의 */
```

### 텍스트 색상

```css
--text-primary: #ffffff              /* 기본 텍스트 */
--text-secondary: rgba(255,255,255,0.7)  /* 보조 텍스트 */
--text-muted: rgba(255,255,255,0.5)      /* 흐린 텍스트 */
```

### 폰트

```css
--font-main: Pretendard, -apple-system, sans-serif
--font-mono: JetBrains Mono, monospace
```

## PPTX 색상과 테마 변수 매핑

테마 추출 시 PPTX 색상은 다음과 같이 매핑됩니다:

| PPTX 색상 | 테마 변수 | 용도 |
|----------|---------|------|
| `accent1` | `--accent` | 기본 강조색 |
| `accent2` | `--accent-light` | 보조 강조색 |
| `accent3` | `--green` | 성공 표시 |
| `accent4` | `--red` | 오류 표시 |
| `accent5` | `--orange` | 경고 표시 |
| `accent6` | `--yellow` | 주의 표시 |
| `dk2` | `--bg-primary` | 배경 (어두운 경우만) |
| `lt1` | `--text-primary` | 텍스트 (밝은 경우만) |
| `hlink` | `--cyan` | 링크 |

## Canvas DSL에서 색상 사용

Canvas DSL에서 색상 키워드로 변수를 참조할 수 있습니다:

```markdown
:::canvas
box api "API Gateway" at 100,150 size 120x60 color=accent
box lambda "Lambda" at 300,150 size 120x60 color=green
box error "Error" at 500,150 size 120x60 color=red
:::
```

### 지원되는 색상 키워드

| 키워드 | CSS 변수 |
|--------|---------|
| `accent` | `--accent` |
| `green` | `--green` |
| `yellow` | `--yellow` |
| `red` | `--red` |
| `blue` | `--blue` |
| `cyan` | `--cyan` |
| `orange` | `--orange` |
| `border` | `--border` |

## 변수 커스터마이징

### theme-override.css 수정

```css
:root {
  /* PPTX에서 추출된 색상 오버라이드 */
  --accent: #41B3FF;        /* 브랜드 색상으로 변경 */
  --accent-light: #AD5CFF;  /* 밝은 변형 */

  /* 추가 커스텀 변수 */
  --brand-primary: #FF9900;
  --brand-secondary: #232F3E;
}
```

### 슬라이드별 오버라이드

특정 슬라이드에서 변수를 오버라이드할 수 있습니다:

```markdown
---
@background: var(--brand-primary)

## Branded Slide

This slide uses the brand primary color as background.
```

## 다크 테마 보존

테마 추출은 어두운 테마 기반을 유지합니다:

- 배경은 어둡게 유지 (`--bg-primary`는 dk2의 휘도가 0.2 미만일 때만 오버라이드)
- 텍스트 색상은 어두운 배경에서 읽기 쉽도록 밝게 유지
- PPTX의 강조색만 직접 적용
- `--accent-glow`는 accent1의 rgba(0.3) 버전으로 자동 생성

## 예제: 커스텀 스타일 적용

```css
/* 타이틀 슬라이드에 그라데이션 배경 적용 */
.title-slide {
  background: linear-gradient(135deg, var(--bg-primary), rgba(65,179,255,0.1));
}

/* 타이틀 슬라이드에서 다른 로고 크기 */
.title-slide .slide-logo {
  height: 48px;
}

/* 강조 카드 스타일 */
.card.highlight {
  border-color: var(--accent);
  box-shadow: 0 0 20px var(--accent-glow);
}
```
