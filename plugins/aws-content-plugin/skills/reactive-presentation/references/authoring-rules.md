# Authoring Rules & Patterns

작성 시 적용하는 상세 규칙·표·복사용 템플릿 모음. SKILL.md는 워크플로·게이트만 담고,
이 문서를 **실제 슬라이드를 작성/검증할 때** 참조합니다.

---

## 1. Validation — Rejection Loop (build 전 필수)

> **LLM 공간 추론 한계 극복**: 언어 모델은 2D 캔버스의 레이아웃·정렬·겹침을 자가 감지하지
> 못합니다. `validate`는 **외부화된 거절 루프**로 빌드 전 구조적/인지적 결함을 기계 검출합니다.

```bash
python3 {skill-dir}/scripts/remarp_to_slides.py validate {repo}/{slug}/
```

**검증 규칙 (거절 기준)**:

| 규칙 | 심각도 | 검사 내용 | 자동 교정 지침 |
|------|--------|---------|-------------|
| `TYPE_MISMATCH` | WARNING | 번호+시간 패턴이 있는데 `@type: agenda` 누락 | `@type: agenda` 추가 |
| `INTERACTIVE_FIRST` | WARNING | 불릿 4+ → 카드/탭 미사용 | `:::html` grid 카드 또는 탭 패턴으로 변환 |
| `CONTENT_OVERFLOW` | CRITICAL | 불릿 8+ 또는 요소 12+ (한 슬라이드) | 다수 슬라이드로 분할 |
| `CANVAS_COMPLEXITY` | CRITICAL/WARN | 캔버스 시각 요소 5+/8+ | `:::html` + `:::css` + flow 유틸리티로 전환 |
| `CANVAS_OVERLAP` | CRITICAL | 캔버스 요소 바운딩 박스 겹침 | 좌표 조정 (최소 40px 간격) |
| `FRAGMENT_ORDER` | WARNING | 다단 레이아웃 + 명시적 `order=N` 없음 | `{.click order=N}` 추가 (td-lr 순서) |
| `MISSING_NOTES` | WARNING | `:::notes` 블록 누락 | 150자+ 스피커 노트 작성 |
| `NOTE_STRUCTURE` | WARNING | 콘텐츠 슬라이드 노트에 `[요약]` 계층 없음 | `:::notes` 상단에 `[요약]` (3~5 불릿) 추가 |
| `TITLE_LENGTH` | WARNING | 슬라이드 제목 28자 초과 | 28자 이하 헤드라인으로 축약 (§3 Slide Title Voice) |
| `STATIC_HTML` | WARNING | `:::html` 요소 3+ 이나 fragment 없음 | `fragment fade-up` + `data-fragment-index` 추가 |

**거절 루프**: 작성 → validate → CRITICAL 있으면 수정 후 재검증(최대 3회) → 없으면 WARNING 검토 → build.

**Verdict**: `❌ REJECT`(CRITICAL≥1, 빌드 금지) · `⚠️ REVIEW`(WARNING≥6) · `⚠️ PASS WITH WARNINGS`(1~5) · `✅ PASS`.

---

## 2. Forbidden — AI-slide tells (피해야 할 AI 슬라이드 티)

각 tell은 강제하는 **lint 규칙 id**(기계 검출) 또는 리뷰 게이트(`content-review-agent`)에 연결됩니다.

