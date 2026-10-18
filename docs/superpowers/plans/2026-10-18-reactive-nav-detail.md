# Reactive-presentation navigation, detail layer, preview fidelity and AI-tone gates: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a hover agenda, ⌘K search and a hover/click detail layer to reactive-presentation decks, make presenter-view previews match the deck, and add copy/AI-tone gates.

**Architecture:** A new self-contained runtime asset pair (`deck-overlay.js` / `deck-overlay.css`) owns agenda, search and detail UI, attached outside `.slide` elements and initialised by `SlideFramework`. The Remarp compiler emits a small DOM contract (block markers on slides, `.rp-detail` terms, a hidden per-slide detail store) that the runtime and `export_pptx.py` consume. Presenter previews render on the deck's real canvas. New lint rules live in `validate_presentation` / `measure_deck.py`.

**Tech Stack:** Vanilla JS/CSS (no new dependency), Python 3 (compiler, measure/export scripts), Playwright for Python (browser tests, skipped when unavailable), TAP shell runner.

**Spec:** `docs/superpowers/specs/2026-10-18-reactive-nav-detail-design.md`

## Global Constraints

- Root for all skill paths below: `plugins/aws-content-plugin/skills/reactive-presentation` (abbreviated `RP/` in prose; file lists use full paths).
- Vanilla JS/CSS only; no CDN, no new runtime dependency.
- Theme tokens only (`var(--surface-*)`, `var(--accent)`, `var(--text-*)`, `var(--space-*)`, `var(--radius-*)`); no raw hex/rgba in new CSS; works under `.theme-light` and `.theme-dark`.
- New UI is attached to `document.body`, never inside `.slide`; it carries class `rp-overlay-ui` so thumbnails, presenter clones, `measure_deck.py` and `export_pptx.py` can hide it.
- No decorative chrome in new UI: no gradients, glow, or left/top colour bars.
- No em dash (U+2014) or middle dot (U+00B7, U+30FB) in any authored copy, docs or UI strings added by this plan.
- Deck window is the only surface for agenda/search/detail; presenter window gets none of them. Jumps use `SlideFramework.goTo(index)`.
- Search excludes speaker notes and excludes framework clones (`.slide-sidebar`, `.slide-scaler`, overview copies).
- `EM_DASH` and `AI_TONE` are `WARNING` severity (build still passes on 0 CRITICAL, `remarp_to_slides.py:1838`). `DETAIL_REF` is `CRITICAL`.
- Never hand-edit `packages/*`; regenerate with `python3 scripts/sync-codex-plugins.py` (host step after Task 6).
- Internal docs in English; public `doc-sites/` pages updated in EN and KO with matching anchors.

## Review Focus

1. Search hotkey while a quiz input or the search box itself has focus: typing `/` or `k` must not reopen/close the modal or advance slides. Pinned by `test_search_ignores_typing_in_inputs` (Task 3).
2. Arrow/space while the detail sidebar is open must still navigate, and the sidebar must close on slide change. Pinned by `test_sidebar_closes_on_slide_change` (Task 3).
3. A `{tip="..."}` value containing quotes, `<`, `&` or Korean must render escaped and not break HTML. Pinned by `test_tip_attribute_is_escaped` (Task 2).
4. Single-block HTML (no merged index, no block titles) must still show an agenda of that block's slides. Pinned by `test_agenda_single_block_lists_slides` (Task 3).
5. `EM_DASH` must not fire on code spans, fenced code, URLs or `&mdash;` inside `<code>`. Pinned by `test_em_dash_skips_code_and_urls` (Task 4).

---

### Task 1: Presenter preview fidelity

