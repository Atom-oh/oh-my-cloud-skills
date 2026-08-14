# Framework Contract — HTML-First Deck Authoring

이 문서가 **컴파일러를 대체한다**: Claude는 Remarp 문법이 아니라 이 계약과
`assets/example-deck/` 골든 예시를 읽고 슬라이드 HTML을 직접 작성한다.
모든 내용은 `assets/`의 실제 코드에서 도출되었다 — 이 문서가 코드와 어긋나면 그건
버그다 (`tests/structure/test-reactive-design-tokens.sh`가 토큰 커버리지를 강제).

## 1. Deck Skeleton (필수 DOM)

`theme.css`와 `slide-framework.js`가 이 구조를 요구한다:

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Deck Title</title>
  <link rel="stylesheet" href="./common/theme.css">
  <!-- PPTX 테마 추출 시에만: -->
  <link rel="stylesheet" href="./common/pptx-theme/theme-override.css">
</head>
<body>
<div class="slide-deck">                <!-- 정확히 1개. theme-dark를 여기 붙이면 덱 전체 다크 -->
  <div class="slide">                   <!-- 슬라이드마다 1개 -->
    <div class="slide-header">
      <h2>제목 (≤28자 헤드라인)</h2>
      <p class="subtitle">부제 (체언 종결, ≤45자)</p>
    </div>
    <div class="slide-body">
      <!-- 콘텐츠 -->
    </div>
    <template class="notes" data-timing="3min">
[요약]
- 핵심 3~5 불릿
구어체 스피커 스크립트 (150자+, 권장 300~500).
{cue: demo} 마커 사용 가능.
    </template>
  </div>
  <!-- ... more .slide ... -->
</div>
<script src="./common/animation-utils.js"></script>
<script src="./common/slide-framework.js"></script>
<script src="./common/quiz-component.js"></script>
<script src="./common/presenter-view.js"></script>
<script>
  // presenterNotes: top-level const — export_pptx.py가 이 형태로 읽는다.
  // <template class="notes">를 쓰면 생략 가능 (프레임워크가 DOM에서 수집).
  const deck = new SlideFramework({
    footer: '© 2026 Company — Session Title',
    logoSrc: './common/logo.png',        // 선택
    logoDarkSrc: './common/logo-w.png',  // 선택: 다크 슬라이드용 밝은 로고
    pagination: true,                    // true: "N / M" 페이지 번호
    sidebar: true,                       // 좌측 썸네일 사이드바 (S 토글)
    onSlideChange: (index, slide) => {}  // 선택
  });
