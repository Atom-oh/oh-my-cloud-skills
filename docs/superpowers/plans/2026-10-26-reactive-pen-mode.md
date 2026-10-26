# Reactive-presentation pen mode: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a presenter draw on the live slide with a pen-shaped pointer (laser trail that fades after about 3 seconds, solid pen, highlighter, eraser, clear), with the same ink visible in the audience window and in the presenter window's current-slide preview.

**Architecture:** A new self-contained overlay module pair `deck-pen.js` / `deck-pen.css` registers with `DeckOverlay` like `deck-detail` and `deck-nav`. One ink model lives in the deck (main) window; both windows render it onto their own transparent canvas from slide-relative 0..1 coordinates, so no extra sync channel is needed. The presenter window already shares objects with the main window (`PresenterView` reads `this.framework` directly), so the pen controller attaches listeners to the presenter document from the main window's code.

**Tech Stack:** Vanilla JS/CSS (no dependency), Node `vm` for model unit tests, Playwright for Python for browser tests (skipped when unavailable), TAP shell runner.

**Spec:** none. The design was agreed in chat on 2026-10-26 (this plan's Global Constraints and key table are the contract). Precedent for adding an overlay module: `docs/superpowers/plans/2026-10-18-reactive-nav-detail.md`.

## Global Constraints

- Skill root: `plugins/aws-content-plugin/skills/reactive-presentation` (written `RP/`). Never hand-edit `packages/*`; regenerate with `python3 scripts/sync-codex-plugins.py --plugin aws-content-plugin`.
- Work on a new branch `feat/reactive-pen-mode` from `origin/main` in its own worktree under `/home/atomoh/worktrees/`, not on `feat/audience-hover-explanations`.
- Vanilla JS/CSS only; no CDN. New CSS uses theme tokens only (no raw hex or rgba); the pen palette is JS constants because canvas strokes cannot read CSS tokens.
- Key map (exact). Every pen key is an `Option` (Alt) chord, matched by `event.code` with `altKey` and no `ctrlKey`/`metaKey`, never by `event.key` (which is `π`, `ø` and similar on macOS, and the plain letter on Linux/Windows). No existing framework shortcut uses Alt, so plain keys keep working at all times, including while pen mode is on. Shift and Ctrl are not used: the framework maps `'P'`, `'O'`, `'S'` the same as lowercase (Shift would collide), and browsers own `Ctrl+P/O/U` and `Ctrl+1-9`.
  - `Option+P`: Laser (strokes fade over `fadeMs`, default 3000). Pen mode off: turns it on in Laser. On in another mode: switches to Laser. Already on in Laser: turns pen mode off.
  - `Option+O` Pen (stays), `Option+I` Highlighter (translucent, 3x width, stays), `Option+U` Eraser (removes whole strokes under the pointer); each turns pen mode on if it is off. `Option+Y` clears all ink on the current slide.
  - `Option+1` `Option+2` `Option+3` thin, medium, thick (4, 8, 16 slide units on a 1920-unit-wide slide). `Option+4` red, `Option+5` yellow, `Option+6` green, `Option+7` blue, `Option+8` white, `Option+9` black. Default red, medium; Highlighter defaults to yellow while no colour was chosen for it.
  - Plain `Esc` leaves pen mode (consumed only while pen mode is on, so it does not also exit fullscreen). Arrow keys, Space, PageUp/Down, `P`, `O`, `S`, `1`-`9` keep their normal meaning.
- Every Alt chord above is consumed in the capture phase with `preventDefault()` and `stopImmediatePropagation()` so the framework's plain-letter handlers never see it (on Linux/Windows `Option+P` reports `key === 'p'`). Chords typed into INPUT, TEXTAREA, SELECT or contenteditable are ignored. Known limit, not verified here: Chrome and Firefox on Linux may reserve `Alt+1-9` for tab switching before the page sees it; document it instead of working around it.
- Persistent ink (Pen, Highlighter) is stored per slide and redrawn when the slide is shown again; Laser ink is dropped on slide change. Nothing is written to disk.
- Coordinates are stored as 0..1 of the slide box. The deck window maps through `deck.getBoundingClientRect()`; the presenter window maps through its scaled preview rectangle.
- The canvases and the status badge are children of `document.body` (deck window) or of `#p-current-wrap` (presenter window), carry class `rp-overlay-ui` (so capture and export hide them via the existing hide rule), and are never inserted into `.slide`. `pointer-events` is `none` unless pen mode is on.
- Options via `new SlideFramework({ pen: { fadeMs: 3000, audienceBadge: true } })`. Defaults shown. `audienceBadge: false` hides the mode badge in the deck window only; the presenter window always shows it.
- No em dash (U+2014) or middle dot (U+00B7, U+30FB) in any copy, docs or UI strings added by this plan.
- Internal docs in English. Public `doc-sites/` shortcut docs updated in EN and KO with matching anchors, then `npm run record:locales` (run `node scripts/check-guide-locales.cjs` from `doc-sites/`).
- Browser tests skip without Playwright; the host must show one unskipped run of each new browser test in the log.
- Each task's own verification runs only its tests; the host runs `bash tests/run-all.sh`, `python3 scripts/test-plugins.py`, `python3 scripts/test-codex-plugins.py`, `python3 scripts/sync-codex-plugins.py --check` after Task 4.

## Review Focus

1. `Option+P` on Linux/Windows reports `event.key === 'p'`; it must toggle pen mode and must not open the presenter window, and the same holds for every other Alt chord (`Option+O` must not toggle overview, `Option+S`-like chords must not reach the framework). Pinned by `test_option_chords_do_not_trigger_framework_keys` (Task 2).
2. Plain `P`, `O`, `S`, `1`-`9` keep their framework meaning with pen mode on and off (presenter opens, overview toggles, slide jumps); plain `Esc` while pen mode is on only leaves pen mode. Pinned by `test_plain_keys_keep_working_in_pen_mode` (Task 2).
3. The presenter preview re-renders on every fragment change and resize (`_renderSlidePreview` empties `#p-current`). Ink in the presenter window must survive and stay aligned after a re-render and after a splitter drag. Pinned by `test_presenter_ink_survives_preview_rerender` (Task 3).
4. Typing in the search box or a quiz input while pen mode is on must not change pen settings. Pinned by `test_pen_ignores_typing_targets` (Task 2).
5. A stroke drawn at one window size and ratio must land at the same slide position in the other window (4:3 deck, resized window, fullscreen). Pinned by `test_ink_position_matches_across_windows_and_ratios` (Task 3).
6. The render loop must stop when nothing is animating (no idle `requestAnimationFrame` spin after laser ink has expired). Pinned by `test_render_loop_stops_when_idle` (Task 1, model) and `test_canvas_loop_idle` (Task 2).

---

### Task 1: Ink model and renderer (`deck-pen.js`, pure core)

**Files:**
- Create: `RP/assets/deck-pen.js`
- Test: `tests/structure/reactive_pen_model.test.cjs`, `tests/structure/test-reactive-pen.sh`

**Interfaces:**
- Produces, on `window.DeckPen` (and `module.exports` when `typeof module !== 'undefined'`, so the Node test can load it with `vm`):
  - `MODES = ['laser','pen','highlighter','eraser']`, `SIZES = {1: 4, 2: 8, 3: 16}`, `PALETTE = ['#e53935','#fdd835','#43a047','#1e88e5','#ffffff','#000000']` (index 0..5 for keys 4..9), `HIGHLIGHTER_ALPHA = 0.35`, `HIGHLIGHTER_WIDTH_FACTOR = 3`.
  - `createModel({ fadeMs = 3000, now = () => Date.now() }) -> Model`.
  - `Model`: `mode`, `size` (1|2|3), `colorIndex`; `setMode(name)`, `setSize(n)`, `setColor(i)` (ignore invalid input); `begin(slide, x, y) -> id`, `extend(x, y)`, `end()`; `eraseAt(slide, x, y, radius = 0.02) -> removedCount`; `clear(slide)`; `showSlide(slide)` (drops Laser strokes, keeps persistent ones); `visible(slide) -> [{ mode, size, colorIndex, points: [{x, y, alpha}] }]` (Laser point alpha = `1 - age / fadeMs`, points with alpha <= 0 pruned; persistent alpha = 1); `animating(slide) -> boolean` (true while any Laser point is alive or a stroke is open).
  - `render(ctx, width, height, strokes)`: clears the canvas, draws each stroke as a round-capped polyline; stroke width = `SIZES[size] * width / 1920` (times `HIGHLIGHTER_WIDTH_FACTOR` for Highlighter); Highlighter draws with `globalAlpha = HIGHLIGHTER_ALPHA`; Laser draws per-segment with the segment's point alpha.
  - `cursorFor(colorIndex, size) -> string`: a CSS `cursor` value using an inline SVG data URI of a pen tip tinted with the palette colour, hotspot at the tip.

- [ ] **Step 1: Write the failing tests** in `tests/structure/reactive_pen_model.test.cjs` (Node `node:test`, load `deck-pen.js` through `vm.runInNewContext` with a `window` stub and an injected clock): `test_laser_points_fade_and_expire` (alpha at 0, 1500, 3000 ms is 1, 0.5, 0 and the point is pruned at 3000), `test_persistent_strokes_never_expire`, `test_show_slide_drops_laser_keeps_pen_per_slide` (draw pen on slide 0, laser on slide 0, `showSlide(1)`, `showSlide(0)`: only the pen stroke is back), `test_erase_removes_whole_stroke_under_pointer_only`, `test_clear_only_affects_the_given_slide`, `test_invalid_size_color_mode_are_ignored`, `test_highlighter_defaults_to_yellow_until_a_colour_is_chosen`, `test_render_loop_stops_when_idle` (`animating` is false once every laser point expired and no stroke is open), `test_render_scales_width_with_canvas` (a recording ctx stub sees `lineWidth` 8 at width 1920 and 4 at width 960 for size 2).
- [ ] **Step 2: Run to verify failure.** Run: `node --test tests/structure/reactive_pen_model.test.cjs`. Expected: FAIL (file not found).
- [ ] **Step 3: Implement `deck-pen.js`** with the interface above. Only the model, `render` and `cursorFor` in this task; no DOM access at load time. Hit test for `eraseAt` is point-to-segment distance in normalized units.
- [ ] **Step 4: Run to verify pass.** Run: `node --test tests/structure/reactive_pen_model.test.cjs` and `node --check RP/assets/deck-pen.js`. Expected: all tests pass.
- [ ] **Step 5: TAP wrapper** `tests/structure/test-reactive-pen.sh` (sourced by `run-all.sh`, no shebang or exit; mirror `test-reactive-detail.sh`): `pass`/`fail` for the Node model test and a `node --check` assertion for `deck-pen.js`. Add the browser test hook in Task 2.
- [ ] **Step 6: Commit** `feat(reactive-presentation): add pen ink model and renderer`.

### Task 2: Deck-window pen UI (overlay module, keys, canvas, badge)

**Files:**
- Modify: `RP/assets/deck-pen.js` (append the DOM controller), `RP/assets/slide-framework.js` (accept `pen` option, default `{ fadeMs: 3000, audienceBadge: true }`, expose it as `this.options.pen` or the constructor's existing options store)
- Create: `RP/assets/deck-pen.css`
- Test: `tests/structure/reactive_pen_test.py`, `tests/structure/reactive_overlay_fixture.py` (add `"pen"` to the overlay modules it can load, same pattern as `detail`/`nav`), `tests/structure/test-reactive-pen.sh`

**Interfaces:**
- Consumes: Task 1 `createModel`, `render`, `cursorFor`; `DeckOverlay.register(name, { priority, init(framework, deck), keydown, slideChange })`; `framework.currentSlide`, `framework.getDeck()`.
- Produces: `DeckPen.attachSurface({ doc, canvas, getRect, isPrimary }) -> { redraw(), destroy() }` where `getRect() -> { left, top, width, height }` in that window's viewport pixels and `isPrimary` tells the surface to also own key handling; `DeckPen.controller` (singleton created in `init`) with `model`, `togglePen()`, `active`, `onChange(fn)` and `handleKey(event) -> boolean` (true when consumed); `register('pen', { priority: 0, init, slideChange })` so the controller calls `model.showSlide(framework.currentSlide)` on `rp:slidechange`.

- [ ] **Step 1: Write the failing browser tests** in `tests/structure/reactive_pen_test.py` (subclass `DeckOverlayFixture` with `overlay_modules = ("pen",)`; construct the deck with `pen: { fadeMs: 300 }` so fades are fast): `test_option_p_toggles_pen_and_does_not_open_presenter` (dispatch `keydown` with `altKey`, `code: 'KeyP'`, once with `key: 'π'` and once with `key: 'p'`; assert pen mode on, then off on a second press while still Laser, and no popup), `test_option_chords_do_not_trigger_framework_keys` (`Option+O/I/U/Y/1/4` with the plain-letter `key` values: no popup, no `overview-mode` class, slide unchanged), `test_plain_keys_keep_working_in_pen_mode` (pen mode on: plain `o` toggles overview, plain `3` jumps to slide 3, plain `Esc` only leaves pen mode), `test_drawing_in_pen_mode_paints_the_canvas_and_does_not_navigate` (pointer down/move/up on the deck; canvas has non-transparent pixels; click did not advance the slide), `test_laser_fades_and_pen_persists` (laser ink gone after 400 ms; pen ink still there; slide change then back restores only the pen ink), `test_mode_size_colour_keys` (`Option+O`, `Option+3`, `Option+5`: `controller.model` reports pen, size 3, colorIndex 1; `Option+I` while pen mode is off turns it on in Highlighter), `test_eraser_removes_one_stroke_and_option_y_clears`, `test_pen_ignores_typing_targets` (focus an input, press `Option+O` and `Option+U`, mode unchanged), `test_canvas_loop_idle` (after ink expired, no pending animation frames: wrap `requestAnimationFrame` and assert none is requested for 200 ms), `test_badge_shows_mode_and_hides_for_audience_when_disabled`, `test_canvas_and_badge_are_overlay_ui_and_pointer_inert_when_off` (class `rp-overlay-ui`, computed `pointer-events` `none` while pen mode is off).
- [ ] **Step 2: Run to verify failure.** Run: `python3 tests/structure/reactive_pen_test.py`. Expected: FAIL (module missing) or SKIP only when Playwright is unavailable.
- [ ] **Step 3: Implement the controller in `deck-pen.js`:** body-level `<canvas class="rp-overlay-ui rp-pen-canvas">` sized to `deck.getBoundingClientRect()` on init, `rp:slidechange`, window resize, and when the deck's inline `style` changes (the deck scale lives there; reuse a `MutationObserver` like `deck-overlay.js` does); a capture-phase `document` keydown listener implementing the Option-chord key map and consumption rules from Global Constraints (plain keys are never touched except `Esc` while pen mode is on); pointer events on the canvas (`setPointerCapture`) converting to normalized coordinates and calling the model; a `requestAnimationFrame` loop that runs only while `model.animating(slide)` or the pointer is down, redrawing via `render`; cursor from `cursorFor` applied to the canvas whenever mode, size or colour changes (Eraser uses `cursor: cell`); a body-level badge `<div class="rp-overlay-ui rp-pen-badge">` showing mode name, size and a colour swatch, hidden when pen mode is off or when `pen.audienceBadge === false`. Register with the overlay core as `register('pen', ...)`. Export `attachSurface` and `controller` as specified.
- [ ] **Step 4: Implement `deck-pen.css`** (theme tokens only): `.rp-pen-canvas { position: fixed; pointer-events: none; z-index: <above slides, below tooltip/detail panel; read the z-index scale in deck-overlay.css> }`, `.rp-pen-canvas.active { pointer-events: auto }`, badge styling matching the existing overlay chrome (no gradients or colour bars).
- [ ] **Step 5: Add `pen` option plumbing in `slide-framework.js`** (defaults merged, unknown keys ignored) without changing any other behaviour.
- [ ] **Step 6: Run to verify pass.** Run: `python3 tests/structure/reactive_pen_test.py`, `node --check RP/assets/deck-pen.js`, `python3 tests/structure/reactive_nav_test.py`, `python3 tests/structure/reactive_detail_test.py` (existing overlay tests must stay green). Expected: PASS, or a visible SKIP only without Playwright.
- [ ] **Step 7: Extend `test-reactive-pen.sh`** with the browser test result (copy the skip handling from `test-reactive-detail.sh`) and add `deck-pen.js` to its `node --check` loop.
- [ ] **Step 8: Commit** `feat(reactive-presentation): draw on slides with a pen overlay`.

### Task 3: Presenter-window surface

**Files:**
- Modify: `RP/assets/presenter-view.js`, `RP/assets/deck-pen.js`
- Test: `tests/structure/reactive_presenter_test.py` (add cases; reuse its popup helper), `tests/structure/reactive_pen_test.py`

**Interfaces:**
- Consumes: Task 2 `DeckPen.attachSurface`, `DeckPen.controller`; `PresenterView._canvasSize()`, `_applyScale`, `_updateAllScales`, `window.__pvScaleUpdate`, `this.presenterWindow.document`.
- Produces: `PresenterView._pen` (the surface handle, created in `open()` after `setupPresenterControls()` when `window.DeckPen` exists, destroyed when the presenter window closes) and `PresenterView._penRect()` returning the viewport rectangle of the scaled current-slide area inside `#p-current` using the same maths as `_applyScale` (`min(containerW / canvas.w, containerH / canvas.h)`, centred).

- [ ] **Step 1: Write the failing tests:** `test_presenter_ink_survives_preview_rerender` (draw in the presenter preview, trigger `updatePresenterView()` and a fragment change, ink still painted and `canvas` still attached), `test_ink_drawn_in_presenter_appears_in_deck_window_at_same_slide_position` (draw from the presenter canvas at the preview's centre; the deck canvas has ink at the deck's centre within 2 px of the normalized position), `test_ink_position_matches_across_windows_and_ratios` (repeat for a 4:3 deck and after resizing the presenter window), `test_presenter_keys_toggle_pen_and_navigation_still_works` (Option+P in the presenter document toggles the same controller state; ArrowRight there still advances), `test_presenter_badge_always_visible_when_pen_on` (also when `audienceBadge: false`), `test_closing_presenter_window_keeps_deck_ink`.
- [ ] **Step 2: Run to verify failure.** Run: `python3 tests/structure/reactive_presenter_test.py && python3 tests/structure/reactive_pen_test.py`. Expected: new cases FAIL.
- [ ] **Step 3: Implement.** In `presenter-view.js` create a `<canvas class="rp-overlay-ui rp-pen-canvas">` appended to `#p-current-wrap` (a sibling of `#p-current`, so `_renderSlidePreview`'s `container.innerHTML = ''` cannot remove it); call `DeckPen.attachSurface({ doc, canvas, getRect: () => this._penRect(), isPrimary: false })`; make `_updateAllScales()` and `_renderSlidePreview()` for `p-current` call `this._pen && this._pen.redraw()`; each surface draws with its own window's `requestAnimationFrame`. Add the presenter document's capture-phase keydown handler that forwards to `DeckPen.controller.handleKey(event)` before the existing arrow handler. Inject the pen canvas/badge styles into the presenter HTML (`createPresenterHTML`) from `deck-pen.css` the same way `_collectStyleSheets` copies the main stylesheets.
- [ ] **Step 4: Implement the pointer path** so a pointer on the presenter canvas calls the shared model with coordinates normalized against `getRect()`, then asks every surface to `redraw()`.
- [ ] **Step 5: Run to verify pass.** Run the two test files above plus `python3 tests/structure/reactive_overlay_fixture.py` consumers (`reactive_nav_test.py`, `reactive_detail_test.py`). Expected: PASS.
- [ ] **Step 6: Commit** `feat(reactive-presentation): mirror pen ink in the presenter preview`.

### Task 4: Wire assets, docs and gates

**Files:**
- Modify: `RP/scripts/remarp_to_slides.py` (head template near line 4624 and script tags near 4637; copy list near 5024; add `deck-pen.css`/`deck-pen.js`, loaded after `deck-nav` and before `slide-framework.js`), `RP/assets/export-utils.js` (`COMMON_FILES` near line 57; PDF head near line 143), `RP/assets/example-deck/index.html`, `RP/scripts/check_deck.py` (only if it lists common assets), `RP/references/keyboard-shortcuts.md`, `RP/references/framework-contract.md`, `RP/references/framework-guide.md`, `RP/SKILL.md` (line with viewer shortcuts), `doc-sites/docs/aws-content-plugin/usage-guide.md` and its KO locale counterpart, `CHANGELOG.md`
- Test: `tests/structure/remarp_contract_test.py` (assert generated HTML references the pen assets in order), `tests/structure/test-reactive-design-lint.sh` (must still pass), `tests/structure/test-reactive-pen.sh`

**Interfaces:**
- Consumes: Tasks 1-3 files. Produces: generated decks and the example deck load the pen module; docs list the key table from Global Constraints verbatim.

- [ ] **Step 1: Write the failing contract tests:** in `remarp_contract_test.py`, a compiled single-file deck contains `./common/deck-pen.css` and `./common/deck-pen.js` after `deck-nav` and before `slide-framework.js`, and `common/deck-pen.js` and `common/deck-pen.css` are copied; a test that `export-utils.js` `COMMON_FILES` includes both. Run: `python3 tests/structure/remarp_contract_test.py`. Expected: FAIL.
- [ ] **Step 2: Implement the wiring** in the three code locations and the example deck; keep decks generated before this change working (the framework treats a missing `DeckPen` as no pen).
- [ ] **Step 3: Update docs.** `keyboard-shortcuts.md` gains a "Pen mode" section with the exact key table, a note that every pen key is an Option (Alt) chord so plain keys (`P`, `O`, `S`, `1`-`9`) are unchanged, that plain Esc leaves pen mode, and the Linux `Alt+1-9` tab-switch caveat; framework-contract and framework-guide gain the `deck-pen` entries and the `pen` option; `SKILL.md` shortcut line mentions Option+P; public usage guide EN and KO get the same table with matching anchors. CHANGELOG entry under Unreleased.
- [ ] **Step 4: Verify.** Run, redirecting to a log under `/home/atomoh/.tmp` and grepping it: `python3 scripts/sync-codex-plugins.py --plugin aws-content-plugin`, `python3 scripts/sync-codex-plugins.py --check`, `bash tests/run-all.sh`, `python3 scripts/test-plugins.py`, `python3 scripts/test-codex-plugins.py`, `python3 scripts/eval-skills.py`, then from `doc-sites/`: `npm run record:locales` and `node scripts/check-guide-locales.cjs`, and the doc-sites build and link checks described in `doc-sites/CLAUDE.md`. Expected: all pass with 0 failed.
- [ ] **Step 5: Manual check** (host, with a real browser): open the example deck, press Option+P, draw with each mode, open the presenter window with `P` first, confirm ink appears in both. Record what was and was not checked in the PR body.
- [ ] **Step 6: Commit** `feat(reactive-presentation): ship pen mode in generated decks and docs`, then push and open the PR.
