# Reactive-presentation navigation, detail layer, preview fidelity and AI-tone gates: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a hover agenda, ⌘K search and a hover/click detail layer to reactive-presentation decks, make presenter-view previews match the deck, and add copy/AI-tone gates.

**Architecture:** A new self-contained runtime asset pair (`deck-overlay.js` / `deck-overlay.css`) owns agenda, search, tooltip and detail panel, attached to `document.body` and initialised by `SlideFramework` once slides are collected. The Remarp compiler emits a small DOM contract (block markers on slides, `.rp-detail` terms, a hidden per-slide detail store) consumed by the runtime and `export_pptx.py`. Presenter previews render on the deck's real canvas with the deck's root font. New lint rules live in `validate_presentation` / `measure_deck.py`.

**Tech Stack:** Vanilla JS/CSS (no new dependency), Python 3 (compiler, measure/export scripts), Playwright for Python (browser tests, skipped when unavailable), TAP shell runner.

**Spec:** `docs/superpowers/specs/2026-10-18-reactive-nav-detail-design.md`

> **Status note (2026-10-18, after implementation):** the single `deck-overlay.js` / `deck-overlay.css` pair described below shipped as three module pairs: `deck-overlay` (core, `window.DeckOverlay` and module registry), `deck-detail` (tooltip and side panel) and `deck-nav` (agenda and search). `reactive_overlay_test.py` became `reactive_overlay_fixture.py` plus `reactive_detail_test.py` and `reactive_nav_test.py`. The tasks below record the original intent.

## Global Constraints

- Skill root: `plugins/aws-content-plugin/skills/reactive-presentation` (written `RP/` in prose; file lists use full paths).
- Vanilla JS/CSS only; no CDN, no new runtime dependency.
- Theme tokens only (`var(--surface-*)`, `var(--accent)`, `var(--text-*)`, `var(--space-*)`, `var(--radius-*)`); no raw hex/rgba in new CSS; works under `.theme-light` and `.theme-dark`.
- Overlay roots (agenda, hot zone, search modal, tooltip, detail panel) are children of `document.body`, never inside `.slide`, and carry class `rp-overlay-ui`.
- Nothing is inserted into `.slide` at runtime. The "has panel" icon is a CSS `::after` pseudo-element on `.rp-detail[data-detail]` (inline, in normal flow, small `margin-inline-start`), present from first paint because `deck-overlay.css` loads in `<head>`, so ReactiveFit fits with it already in place and nothing shifts later.
- Capture/measurement hide rule (used verbatim by `measure_deck.py` and `export_pptx.py`): `.rp-overlay-ui { display:none !important } .rp-detail { text-decoration:none !important } .rp-detail::after { visibility:hidden !important }` (`visibility`, not `display`, so captured layout equals live layout). The browser-side capture paths in `export-utils.js` inject the same rule.
- No decorative chrome in new UI: no gradients, glow, or left/top colour bars.
- No em dash (U+2014) or middle dot (U+00B7, U+30FB) in any copy, docs or UI strings added by this plan.
- Deck window is the only surface for agenda/search/detail; presenter window gets none of them. Jumps use `SlideFramework.goTo(index)`.
- Search excludes speaker notes and framework clones (`.slide-sidebar`, presenter `.slide-scaler`, overview copies).
- `EM_DASH` and `AI_TONE` are `WARNING` (build still passes on 0 CRITICAL). `DETAIL_REF` is `CRITICAL`.
- Each task's own verification runs only that task's test files (or `bash tests/run-all.sh <name-filter>`); the host runs the full `bash tests/run-all.sh` after each wave.
- Browser tests skip without Playwright; their TAP wrappers then print `ok - <name> # SKIP <reason>`. The host must show at least one unskipped run of every browser test file (test counts in the log) before Task completion is accepted.
- Slide indices in the runtime contract (`data-goto`, `goTo`, `buildIndex().index`) are 0-based. Prose "slide N" in fixtures is 1-based; tests assert 0-based values.
- Every attribute value the compiler emits from author text (`data-tip`, `data-title`, `data-text`, `data-block-title`) goes through `html.escape(value, quote=True)`.
- Never hand-edit `packages/*`; the host regenerates and commits them after Task 6.
- Internal docs in English; public `doc-sites/` pages updated in EN and KO with matching anchors, then `npm run record:locales`.

## Review Focus

1. Search hotkey while a quiz input or the search box has focus: typing `/` or `k` must not reopen/close the modal or advance slides. Pinned by `test_search_ignores_typing_in_inputs` (Task 3).
2. Arrow/space while the detail panel is open must still navigate, and the panel must close on slide change. Pinned by `test_panel_closes_on_slide_change` (Task 3).
3. A tip value with quotes, `<`, `&`, `*` or Korean must render escaped and verbatim. Pinned by `test_tip_attribute_is_escaped` and `test_tip_value_not_markdown_converted` (Task 2).
4. Single-block HTML (no `data-block`) must still show an agenda of that block's slides. Pinned by `test_agenda_single_block_lists_slides` (Task 3).
5. Raw-HTML authored `data-tip`/`data-title` containing `<img onerror>` must not execute. Pinned by `test_tooltip_and_panel_title_are_text` (Task 3).