| 안티패턴 (AI-slide tell) | 왜 티가 나는가 | 대신 | 강제 (lint rule / gate) |
|--------------------------|----------------|------|--------------------------|
| 하드코딩 hex (생 6자리 색상값) | 테마 토큰 무시, 단일 테마 고착 | `var(--accent)` 등 시맨틱 역할 토큰 | `RAW_HEX` (lint) |
| 인라인 색상/여백 style (`style=`에 color/padding 직접 기입) | 토큰 시스템 우회, 일관성 붕괴 | 토큰 클래스 (`.card-grid`, `.metric-card`) + `:::css` | `INLINE_STYLE` (lint) |
| 생(raw) rgba 색상 함수 | 테마 적응 불가, 하드코딩 그림자/오버레이 | `var(--surface-*)`, `color-mix()` 토큰 | `RAW_RGBA` (lint) |
| 매직넘버 타입/오프스케일 여백 (4·8px 스케일 밖의 px) | 들쭉날쭉한 간격 | 스페이싱 스케일 토큰 (`var(--space-*)`) | `OFF_SCALE` (lint) + 토큰 시스템 |
| 텍스트 벽 불릿 (8+ 줄) | 한 슬라이드 과부하, 읽히지 않음 | 슬라이드 분할 또는 카드/탭 분리 | `CONTENT_OVERFLOW` (lint) |
| 다크 전용 / 제네릭 blue-teal 기본 | "AI 기본 테마" 인상 | **light 기본** 듀얼 테마 + 역할 토큰 | dual-theme (light default) |
| 그라데이션 텍스트 헤딩 · 장식용 gradient orb · 빈 하단 영역 | 의미 없는 장식, 정보 밀도 0 | 콘텐츠/시각 계층으로 영역 채우기, 장식 제거 | 가이드 (리뷰 게이트) |
| 서술형 백과사전 톤 제목 ("2026년 Frontier AI 모델 동향") | 밋밋한 라벨, 엣지 없음 | 단정/주장/질문/반전 헤드라인 (28자 이하) | Slide Title Voice (게이트) + `TITLE_LENGTH` (길이만 lint) |
| 자유형 / 누락 스피커 노트 | 발표 불가, 구조 없음 | `[요약]` 5계층 구조 노트 (150자+) | `NOTE_STRUCTURE` / `MISSING_NOTES` (lint) |

> 규칙 id가 붙은 항목은 `validate`가 기계적으로 잡고(§1), 게이트 항목(장식·제목 보이스)은 `content-review-agent`에서 감점됩니다.

---

## 3. Slide Title Voice (제목 보이스)

슬라이드 제목(`## heading`)은 1초 안에 읽히는 **헤드라인** — 단정/주장/질문/반전으로 엣지를 담고 **28자 이하**.
부제목은 **체언 종결**(명사형 어미 `~화/~등극/~재편/~본격화` …) **45자 이하**.
✅ "비용은 싸졌고, 모델은 똑똑해졌다"  ❌ "2026년 Frontier AI 모델 동향"(밋밋한 라벨).
**레벨 게이트**: `level` 100~200은 헤드라인 권장, 300~400은 서술형 제목(API명·설정 키)도 허용.
28자 초과 시 `validate`의 `TITLE_LENGTH` 경고. 전체 예시: [slide-patterns.md](slide-patterns.md) "Slide Title Voice".

---

## 4. Interactive Design (★ 최우선)

> **핵심: 정보가 많은 슬라이드일수록 interactive하게.** 불릿 10줄 < 탭 3개 × 카드 3개.
> "데이터를 시각 카드로 배치 + 탭/토글로 점진적 공개"가 기본 패턴.

1. **탭 분할**: 동일 주제 3+ 하위 항목 → 탭으로 분리
2. **카드 그리드**: 4+ 나열 항목 → `.card-grid` 토큰 클래스 (불릿 리스트 금지)
3. **자체 완결**: 모든 인터랙션은 `:::html` 안 inline onclick으로 완결 (외부 JS 비의존)
4. **시각 계층**: 색상은 시맨틱 역할 토큰(`var(--accent/--info/--success/--warning/--danger)`)으로만. 하드코딩 hex/rgba·단색 배경 금지
5. **`:::html` reactive**: 3+ 동위 요소는 `class="fragment fade-up" data-fragment-index="N"`로 순차 등장 (정적 HTML 금지)

> **테마**: light 기본. dark는 덱 루트 `class="… theme-dark"`. 슬라이드별 다크는 `@theme: dark`. 모든 색은 theme.css 토큰으로 양쪽 자동 적응.

### 자체 완결 Tab 패턴 (복사-붙여넣기)

slide-framework.js 없이 동작. 색상은 theme.css `.tab-set`/`.tab-btn.active`/`.metric-card`/`.callout`가 담당(inline 스타일 금지). 데이터가 3+ 카테고리일 때:

```markdown
:::html
<div class="tab-set" onclick="(function(e){var b=e.target.closest('.tab-btn');if(!b)return;var bar=b.parentNode,p=bar.parentNode,i=[].indexOf.call(bar.children,b);bar.querySelectorAll('.tab-btn').forEach(function(x){x.classList.remove('active')});b.classList.add('active');p.querySelectorAll('.tc').forEach(function(c,j){c.hidden=j!==i})})(event)">
  <button class="tab-btn active">Tab 1</button>
  <button class="tab-btn">Tab 2</button>
  <button class="tab-btn">Tab 3</button>
</div>
<div class="tc">
  <div class="card-grid">
    <div class="metric-card"><strong class="text-accent">Card Title</strong><div class="on-surface-muted">Description</div></div>
    <div class="metric-card"><strong class="text-success">Next Step</strong><div class="on-surface-muted">Description</div></div>
  </div>
</div>
<div class="tc" hidden>
  <div class="card-grid">
    <div class="callout callout-info"><strong class="text-info">item-1</strong> — Description</div>
    <div class="callout callout-warning"><strong class="text-warning">item-2</strong> — Description</div>
  </div>
</div>
<div class="tc" hidden>
  <div class="card-grid">
    <div class="callout callout-success"><strong class="text-success">Type A</strong><div class="on-surface-muted">Details here</div></div>
    <div class="callout callout-info"><strong class="text-accent">Type B</strong><div class="on-surface-muted">Details here</div></div>
  </div>
</div>
:::

:::css
.text-accent  { color: var(--accent);  font-weight: var(--weight-bold); }
.text-info    { color: var(--info);    font-weight: var(--weight-bold); }
.text-success { color: var(--success); font-weight: var(--weight-bold); }
.text-warning { color: var(--warning); font-weight: var(--weight-bold); }
.text-danger  { color: var(--danger);  font-weight: var(--weight-bold); }
.on-surface-muted { color: var(--on-surface-muted); font-size: var(--text-sm); }
:::
```

**시맨틱 색상 역할** (하드코딩 hex 대신):

| 역할 | 토큰 | subtle 배경 | 클래스 헬퍼 | 용도 |
|------|------|------------|-------------|------|
| accent | `var(--accent)` | `var(--accent-subtle)` | `.text-accent` | 기본/입력/소스 |
| success | `var(--success)` | `var(--success-subtle)` | `.callout-success` | 성공/결과/자동화 |
| warning | `var(--warning)` | `var(--warning-subtle)` | `.callout-warning` | 경고/처리/AI |
| info | `var(--info)` | `var(--info-subtle)` | `.callout-info` | 보조/스트리밍/분석 |
| danger | `var(--danger)` | `var(--danger-subtle)` | `.callout-danger` | 에러/위험/알림 |

서피스/텍스트는 `var(--surface-1/2/3)`, `var(--on-surface)`, `var(--on-surface-muted)`. 전체: [colors-reference.md](colors-reference.md).

### 불릿 리스트 → 카드 변환

**Before(비효과적)**: `- CloudWatch Agent: 메트릭 수집` … 불릿 나열
**After(효과적)** — `.card-grid` + `.metric-card` (색상은 theme.css):
```html
<div class="card-grid">
  <div class="metric-card"><strong class="text-accent">CloudWatch Agent</strong><div class="on-surface-muted">메트릭 수집</div></div>
  <!-- ... 반복 ... -->
</div>
```

복잡한 인터랙션(슬라이더·시뮬레이터·대시보드)은 `:::html` + `:::script` + `:::css`. 템플릿/예시: [interactive-patterns-guide.md](interactive-patterns-guide.md).

---

## 5. Slide Type Decision Guide

> ⛔ 모든 슬라이드에 명시적 `@type`을 작성. auto-detect 의존 금지. 특히 `agenda`/`tabs`/`steps`는 필수.