</script>
</body>
</html>
```

- 커버/섹션 슬라이드는 `.slide-header`/`.slide-body` 없이 자유 레이아웃 가능 —
  단 최상위는 반드시 `.slide`.
- 첫 슬라이드 = Session Cover, 마지막 = Thank You(목차 링크) 관례 유지.
- 스피커 노트: `<template class="notes">` 권장 (이스케이프 불필요, diff 깨끗).
  구형 `const presenterNotes = {1: "...", ...}` + `presenterNotes:` 옵션도 계속 동작.
  둘 다 있으면 옵션 객체가 우선.

## 2. Theme Tokens (theme.css)

**3개 스코프**: `:root, .theme-light`(기본 — AWS 콘솔 라이트) · `.theme-dark`(squid-ink
night; 덱 루트 또는 개별 `.slide`에 클래스) · `.preset-paper`(웜 룩, 명시 선택 시만).
PPTX 추출 브랜드는 `--pptx-accent1/dk1/lt1/dk2/lt2`로 들어와 항상 우선한다
(`--accent: var(--pptx-accent1, #ec7211)`).

**시맨틱 롤 (색상은 반드시 이 토큰으로 — raw hex/rgba 금지, check_deck.py가 잡음):**

| 롤 | 토큰 | subtle 배경 | on-색 | 용도 |
|----|------|------------|-------|------|
| accent | `--accent` | `--accent-subtle` | `--accent-on` | 강조/입력/소스 (light: Smile orange #ec7211) |
| info | `--info` | `--info-subtle` | `--info-on` | 보조/분석 (Cloudscape blue) |
| success | `--success` | `--success-subtle` | `--success-on` | 성공/결과 |
| warning | `--warning` | `--warning-subtle` | `--warning-on` | 경고/처리 |
| danger | `--danger` | `--danger-subtle` | `--danger-on` | 에러/위험 |

**서피스/텍스트**: `--surface-1/2/3` (카드 배경 단계) · `--on-surface` ·
`--on-surface-muted` · `--bg-primary`(페이지 캔버스) · `--border` · `--border-focus`.

**레거시 별칭** (구 마크업·캔버스 호환, 새 코드는 롤 토큰 우선):
`--green/--yellow/--red/--blue/--orange`(+`-bg`) → 롤 토큰으로 라우팅됨 ·
`--cyan`/`--pink`(스코프별 고유 hue — 캔버스 다이어그램이 blue/red와 구분에 의존) ·
`--bg-secondary/tertiary/card` · `--surface` · `--text-primary/secondary/muted/accent` ·
`--accent-light` · `--accent-glow` · `--shadow-glow`.

**design-tokens.css (theme.css가 @import)**:

| 그룹 | 토큰 |
|------|------|
| 타입 스케일 (모듈러 1.25) | `--text-xs` `--text-sm` `--text-base` `--text-lg` `--text-xl` `--text-2xl` `--text-3xl` `--text-4xl` |
| 행간 | `--leading-tight` `--leading-normal` `--leading-relaxed` |
| 굵기 | `--weight-regular` `--weight-medium` `--weight-semibold` `--weight-bold` |
| 자간 | `--tracking-tight` `--tracking-normal` `--tracking-wide` |
| 스페이싱 (8px 그리드 — px 매직넘버 금지, OFF_SCALE 린트) | `--space-1` `--space-2` `--space-3` `--space-4` `--space-5` `--space-6` `--space-7` `--space-8` |
| 라운딩 | `--radius-sm` `--radius-md` `--radius-lg` `--radius-pill` |
| 그림자 | `--shadow-1` `--shadow-2` `--shadow-3` `--shadow-glow` |
| 모션 | `--duration-fast` `--duration-normal` `--duration-slow` `--ease-out` |
| z-index | `--z-base` `--z-nav` `--z-overlay` `--z-modal` `--z-toast` |

**폰트**: `--font-display`(Space Grotesk→Pretendard, 헤딩) · `--font-main`(Pretendard) ·
`--font-mono`(JetBrains Mono).

**사이징**: `--slide-width/height`, `--slide-ratio-w/h`(기본 16/9) — 비 16:9 덱만 재정의.

## 3. Scaling Model

고정 1920×1080 디자인 캔버스, `.slide-deck`이 `transform: scale(min(100vw/1920,
100vh/1080))`로 뷰포트에 맞춰 통째로 축소된다. 슬라이드 안에서는 절대 px 좌표를
써도 안전하다(캔버스가 통째로 스케일됨). **뷰포트 단위(vw/vh)를 콘텐츠 크기에 쓰지 말 것**
— 스케일 밖에서 이중 반응해 비율이 깨진다.

## 4. SlideFramework API (slide-framework.js)

```js
new SlideFramework({ footer, logoSrc, logoDarkSrc, presenterNotes, pagination,
                     sidebar, onSlideChange })
deck.registerSlideAction(slideIndex, { up: fn, down: fn })  // ↑↓ 키 가로채기; false 반환 시 슬라이드 이동
deck.goTo(i) / deck.next() / deck.prev()
```

- 프레임워크가 자동 생성: progress bar, slide counter/number, nav hint, footer,
  logo, ref 컨테이너, 썸네일 사이드바(1920px 콘텐츠를 scale로 축소).
- **키맵** (기본): `←→ Space PageUp/Down` 이동+fragment · `↑↓` slideAction →
  인터랙티브 순환(canvas step/tabs/compare) → fragment · `Home/End` · `P` presenter ·
  `F` fullscreen · `O` overview · `S` sidebar · `Esc`. `window.__remarpKeys`로 재매핑.
- 슬라이드에 `<img>`가 있으면 footer/logo/번호 자동 숨김.
- `data-transition="fade|slide|zoom"` per-slide 전환.
- `data-refs='[{"url":"…","label":"…"}]'` → 하단 참조 링크.
- URL 해시 `#N`으로 슬라이드 딥링크.

**Fragments**: `class="fragment fade-up" data-fragment-index="N"` — Space/→로 순차
공개. 같은 index는 동시 공개. 애니메이션: `fade-in/up/down/left/right, grow, shrink,
highlight(-red/-green), strike, fade-out`.

**Canvas step 슬라이드**: 슬라이드 요소에 `slide.__canvasStep = (dir) => bool` 를
달면 ↑↓가 step을 몰고, 끝에서 `false`를 반환하면 슬라이드가 넘어간다.
(또는 `registerSlideAction`.)

**자동 초기화되는 컴포넌트** (DOMContentLoaded에서 `initTabs/initChecklists/
initCompareToggles`):
- 탭: `.tab-bar > .tab-btn[data-tab="id"]` + 형제 `.tab-content[data-tab="id"]`
  (`.active`로 표시). ↑↓ 키로도 순환.
- 체크리스트: `.checklist li` 클릭 토글(+`.checklist-detail` 펼침).
- 비교: `.compare-toggle > .compare-btn[data-compare]` + `.compare-content[data-compare]`;
  컨테이너 `data-compare-mode="side-by-side"`면 하이라이트 모드.
- 프레임워크 JS 없이 동작해야 하는 자체완결 탭은 inline onclick 패턴도 허용
  (골든 예시 참조).

## 5. Canvas Animation (animation-utils.js)

**필수 패턴** — 모든 캔버스는 비례 스케일 + DPR 보정 (FHD/4K 대응):

```js
(function() {
  const BASE_W = 960, BASE_H = 400;
  const canvas = document.getElementById('my-canvas');
  const ctx = canvas.getContext('2d');
  let step = 0; const MAX_STEP = 3;
  function draw() {
    const dpr = window.devicePixelRatio || 1;
    // 반드시 clientWidth/Height (레이아웃 px) — getBoundingClientRect()는
    // transform 반영 시각 px라 덱 스케일과 이중 적용되어 캔버스가 넘친다.
    const pw = canvas.parentElement.clientWidth;
    const ph = canvas.parentElement.clientHeight;
    const scale = Math.min(pw / BASE_W, ph / BASE_H);
    canvas.width = BASE_W * scale * dpr; canvas.height = BASE_H * scale * dpr;
    canvas.style.width = BASE_W * scale + 'px'; canvas.style.height = BASE_H * scale + 'px';
    ctx.setTransform(1,0,0,1,0,0); ctx.scale(scale * dpr, scale * dpr);
    ctx.clearRect(0, 0, BASE_W, BASE_H);
    refreshThemeColors();
    // ... BASE_W/BASE_H 좌표계로 그리기 ...
    if (step >= 1) drawArrow(ctx, 180, 200, 260, 200, Colors.accent);
  }
  new ResizeObserver(draw).observe(canvas.parentElement);
  const slide = canvas.closest('.slide');
  slide.__canvasStep = (dir) => {
    const n = step + (dir === 'next' ? 1 : -1);
    if (n < 0 || n > MAX_STEP) return false;   // 슬라이드 이동 허용
    step = n; draw(); return true;
  };
  draw();
})();
```

**드로잉 헬퍼** (BASE 좌표계 인자): `drawBox(ctx,x,y,w,h,label,color)` ·
`drawArrow(ctx,x1,y1,x2,y2,color,dashed,showHead)` · `drawOrthogonalArrow(ctx,points,color)` ·
`drawCircle` · `drawText(ctx,text,x,y,{size,color,weight,align})` ·
`drawGroup(ctx,x,y,w,h,label,color)`(점선 그룹 박스) · `drawIcon(ctx,src,x,y,size)` ·
`drawPod` · `drawNode` · `drawCluster` · `drawRoundRect`.

**색상**: `Colors.accent/.blue/.green/.yellow/.red/.cyan/.pink/...` — CSS 변수에서
읽으므로 테마 자동 적응. 테마 전환 후 `refreshThemeColors()` 필요(위 패턴이 draw마다 호출).
`withAlpha(color, a)` · `resolveColor(ref)`.

**유틸**: `AnimationLoop(drawFn)` · `TimelineAnimation(steps, duration)` ·
`ParticleSystem` · `Ease.linear/inOut/out/in/elastic/bounce` · `lerp` · `clamp`.

**프리셋 5종** — `CanvasPresets[type](ctx, config, step, w, h)`:
`eks-pod-scaling` · `eks-node-scaling` · `traffic-flow` · `rolling-update` · `failover`.
직접 호출해 config 객체만 넘기면 됨.

**복잡도 규칙**: 박스 ≤4 + 단방향 화살표만 canvas. 5+ 박스/다계층은 HTML flow
유틸리티(§6)로. 정적 전체 아키텍처는 draw.io PNG/SVG `<img>`.

## 6. CSS Component Inventory (theme.css)

| 그룹 | 클래스 | 비고 |
|------|--------|------|
| 카드 | `.card-grid` `.card` `.metric-card` `.metric-value/.metric-label` `.kpi-row/.kpi-card/.kpi-value/.kpi-label/.kpi-delta` `.badge(-blue/-green/-red/-yellow/-up/-down)` | 4+ 나열은 불릿 대신 카드 |
| 콜아웃 | `.callout` `.callout-info/-success/-warning/-danger` `.pain-quote` `.stat-highlight` | |
| 레이아웃 | `.columns` `.col-2/.col-3` `.columns-1-2/-2-1/-3` `.grid-2x2/.grid-3x2` `.center-content` | |
| Flow(HTML 아키텍처) | `.flow-h/.flow-v` `.flow-group` `.flow-box` `.flow-arrow` `.flow-col` `.flow-step` `.flow-desc` `.icon-item` + `.bg-blue/-orange/-pink/-green/-purple/-red/-dark/-accent` | 박스 5+ 다이어그램의 기본 수단; stage 높이·너비 자동 균일 |
| 탭/비교 | `.tab-bar/.tab-btn/.tab-content` `.tab-set`(자체완결형) `.compare-toggle/.compare-btn/.compare-content/.compare-highlight` | §4 자동 init |
| 타임라인/스텝 | `.timeline/.timeline-step/-dot/-label/-desc/-connector` `.steps-container` `.steps--horizontal/--vertical/--circle/--rect/--icon` `.step-item/-marker/-label/-desc` `.agenda-timeline/.agenda-step/-dot/-label/-connector` | |
| 체크리스트/퀴즈 | `.checklist` `.checklist-detail` `.quiz`+`data-quiz` `.quiz-option`+`data-correct` | §4/§7 |
| 코드 | `.code-block` `.code-label` + `.keyword/.string/.comment/.number/.function` span | 하이라이트는 span 직접 또는 highlight.js CDN |
| 대시보드 | `.dashboard-grid` `.node-grid/.node-cell(-ready/-cordoned/-terminating/-empty)` `.event-log` `.data-table` `.qos-card/.qos-display` `.simulator-layout/.simulator-results` `.slider-container/-group/-row/-value` `.command-card/-header/-output` `.chart-container` `.yaml-output` `.mode-selector/-btn/-content` `.alert-toggle` | 인터랙티브 대시보드/시뮬레이터 |
| 타이포 헬퍼 | `.eyebrow` `.heading-group` `.text-blue/-green/-orange/-pink/-purple/-red/-icon` | |
| 캔버스 | `.canvas-container`(aspect-ratio 960/400) `.canvas-controls` | |
| 버튼 | `.btn/.btn-primary/.btn-sm/.btn-group` `.export-toolbar/.export-btn` | |
| 프레임워크 전용(직접 쓰지 말 것) | `.progress-bar` `.slide-counter/-number/-footer/-logo/-ref` `.nav-hint` `.slide-sidebar/.sidebar-thumb*` `.overview-mode` `.presenter-*` `.export-overlay/-progress*` | JS가 생성/관리 |

## 7. Quiz (quiz-component.js)

```html
<div class="quiz" data-quiz="q1">
  <p class="quiz-question">질문?</p>
  <div class="quiz-options">
    <button class="quiz-option" data-correct="false">A) 오답</button>
    <button class="quiz-option" data-correct="true">B) 정답</button>
  </div>
</div>
```
자동 init. `quizManager.reset(id)/resetAll()/getScore()`.

## 8. Presenter View & Export

- **P 키** → `PresenterView` 새 창: 현재+다음 슬라이드, 노트(cue/timing 렌더),
  경과 타이머, 드래그 분할. 노트 소스는 §1의 `presenterNotes`/`<template class="notes">`.
- **export-utils.js** (toc.html에서만 로드): `ExportUtils.exportPDF({title})` ·
  `exportPPTX({title})`(html2canvas+PptxGenJS CDN) · `downloadZIP()`.
- 고품질 PPTX는 headless 경로: `scripts/export_pptx.py <deck-dir>/ -o out.pptx`
  (Playwright 픽셀 캡처 + 스피커 노트 포함).

## 9. AWS Icons

- 공식 아이콘 필수 (아키텍처/서비스 소개 슬라이드) — 임의 그림 금지.
- 경로: `common/aws-icons/services/Arch_{Service}_48.svg` 등.
- `scripts/deck_assets.py`가 참조된 아이콘만 `common/aws-icons/`로 복사하고
  미해석 이름을 보고한다. (전체 811개 복사 금지.)

## 10. Authoring Rules (요약 — 상세는 design-direction.md)

- 색상은 롤 토큰만: raw hex/rgba/inline style 금지 (`check_deck.py` RAW_HEX/RAW_RGBA/INLINE_STYLE).
- 스페이싱은 8px 그리드 토큰 (OFF_SCALE).
- 불릿 4+ → 카드 그리드, 8+ → 슬라이드 분할.
- 제목 ≤28자 헤드라인 (단정/주장/질문/반전), 부제 체언 종결 ≤45자.
- 모든 콘텐츠 슬라이드에 `<template class="notes">` 150자+.
- light 기본 듀얼 테마 — 다크 전용 금지. 모든 색이 두 테마에서 성립해야 함.
- 덱 로컬 `<style>`은 최소화; 일반화 가능한 규칙은 스킬 `assets/theme.css`에
  패치하고 프레임워크 버전을 올린다 (덱별 재발명 금지 — check_deck.py가 중복 경고).
