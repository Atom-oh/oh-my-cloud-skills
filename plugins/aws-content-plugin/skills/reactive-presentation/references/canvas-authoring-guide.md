# Canvas Authoring Guide

> **MANDATORY**: read this before writing any `:::canvas` block. The grammar is
> strict (variants silently fail to parse) and the coordinate formula is required —
> LLM spatial reasoning is weak, so place boxes by formula, not by "imagination".
> The `validate` command (rejection loop) backstops overlaps (`CANVAS_OVERLAP`).

## Canvas DSL 문법 (필수 준수)

> **주의**: 아래 정확한 문법만 파서가 인식합니다. bracket syntax `[x=..., y=...]`이나 다른 변형은 동작하지 않습니다.

```
box <id> "<label>" at <x>,<y> size <w>,<h> color <#hex> [step <n>]
icon <id> "<service-name>" at <x>,<y> size <s> [step <n>]
arrow <from-id> -> <to-id> "<label>" [color <#hex>] [step <n>]
group "<label>" containing <id1>, <id2> [color <#hex>] [step <n>]
```

예시:
```markdown
:::canvas
box api "API Gateway" at 100,180 size 130,55 color #FF9900 step 1
box lambda "Lambda" at 320,180 size 130,55 color #FF9900 step 2
box db "DynamoDB" at 540,180 size 130,55 color #3B48CC step 3
arrow api -> lambda "invoke" step 2
arrow lambda -> db "query" step 3
:::
```

## Canvas 좌표 계산 공식 (필수 — LLM 공간 추론 보정)

> **원칙**: 좌표를 "상상"으로 배치하지 마세요. 아래 공식으로 계산하세요.
> LLM은 공간 추론이 취약하므로 수학적 공식 기반 배치가 필수입니다.

**캔버스 좌표계**: 960 × 400 (BASE_W × BASE_H), 안전 영역 40px 마진

**수평 N-박스 직선 흐름** (A → B → C → ...):
```
gap = (880 - N * box_width) / (N - 1)     # 880 = 960 - 40*2 마진
x[i] = 40 + i * (box_width + gap)         # i = 0, 1, 2, ...
y = 180                                    # 수직 중앙
```

**2행 레이아웃** (위: 소스, 아래: 타겟):
```
row1_y = 100                               # 상단 행
row2_y = 280                               # 하단 행
x[i] = 40 + i * (880 / cols_in_row)       # 각 행 내 균등 분배
```

**박스 크기 규칙**:
```
width ≥ max(label_length × 9, 100)        # 영문 기준, 한글은 × 14
height = 55                                # 기본값
min_gap = 40                               # 박스 간 최소 간격 (edge-to-edge)
```

**아이콘 간격 규칙**:
```
min_gap = 60                               # 아이콘 center-to-center
icon_size = 48                             # 기본 아이콘 크기
x[i] = 40 + i * max(icon_size + min_gap, 880 / N)
```

**자가 검증 (작성 후 반드시 확인)**:
1. 모든 x값이 40~880 범위 내인가?
2. 모든 y값이 30~350 범위 내인가?
3. 인접 박스 간 edge-to-edge 거리 ≥ 40px인가?
4. `validate` 명령으로 CANVAS_OVERLAP 없는지 확인했는가?

## Fragment 순서 규칙 (td-lr: Top-Down Left-Right)

> **원칙**: 독자의 시선 흐름을 따릅니다 — **위에서 아래, 왼쪽에서 오른쪽**.

**단일 컬럼**: DOM 순서대로 auto-increment (기본 동작)
```markdown
- Item A {.click}          ← order=1 (자동)
- Item B {.click}          ← order=2 (자동)
- Item C {.click}          ← order=3 (자동)
```

**다단 컬럼 (:::left/:::right)** — **반드시 명시적 order 사용**:
```markdown
::: left
- Left Top {.click order=1}
- Left Bottom {.click order=3}
:::

::: right
- Right Top {.click order=2}
- Right Bottom {.click order=4}
:::
```
시각적 순서: 1(좌상) → 2(우상) → 3(좌하) → 4(우하)

**:::html 블록 내 다단**: `data-fragment-index` 직접 지정:
```html
<div class="col-2">
  <div class="fragment fade-up" data-fragment-index="1">좌상</div>
  <div class="fragment fade-up" data-fragment-index="2">우상</div>
  <div class="fragment fade-up" data-fragment-index="3">좌하</div>
  <div class="fragment fade-up" data-fragment-index="4">우하</div>
</div>
```

## 콘텐츠 작성 규칙

1. **슬라이드 주석**: 각 슬라이드 구분선(`---`) 아래에 `<!-- Slide N: 제목 (슬라이드 타입) -->` 주석 필수
2. **Raw HTML**: 마크다운 본문에 `<div>`, `<table>` 등 블록 HTML을 직접 삽입하면 `<p>` 태그로 감싸여 깨짐 → 반드시 `:::html` 블록 사용
3. **AWS 아이콘 경로**: `../common/aws-icons/services/Arch_{ServiceName}_48.svg` 형식 사용 (전체 디렉토리 경로 `Architecture-Service-Icons_07312025/...` 금지)
