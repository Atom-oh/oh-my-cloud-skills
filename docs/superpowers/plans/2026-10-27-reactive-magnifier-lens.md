# Reactive-presentation magnifier lens and footer spacing: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a magnifier lens to reactive-presentation pen mode (a round lens that follows the mouse and shows the slide enlarged 2x/3x/4x, mirrored in the audience window and the presenter preview), and fix the default footer text colliding with the logo.

**Architecture:** The lens is one more pen-mode mode (`magnifier`) owned by the existing `DeckPen.controller`; it draws nothing, it only tracks a slide-relative pointer position and a zoom. Each surface (deck window, presenter preview) renders a lens element holding a clone of the active slide scaled around the pointer. All code lives in `deck-pen.js` / `deck-pen.css`, so no new asset has to be wired into the compiler, exports, fixtures or packages beyond regeneration. The footer fix is independent and lives in `slide-framework.js` / `theme.css`.

**Tech Stack:** Vanilla JS/CSS (no dependency), Node `vm` for model unit tests, Playwright for Python for browser tests (skipped when unavailable), TAP shell runner.

**Spec:** none. Design agreed in chat on 2026-10-27 (key map below is the contract). Predecessor: `docs/superpowers/plans/2026-10-26-reactive-pen-mode.md` (merged as #282); read it for the pen architecture.

## Global Constraints

- Skill root: `plugins/aws-content-plugin/skills/reactive-presentation` (written `RP/`). Never hand-edit `packages/*`; regenerate with `python3 scripts/sync-codex-plugins.py --plugin aws-content-plugin` and commit with the change (run-all has an "adapters match source" check).
- Work in the worktree `/home/atomoh/worktrees/magnifier` on branch `feat/reactive-magnifier` (from `origin/main` at d102d3eb, which includes pen mode).
- Vanilla JS/CSS only. New CSS uses theme tokens only (no raw hex or rgba). No em dash (U+2014) or middle dot (U+00B7, U+30FB) in anything added. Internal docs in English; public `doc-sites/` pages in EN and KO with matching anchors, then `npm run record:locales` and `node scripts/check-guide-locales.cjs` from `doc-sites/` (symlink `doc-sites/node_modules` from `/home/atomoh/oh-my-cloud-skills/doc-sites/node_modules` in the worktree if absent; it is git-ignored).
- Key map change (exact). Pen keys stay Option (Alt) chords matched by `event.code` with `altKey` and no ctrl/meta. Existing: `Option+P` Laser (on / switch to Laser / off), `O` Pen, `I` Highlighter, `U` Eraser, `1/2/3` size, `4`-`9` colour, plain Esc leaves pen mode. Changed or new:
  - `Option+Y` selects Magnifier (turns pen mode on if off). Pressing it while Magnifier is the current mode does nothing special (it is not a toggle; leave with `Option+P/O/I/U`, `Esc`).
  - `Option+T` clears all ink on the current slide (moved from `Option+Y`).
  - In Magnifier mode `Option+1/2/3` set zoom 2x/3x/4x (default 2x) and do not change the pen size; `Option+4`-`9` do nothing there. Zoom is remembered and shown in the badge ("Magnifier 2x").
- Magnifier behaviour: the lens is a circle (diameter 28% of the slide height, centred on the pointer, clamped so it stays fully inside the slide box), `pointer-events: none`, class `rp-overlay-ui` (hidden by the existing capture/export rule), never inside `.slide`. It shows the active slide content enlarged around the pointer position, with the pointer position at the lens centre. No clicks or strokes happen in Magnifier mode (pen `begin` returns null like Eraser). The lens appears at the pointer when the mouse moves over the slide in that window and hides when the pointer leaves or the mode changes. Pen ink is part of the magnified picture (copy the pen canvas into the lens) in the deck window and presenter preview.
- Mirroring: pointer position is stored once as 0..1 slide coordinates in the controller; every surface draws its own lens at the same slide position (pointer over the presenter preview shows the lens in the audience window and the reverse).
- The lens clone must be inert: `inert` and `aria-hidden="true"` on the lens, all `id` attributes removed from the clone, no scripts executed. Canvas elements in the slide clone do not copy their bitmap, so while the lens is visible the lens copies each source canvas into its clone with `drawImage` on the surface's own `requestAnimationFrame`; iframes and videos are cloned as plain elements (iframes reload, video shows its poster): document this limit.
- Re-clone the active slide when the slide changes, on fragment/class changes in the active slide (debounced about 50 ms, same idea as `PresenterView._observeCurrentSlide`), and on resize; never per frame. The animation loop runs only while the lens is visible and canvases need copying, and stops when idle.
- Overview mode: no lens (the surface is inert there, as for ink).
- Footer fix (independent of the lens): the default footer position must follow the logo width instead of a fixed 70px. Decks whose `theme-override.css` sets `.slide-footer { left: ... }` must keep their layout exactly.
- Browser tests skip without Playwright; Playwright for Python and Chromium are installed here, so the host requires unskipped runs and the report must show the commands and result lines.

## Review Focus

1. The footer must never overlap the logo with any logo width (53px AWS logo, a 120px wide logo, no logo), and a deck override that sets `left` keeps winning. Pinned by `test_footer_follows_logo_width_and_override_still_wins` (Task 1).
2. Plain `Option+Y` no longer clears ink, and `Option+T` does; `Option+1/2/3` in Magnifier mode change zoom only and leave pen size unchanged, and switching back to Pen restores the previous size and colour. Pinned by `test_clear_moved_to_option_t_and_digits_mean_zoom_in_magnifier` (Task 2).
3. The lens shows the right part of the slide: the pixel at the lens centre equals the slide pixel under the pointer, magnified by the zoom, at 16:9 and 4:3 and after the window is resized. Pinned by `test_lens_centre_shows_the_slide_point_under_the_pointer` (Task 3).
4. The lens never receives pointer events and never changes slide state: no tooltip, hover, click, drag or navigation reaches the clone; ids in the clone do not collide with the live slide. Pinned by `test_lens_is_inert_and_clone_has_no_ids` (Task 3).
5. The lens follows slide changes, fragment reveals and Canvas animation (a canvas redraw shows up inside the lens), and no rAF loop runs when the lens is hidden. Pinned by `test_lens_tracks_fragments_and_copies_canvas_frames` and `test_lens_loop_stops_when_hidden` (Task 3).
6. Pointer over the presenter preview shows the lens in the audience window at the same slide position and the reverse; closing the presenter window leaves the deck lens working. Pinned by `test_lens_mirrors_between_windows` (Task 4).

---

### Task 1: Footer spacing follows the logo

**Files:**
- Modify: `RP/assets/theme.css` (`.slide-footer` rule near the logo rules), `RP/assets/slide-framework.js` (`positionNavHint` neighbourhood; the logo `load` handler and `updateFooterVisibility` logo swap)
- Test: `tests/structure/reactive_fit_test.py` or a new `tests/structure/reactive_footer_test.py` (follow how existing browser tests build pages; wrap in a TAP shell file `tests/structure/test-reactive-footer.sh` if a new file is created, mirroring `test-reactive-pen.sh`)

**Interfaces:**
- Consumes: `SlideFramework` options `footer`, `logoSrc`, `logoDarkSrc`; existing `.slide-logo` and `.slide-footer` elements and `positionNavHint()`.
- Produces: CSS custom property `--rp-footer-left` set on `.slide-footer` by the framework to `logo.offsetLeft + logo.offsetWidth + 16` (px) whenever the logo loads, its `src` swaps, or the deck rescales; default rule `.slide-footer { left: var(--rp-footer-left, 96px); }` so a deck override `.slide-footer { left: Npx }` (later stylesheet, same specificity) still wins.

- [ ] **Step 1: Write the failing test** `test_footer_follows_logo_width_and_override_still_wins`: build three pages with the fixture pattern (logo 53px wide, logo 120px wide, no logo) and assert `footer.getBoundingClientRect().left - logo.getBoundingClientRect().right >= 12` in deck pixels (use `offsetLeft` and `offsetWidth` to stay independent of the deck scale) for the first two, `footer.offsetLeft === 96` with no logo, and a fourth page whose stylesheet sets `.slide-footer { left: 200px }` keeps `offsetLeft === 200`. Also assert the swap case: after a light-to-dark slide change the footer offset is recomputed.
- [ ] **Step 2: Run to verify failure.** Run the new test file. Expected: FAIL (gap is -3 for the 53px logo).
- [ ] **Step 3: Implement.** In `theme.css` change the default footer `left` to `var(--rp-footer-left, 96px)` (keep every other declaration). In `slide-framework.js` add `positionFooter()` that sets the property on the footer element from the logo box (remove it when there is no logo or the logo is `display:none`), call it from the logo `load` handler, from `updateFooterVisibility` after a logo swap, from `positionNavHint`'s callers on resize/scale changes (reuse the existing hooks; do not add a new listener if one already runs on scale changes), and make `positionNavHint` and `positionFooter` share the `logo.offsetLeft + logo.offsetWidth + 16` maths.
- [ ] **Step 4: Run to verify pass**, then run `python3 tests/structure/reactive_nav_test.py`, `reactive_detail_test.py`, `reactive_pen_test.py`, `reactive_presenter_test.py` (must stay green).
- [ ] **Step 5: Regenerate packages, commit** `fix(reactive-presentation): place the footer after the logo instead of a fixed offset`.

### Task 2: Magnifier mode, key map and badge (no lens drawing yet)

**Files:**
- Modify: `RP/assets/deck-pen.js` (model modes, controller keys and state, badge text), `RP/assets/deck-pen.css` only if the badge needs a style
- Test: `tests/structure/reactive_pen_model.test.cjs`, `tests/structure/reactive_pen_test.py`

**Interfaces:**
- Consumes: Task 1 of the pen plan's model and controller (`createModel`, `createController`, `chordAction`, `selectMode`, `buildBadge`, `MODE_LABELS`, `MODE_CODES`).
- Produces: `DeckPen.MODES` gains `'magnifier'` (after `'eraser'`); `model.begin()` returns null in magnifier mode like eraser; `model.zoom` (2, 3 or 4; default 2) with `model.setZoom(n)` (ignores other values); controller state `lens` = `{ x: number, y: number, visible: boolean }` with `controller.setLens(x, y, visible)` (0..1 slide coordinates, emits change and calls `schedule()`), `controller.lens`; key map as in Global Constraints (`Option+Y` magnifier, `Option+T` clear, digits `1-3` mean zoom while the mode is magnifier and size otherwise, `4-9` ignored in magnifier mode); badge text "Magnifier 2x" with a neutral swatch; `controller.setActive(false)` and every mode change hide the lens (`visible: false`).

- [ ] **Step 1: Write the failing tests.** Model: `test_magnifier_mode_creates_no_stroke_and_remembers_zoom` (begin returns null, setZoom(3) then setMode away and back keeps 3, setZoom(5) ignored). Browser: `test_clear_moved_to_option_t_and_digits_mean_zoom_in_magnifier` (Option+Y selects magnifier and turns pen on; Option+Y does not clear ink; Option+T clears ink; in magnifier Option+2 sets zoom 3 and pen size unchanged, Option+5 ignored; Option+O restores the previous pen size and colour), `test_badge_shows_magnifier_and_zoom`, `test_changing_mode_hides_the_lens_state`.
- [ ] **Step 2: Run to verify failure.** Run: `node --test tests/structure/reactive_pen_model.test.cjs` and `python3 tests/structure/reactive_pen_test.py`. Expected: new cases FAIL.
- [ ] **Step 3: Implement** in `deck-pen.js` per the interface; keep Esc, typing-target and dead-key (keyCode 229) handling untouched; update the badge builder to show zoom instead of size/colour for magnifier.
- [ ] **Step 4: Run to verify pass** including the existing pen and presenter tests; update any existing test that used `Option+Y` for clear to `Option+T`.
- [ ] **Step 5: Regenerate packages, commit** `feat(reactive-presentation): add magnifier mode and move clear to Option+T`.

### Task 3: Lens rendering in the deck window

**Files:**
- Modify: `RP/assets/deck-pen.js` (lens surface part of `attachSurface` and the deck initialiser), `RP/assets/deck-pen.css` (`.rp-lens` rules)
- Test: `tests/structure/reactive_pen_test.py`, `tests/structure/reactive_pen_model.test.cjs` only for pure helpers

**Interfaces:**
- Consumes: Task 2 `controller.lens`, `controller.model.zoom`, `controller.model.mode === 'magnifier'`, `controller.onChange`; surface `getRect()`; the pen canvas of the surface (to copy ink); `framework.slides[currentSlide]` for the source slide.
- Produces: per surface a lens element created lazily (`div.rp-overlay-ui.rp-lens`, `inert`, `aria-hidden="true"`, `pointer-events: none`) containing a scaler `div` of the design canvas size (height 1080, width from the ratio; same maths as `PresenterView._canvasSize()`) holding a clone of the active slide, positioned with `transform: translate(...) scale(zoom * rect.width / canvasWidth)` so the pointer's slide point is at the lens centre; pure helper `DeckPen.lensGeometry({ rect, x, y, zoom, canvasW, canvasH, diameter }) -> { left, top, size, tx, ty, scale }` (clamps the lens inside `rect`), exported for the Node test; pointer tracking: in magnifier mode the surface's canvas stays `pointer-events: auto` for `pointermove`, `pointerleave` only (no strokes), converts to 0..1 and calls `controller.setLens(x, y, true|false)`; canvas bitmap copy on the surface's own rAF only while the lens is visible; re-clone on slide change, class mutation of the active slide (debounced 50 ms) and resize.

- [ ] **Step 1: Write the failing tests.** Node: `test_lens_geometry_clamps_and_centres_the_pointer_point` (pointer at the corner keeps the lens inside the rect; tx/ty put the pointer's slide point at the lens centre for zoom 2, 3, 4). Browser: `test_lens_centre_shows_the_slide_point_under_the_pointer` (a slide with a 20x20 coloured square at a known position; pointer over it; read the lens centre pixel via a screenshot clip or `elementFromPoint` plus canvas copy; compare to the square colour; repeat at 4:3 and after `setViewportSize`), `test_lens_is_inert_and_clone_has_no_ids` (clone contains no `[id]`, lens has `inert` and `pointer-events: none`, a click and a hover over a `.rp-detail` term under the lens still reach the live slide, slide index unchanged), `test_lens_tracks_fragments_and_copies_canvas_frames` (reveal a fragment: appears in the lens within 200 ms; a canvas animation frame appears in the lens), `test_lens_hides_on_pointer_leave_mode_change_and_overview`, `test_lens_loop_stops_when_hidden` (wrap `requestAnimationFrame`; no requests 250 ms after hide).
- [ ] **Step 2: Run to verify failure.**
- [ ] **Step 3: Implement.** Reuse the presenter preview's approach for the cloned deck wrapper (copy the live deck's classes, drop `overview-mode`, set the clone `active`, strip transition classes) and neutralise the wrapper's deck transform inside the lens with `.rp-lens .slide-deck { transform: none; position: static; width/height set }`; copy the pen canvas into the lens with `drawImage` so ink is magnified too; keep the lens z-index above the pen canvas and below the tooltip/modal layers (read the scale in `deck-overlay.css`).
- [ ] **Step 4: Run to verify pass** plus nav, detail, presenter and pen suites.
- [ ] **Step 5: Regenerate packages, commit** `feat(reactive-presentation): draw the magnifier lens in the deck window`.

### Task 4: Presenter-preview lens, mirroring, docs, gates

**Files:**
- Modify: `RP/assets/presenter-view.js` (create the lens on the presenter surface), `RP/assets/deck-pen.js` (lens part of presenter surface if needed), docs: `RP/references/keyboard-shortcuts.md`, `RP/references/framework-guide.md`, `RP/SKILL.md` shortcut line if it mentions pen keys, `doc-sites/docs/remarp-guide/keyboard-shortcuts.md` and its KO counterpart under `doc-sites/i18n/ko/docusaurus-plugin-content-docs/current/remarp-guide/`, `CHANGELOG.md` (Unreleased: Added magnifier, Changed `Option+Y` clear to `Option+T`, Fixed footer spacing)
- Test: `tests/structure/reactive_presenter_test.py`, `tests/structure/reactive_pen_test.py`

**Interfaces:**
- Consumes: Tasks 2-3 lens state and surface lens support; `PresenterView._penRect()`, `_destroyPen()`.
- Produces: the presenter surface renders its own lens over `#p-current-wrap` (clone sourced from the presenter window's document via the same cloning helper, using `doc.importNode` semantics the presenter preview already uses), pointer over the presenter canvas in magnifier mode drives `controller.setLens`; both windows show the lens at the same slide position; presenter lens is removed with the surface on close and recreated on reopen.

- [ ] **Step 1: Write the failing tests:** `test_lens_mirrors_between_windows` (pointer over the presenter preview: deck window lens centred at the same slide point within 2 px, and the reverse; 16:9 and 4:3), `test_presenter_lens_survives_preview_rerender` (re-render of `#p-current` does not remove the lens), `test_closing_presenter_window_keeps_deck_lens`.
- [ ] **Step 2: Run to verify failure.**
- [ ] **Step 3: Implement** the presenter lens; update docs (key table with `Option+Y` Magnifier, `Option+T` clear, zoom keys, mirroring, the clone limits for iframe/video, and the unchanged plain keys) in EN, KO and internal references; CHANGELOG entry.
- [ ] **Step 4: Verify.** Redirect to logs under `/home/atomoh/.tmp`: `python3 scripts/sync-codex-plugins.py --plugin aws-content-plugin` then `--check`; `bash tests/run-all.sh`; `python3 scripts/test-plugins.py`; `python3 scripts/test-codex-plugins.py`; `python3 scripts/eval-skills.py`; the four browser suites unskipped; `npm run record:locales`, `node scripts/check-guide-locales.cjs`, `npm run build` in `doc-sites/`. Expected: all pass.
- [ ] **Step 5: Commit** `feat(reactive-presentation): mirror the magnifier lens in the presenter preview and document it`.
