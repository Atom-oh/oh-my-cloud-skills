---
sidebar_position: 2
title: CSS 변수 (토큰 디자인 시스템)
---

# CSS 변수 — 토큰 디자인 시스템 (v1.9.0)

reactive-presentation은 **토큰 기반 디자인 시스템**을 사용합니다. 슬라이드에 색상·간격을 직접 하드코딩하지 않고 **시맨틱 역할 토큰**을 쓰면, **light 기본 테마**와 `.theme-dark` 양쪽에 자동으로 적응합니다.

> **원칙**: 생(raw) hex/rgba·인라인 색상 대신 `var(--token)`과 토큰 클래스(`.card-grid`·`.metric-card`·`.callout`·`.flow-h`)를 사용하세요. `validate`의 `RAW_HEX`/`RAW_RGBA`/`INLINE_STYLE`/`OFF_SCALE` 린트가 이를 강제합니다.

아래는 토큰만으로 구성한 슬라이드 예시입니다 — light 기본 테마, AWS 블루 액센트, 고대비 텍스트:

![토큰 디자인 시스템으로 렌더된 슬라이드](/img/demos/compare-tabs-newtheme.png)

## 테마 스코프 — light가 기본

색상 토큰은 두 스코프에 정의됩니다. **light가 기본**이며, 덱 루트에 `theme-dark` 클래스를 붙이면 dark로 전환됩니다.

```css
/* light (기본) — 클래스 불필요 */
:root, .theme-light { /* … role/surface 토큰 … */ }

/* dark — 덱 루트에 class="slide-deck theme-dark" */
.theme-dark { /* … 동일 토큰의 dark 값 … */ }
```

```html
<!-- 기본 light -->
<div class="slide-deck">…</div>
<!-- dark로 전환 -->
<div class="slide-deck theme-dark">…</div>
```

## 1. 역할 색상 토큰 (role tokens)

용도별 **시맨틱 역할**로 색을 고릅니다. 각 역할은 본색 / `-subtle`(배경 틴트) / `-on`(역할색 위 텍스트) 3종을 가집니다.

| 역할 | 토큰 | light 기본값 | 용도 |
|------|------|--------------|------|
| accent | `--accent` | `var(--pptx-accent1, #5b51d8)` | 기본 강조·입력·소스 |
| info | `--info` | `#2563eb` | 보조 정보·스트리밍·분석 |
| success | `--success` | `#0e9f6e` | 성공·결과·자동화 |
| warning | `--warning` | `#b45309` | 경고·처리·주의 |
| danger | `--danger` | `#dc2626` | 에러·위험·알림 |

```css
.badge { background: var(--accent-subtle); color: var(--accent); }
.cta   { background: var(--accent); color: var(--accent-on); }
```

각 역할의 변형: `--accent-subtle`·`--accent-on`, `--info-subtle`·`--info-on`, … (`success`/`warning`/`danger` 동일).

## 2. 서피스 / 텍스트 토큰

```css
--surface-1: #ffffff   /* 최상위 표면 (카드 배경) */
--surface-2: #f6f7f9   /* 보조 표면 */
--surface-3: #eceff3   /* 3차 표면·구분 */
--on-surface: #1a1d2e        /* 표면 위 기본 텍스트 (고대비) */
--on-surface-muted: #5b6072  /* 보조/설명 텍스트 */
```

> 레거시 별칭도 토큰으로 매핑됩니다: `--bg-primary→var(--surface-1)`, `--bg-card→var(--surface-2)`, `--text-primary→var(--on-surface)`, `--text-secondary→var(--on-surface-muted)`. 기존 슬라이드는 그대로 동작하되, 신규는 위 토큰을 권장합니다.

## 3. 간격 · 반경 · 그림자 · 타이포 토큰

```css
--space-1 … --space-6   /* 4·8px 기반 스페이싱 스케일 */
--radius-sm / --radius-md / --radius-pill
--shadow-1 / --shadow-2
--weight-semibold / --weight-bold
```

> 매직넘버 px 대신 `var(--space-*)`를 쓰세요 — 들쭉날쭉한 간격을 막고 `OFF_SCALE` 린트를 통과합니다.

## 4. 브랜드 입력 — `--pptx-*`

PPTX 테마(또는 브랜드)는 **`--pptx-*` 입력 토큰**으로만 주입합니다. theme.css가 이를 per-theme로 소비합니다(`--accent: var(--pptx-accent1, …)`). 따라서 브랜드 색이 light/dark 양쪽으로 자연스럽게 흐릅니다.

```css
/* theme-override.css — 브랜드 입력만! role/bg 토큰을 :root에 직접 박지 말 것 */
:root {
  --pptx-accent1: #2563EB;  /* → --accent */
  --pptx-accent3: #1B843F;  /* → success 계열 */
  --pptx-dk2:     #161D26;  /* .theme-dark 표면 */
  --pptx-lt1:     #FFFFFF;  /* light 표면 */
}
```

> ⚠️ **흔한 실수**: 구 추출기처럼 `:root { --bg-primary:…; --text-primary:#fff }`를 직접 쓰면 light 배경에 흰 글자(가독성 깨짐) + 카드/배경 테마 혼합이 발생합니다. **`--pptx-*`만** 세팅하세요. (`themes/pptx-extraction.md` 참조)

## 5. 토큰 클래스 (직접 var 쓰기 전에)

대부분의 레이아웃은 토큰을 내장한 클래스로 해결됩니다 — 인라인 스타일이 필요 없습니다.

| 클래스 | 용도 |
|--------|------|
| `.card-grid` | 반응형 카드 그리드 (`auto-fit, minmax`) |
| `.metric-card` / `.metric-label` | 카드 + 보조 라벨(muted) |
| `.callout` + `.callout-info/-success/-warning/-danger` | 역할별 콜아웃 |
| `.flow-h` / `.flow-group` / `.flow-box` / `.flow-arrow` | 가로 흐름 다이어그램 (박스 5+) |
| `.tab-bar` / `.tab-btn` / `.tab-content` | `@type: tabs` 렌더 |

```html
<div class="card-grid">
  <div class="metric-card"><strong>Runtime</strong><div class="metric-label">8시간 실행</div></div>
  <div class="callout callout-success"><strong>결과</strong> 자동 복구</div>
</div>
```

## 6. Canvas에서 토큰 쓰기

`<canvas>`의 `ctx.fillStyle`은 **CSS 변수를 해석하지 못합니다**. `:::canvas` DSL은 프레임워크가 토큰을 대신 읽어 처리하지만, 직접 `:::script`로 캔버스를 그릴 때는 런타임에 값을 읽어야 합니다:

```js
const root = el.closest('.slide-deck') || document.documentElement;
const css = getComputedStyle(root);
const accent = css.getPropertyValue('--accent').trim() || '#2563EB';  // fallback 필수
// draw 루프 밖에서 1회 읽어 캐시. 테마 토글은 MutationObserver로 갱신.
```

## 관련 문서

- [커스텀 테마](./custom-themes) — 토큰 오버라이드로 브랜드 적용
- [PPTX 테마 추출](./pptx-extraction) — `--pptx-*` 브랜드 입력 생성
- [Build CLI](../build-cli) — `validate`의 디자인 린트 규칙
