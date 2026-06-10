# Semantic Color Token Reference

Reactive-presentation 색상은 **하드코딩 hex가 아니라 시맨틱 역할 토큰**으로 표현합니다. 토큰은
`assets/design-tokens.css`에 정의되고, `assets/theme.css`의 `.theme-light`(기본) / `.theme-dark`
스코프에서 실제 값으로 바인딩됩니다. 슬라이드/템플릿은 항상 `var(--*)` 토큰을 사용하므로
light/dark 테마 전환과 PPTX 브랜드 추출(Phase 1)에 자동으로 적응합니다.

> **테마 기본값**: light가 기본입니다. dark로 되돌리려면 덱 루트 요소에 `class="… theme-dark"`를
> 지정하세요. 토큰을 쓰면 같은 마크업이 양쪽 테마에서 올바른 대비로 렌더링됩니다.

---

## Role Tokens (사용 우선순위 1순위)

### Surfaces & Text

| 토큰 | 역할 | 사용 |
|------|------|------|
| `--surface-1` | 가장 낮은 표면 (덱/슬라이드 배경) | `background: var(--surface-1)` |
| `--surface-2` | 카드/패널 표면 | `background: var(--surface-2)` |
| `--surface-3` | 표면 위 경계/구분선/그리드 라인 | `border-color: var(--surface-3)` |
| `--on-surface` | 표면 위 본문 텍스트 | `color: var(--on-surface)` |
| `--on-surface-muted` | 보조/캡션 텍스트, 차트 축 라벨 | `color: var(--on-surface-muted)` |

### Accent & Status

각 역할은 3종 토큰을 가집니다: **base**(채움/선), **`-subtle`**(연한 배경 틴트), **`-on`**(base 위 텍스트).

| 역할 | base | subtle 배경 | on (텍스트) | 의미 |
|------|------|-------------|-------------|------|
| accent | `--accent` | `--accent-subtle` | `--accent-on` | 기본 강조, 입력/소스, 1차 CTA |
| info | `--info` | `--info-subtle` | `--info-on` | 보조 정보, 스트리밍/분석 |
| success | `--success` | `--success-subtle` | `--success-on` | 성공, 결과, 자동화 |
| warning | `--warning` | `--warning-subtle` | `--warning-on` | 경고, 처리 중, AI/추론 |
| danger | `--danger` | `--danger-subtle` | `--danger-on` | 에러, 위험, 알림 |

**사용 패턴**:

```css
/* 카드: 표면 + 본문 텍스트 */
.metric-card { background: var(--surface-2); color: var(--on-surface); border: 1px solid var(--surface-3); }

/* 상태 배지: base 채움 + on 텍스트 (대비 보장) */
.badge-warn  { background: var(--warning); color: var(--warning-on); }

/* 연한 강조 영역: subtle 틴트 + base 보더 + role 텍스트 */
.callout-info { background: var(--info-subtle); border: 1px solid var(--info); color: var(--on-surface); }

/* 강조 텍스트 */
.text-accent { color: var(--accent); }
```

> 옛 레거시 별칭(`--blue`, `--cyan`, `--green`, `--yellow`, `--red`, `--text-muted`)은
> 하위호환을 위해 theme.css에 남아 있을 수 있으나, **새 콘텐츠는 위 역할 토큰을 사용하세요.**
> 매핑: blue/cyan→`--info`·`--accent`, green→`--success`, yellow/orange→`--warning`,
> red→`--danger`, text-muted→`--on-surface-muted`.

---

## Scale Tokens (간격·반경·타이포·그림자)

색상 외 디자인 값도 토큰을 사용합니다. 하드코딩 px/rem 대신:

