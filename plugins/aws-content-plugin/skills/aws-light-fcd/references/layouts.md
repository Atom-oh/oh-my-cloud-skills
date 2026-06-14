# Layout Guide

All builders take `(pres, opts)`. `pres = kit.newDeck()`. Every builder adds its own
footer; pass `pageNum` (omit/null on cover). Read `scripts/demo_build.js` for a full
runnable example of all five.

Canvas: 13.333 × 7.5 in (16:9). Left margin `PAD = 0.92`. Title baseline `y = 0.55`.

---

## 1. Cover — `kit.cover(pres, opts)`

White canvas with a soft purple/blue glow in the upper-right; big product title,
Korean sub-headline, date, presenter block; large AWS logo bottom-right.

```js
kit.cover(pres, {
  product: "Amazon Bedrock",                    // 54pt bold, near-black
  subtitle: "한 줄 또는 두 줄.\n줄바꿈은 \\n",     // 22pt body; keep to ≤2 lines
  date: "June 11, 2026",                        // italic muted
  presenter: { name: "오준석", title: "Senior Solutions Architect", org: "AWS Korea" },
});
```

Keep the subtitle short — one punchy line reads best. No page number on the cover.

---

## 2. Agenda — `kit.agenda(pres, opts)`

Table of contents. 2-column grid, up to 6 items. Each row: tinted icon tile +
small blue number + bold title + muted one-line description. Hairlines separate rows.

```js
const icons = await Promise.all(
  [FiZap, FiSearch, FiGitBranch, FiShield].map(ic => arch.renderIcon(ic, "#" + kit.C.blue))
);
kit.agenda(pres, {
  pageNum: 2,
  title: "Agenda",                              // or "오늘의 논의"
  items: [
    { num: "01", title: "...", desc: "...", iconData: icons[0] },
    { num: "02", title: "...", desc: "...", iconData: icons[1] },
    // up to 6
  ],
});
```

**Rule:** content chapters only. Do **not** add "다음 단계 / PoC / 워크샵 / 감사합니다".
Layout auto-adjusts spacing: ≤4 items → roomy 2×2; 5–6 → tighter 2×3.

---

## 3. Big Stat — `kit.bigStat(pres, opts)`

2–4 large headline numbers (solid blue, NOT gradient) with 3-line supporting copy and
a source. Best with the subtle glow background for emphasis.

```js
kit.bigStat(pres, {
  pageNum: 3, title: "AI 에이전트, 이미 현실이 되었습니다", bg: "glow",
  stats: [
    { num: "80%",
      lines: [{ t: "의 고객 서비스 이슈를" },
              { t: "에이전틱 AI가 자율적으로 해결", blue: true },  // blue:true = emphasized blue bold line
              { t: "2029년까지 운영비용 30% 절감" }],
      source: "Gartner, CXToday 2026" },
    { num: "51%", lines: [...], source: "..." },
  ],
});
```

