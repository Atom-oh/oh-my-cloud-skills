# Fullscreen Esc keeps pen mode first: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** In a deck entered into fullscreen with the Fullscreen API (the `F` key), plain `Esc` must reach the page so pen mode (and overview, search, detail panel) handle it first; only an `Esc` with nothing to close exits fullscreen.

**Architecture:** While `document.fullscreenElement` is set, the framework calls `navigator.keyboard.lock(['Escape'])` (Chromium only; absent or rejected means today's behaviour) and calls `navigator.keyboard.unlock()` when fullscreen ends. No change to the Esc handlers: `DeckPen.controller.handleKey` already turns pen mode off on plain Esc, and the framework's `escape` action already closes overview or calls `document.exitFullscreen()`.

**Tech Stack:** Vanilla JS, Playwright for Python (browser tests), TAP shell runner.

**Spec:** none; agreed in chat on 2026-10-27 (the user chose this fix).

## Global Constraints

- Skill root `plugins/aws-content-plugin/skills/reactive-presentation` (RP). Work in `/home/atomoh/worktrees/fs-esc` on `fix/fullscreen-esc-keyboard-lock` from `origin/main` (29f31ec7, v3.0.6). Never hand-edit `packages/*`: regenerate with `python3 scripts/sync-codex-plugins.py --plugin aws-content-plugin` and commit with the change.
- Only pages that enter fullscreen through the Fullscreen API get the lock; fullscreen entered from the browser UI (`Cmd+Ctrl+F`, `F11`) is not controllable and stays as is. Browsers without `navigator.keyboard.lock` (Safari, Firefox) behave as today.
- Lock only for `['Escape']`. Always unlock when fullscreen ends, on `pagehide`, and never throw (wrap in try/catch, swallow the promise rejection).
- With the lock on, holding `Esc` still exits fullscreen at the browser level; do not try to prevent that.
- Behaviour contract in fullscreen with the lock: Esc with pen mode on turns pen mode off and stays fullscreen; Esc with overview open closes overview; Esc with nothing to close exits fullscreen. Outside fullscreen nothing changes.
- No em dash (U+2014) or middle dot (U+00B7, U+30FB) in anything added. English internal docs; public pages in EN and KO with matching anchors, natural KO. After doc-sites edits run `npm run record:locales`, `node scripts/check-guide-locales.cjs`, `npm run build` in `doc-sites/` (symlink `/home/atomoh/oh-my-cloud-skills/doc-sites/node_modules` into the worktree's `doc-sites/` and remove it afterwards).
- Playwright for Python and Chromium are installed: browser test runs must be unskipped, with commands and result lines in the report.

## Review Focus

1. A page without `navigator.keyboard` (Safari, Firefox) or with a `lock()` that rejects behaves exactly as before and logs no error. Pinned by `test_keyboard_lock_absent_or_rejected_is_harmless` (Task 1).
2. Lock is requested on every fullscreen entry (also after the user exited with a long Esc press and re-entered) and released on every exit. Pinned by `test_escape_lock_follows_fullscreen_state` (Task 1).
3. In fullscreen, Esc with pen mode on turns the pen off and keeps fullscreen; a second Esc exits. Pinned by `test_esc_in_fullscreen_leaves_pen_mode_before_fullscreen` (Task 1).
4. The docs no longer promise more than the code does: Chromium and the `F` key only; other browsers and browser-UI fullscreen unchanged. Pinned by review of Task 2 text.

---

### Task 1: Lock Escape while the page is fullscreen

**Files:**
- Modify: `RP/assets/slide-framework.js` (a `bindEscapeLock()` called from init next to the other fullscreen binding, independent of `sidebarEnabled`)
- Test: `tests/structure/reactive_fullscreen_test.py` (new, with TAP wrapper `tests/structure/test-reactive-fullscreen.sh`; mirror `test-reactive-footer.sh` / `reactive_footer_test.py`)

**Interfaces:**
- Consumes: `document.fullscreenElement`, `fullscreenchange`, `navigator.keyboard.lock/unlock`, `DeckPen.controller` (`active`, `setActive`, `handleKey`), the framework's `escape` action.
- Produces: `SlideFramework.bindEscapeLock()` (idempotent) and no new public option.

- [ ] **Step 1: Write the failing tests** (Chromium, unskipped), stubbing `navigator.keyboard` with an init script that records calls: `test_escape_lock_follows_fullscreen_state` (enter fullscreen with the `F` key: lock called once with `['Escape']`; exit: unlock called; enter again: lock called again), `test_keyboard_lock_absent_or_rejected_is_harmless` (no `navigator.keyboard`; and a stub whose `lock()` returns a rejected promise: no page error, fullscreen still toggles), `test_esc_in_fullscreen_leaves_pen_mode_before_fullscreen` (dispatch a synthetic plain `Escape` keydown on the document: pen mode off, `document.fullscreenElement` still set; second Escape: `fullscreenElement` null), `test_esc_closes_overview_before_leaving_fullscreen`.
- [ ] **Step 2: Run to verify failure:** `python3 tests/structure/reactive_fullscreen_test.py`. Expected: the lock tests FAIL.
- [ ] **Step 3: Implement** `bindEscapeLock()`; also unlock on `pagehide`; no change to the Esc handlers.
- [ ] **Step 4: Verify:** the new test, `reactive_pen_test.py`, `reactive_presenter_test.py`, `reactive_nav_test.py`, `reactive_detail_test.py`, `reactive_footer_test.py`, `python3 scripts/sync-codex-plugins.py --plugin aws-content-plugin` then `--check`, `bash tests/run-all.sh`.
- [ ] **Step 5: Commit** `fix(reactive-presentation): keep Esc for pen mode while the deck is fullscreen`.

### Task 2: Docs and CHANGELOG

**Files:**
- Modify: `RP/references/keyboard-shortcuts.md`, `RP/references/framework-guide.md` (only if it repeats the fullscreen Esc caveat), `doc-sites/docs/remarp-guide/keyboard-shortcuts.md` and its KO counterpart under `doc-sites/i18n/ko/docusaurus-plugin-content-docs/current/remarp-guide/`, `CHANGELOG.md` (Unreleased, Fixed)

**Interfaces:** Consumes Task 1's behaviour contract (Global Constraints). Produces the corrected caveat text.

- [ ] **Step 1: Find every statement** about Esc and fullscreen (`grep -rn -i "fullscreen" RP/references doc-sites/docs doc-sites/i18n CHANGELOG.md`, excluding packages and node_modules) and rewrite it: in Chrome or Edge, in fullscreen entered with the `F` key, the first `Esc` leaves pen mode (or closes overview), the next `Esc` exits fullscreen, and holding `Esc` exits at any time; in Safari, Firefox, and in fullscreen entered from the browser menu or `Cmd+Ctrl+F` / `F11`, the browser takes `Esc` first and exits fullscreen, so use `Option+P` (press again from another mode, which first switches to Laser) to leave pen mode.
- [ ] **Step 2: CHANGELOG** one Fixed line.
- [ ] **Step 3: Verify:** locale record and check, doc-sites build, `bash tests/run-all.sh`, `python3 scripts/sync-codex-plugins.py --plugin aws-content-plugin` then `--check`.
- [ ] **Step 4: Commit** `docs(reactive-presentation): describe Esc in fullscreen with the keyboard lock`.