| 그룹 | 토큰 | 용도 |
|------|------|------|
| Spacing (8px 그리드) | `--space-1`…`--space-8` | `padding`, `gap`, `margin` |
| Radius | `--radius-sm` / `--radius-md` / `--radius-lg` / `--radius-pill` | `border-radius` |
| Type scale | `--text-xs`…`--text-4xl` | `font-size` |
| Type role | `--leading-tight/normal/relaxed`, `--weight-regular/medium/semibold/bold` | line-height, weight |
| Shadow | `--shadow-1/2/3`, `--shadow-glow` | `box-shadow` |
| Motion | `--duration-fast/normal/slow` | transition/animation |
| Z ladder | `--z-base/nav/overlay/modal/toast` | `z-index` |

---

## Token-backed Primitive Classes

대부분의 슬라이드는 직접 `var(--*)`를 쓰기보다 theme.css의 **프리미티브 클래스**를 조합합니다
(클래스가 토큰을 소비하므로 테마 적응이 자동):

| 클래스 | 역할 |
|--------|------|
| `.card-grid` | auto-fit 반응형 카드 그리드 |
| `.metric-card` | 표면 카드 (KPI/지표) |
| `.callout` + `.callout-info/-warning/-danger/-success` | 상태별 강조 박스 |
| `.comparison` | 비교 표면 박스 |
| `.tab-set` / `.tab-btn`(+`.active`) | 탭 바 (active는 accent로 채움) |
| `.flow-group` / `.flow-h` / `.flow-box` / `.flow-arrow` | 아키텍처 흐름 레이아웃 |

---

## Canvas & JSON 색상 (named tokens)

런타임 렌더링 경로는 hex 대신 **이름 토큰**을 받습니다.

- **Canvas DSL** (`:::canvas`): `box id "label" at X,Y size W,H color <name>` — `<name>`은
  `accent`, `green`, `yellow`, `red`, `blue`, `cyan` (animation-utils.js `Colors.*`로 해석, 테마/PPTX 적응).
- **slides.json**: `"color"` / `"colors"` 필드에 같은 이름 토큰(`accent`, `cyan`, `yellow`, `red`, `muted` 등)을 사용.
- **Chart.js**: `getComputedStyle(document.documentElement).getPropertyValue('--accent')`로 토큰을 읽어 사용 (slide-patterns.md §16 참조).

---

## PPTX 브랜드 추출 → 토큰 (Phase 1)

`.pptx` 템플릿을 제공하면 `extract_pptx_theme.py`가 브랜드 색을 추출해 `theme-override.css`에서
역할 토큰을 재바인딩합니다. 즉 **추출된 브랜드 색이 `--accent`, `--surface-*` 등으로 흘러들어가**
모든 토큰 기반 슬라이드에 일괄 반영됩니다. 슬라이드 마크업은 바뀌지 않습니다 — 토큰 값만 바뀝니다.

PPTX MCP 도구(`mcp__ppt__*`)는 토큰을 직접 받지 않고 `[r, g, b]` 배열을 받으므로, 추출된 매니페스트
(`theme-manifest.json`)의 RGB 값을 그대로 전달합니다. 이때도 의미는 동일한 역할(accent/surface/on-surface)에
매핑하여 사용하세요. 예:

```yaml
# 표면 배경 = surface 역할, 텍스트 = on-surface 역할 (값은 매니페스트에서)
mcp__ppt__add_table:
  header_bg_color: <theme-manifest surface RGB>
  header_font_color: <theme-manifest on-surface RGB>
mcp__ppt__add_shape:
  fill_color: <theme-manifest accent RGB>   # accent 역할
```

---

## Accessibility

1. **대비율**: 본문 텍스트는 표면 대비 최소 4.5:1. `--on-surface` / `--on-surface-muted`와
   `--surface-*` 조합, 그리고 status base와 짝지어진 `-on` 토큰은 이 대비를 만족하도록 정의되어 있습니다.
2. **색맹 고려**: 색만으로 의미를 전달하지 말고 아이콘/라벨을 병행 (특히 success/danger).
3. **일관성**: 같은 의미에는 같은 역할 토큰을 사용 (예: "성공"은 항상 `--success`).