| Content Type | Slide Pattern | Interactive Element |
|---|---|---|
| Architecture overview (static) | Diagram Image | draw.io → PNG/SVG, `@img:` |
| Step-by-step flow (박스 ≤4) | Canvas Animation | `:::canvas` DSL, step ↑↓ |
| Multi-layer architecture (박스 5+) | HTML Architecture | `:::html` + `:::css` flexbox/grid (§6) |
| A vs B comparison | Compare Toggle | `.compare-toggle` buttons |
| Config variants | Tab Content | `.tab-bar` + YAML code |
| Step-by-step process | Timeline | `.timeline` animated steps |
| Monitoring/dashboard (박스 5+) | `:::html` + `:::script` | Stat panels + node grid |
| Parameter exploration / 계산기 | Slider | `input[type=range]` + live output |
| Best practices | Checklist | `.checklist` click-to-toggle |
| YAML/code example | Code Block | `.code-block` syntax spans |
| Customer problem | Pain Quote | `.pain-quote` + challenge list |
| Session agenda/목차 | Agenda | `@type: agenda` numbered dots + time |
| Block summary | Quiz(퀴즈 시) / Content(Key Takeaways) | `data-quiz` 3-4문항 / 요약 리스트 |
| Block closing | Thank You | Gradient heading + TOC link |
| 시뮬레이터/대시보드/테스터/빌더 (VPA·Grafana·Regex·YAML·Mode·비용) | `:::html` + `:::script` | sliders/inputs → live output |

### Canvas DSL vs `:::html` (중요)

> 복잡한 다이어그램/인터랙션은 `:::html` + `:::css`(+`:::script`)를 우선. Canvas DSL은 단순 박스+화살표만.

| 복잡도 | 방식 | 예시 |
|--------|------|------|
| **단순** (박스 ≤4 + 화살표) | `:::canvas` DSL 허용 | A→B→C |
| **중간** (박스 5+, 다계층) | `:::html` + `:::css` 필수 (canvas 금지) | 3-tier, 서비스 맵, 에코시스템 |
| **복잡** (인터랙션 + 계산) | `:::html` + `:::script` 필수 | 슬라이더, 계산기, 대시보드 |
| **정적 아키텍처** | `@img:` + draw.io | AWS 전체 아키텍처, VPC |

### Canvas vs Diagram

| 기준 | Canvas (`@type: canvas`) | Diagram (`@img:`) |
|------|--------------------------|---------------------|
| 목적 | 단계별 흐름 애니메이션 | 전체 아키텍처 한눈에 |
| 장점 | ↑↓ step 순차 설명 | 복잡 레이아웃/화살표 정확 |
| 제작 | Canvas DSL 직접 코딩 | draw.io/architecture-diagram → PNG/SVG |

**원칙**: 애니메이션이 설명력을 높이지 않으면 diagram 이미지. 복잡한 다이어그램은 `:::html`+`:::css` 우선.

> `:::canvas`를 쓰기 전 반드시 [canvas-authoring-guide.md](canvas-authoring-guide.md)를 읽으세요 — DSL 문법, 필수 좌표 공식, fragment 순서.

---

## 6. HTML Architecture 패턴 (박스 5+ 필수)

```markdown
## Service Pipeline

:::html
<div class="flow-h">
  <div class="flow-group bg-blue" data-fragment-index="1">
    <div class="flow-group-label">수집</div>
    <div class="icon-item"><img src="common/aws-icons/services/Arch_Amazon-CloudWatch_48.svg"><span>CloudWatch</span></div>
    <div class="icon-item"><img src="common/aws-icons/services/Arch_AWS-X-Ray_48.svg"><span>X-Ray</span></div>
  </div>
  <div class="flow-arrow">→</div>
  <div class="flow-group bg-orange" data-fragment-index="2">
    <div class="flow-group-label">분석</div>
    <div class="flow-box">DevOps Guru</div>
    <div class="flow-box">Bedrock</div>
  </div>
  <div class="flow-arrow">→</div>
  <div class="flow-group bg-pink" data-fragment-index="3">
    <div class="flow-group-label">대응</div>
    <div class="flow-box">EventBridge</div>
    <div class="flow-box">Lambda</div>
  </div>
</div>
:::
```

- `flow-h`/`flow-group`/`flow-box`/`flow-arrow`: theme.css 유틸리티 (커스텀 CSS 불필요, stage 높이·너비 자동 균일)
- `bg-blue`/`bg-orange`/`bg-pink`: 색상 유틸리티 · `data-fragment-index="N"`: 그룹별 순차 등장
- AWS 아이콘: `common/aws-icons/services/Arch_{Name}_48.svg`

> Canvas vs HTML의 임계값 canon은 §5의 복잡도 표 — validate의 `CANVAS_COMPLEXITY`가 같은 기준으로 backstop.