**Files:**
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/assets/presenter-view.js`
- Create: `tests/structure/reactive_presenter_test.py`
- Create: `tests/structure/test-reactive-presenter.sh`

**Interfaces:**
- Consumes: existing `SlideFramework` (`window.deck` is not guaranteed; tests reach the framework via the presenter opener).
- Produces: `PresenterView._canvasSize(): {w: number, h: number}` read from the live `.slide-deck` (`offsetWidth`/`offsetHeight`, i.e. 1920×1080 for 16:9). `_applyScale(scaler, containerW, containerH)` keeps its signature but scales from `_canvasSize()`.

Root causes to remove (spec G4): hard-coded 960×540 in `.slide-scaler` CSS and `_applyScale`; `html { font-size: 16px !important }`; `body { font-family … !important }` leaking into previews; `clone.className = 'slide active'` dropping classes; deck classes / `data-fit` / theme preset / `lang` not reproduced on the preview `.slide-deck`.

- [ ] **Step 1: Write the failing test** `tests/structure/reactive_presenter_test.py` (unittest; `skipTest` when `playwright` import or `chromium.launch()` fails). Build fixture: copy `RP/assets/*.js|*.css` into a temp `common/` dir and write an `index.html` with two slides (slide 2 carries `class="slide theme-dark"` and a 4-column table with long Korean cells), served over `http.server` on a free port. Open deck at 1600×900, press `p`, capture the popup.

```python
def test_preview_uses_deck_canvas(self):
    # inside presenter window
    w, h = presenter.evaluate("() => { const s = document.querySelector('#p-current .slide-scaler'); return [s.offsetWidth, s.offsetHeight]; }")
    self.assertEqual((w, h), (1920, 1080))

def test_preview_root_font_matches_deck(self):
    deck_fs = page.evaluate("() => getComputedStyle(document.documentElement).fontSize")
    prev_fs = presenter.evaluate("() => getComputedStyle(document.querySelector('#p-current .slide')).fontSize")
    self.assertEqual(deck_fs, "24px")
    self.assertEqual(prev_fs, page.evaluate("() => getComputedStyle(document.querySelector('.slide.active')).fontSize"))

def test_preview_font_family_matches_deck(self):
    self.assertEqual(presenter_ff_of_current_slide_h2, deck_ff_of_active_slide_h2)

def test_preview_keeps_slide_and_deck_classes(self):
    # navigate deck to slide 2
    self.assertIn("theme-dark", presenter.evaluate("() => document.querySelector('#p-current .slide').className"))
    self.assertEqual(presenter.evaluate("() => document.querySelector('#p-current .slide-deck').getAttribute('lang') || document.documentElement.lang"), "ko")

def test_preview_table_layout_matches_deck(self):
    # same row heights ratio: each <tr> height / table height, deck vs preview, within 0.02
    for d, p in zip(deck_ratios, preview_ratios):
        self.assertAlmostEqual(d, p, delta=0.02)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 tests/structure/reactive_presenter_test.py -v`
Expected: FAIL on `test_preview_uses_deck_canvas` (960, 540) and `test_preview_root_font_matches_deck` (16px).

- [ ] **Step 3: Implement in `presenter-view.js`**

Scope presenter-chrome rules under a `.pv-chrome` wrapper class (topbar, notes, controls) instead of `html`/`body !important`; keep only `body { margin:0; background; height:100vh; overflow:hidden }` without `font-family`/`font-size`. Previews: `.slide-scaler` gets inline `width/height` from `_canvasSize()`; `.slide-scaler .slide-deck` copies the live deck's `className`, `data-fit` and `lang`; clone keeps `sourceSlide.className` plus `active`; `<html>` of the presenter doc copies the deck document's `lang` and `class`. Keep fragments as they are in the source clone for "current"; add `visible` to every `.fragment` in the "next" clone.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 tests/structure/reactive_presenter_test.py -v`
Expected: all PASS (or all `skipped` with reason when Playwright is absent).

- [ ] **Step 5: Wire into TAP and commit**

`tests/structure/test-reactive-presenter.sh` mirrors `test-remarp-contract.sh` (pass/fail on the Python exit code; skipped tests still exit 0). Also `node --check` on `presenter-view.js`.

```bash
git add plugins/aws-content-plugin/skills/reactive-presentation/assets/presenter-view.js tests/structure/reactive_presenter_test.py tests/structure/test-reactive-presenter.sh
git commit -m "fix(reactive-presentation): render presenter previews on the deck canvas"
```

---

### Task 2: Compiler DOM contract (blocks, detail terms, detail store, export)

**Files:**
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/scripts/export_pptx.py`
- Test: `tests/structure/remarp_contract_test.py`

**Interfaces:**
- Consumes: generic block parser (`_BLOCK_OPEN_RE`, `all_blocks[...]`), `_convert_markdown`, `_build_merged_index`, `wrap_html`, asset copy list (`remarp_to_slides.py:4696`).
- Produces (DOM contract consumed by Task 3 and `export_pptx.py`):
  - Every built `.slide` carries `data-block="<block key>"` and `data-block-title="<title>"`. Title source: block frontmatter `title`, else first `# ` heading in the block file, else file stem. Single-block builds carry the same attributes.
  - Inline `[text]{tip="T"}` → `<span class="rp-detail" tabindex="0" data-tip="T">text</span>`.
  - Inline `[text]{detail=ID}` → `<span class="rp-detail" tabindex="0" data-detail="ID" data-tip="TIP">text</span>` where TIP is the block's `tip:` line, else its title.
  - `:::detail ID "Title"` block (body Markdown, optional first line `tip: ...`) → removed from flow; emitted once per slide as `<div class="rp-detail-store" hidden><section data-detail-id="ID" data-title="Title">HTML</section>…</div>` as the last child of the `.slide`.
  - `Slide.details: List[Dict[str, str]]` with keys `id`, `title`, `tip`, `html`, `text`.
  - `wrap_html` adds `<link rel="stylesheet" href="./common/deck-overlay.css">` after `theme.css` and `<script src="./common/deck-overlay.js"></script>` before `slide-framework.js`; both names added to the asset copy list.
  - `validate`: CRITICAL `DETAIL_REF` for a reference to a missing id or a duplicate id in one slide.
  - `export_pptx.py`: `_details_to_text(details: list[dict]) -> str` appends `[디테일]` (`lang` ko) or `[Details]` (else) followed by `- {title}: {text}` lines to each slide's notes; details are read in the page with `slide.querySelectorAll('.rp-detail-store section')`.

- [ ] **Step 1: Write the failing tests** in `remarp_contract_test.py`:

```python
def test_tip_inline_renders_span(self):
    html = build_one("## T\n\n표: [UDP 8472]{tip=\"Cilium VXLAN 포트\"}\n")
    self.assertIn('<span class="rp-detail" tabindex="0" data-tip="Cilium VXLAN 포트">UDP 8472</span>', html)

def test_tip_attribute_is_escaped(self):
    html = build_one('## T\n\n[a]{tip="x \\"q\\" <b> & y"}\n')
    self.assertIn('data-tip="x &quot;q&quot; &lt;b&gt; &amp; y"', html)

def test_detail_block_moves_to_store(self):
    src = '## T\n\n[UDP 8472]{detail=vxlan}\n\n:::detail vxlan "UDP 8472가 필요한 이유"\ntip: hybrid 노드 간 VXLAN\n\n- direct routing, Gateway 모두 필요\n:::\n'
    html = build_one(src)
    self.assertIn('data-detail="vxlan" data-tip="hybrid 노드 간 VXLAN"', html)
    self.assertRegex(html, r'<div class="rp-detail-store" hidden><section data-detail-id="vxlan" data-title="UDP 8472가 필요한 이유">.*<li>direct routing, Gateway 모두 필요</li>')
    self.assertNotIn(':::detail', html)

def test_detail_in_table_cell(self):  # pipe table cell keeps the span
    ...assertIn('<td><span class="rp-detail"', html)

def test_detail_ref_missing_is_critical(self):
    findings = validate_text('## T\n\n[x]{detail=nope}\n')
    self.assertIn(('CRITICAL', 'DETAIL_REF'), {(f['severity'], f['rule']) for f in findings})

def test_detail_duplicate_id_is_critical(self): ...

def test_merged_index_marks_blocks(self):
    # two block files 01-a.md (frontmatter title "개요"), 02-b.md (no title, "# 2부: 네트워킹")
    self.assertIn('data-block="01-a" data-block-title="개요"', index_html)
    self.assertIn('data-block-title="2부: 네트워킹"', index_html)

def test_wrap_html_loads_overlay_assets(self):
    self.assertIn('./common/deck-overlay.css', html); self.assertIn('./common/deck-overlay.js', html)
    self.assertLess(html.index('deck-overlay.js'), html.index('slide-framework.js'))

def test_export_details_to_text(self):
    self.assertEqual(export._details_to_text([{'title': 'A', 'text': 'b'}], 'ko'), '[디테일]\n- A: b')
```

(`build_one` / `validate_text` are small helpers in the test class that write a temp source and call the existing CLI/`validate_presentation`. `_details_to_text(details, lang)` takes `lang` as second parameter.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 tests/structure/remarp_contract_test.py -v`
Expected: new tests FAIL; existing tests PASS.

- [ ] **Step 3: Implement** the contract above. Inline syntax is converted in `_convert_markdown` after code spans are masked (so `` `[a]{tip="x"}` `` stays literal) and before the link rule. Escape attribute values with `html.escape(value, quote=True)`. `:::detail` args parse as `ID "Title"`; `tip:` is only recognised on the first non-empty body line.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 tests/structure/remarp_contract_test.py -v && bash tests/run-all.sh > /tmp/run-all.log 2>&1; grep -E "^not ok|# Results" /tmp/run-all.log`
Expected: all PASS; `# Results: … 0 failed`.

- [ ] **Step 5: Commit**

```bash
git add plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py plugins/aws-content-plugin/skills/reactive-presentation/scripts/export_pptx.py tests/structure/remarp_contract_test.py
git commit -m "feat(remarp): detail terms, detail store and block markers"
```

---

### Task 3: Runtime overlay (agenda, ⌘K search, tooltip, detail sidebar)

**Files:**
- Create: `plugins/aws-content-plugin/skills/reactive-presentation/assets/deck-overlay.js`
- Create: `plugins/aws-content-plugin/skills/reactive-presentation/assets/deck-overlay.css`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/assets/slide-framework.js`
- Create: `tests/structure/reactive_overlay_test.py`
- Create: `tests/structure/test-reactive-overlay.sh`

**Interfaces:**
- Consumes: Task 2 DOM contract (`.slide[data-block][data-block-title]`, `.rp-detail[data-tip][data-detail]`, `.rp-detail-store section[data-detail-id][data-title]`). Tests use a hand-written fixture HTML with that markup, so this task does not depend on Task 2's code.
- Produces:
  - `window.DeckOverlay = { init(framework), openSearch(), closeSearch(), openDetail(slideEl, id), closeDetail(), buildIndex(): Array<{index:number, block:string, blockTitle:string, title:string, text:string, detailText:string}> }`.
  - `SlideFramework` constructor calls `if (window.DeckOverlay) window.DeckOverlay.init(this)` after slides are collected; `showSlide(index)` dispatches `document.dispatchEvent(new CustomEvent('rp:slidechange', { detail: { index } }))`.
  - `SlideFramework` keydown handler returns early when `e.target.isContentEditable`, when the target is `INPUT`/`TEXTAREA`/`SELECT`, or when `document.body.classList.contains('rp-search-open')`.
  - Body classes: `rp-search-open`, `rp-agenda-open`, `rp-detail-open`. All overlay roots carry `rp-overlay-ui`.
  - Element ids: `#rp-agenda`, `#rp-agenda-hotzone`, `#rp-search`, `#rp-search-input`, `#rp-search-results`, `#rp-tooltip`, `#rp-detail-panel`.

Behaviour (spec G1-G3): hot zone 64×64px fixed top-right, open on `mouseenter`, close 300ms after `mouseleave` of zone+panel; agenda groups slides by `data-block` (fallback: one group titled with `document.title`), highlights current slide, click → `goTo`. Search opens on `Meta+K`/`Ctrl+K`/`/` (not when typing in inputs), `Esc` closes, `ArrowUp/Down` moves, `Enter` → `goTo`; index built once from `.slide-deck > .slide` (title = first `h1,h2`, text = `textContent` minus `.rp-detail-store` and `template.notes`, detailText = store text); case-insensitive substring, rank title > text > detail then slide order, cap 20 results; result row shows block title, `N`, slide title, snippet with `<mark>`. Tooltip shows on `mouseenter`/`focus` of `.rp-detail`, hides on leave/blur. Terms with `data-detail` get class `has-panel` and an appended `<button class="rp-detail-icon" aria-label="자세히">` (label in `en` decks: "Details"); click on term or icon → `openDetail`; `Enter` on focused term → `openDetail`; tip-only terms ignore click. Panel: fixed right, overlays deck, closes on `Esc`, outside click, close button and `rp:slidechange`. Overlay never changes `.slide` layout (no reflow, no ReactiveFit call).

- [ ] **Step 1: Write the failing tests** `reactive_overlay_test.py` (same skip and serving pattern as Task 1; fixture: two blocks × 3 slides, slide 2 contains `UDP 8472` with a detail and a tip-only term, slide 5 contains "vxlan" only in body, one slide has an `<input>`):

```python
def test_agenda_opens_on_hover_and_jumps(self):
    page.hover('#rp-agenda-hotzone'); page.wait_for_selector('#rp-agenda', state='visible')
    self.assertEqual(page.locator('#rp-agenda .rp-agenda-block').count(), 2)
    page.click('#rp-agenda [data-goto="4"]')
    self.assertEqual(active_index(page), 4)

def test_agenda_single_block_lists_slides(self):  # fixture without data-block
    self.assertEqual(page.locator('#rp-agenda [data-goto]').count(), 3)

def test_search_cmd_k_finds_body_text(self):
    page.keyboard.press('Meta+K'); page.keyboard.type('VXLAN')
    first = page.locator('#rp-search-results [data-goto]').first
    self.assertEqual(first.get_attribute('data-goto'), '4')
    page.keyboard.press('Enter'); self.assertEqual(active_index(page), 4)
    self.assertFalse(page.evaluate("document.body.classList.contains('rp-search-open')"))

def test_search_excludes_notes_and_clones(self):
    # term only in <template class="notes"> → 0 results; sidebar thumbnails present → no duplicate rows
def test_search_ignores_typing_in_inputs(self):
    page.focus('#fixture-input'); page.keyboard.type('/k')
    self.assertFalse(search_open(page)); self.assertEqual(active_index(page), start)
    # and inside the search box, ArrowRight does not change slide
def test_tooltip_on_hover_tip_only_no_icon(self):
    page.hover('.rp-detail:not([data-detail])')
    self.assertIn('짧은 설명', page.inner_text('#rp-tooltip'))
    self.assertEqual(page.locator('.rp-detail:not([data-detail]) .rp-detail-icon').count(), 0)
    page.click('.rp-detail:not([data-detail])'); self.assertFalse(detail_open(page))
def test_click_term_with_detail_opens_panel(self):
    page.click('.rp-detail[data-detail="vxlan"]')
    self.assertIn('UDP 8472가 필요한 이유', page.inner_text('#rp-detail-panel'))
def test_sidebar_closes_on_slide_change(self):
    open panel; page.keyboard.press('ArrowRight'); self.assertFalse(detail_open(page)); self.assertEqual(active_index(page), start + 1)
def test_esc_closes_panel_and_search(self): ...
def test_overlay_outside_slides(self):
    self.assertEqual(page.locator('.slide .rp-overlay-ui').count(), 0)
```

- [ ] **Step 2: Run to verify fail**

Run: `python3 tests/structure/reactive_overlay_test.py -v`
Expected: FAIL (no `#rp-agenda-hotzone`).

- [ ] **Step 3: Implement** `deck-overlay.js` (IIFE, no globals other than `window.DeckOverlay`), `deck-overlay.css` (token-only, both themes, `@media print { .rp-overlay-ui { display:none } }`), and the three `slide-framework.js` hooks listed in Interfaces. Escape all user text inserted into result rows (build nodes with `textContent`; `<mark>` via split text nodes).

- [ ] **Step 4: Run to verify pass**

Run: `python3 tests/structure/reactive_overlay_test.py -v && node --check plugins/aws-content-plugin/skills/reactive-presentation/assets/deck-overlay.js && node --check plugins/aws-content-plugin/skills/reactive-presentation/assets/slide-framework.js`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/aws-content-plugin/skills/reactive-presentation/assets/deck-overlay.js plugins/aws-content-plugin/skills/reactive-presentation/assets/deck-overlay.css plugins/aws-content-plugin/skills/reactive-presentation/assets/slide-framework.js tests/structure/reactive_overlay_test.py tests/structure/test-reactive-overlay.sh
git commit -m "feat(reactive-presentation): hover agenda, cmd-k search and detail layer"
```

---

### Task 4: Copy gates (EM_DASH, AI_TONE, SENTENCE_RUNON) and overlay hiding in measurement

**Files:**
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/scripts/measure_deck.py`
- Test: `tests/structure/remarp_contract_test.py`
- Create: `tests/structure/measure_runon_test.py`
- Create: `tests/structure/test-measure-runon.sh`

**Interfaces:**
- Consumes: `_validate_slide` `add(severity, rule, message, fix)`; `_mask_code_fences`; Task 2's `Slide.details` (detail bodies are scanned) and notes text.
- Produces: module constants `AI_TONE_LABELS = ("한 줄 정리", "핵심 정리", "핵심:", "Key takeaway")`, `AI_TONE_NOTE_CLICHES = ("꼭 기억해 두세요", "중요한 포인트는", "결론적으로")`, `AI_TONE_MAX_ARROWS = 3`, `AI_TONE_MAX_LABEL_REPEATS = 2`; deck-level pass `_validate_deck_tone(slides) -> List[finding]` called from `validate_presentation` for label repeats; measure rule `SENTENCE_RUNON` (WARN).

- [ ] **Step 1: Write failing tests**

```python
def test_em_dash_warns_in_body_notes_and_detail(self):
    for src in ("## T\n\nA — B\n", "## T\n\nx\n\n:::notes\n{timing: 1min}\n[요약]\n- a&mdash;b\n:::\n",
                '## T\n\n[a]{detail=d}\n\n:::detail d "t"\nx · y\n:::\n'):
        self.assertIn(('WARNING', 'EM_DASH'), rules(validate_text(src)))

def test_em_dash_skips_code_and_urls(self):
    for src in ("## T\n\n`a — b`\n", "## T\n\n```\na — b\n```\n", "## T\n\n[l](https://x.com/a—b)\n", "## T\n\n<code>&mdash;</code>\n"):
        self.assertNotIn('EM_DASH', {r for _, r in rules(validate_text(src))})

def test_ai_tone_arrows(self):
    self.assertIn('AI_TONE', rule_ids(validate_text("## T\n\na → b → c → d → e\n")))   # 4 arrows
    self.assertNotIn('AI_TONE', rule_ids(validate_text("## T\n\na → b → c → d\n")))     # 3 arrows

def test_ai_tone_label_repeats_deck_wide(self):  # "한 줄 정리" on 3 slides → one WARNING; on 2 → none
def test_ai_tone_note_cliche(self):
def test_copy_gates_do_not_block_build(self):  # deck with only these findings: build exit 0
```

`measure_runon_test.py` (Playwright skip pattern): fixture card `<div class="card-desc" style="width:560px">Public-only 또는 Private-only 권장. "Public and Private"는 VPC 밖 노드에서 endpoint가 public IP로 해석되어 join이 실패할 수 있음</div>` → `SENTENCE_RUNON` WARN on that slide; same text split into two `<div>`s → none; a single long sentence wrapping 3 lines → none.

Also assert `_PREPARE_JS` hides `.rp-overlay-ui`: `self.assertIn('.rp-overlay-ui', measure_deck._PREPARE_JS)`.

- [ ] **Step 2: Run to verify fail**

Run: `python3 tests/structure/remarp_contract_test.py -v; python3 tests/structure/measure_runon_test.py -v`
Expected: new tests FAIL.

- [ ] **Step 3: Implement.** `EM_DASH` scans masked slide markdown, html blocks (with `<code>…</code>` and `<pre>…</pre>` stripped), notes and detail bodies for `—|·|・|&mdash;|&#8212;|&#x2014;|&middot;|&#183;|&#xb7;`, after removing URLs (`https?://\S+`). Arrows counted over visible text (`→` and `->` outside code). `SENTENCE_RUNON` in the page-side checks: for each leaf-ish text block (`p, li, td, .card-desc, .on-surface-muted, .callout div`) with ≥ 2 sentences (split on `. `, `? `, `! `, `다. `) and ≥ 3 rendered lines (`getClientRects` of a Range over line boxes), WARN when a sentence's first character's rect `left` is greater than the block's content-left + 1px. Add `.rp-overlay-ui { display:none !important }` to `_PREPARE_JS`. Update the module docstring check list.

- [ ] **Step 4: Run to verify pass**

Run: `python3 tests/structure/remarp_contract_test.py -v && python3 tests/structure/measure_runon_test.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py plugins/aws-content-plugin/skills/reactive-presentation/scripts/measure_deck.py tests/structure/remarp_contract_test.py tests/structure/measure_runon_test.py tests/structure/test-measure-runon.sh
git commit -m "feat(reactive-presentation): EM_DASH, AI_TONE and SENTENCE_RUNON copy gates"
```

---

### Task 5: Theme cleanup (accent bars, logo overlap)

**Files:**
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/assets/theme.css`
- Modify: `tests/structure/test-reactive-design-tokens.sh`

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: `.callout` and `.pain-quote` without `border-left`; role conveyed by `background` (`color-mix(in srgb, var(--role) 10%, var(--surface-1))` or existing `*-bg` tokens) and title colour. `.slide-logo` and `.nav-hint` never overlap.

- [ ] **Step 1: Write failing assertions** in `test-reactive-design-tokens.sh`:

```bash
TC_FLAT="$(tr '\n' ' ' < "$RP/assets/theme.css")"
assert_grep_no_match "\.callout\s*\{[^}]*border-left" "$TC_FLAT" ".callout has no left accent bar"
assert_grep_no_match "\.pain-quote\s*\{[^}]*border-left" "$TC_FLAT" ".pain-quote has no left accent bar"
assert_grep_no_match "\.callout-[a-z]+\s*\{[^}]*border-left-color" "$TC_FLAT" "callout variants do not colour a left bar"
```

Logo overlap is asserted statically (browser fixtures belong to other tasks). The logo is `bottom:16px; left:20px; height:32px` (`theme.css:1126`) and the slide counter owns the bottom-right, so lift `.nav-hint` above the logo row instead: `bottom: calc(16px + 32px + var(--space-2))`:

```bash
assert_grep_match "\.nav-hint\s*\{[^}]*bottom:\s*calc\(16px \+ 32px" "$TC_FLAT" "nav hint sits above the 32px logo row"
```

- [ ] **Step 2: Run to verify fail**

Run: `bash tests/run-all.sh > /tmp/run-all.log 2>&1; grep -E "accent bar|nav hint" /tmp/run-all.log`
Expected: `not ok` lines.

- [ ] **Step 3: Implement** in `theme.css`; also scan for any other `border-left: Npx solid` / `border-top: Npx solid var(--accent…)` decorative bars on card-like primitives and remove them (keep 1px neutral dividers like `border-top: 1px solid var(--border)`).

- [ ] **Step 4: Run to verify pass** — same command; expected `ok`, `# Results: … 0 failed`.

- [ ] **Step 5: Commit**

```bash
git add plugins/aws-content-plugin/skills/reactive-presentation/assets/theme.css tests/structure/test-reactive-design-tokens.sh
git commit -m "style(reactive-presentation): drop callout accent bars and clear logo from nav hint"
```

---

### Task 6: Docs, agent prompt, example deck, changelog

**Files:**
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/REMARP.md`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/references/remarp-format-guide.md`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/references/keyboard-shortcuts.md`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/references/authoring-rules.md`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/references/framework-contract.md`
- Modify: `plugins/aws-content-plugin/agents/reactive-presentation-agent.md`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/assets/example-deck/index.html`
- Modify: `doc-sites/docs/aws-content-plugin/skills/reactive-presentation.md`
- Modify: `doc-sites/i18n/ko/docusaurus-plugin-content-docs/current/aws-content-plugin/skills/reactive-presentation.md`
- Modify: `CHANGELOG.md`
- Test: `tests/structure/test-reactive-design-lint.sh`

**Interfaces:**
- Consumes: final names from Tasks 2-5 (`[text]{tip="..."}`, `[text]{detail=ID}`, `:::detail ID "Title"` + `tip:`, `⌘K`/`Ctrl+K`/`/`, `EM_DASH`, `AI_TONE`, `SENTENCE_RUNON`, `DETAIL_REF`, `deck-overlay.js/.css`).
- Produces: documentation only.

- [ ] **Step 1: Write failing assertions** in `test-reactive-design-lint.sh`: `REMARP.md` and `remarp-format-guide.md` contain `:::detail` and `{tip=`; `keyboard-shortcuts.md` contains `Ctrl+K`; `authoring-rules.md` §2 table rows reference `EM_DASH`, `AI_TONE`, `SENTENCE_RUNON` and the line "one claim line"; the agent prompt mentions `:::detail`; both doc-site pages contain `:::detail` and the same `<span id="keyboard-shortcuts" />` anchor; no file in the Task 6 list contains U+2014 in lines added by this plan (check new sections only, by grepping the new headings' sections).
- [ ] **Step 2: Run to verify fail** (`bash tests/run-all.sh > /tmp/run-all.log 2>&1; grep "not ok" /tmp/run-all.log`).
- [ ] **Step 3: Write the docs.** `authoring-rules.md` §2: change the em dash row enforcement to `EM_DASH` (lint); add `AI_TONE` and `SENTENCE_RUNON` rows; add rule "card description = one claim line + optional one reason line; elaboration goes to `:::detail`". Example deck: add one tip-only term and one `:::detail`-backed term (hand-edited HTML following the Task 2 contract). CHANGELOG `[Unreleased]` → `### Added` / `### Fixed` / `### Changed` entries.
- [ ] **Step 4: Run to verify pass**; then host runs `python3 scripts/sync-codex-plugins.py` and `--check`, `python3 scripts/test-plugins.py`, `python3 scripts/test-codex-plugins.py`, `python3 scripts/eval-skills.py`, and the doc-site build/link check per `doc-sites/CLAUDE.md`.
- [ ] **Step 5: Commit**

```bash
git add plugins/aws-content-plugin/skills/reactive-presentation/REMARP.md plugins/aws-content-plugin/skills/reactive-presentation/references plugins/aws-content-plugin/agents/reactive-presentation-agent.md plugins/aws-content-plugin/skills/reactive-presentation/assets/example-deck/index.html doc-sites/docs/aws-content-plugin/skills/reactive-presentation.md doc-sites/i18n/ko/docusaurus-plugin-content-docs/current/aws-content-plugin/skills/reactive-presentation.md CHANGELOG.md tests/structure/test-reactive-design-lint.sh
git commit -m "docs(reactive-presentation): document detail layer, search and copy gates"
```

---

## Waves (file-disjoint)

- Wave 1: Task 1, Task 2, Task 3
- Wave 2: Task 4 (after Task 2: same `remarp_to_slides.py`, `remarp_contract_test.py`), Task 5
- Wave 3: Task 6, then host-only package regeneration and full validation