---

### Task 1: Presenter preview fidelity

**Files:**
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/assets/presenter-view.js`
- Create: `tests/structure/reactive_presenter_test.py`
- Create: `tests/structure/test-reactive-presenter.sh`

**Interfaces:**
- Consumes: the deck page (`window.opener` from the presenter window).
- Produces: `PresenterView._canvasSize(): {w: number, h: number}` computed as `h = 1080`, `w = round(1080 * ratioW / ratioH)` from the live deck's computed `--slide-ratio-w` / `--slide-ratio-h` (default 16/9), so it is correct even in overview mode. Existing `_applyScale(scaler, containerW, containerH)` (`presenter-view.js:703`) keeps its signature and scales from `_canvasSize()`.

Root causes (spec G4): hard-coded 960×540 in `.slide-scaler` CSS and `_applyScale`; `html { font-size: 16px !important }`; `body { font-family … !important }` leaking into previews; `clone.className = 'slide active'`; deck classes / `data-fit` / `lang` not reproduced; presenter `<html lang="ko">` hard-coded.

- [ ] **Step 1: Write the failing test** `reactive_presenter_test.py` (unittest; `skipTest` when `playwright` import or `chromium.launch()` fails). Fixture: copy `RP/assets/*.js|*.css` into a temp `common/`, write `index.html` with `<html lang="en">`, deck class `slide-deck preset-paper`, `data-fit="auto"`, three slides: slide 2 `class="slide theme-dark"` with a 4-column table of long Korean cells; slide 3 with two `.fragment` items. Serve via `http.server` on a free port, open at 1600×900, press `p`, capture the popup, wait 500ms (first render is deferred 300ms), then call `window.__pvScaleUpdate()` on the deck page (it is defined on the opener, `presenter-view.js:53`).

```python
def test_preview_uses_deck_canvas(self):            # (w,h) of '#p-current .slide-scaler' == (1920,1080)
def test_preview_root_font_matches_deck(self):      # presenter documentElement fontSize == deck's ("24px"); preview h2 fontSize == deck h2 fontSize
def test_preview_font_family_matches_deck(self):    # preview h2 fontFamily == deck h2 fontFamily
def test_preview_keeps_slide_and_deck_classes(self):# on slide 2: 'theme-dark' in preview slide class; preview .slide-deck has 'preset-paper' and data-fit="auto"; presenter documentElement.lang == "en"
def test_preview_table_layout_matches_deck(self):   # per-row height / table height, deck vs preview, abs diff <= 0.02
def test_next_preview_reveals_fragments(self):      # deck on slide 2: every '#p-next .fragment' has class visible
def test_current_preview_keeps_reveal_state(self):  # deck on slide 3, press ArrowRight once (1 fragment shown): within 500ms '#p-current .fragment.visible' count == 1
def test_presenter_chrome_size_unchanged(self):     # '.presenter-timer' computed fontSize == "24px" (1.5rem at the old 16px base)
```

- [ ] **Step 2: Run to verify fail**

Run: `python3 tests/structure/reactive_presenter_test.py -v`
Expected: FAIL on canvas (960, 540), root font (16px), lang ("ko").

- [ ] **Step 3: Implement in `presenter-view.js`**

The presenter document's `html` font-size is set to the opener's computed root font-size, and `<html lang>` / class copy the opener's. All presenter-chrome CSS values currently in `rem` are converted to `px` at the old 16px base (1.5rem → 24px, etc.), so chrome size is unchanged. Keep the body column layout (`display:flex; flex-direction:column; align-items:stretch; justify-content:stretch`), but drop `font-family`/`font-size` from `body`; chrome font is set on `.presenter-topbar, .presenter-notes, .presenter-nav` (existing chrome containers) instead. `.slide-scaler` width/height come from `_canvasSize()` inline, and the existing `.slide-scaler .slide-deck { width: 960px !important; height: 540px !important }` rule is replaced by `width: 100% !important; height: 100% !important`. The preview `.slide-deck` copies the live deck's `className` (minus `overview-mode`), `data-fit` and `lang`; the clone keeps `sourceSlide.className` plus `active`. "Next" clone: add `visible` to every `.fragment`. "Current" clone: mirrors the live reveal state; because fragment reveals do not call the presenter (`slide-framework.js:114-153`), `PresenterView` attaches a `MutationObserver` (attribute `class`, subtree) to the live active slide and re-renders the current preview on change (debounced 50ms), re-attaching on slide change.

- [ ] **Step 4: Run to verify pass**

Run: `python3 tests/structure/reactive_presenter_test.py -v && node --check plugins/aws-content-plugin/skills/reactive-presentation/assets/presenter-view.js`
Expected: all PASS (or all skipped with reason when Playwright is absent).

- [ ] **Step 5: Wire into TAP and commit**

`test-reactive-presenter.sh` mirrors `test-remarp-contract.sh` (pass/fail on the Python exit code).

```bash
git add plugins/aws-content-plugin/skills/reactive-presentation/assets/presenter-view.js tests/structure/reactive_presenter_test.py tests/structure/test-reactive-presenter.sh
git commit -m "fix(reactive-presentation): render presenter previews on the deck canvas"
```

---

### Task 2: Compiler DOM contract (blocks, detail terms, detail store, export, asset wiring)

**Files:**
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/scripts/export_pptx.py`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/scripts/check_deck.py`
- Test: `tests/structure/remarp_contract_test.py`

**Interfaces:**
- Consumes: Task 3's asset files `RP/assets/deck-overlay.js`, `RP/assets/deck-overlay.css` (exist after Wave 1).
- Produces:
  - `_mask_code_spans(text: str) -> Tuple[str, List[str]]` and `_restore_code_spans(text: str, spans: List[str]) -> str` (module-level). Inline code spans become `\x00CS{n}\x00` placeholders. `_convert_markdown` masks spans first, runs all rules (incl. detail syntax), then restores spans as `<code>…</code>`. Task 4 reuses these.
  - Tip grammar: `\{tip="((?:[^"\\]|\\.)*)"\}`; inside the value `\"` → `"` and `\\` → `\`; the value is never Markdown-converted; emitted via `html.escape(value, quote=True)`.
  - Inline `[text]{tip="T"}` → `<span class="rp-detail" tabindex="0" data-tip="T">text</span>`.
  - Inline `[text]{detail=ID}` (ID = `[A-Za-z0-9_-]+`) → `<span class="rp-detail" tabindex="0" data-detail="ID" data-tip="TIP">text</span>`; TIP = the block's `tip:` line, else its title.
  - `:::detail ID "Title"` blocks are top-level slide blocks only. `RemarpParser` collects them into `Slide.details: List[Dict[str, str]]` with keys `id`, `title`, `tip`, `body` (raw Markdown), before any rendering, so references may precede definitions. A `:::detail` nested in a tab/column/click block is CRITICAL `DETAIL_REF`.
  - `RemarpHTMLGenerator` sets `self._detail_tips = {d['id']: d['tip'] or d['title'] for d in slide.details}` before converting a slide, and appends as the last child of `.slide`: `<div class="rp-detail-store" hidden><section data-detail-id="ID" data-title="Title">HTML</section>…</div>` (HTML = the generator's existing Markdown rendering of `body`).
  - Each store `section` also carries `data-text`: the detail body Markdown with markup removed, one output line per source line (list markers kept as `- `, table rows as cells joined by ` | `), so export/search never concatenate adjacent `<li>`/`<td>` text.
  - Every built `.slide` carries `data-block="<block key>"` and `data-block-title="<title>"`. Title = the block file's own frontmatter `title` (block-only `config`, not `merged_config`), else its first `# ` heading, else the file stem. Single-block builds carry the same attributes.
  - `wrap_html` adds `<link rel="stylesheet" href="./common/deck-overlay.css">` after `theme.css`, and `<script src="./common/deck-overlay.js"></script>` before `slide-framework.js`; both names added to the asset copy list (`remarp_to_slides.py:4696`) and to ``check_deck.py` gains a `WARN` (its own severity vocabulary) `MISSING_OVERLAY` only when the deck contains `class="rp-detail` but lacks `deck-overlay.js` or `deck-overlay.css`. `FRAMEWORK_SCRIPTS` is not changed, so existing decks keep passing.
  - `validate`: CRITICAL `DETAIL_REF` for (a) `{detail=ID}` or `data-detail="ID"` anywhere in the slide's raw source (`slide.content`, which still holds nested tab/column/html children) after masking code fences/spans and removing `:::notes`, with no matching `:::detail` on that slide, (b) duplicate `:::detail` id on a slide, (c) nested `:::detail`.
  - `export_pptx.py`: `_details_to_text(details: List[Dict[str, str]], lang: str) -> str` returns `""` for no details, else a heading (`[디테일]` when `lang` starts with `ko`, else `[Details]`) followed by `- {title}: {text}` lines. The page side reads `document.documentElement.lang` and each `.rp-detail-store section` (`data-title`, `data-text`); text is appended to that slide's notes after a blank line. `export_pptx.py`'s `_PREPARE_JS` style gets the capture hide rule from Global Constraints.

- [ ] **Step 1: Write the failing tests** in `remarp_contract_test.py` (helpers `build_one(src) -> str` builds a single-file deck via the CLI and returns the HTML; `validate_text(src) -> list` calls `remarp.validate_presentation` on a temp file):

```python
def test_tip_inline_renders_span(self):
    self.assertIn('<span class="rp-detail" tabindex="0" data-tip="Cilium VXLAN 포트">UDP 8472</span>',
                  build_one(FRONT + '## T\n\n표: [UDP 8472]{tip="Cilium VXLAN 포트"}\n'))
def test_tip_attribute_is_escaped(self):
    self.assertIn('data-tip="x &quot;q&quot; &lt;b&gt; &amp; y"', build_one(FRONT + '## T\n\n[a]{tip="x \\"q\\" <b> & y"}\n'))
def test_tip_value_not_markdown_converted(self):
    self.assertIn('data-tip="**a** `b`"', build_one(FRONT + '## T\n\n[a]{tip="**a** `b`"}\n'))
def test_tip_inside_code_span_is_literal(self):
    self.assertIn('<code>[a]{tip="x"}</code>', build_one(FRONT + '## T\n\n`[a]{tip="x"}`\n'))
def test_detail_block_moves_to_store(self):
    src = FRONT + '## T\n\n[UDP 8472]{detail=vxlan}\n\n:::detail vxlan "UDP 8472가 필요한 이유"\ntip: hybrid 노드 간 VXLAN\n\n- direct routing, Gateway 모두 필요\n:::\n'
    html = build_one(src)
    self.assertIn('data-detail="vxlan" data-tip="hybrid 노드 간 VXLAN"', html)
    self.assertRegex(html, r'(?s)<div class="rp-detail-store" hidden><section data-detail-id="vxlan" data-title="UDP 8472가 필요한 이유">.*<li>direct routing, Gateway 모두 필요</li>')
    self.assertNotIn(':::detail', html)
def test_detail_reference_before_definition_gets_title_tip(self):  # no tip: line → data-tip == title
def test_detail_in_table_cell(self):          # '| a | [x]{tip="t"} |' → '<td><span class="rp-detail"'
def test_detail_ref_missing_is_critical(self):   # inline, raw '<span class="rp-detail" data-detail="nope">' in :::html, and inside a :::tab and a :::left column
def test_detail_title_and_block_title_escaped(self):  # ':::detail d "a <b> & \"c\""' → data-title="a &lt;b&gt; &amp; &quot;c&quot;"; block title '<x>' → data-block-title="&lt;x&gt;"
def test_detail_store_data_text_lines(self):  # body '- a\n- b' → data-text="- a\n- b" (newline kept, &#10; or literal)
def test_check_deck_missing_overlay_warns(self): # html with rp-detail but no deck-overlay.js → WARNING MISSING_OVERLAY; html without rp-detail → no finding
def test_detail_duplicate_and_nested_are_critical(self):
def test_merged_index_marks_blocks(self):
    # _presentation.md title "덱", 01-a.md frontmatter title "개요", 02-b.md no title with "# 2부: 네트워킹", 03-c.md no title/heading
    # asserts data-block="01-a" data-block-title="개요"; data-block-title="2부: 네트워킹"; data-block-title="03-c"
def test_wrap_html_loads_overlay_assets(self):   # both refs present; deck-overlay.js before slide-framework.js; existing test_standalone_build_copies_assets still passes
def test_export_details_to_text(self):
    self.assertEqual(export._details_to_text([{'title': 'A', 'text': 'b'}], 'ko'), '[디테일]\n- A: b')
    self.assertEqual(export._details_to_text([], 'en'), '')
def test_export_prepare_hides_overlay(self):
    self.assertIn('.rp-overlay-ui', export._PREPARE_JS); self.assertIn('.rp-detail::after', export._PREPARE_JS)
```

- [ ] **Step 2: Run to verify fail**

Run: `python3 tests/structure/remarp_contract_test.py -v`
Expected: new tests FAIL; existing tests PASS.

- [ ] **Step 3: Implement** the contract above.

- [ ] **Step 4: Run to verify pass**

Run: `python3 tests/structure/remarp_contract_test.py -v && python3 tests/structure/remarp_eval_test.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py plugins/aws-content-plugin/skills/reactive-presentation/scripts/export_pptx.py plugins/aws-content-plugin/skills/reactive-presentation/scripts/check_deck.py tests/structure/remarp_contract_test.py
git commit -m "feat(remarp): detail terms, detail store, block markers and overlay wiring"
```

---

### Task 3: Runtime overlay (agenda, ⌘K search, tooltip, detail panel) and nav-hint/logo overlap

**Files:**
- Create: `plugins/aws-content-plugin/skills/reactive-presentation/assets/deck-overlay.js`
- Create: `plugins/aws-content-plugin/skills/reactive-presentation/assets/deck-overlay.css`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/assets/slide-framework.js`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/assets/export-utils.js`
- Create: `tests/structure/reactive_overlay_test.py`
- Create: `tests/structure/test-reactive-overlay.sh`

**Interfaces:**
- Consumes: the Task 2 DOM contract (`.slide[data-block][data-block-title]`, `.rp-detail[data-tip][data-detail]`, `.rp-detail-store section[data-detail-id][data-title]`). Tests use a hand-written fixture with that markup and explicit `<link>`/`<script>` tags, so this task does not depend on Task 2's code.
- Produces:
  - `window.DeckOverlay = { init(framework), openSearch(), closeSearch(), openDetail(slideEl, id), closeDetail(), buildIndex(): Array<{index:number, block:string, blockTitle:string, title:string, text:string, detailText:string}> }`.
  - `SlideFramework.init()`'s `DOMContentLoaded` handler calls `if (window.DeckOverlay) window.DeckOverlay.init(this)` after `this.slides` is set and after `createSidebar()` (sidebar clones exist, so the index can exclude them) and before the first `ReactiveFit.fitAll()`.
  - `showSlide(index)` dispatches `document.dispatchEvent(new CustomEvent('rp:slidechange', { detail: { index } }))`.
  - The framework keydown handler (`slide-framework.js:465`) returns early when the target is `INPUT`/`TEXTAREA`/`SELECT` or `isContentEditable`, or when `document.body.classList.contains('rp-search-open')`.
  - Body classes: `rp-search-open`, `rp-agenda-open`, `rp-detail-open`. Element ids: `#rp-agenda`, `#rp-agenda-hotzone`, `#rp-search`, `#rp-search-input`, `#rp-search-results`, `#rp-tooltip`, `#rp-detail-panel`. Agenda: `.rp-agenda-block` groups, each with a header `.rp-agenda-block-title[data-goto]` (first slide index) and rows `.rp-agenda-row[data-goto]`; current row class `is-current`, current block `is-current-block`. Search rows: `.rp-search-row[data-goto]`.
  - `export-utils.js` `COMMON_FILES` includes `deck-overlay.js` and `deck-overlay.css`.

Behaviour (spec G1-G3): hot zone 64×64px fixed top-right; open on `mouseenter`, close 300ms after leaving zone+panel. Agenda groups slides by `data-block` (none → one group titled `document.title`); all groups expanded; current block/slide highlighted; click block header or row → `goTo`. Search opens on `(e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k'` or `/` (not when typing in inputs/contenteditable), `Esc` closes, `ArrowUp/Down` move, `Enter` → `goTo` and close; arrow/space inside the modal never reach the framework. Index built once from `.slide-deck > .slide`: title = first `h1, h2`; text = `textContent` excluding `.rp-detail-store` and `template.notes`; detailText = every store `section`'s `data-text` plus every `data-tip`. Case-insensitive substring; rank title > text > detail, then slide order; cap 20; row = block title, slide number, slide title, snippet with `<mark>`. All overlay text (rows, tooltip, panel title) set with `textContent`/text nodes; panel body clones the store `section`'s child nodes (compiler-generated HTML). Tooltip on `mouseenter`/`focus` of `.rp-detail`, hidden on leave/blur; on touch (`pointerdown` with `pointerType === 'touch'`) a tip-only term toggles its tooltip. A term with `data-detail` opens the panel on click or `Enter`; tip-only terms ignore mouse click. `init` sets `tabindex="0"` on any `.slide-deck > .slide .rp-detail` lacking it (raw-HTML terms). All term handlers are delegated from `.slide-deck` and only act on targets inside `.slide-deck > .slide`; terms inside sidebar thumbnails get `tabindex="-1"` so Tab skips them. The `::after` icon is CSS-only (Global Constraints). Panel: fixed right, overlays deck, closes on `Esc`, outside click, close button, `rp:slidechange`. Overview mode: CSS `body:has(.slide-deck.overview-mode) .rp-overlay-ui { display:none !important }` and hotkeys ignored while `.overview-mode` is present. Nav hint: new `SlideFramework.positionNavHint()` sets the hint's left offset to the visible logo's right edge + 16px (canvas px; logo hidden or absent: the CSS default). It runs after `createLogo()` in `init`, on the logo `<img>` `load` event, and at the end of `updateFooterVisibility()` (which hides the logo per slide). The existing inline `bottom: 2.2rem` for decks with a footer stays.

`export-utils.js` capture paths that screenshot or print the live page (PPTX image export and direct print, `export-utils.js:378-410,514-520`) inject the capture hide rule from Global Constraints for the duration of the capture.

- [ ] **Step 1: Write the failing tests** `reactive_overlay_test.py` (skip/serve pattern from Task 1; fixture A: two blocks × 3 slides; slide 1 has `UDP 8472` with `data-detail="vxlan"` plus a store section titled `UDP 8472가 필요한 이유`, and a tip-only term `data-tip="짧은 설명"`; slide 4 contains "VXLAN" only in body; slide 5 has `<input id="fixture-input">`; slide 6 has a notes template containing `notesonlyword`; one raw term `data-tip='<img src=x onerror="window.__xss=1">'` and store title the same; sidebar enabled; logo and footer configured. Fixture B: one block without `data-block`, 3 slides):

```python
def test_agenda_opens_on_hover_and_jumps(self):      # 2 .rp-agenda-block; click '.rp-agenda-row[data-goto="3"]' → active index 3; hover again: that row has is-current, its block is-current-block
def test_agenda_block_header_jumps_to_first_slide(self):  # click second '.rp-agenda-block-title' → active index 3
def test_agenda_single_block_lists_slides(self):    # fixture B: 3 '.rp-agenda-row' rows
def test_search_cmd_k_finds_body_text(self):        # Meta+K, type 'vxlan' → first '.rp-search-row' data-goto == '3' (4th slide); Enter → index 3, rp-search-open removed
def test_search_ctrl_k_and_slash_open(self):
def test_search_indexes_tips(self):                 # '짧은 설명' → row for slide 1
def test_search_excludes_notes_and_clones(self):    # 'notesonlyword' → 0 rows; 'VXLAN' → exactly 1 row with sidebar visible
def test_search_ignores_typing_in_inputs(self):     # focus #fixture-input, type '/k' → search closed, index unchanged; in search box ArrowRight keeps index
def test_tooltip_on_hover_tip_only(self):           # hover tip-only → '#rp-tooltip' text '짧은 설명'; click → panel stays closed
def test_icon_only_on_detail_terms(self):           # getComputedStyle(el,'::after').content != 'none' for [data-detail], == 'none' for tip-only
def test_icon_static_from_first_paint(self):        # data-fit-scale and term rect identical before and after hovering the term and opening/closing the panel
def test_thumbnail_terms_inert(self):              # '.slide-sidebar .rp-detail' all tabindex -1; hovering a thumbnail shows no tooltip
def test_click_term_with_detail_opens_panel(self):  # panel contains 'UDP 8472가 필요한 이유'
def test_panel_closes_on_slide_change(self):        # open, ArrowRight → closed and index + 1
def test_esc_closes_panel_and_search(self):
def test_tooltip_and_panel_title_are_text(self):    # hover/open the raw term: window.__xss undefined; no <img> inside #rp-tooltip or panel title
def test_touch_tap_toggles_tip(self):               # context has_touch=True; tap tip-only twice → visible then hidden
def test_overlay_hidden_in_overview(self):          # press 'o' → '#rp-agenda-hotzone' not visible; Meta+K does not open
def test_overlay_outside_slides(self):              # '.slide .rp-overlay-ui' count 0
def test_nav_hint_clear_of_logo(self):              # after logo load, rects of .nav-hint and .slide-logo do not intersect (fixture A with footer, and a variant without footer)
```

- [ ] **Step 2: Run to verify fail**

Run: `python3 tests/structure/reactive_overlay_test.py -v`
Expected: FAIL (no `#rp-agenda-hotzone`).

- [ ] **Step 3: Implement** `deck-overlay.js` (IIFE; only global is `window.DeckOverlay`), `deck-overlay.css` (token-only, both themes, `@media print { .rp-overlay-ui { display:none } }`, the overview rule, the `::after` icon), the `slide-framework.js` hooks and nav-hint positioning, and the `export-utils.js` list.

- [ ] **Step 4: Run to verify pass**

Run: `python3 tests/structure/reactive_overlay_test.py -v && for f in deck-overlay.js slide-framework.js export-utils.js; do node --check plugins/aws-content-plugin/skills/reactive-presentation/assets/$f; done`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/aws-content-plugin/skills/reactive-presentation/assets/deck-overlay.js plugins/aws-content-plugin/skills/reactive-presentation/assets/deck-overlay.css plugins/aws-content-plugin/skills/reactive-presentation/assets/slide-framework.js plugins/aws-content-plugin/skills/reactive-presentation/assets/export-utils.js tests/structure/reactive_overlay_test.py tests/structure/test-reactive-overlay.sh
git commit -m "feat(reactive-presentation): hover agenda, cmd-k search and detail layer"
```

---

### Task 4: Copy gates (EM_DASH, AI_TONE, SENTENCE_RUNON) and overlay hiding in measurement

**Files:**
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/scripts/measure_deck.py`
- Create: `tests/structure/remarp_copy_gates_test.py`
- Create: `tests/structure/test-remarp-copy-gates.sh`
- Create: `tests/structure/measure_runon_test.py`
- Create: `tests/structure/test-measure-runon.sh`

**Interfaces:**
- Consumes: Task 2's `_mask_code_spans`, `Slide.details` (`body`), `_mask_code_fences`; `_validate_slide`'s `add(severity, rule, message, fix)`; `slide.notes`.
- Produces: module constants `AI_TONE_LABELS = ("한 줄 정리", "핵심 정리", "핵심:", "Key takeaway")`, `AI_TONE_NOTE_CLICHES = ("꼭 기억해 두세요", "중요한 포인트는", "결론적으로")`, `AI_TONE_MAX_ARROWS = 3`, `AI_TONE_MAX_LABEL_REPEATS = 2`; `_validate_deck_tone(entries: List[Tuple[Slide, Path, str]]) -> List[Dict]` (slide, source file, block name; findings carry that file/block/slide like `_validate_slide`) called once from `validate_presentation` after all files are parsed (label repeats are deck-wide); measure rule `SENTENCE_RUNON` (WARN) added to `_DENSITY_RULES` (`measure_deck.py:536`).

- [ ] **Step 1: Write failing tests** `remarp_copy_gates_test.py` (same import pattern as `remarp_contract_test.py`):

```python
def test_em_dash_warns_in_body_notes_and_detail(self):
    for src in ("## T\n\nA — B\n", "## T\n\nx\n\n:::notes\n{timing: 1min}\n[요약]\n- a&mdash;b\n:::\n",
                '## T\n\n[a]{detail=d}\n\n:::detail d "t"\nx · y\n:::\n', "## T\n\n:::html\n<p>a &#8212; b</p>\n:::\n"):
        self.assertIn(('WARNING', 'EM_DASH'), rules(validate_text(src)))
def test_em_dash_skips_code_and_urls(self):
    for src in ("## T\n\n`a — b`\n", "## T\n\n```\na — b\n```\n", "## T\n\n[l](https://x.com/a—b)\n",
                "## T\n\n:::html\n<code>&mdash;</code><pre>a — b</pre>\n:::\n", '## T\n\n:::html\n<div id="a·b">x</div>\n:::\n'):
        self.assertNotIn('EM_DASH', rule_ids(validate_text(src)))
def test_em_dash_scans_visible_attributes(self):  # '<span class="rp-detail" data-tip="a — b">x</span>' and title="a — b" → EM_DASH
def test_ai_tone_arrows(self):        # 4 '→' → AI_TONE; 3 → none; '->' and '<!-- x -->' never count
def test_ai_tone_label_repeats_deck_wide(self):  # "한 줄 정리" on 3 slides across 2 files → exactly one WARNING; on 2 → none
def test_ai_tone_note_cliche(self):
def test_copy_gates_do_not_block_build(self):    # deck whose only findings are EM_DASH/AI_TONE: `build` exit 0
```

`measure_runon_test.py` (Playwright skip pattern; build a minimal deck from `RP/assets`, call `measure_deck.measure(...)` or the CLI with `--json --viewports 1920x1080 --themes light`):
- card `.card-desc` (width 560px): `Public-only 또는 Private-only 권장. "Public and Private"는 VPC 밖 노드에서 endpoint가 public IP로 해석되어 join이 실패할 수 있음` → one `SENTENCE_RUNON` WARN on that slide.
- card text `SNAT_EXCLUDE_CIDRS는 기존 제외 범위와 모든 hybrid Pod CIDR의 합집합입니다. Auto Mode는 aws-node DaemonSet이 없고, serviceAccount.annotations는 1.0.2에서 무시됩니다.` (width 560px) → one WARN.
- the first text split into two `<div>` lines → none; a single long sentence wrapping 3 lines → none.
- running with two viewports yields the WARN once (dedupe).
- `self.assertIn('.rp-overlay-ui', measure_deck._PREPARE_JS)` and `'.rp-detail::after'`.

- [ ] **Step 2: Run to verify fail**

Run: `python3 tests/structure/remarp_copy_gates_test.py -v; python3 tests/structure/measure_runon_test.py -v`
Expected: new tests FAIL.

- [ ] **Step 3: Implement.** `EM_DASH` pattern `—|·|・|&mdash;|&#8212;|&#x2014;|&middot;|&#183;|&#xb7;` over: slide Markdown after `_mask_code_fences` + `_mask_code_spans` + URL removal (`https?://\S+`); `:::html` blocks after removing `<code>…</code>`, `<pre>…</pre>`, HTML comments and the values of identifier-like attributes only (`id`, `class`, `href`, `src`, `style`, `data-detail`, `data-detail-id`, `data-block`, `data-fragment-index`, `data-goto`); visible-text attributes (`title`, `alt`, `aria-label`, `data-tip`, `data-title`) are scanned; notes; detail bodies. Arrows: count `→` in the same masked visible text only. `SENTENCE_RUNON` page-side: for each text block matching `p, li, td, .card-desc, .on-surface-muted, .callout > div` with no block-level children, ≥ 2 sentences (boundaries after `.`, `?`, `!` followed by a space) and ≥ 3 line boxes (distinct `top` of `Range.getClientRects()`), WARN when the first character after a boundary has `left > blockContentLeft + 1`. (Revised during implementation, 2026-10-18: the boundary-position condition missed the slide 31 report where the wrap happened to fall on the boundary; the rule is now ≥ 2 sentences and ≥ 3 line boxes in one leaf text block, regardless of where the boundary lands.) Add the Global Constraints capture hide rule to `_PREPARE_JS`. Update the module docstring check list.

- [ ] **Step 4: Run to verify pass**

Run: `python3 tests/structure/remarp_copy_gates_test.py -v && python3 tests/structure/measure_runon_test.py -v && python3 tests/structure/remarp_contract_test.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py plugins/aws-content-plugin/skills/reactive-presentation/scripts/measure_deck.py tests/structure/remarp_copy_gates_test.py tests/structure/test-remarp-copy-gates.sh tests/structure/measure_runon_test.py tests/structure/test-measure-runon.sh
git commit -m "feat(reactive-presentation): EM_DASH, AI_TONE and SENTENCE_RUNON copy gates"
```

---

### Task 5: Theme cleanup (callout accent bars)

**Files:**
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/assets/theme.css`
- Modify: `tests/structure/test-reactive-design-tokens.sh`

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: `.callout` (`theme.css:752-757`) and `.pain-quote` (`theme.css:1038`) without `border-left`; the `.callout.callout-*` variants (`theme.css:2152-2155`) set only `background` (existing `*-subtle` tokens), not `border-color`, so callouts keep the neutral `1px solid var(--surface-3)` primitive border; the variant's title (`strong`/first heading) takes the role colour.

- [ ] **Step 1: Write failing assertions** in `test-reactive-design-tokens.sh`:

```bash
TC_FLAT="$(tr '\n' ' ' < "$RP/assets/theme.css")"
assert_grep_no_match "\.callout\s*\{[^}]*border-left" "$TC_FLAT" ".callout has no left accent bar"
assert_grep_no_match "\.pain-quote\s*\{[^}]*border-left" "$TC_FLAT" ".pain-quote has no left accent bar"
assert_grep_no_match "\.callout\.callout-[a-z]+\s*\{[^}]*border-color" "$TC_FLAT" "callout variants do not colour the border"
assert_grep_match "\.callout\.callout-info\s*(:is\([^)]*\)|strong)" "$TC_FLAT" "callout variant title takes the role colour"
```

- [ ] **Step 2: Run to verify fail**

Run: `bash tests/run-all.sh design-tokens > /tmp/rp-t5.log 2>&1; grep -E "accent bar|colour the border|role colour" /tmp/rp-t5.log`
Expected: `not ok` lines.

- [ ] **Step 3: Implement** in `theme.css`; also remove any other decorative `border-left: Npx solid` / accent `border-top` bars on card-like primitives (keep 1px neutral dividers such as `border-top: 1px solid var(--border)`).

- [ ] **Step 4: Run to verify pass** (same command; `ok` lines).

- [ ] **Step 5: Commit**

```bash
git add plugins/aws-content-plugin/skills/reactive-presentation/assets/theme.css tests/structure/test-reactive-design-tokens.sh
git commit -m "style(reactive-presentation): drop callout accent bars and coloured outlines"
```

---

### Task 6: Docs, agent prompt, example deck, changelog

**Files:**
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/REMARP.md`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/references/remarp-format-guide.md`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/references/keyboard-shortcuts.md`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/references/authoring-rules.md`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/references/framework-contract.md`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/references/framework-guide.md`
- Modify: `plugins/aws-content-plugin/agents/reactive-presentation-agent.md`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/assets/example-deck/index.html`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/assets/example-deck/toc.html`
- Modify: `doc-sites/docs/aws-content-plugin/skills/reactive-presentation.md`
- Modify: `doc-sites/i18n/ko/docusaurus-plugin-content-docs/current/aws-content-plugin/skills/reactive-presentation.md`
- Modify: `doc-sites/docs/aws-content-plugin/agents/reactive-presentation-agent.md`
- Modify: `doc-sites/i18n/ko/docusaurus-plugin-content-docs/current/aws-content-plugin/agents/reactive-presentation-agent.md`
- Modify: `CHANGELOG.md`
- Test: `tests/structure/test-reactive-design-lint.sh`

**Interfaces:**
- Consumes: final names from Tasks 1-5 (`[text]{tip="..."}`, `[text]{detail=ID}`, `:::detail ID "Title"` + `tip:`, `⌘K`/`Ctrl+K`/`/`, `EM_DASH`, `AI_TONE`, `SENTENCE_RUNON`, `DETAIL_REF`, `deck-overlay.js/.css`, capture hide rule).
- Produces: documentation; the example deck demonstrates the feature.

- [ ] **Step 1: Write failing assertions** in `test-reactive-design-lint.sh`: `REMARP.md` and `remarp-format-guide.md` contain `:::detail` and `{tip=`; `keyboard-shortcuts.md` contains `Ctrl+K`; `authoring-rules.md` §2 rows name `EM_DASH`, `AI_TONE`, `SENTENCE_RUNON` and contain "one claim line"; the agent prompt contains `:::detail` and states that `EM_DASH` findings must be fixed in the authoring loop; `framework-guide.md` lists `deck-overlay.js`; the example deck links `deck-overlay.css`, loads `deck-overlay.js` before `slide-framework.js`, and has one `data-detail` term with its store section; all four doc-site pages contain `:::detail`, and the EN/KO skill pages share the `<span id="keyboard-shortcuts" />` anchor; the new doc sections contain no U+2014.
- [ ] **Step 2: Run to verify fail**: `bash tests/run-all.sh design-lint > /tmp/rp-t6.log 2>&1; grep "not ok" /tmp/rp-t6.log`.
- [ ] **Step 3: Write the docs.** `authoring-rules.md` §2: em dash row enforcement becomes `EM_DASH` (lint); add `AI_TONE` and `SENTENCE_RUNON` rows; add "card description = one claim line + optional one reason line; elaboration goes to `:::detail`". CHANGELOG `[Unreleased]` entries under `### Added`, `### Fixed`, `### Changed`. Then `cd doc-sites && npm run record:locales` after the KO pages are translated.
- [ ] **Step 4: Run to verify pass**: same command, no `not ok` for the new assertions.
- [ ] **Step 5: Commit**

```bash
git add plugins/aws-content-plugin/skills/reactive-presentation/REMARP.md plugins/aws-content-plugin/skills/reactive-presentation/references plugins/aws-content-plugin/agents/reactive-presentation-agent.md plugins/aws-content-plugin/skills/reactive-presentation/assets/example-deck/index.html doc-sites CHANGELOG.md tests/structure/test-reactive-design-lint.sh
git commit -m "docs(reactive-presentation): document detail layer, search and copy gates"
```

---

## Waves (file-disjoint)

- Wave 1: Task 1, Task 3, Task 5 (Task 3 creates the overlay assets Task 2 wires in)
- Wave 2: Task 2
- Wave 3: Task 4 (after Task 2: same `remarp_to_slides.py`), Task 6
- Host after Wave 3 (not a delegated task): show an unskipped run of `reactive_presenter_test.py`, `reactive_overlay_test.py`, `measure_runon_test.py`; `python3 scripts/sync-codex-plugins.py`, then commit `packages/claude` and `packages/codex`; run the root `CLAUDE.md` validation commands, `bash tests/run-all.sh`, the doc-site build and link checks from `doc-sites/CLAUDE.md`; build the example deck and run content-review-agent on it (PASS required before completion).