2 stats → 96pt numbers, wide columns. 3–4 stats → 72pt, narrower. Numbers are solid
`C.gradBlue` (#41B3FF) — the reference deck's big numbers read as solid blue, and text
gradients don't preview reliably, so we keep them solid.

---

## 4. AgentCore 3-card — `kit.agentcoreCards(pres, opts)`

Signature layout: centered AgentCore icon + title, optional subtitle, then 3 cards.
Each card = soft fill + shadow, a **gradient pill header** (purple→blue→green), a
centered AgentCore icon, and a centered description.

```js
kit.agentcoreCards(pres, {
  pageNum: 4,
  headerIcon: "agentcore",                       // header icon (agentcore icon name)
  headerTitle: "Amazon Bedrock AgentCore",       // centered as a group with the icon
  subtitle: "어떤 프레임워크와 모델로도 ...",       // centered, muted
  cards: [
    { title: "가치 실현 시간 단축", icon: "runtime",      desc: "두 줄\n권장" },
    { title: "유연성",            icon: "ai_agent",     desc: "..." },
    { title: "신뢰성",            icon: "policy_engine", desc: "..." },
  ],
});
```

Card `icon` = an AgentCore icon name (`references/icons.md`). Pill header text is white.
Supports 2 or 3 cards (auto-centers). The gradient comes from
`assets/backgrounds/grad_pill.png`, never from text.

---

## 5. AWS Architecture Diagram — `arch_kit.js`

Built from primitives, not a single builder, so you control the topology. Pattern:
group boxes (dashed) → service icons inside → numbered step markers at connection
points → arrows between stages → a right-side numbered step legend.

```js
const s = arch.archSlide(kit, pres, { pageNum: 19, title: "자동 확장 추론 아키텍처" });

arch.groupBox(kit, pres, s, x, y, w, h, "스토리지");        // dashed container + label
arch.svc(kit, pres, s, cx, y, "ecr", "Amazon ECR");        // icon centered on cx + caption
arch.stepMarker(kit, pres, s, x, y, 1);                    // magenta numbered circle
arch.arrow(kit, pres, s, x, y, w);                         // horizontal arrow, w = length
arch.stepLegend(kit, pres, s, ["1단계 설명", "2단계 ...", ...]); // far-right numbered list

kit.addFooter(pres, s, 19);                                // add footer manually for arch slides
```

Guidelines:
- Lay out left→right as a flow: sources (registry/storage) → compute (GPU) →
  serving → endpoints. Group related services in dashed `groupBox`es with a top label.
- Use `stepMarker` numbers that correspond 1:1 with `stepLegend` entries on the right.
- Endpoints (users / agents / programs): small labeled chips, **never emoji**.
- Keep service captions inside their group box; give the box enough height
  (≈1.05" per stacked icon+caption).
- For "progressive build" slides (reveal one stage at a time), render the full diagram
  then fade non-active elements by using `C.hairline`/tints instead of full colors —
  duplicate the slide and recolor per step.

See `scripts/demo_build.js` (slide 5) for the complete inference-architecture example.

---

## 6. Title + Visual — `kit.titleWithVisual(pres, opts)`

Big emphasis title on the left (accent color), a freeform visual region on the right.
EKS slide-21 style — ideal for a single hero diagram (responsibility split, layered
architecture, before/after) paired with a short punchy title. You draw the right side
via a `draw(pres, s, region)` callback; `region = {x,y,w,h}` is the right column
(roughly x 6.55, w 5.85), already offset below the optional caption.

```js
kit.titleWithVisual(pres, {
  pageNum: 21,
  title: "GPU 지원 EKS\n클러스터 생성 옵션 1",   // left, accent color (default blueBright)
  titleColor: kit.C.blueBright,                 // optional
  caption: "자체 관리형 애드온을 사용하는 EKS",   // optional bold caption above the visual
  draw: (pres, s, r) => {
    // r = { x, y, w, h } — draw your diagram here with shapes/icons
    s.addShape(pres.shapes.RECTANGLE, { x: r.x, y: r.y, w: r.w, h: 3.5,
      fill: { type: "none" }, line: { color: "ED8B00", width: 1.5 } });
    s.addImage({ path: kit.awsIcon("gpu"), x: r.x + 1, y: r.y + 0.8, w: 0.85, h: 0.85 });
    // ... nested boxes, cells, labels ...
  },
});
```

The full responsibility-split diagram (orange "고객 책임" box with GPU chips + dashed
add-on cells + blue "AWS 책임" box) is implemented in `demo_build.js` (slide 6) — copy
that `draw` callback as a starting point for layered/responsibility diagrams.

Use `arch_kit.js` primitives inside the `draw` callback too if the right-side visual is
a flow diagram rather than nested boxes.

---

## 7. Pipeline — `kit.pipeline(pres, opts)`

Numbered circles + soft cards + arrows, left→right. For sequential workflows / "N steps".

```js
kit.pipeline(pres, {
  pageNum: 14, title: "Bedrock 시작, 세 단계",
  steps: [
    { n: 1, title: "모델 액세스 요청", desc: "콘솔에서 모델 액세스 요청" },
    { n: 2, title: "플레이그라운드 평가", desc: "Chat/Test에서 테스트" },
    { n: 3, title: "API로 연결", desc: "엔드포인트 구성 후 연결" },
  ],
});
```

2–4 steps; card width/gap auto-adjust. Number circle is `blueBright`, arrows are muted.

---

## 8. Why / What — `kit.whyWhat(pres, opts)`

Top WHY panel (3 points, purple tint) + down arrow + bottom WHAT cards, each with a
"차별점" (differentiator) box. EKS slide-31 style. Strong for compare/contrast.

```js
kit.whyWhat(pres, {
  pageNum: 31, title: "신규 콘솔, 왜 나왔고 무엇이 다른가", subtitle: "...",
  why: [
    { dot: kit.C.magenta, t: "모델 생태계 확장", d: "멀티 프로바이더 시대" },
    { dot: kit.C.purple,  t: "표준 API 호환",   d: "최소 변경으로 운영" },
    { dot: kit.C.blue,    t: "운영·거버넌스",   d: "통합 관리" },
  ],
  what: [
    { n: "01", t: "표준 호환 API", d: "설명 2줄", diff: "차별점 한 줄(짧게)", dc: kit.C.magenta },
    { n: "02", t: "...",          d: "...",     diff: "...",            dc: kit.C.purple },
    { n: "03", t: "...",          d: "...",     diff: "...",            dc: kit.C.blue },
  ],
});
```

Keep `diff` to one concise clause — it renders at 11.5pt and wraps to 2 lines if long.
`dc` is the per-card accent (magenta/purple/blue makes a nice left-to-right sequence).

---

## 9. Chart with Callout — `kit.chartWithCallout(pres, opts)`

Native **editable** chart (bar or line) on the left + a callout card (big number +
copy) on the right. The chart is real PowerPoint chart data — users can edit values.

```js
kit.chartWithCallout(pres, {
  pageNum: 23, title: "추론 비용, 1년 만에 급감", subtitle: "월간 추론 비용 추이 (상대값)",
  chartType: "bar",                       // "bar" | "line"
  chartColors: [kit.C.gradBlue], maxVal: 110,
  series: [{ name: "추론 비용", labels: ["Q1","Q2","Q3","Q4","Q5"], values: [100,78,55,38,24] }],
  callout: { big: "76%", lines: [{ t: "5분기 만에 " }, { t: "76% 절감", blue: true }, { t: ". 같은 예산으로 더 많은 추론." }] },
});
```

Multi-series: pass more objects in `series` and set `showLegend: true`. Numbers/labels
are solid colored (no gradient on text — rule 3). Callout is optional.

---

## 10. Chip Grid — `kit.chipGrid(pres, opts)`

Rows of outlined, vendor-colored chips (EKS slide-23 style). For portfolio/matrix
content — instance families, model lineups, SKU grids. Optional vendor group boxes on top.

```js
kit.chipGrid(pres, {
  pageNum: 23, title: "광범위하고 심층적인 가속 컴퓨팅 포트폴리오",
  leftLabel: "GPU 및 AWS ML 가속기",
  vendorBoxes: [
    { name: "NVIDIA", color: "76B900", items: "H200, H100, A100, L4, ..." },
    { name: "AWS",    color: kit.C.blueBright, items: "Trainium · Inferentia" },
  ],
  rows: [
    { label: "훈련", groups: [
      { color: "76B900", chips: ["P4d","P5","P6"] },
      { color: "ED8B00", chips: ["Trn1","Trn2"] }] },
    { label: "추론", panel: true, groups: [
      { color: "76B900", chips: ["G4","G5","G6"] },
      { color: "ED8B00", gapBefore: 1.6, chips: ["Inf1","Inf2"] }] },
  ],
});
```

`panel: true` draws a gray background band behind that row. `gapBefore` adds horizontal
space before a chip group (to separate vendors). Chip outline color = vendor color
(NVIDIA green `76B900`, AWS orange `ED8B00`).

---

## 11. Section Divider — `kit.sectionDivider(pres, opts)`

Full-bleed signature-gradient background (purple→blue→green) + chapter number + big
white title + optional kicker. Use to mark chapter transitions in longer decks. Footer
auto-switches to the white variant so it stays legible on the gradient.

```js
kit.sectionDivider(pres, {
  pageNum: 5, num: "01", title: "무엇이 새로워졌나",
  kicker: "두 모델의 정식 출시와 오픈 웨이트의 의미",   // optional one-line
});
```

`num` and `kicker` are optional. Title renders white at 50pt. The gradient asset is
`assets/backgrounds/section_grad.png`.

---

## 12. Closing — `kit.closing(pres, opts)`

Same gradient background, a single large "Thank you." Always the last slide. English by
convention (matches AWS deck style), but `text` is overridable.

```js
kit.closing(pres, { pageNum: 32 });            // "Thank you."
kit.closing(pres, { pageNum: 32, text: "감사합니다." }); // override if you prefer Korean
```

---

## Adding your own layout

Keep new builders in `deck_kit.js` (or a new module), follow the same `(pres, opts)`
signature, always call `addFooter(pres, s, pageNum)` last, and use only tokens from
`C`. Anchor titles at `(PAD, 0.55)`. Don't introduce a second accent family or put
gradients on text.
