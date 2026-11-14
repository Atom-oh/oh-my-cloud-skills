# Reactive Step Guidance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give decks built with reactive-presentation a step contract, a presenter step cue, `↓` marks in the notes, authoring rules for step animations, and checkers that confirm the marks match real key presses.

**Architecture:** `slide-framework.js` gains `getStepInfo`, `notifyStepChange` and two events; `presenter-view.js` renders a cue and a notes badge from them; `check_deck.py` lints note text statically; `measure_deck.py` presses Down in a browser and compares. Rules are documented once in a new reference and linked from the skill and agent docs.

**Tech Stack:** vanilla JS (framework, presenter window), Python 3 with Playwright (checkers, tests), Bash TAP wrappers.

**Spec:** `docs/superpowers/specs/2026-11-14-reactive-step-guidance-design.md`

## Global Constraints

- `$P` = `plugins/aws-content-plugin/skills/reactive-presentation`. Edit sources under `plugins/`; run `python3 scripts/sync-codex-plugins.py` to regenerate `packages/`; never hand-edit `packages/`.
- Branch from a base that contains PR #303 (`AnimationLoop.drawNow`, redraw after a slide action). Stop and tell the maintainer if it is not merged.
- Down order in `handleNavigationAction('down')`: registered slide action, then `cycleInteractive` (tabs, compare, `__canvasStep`), then next fragment, then next slide. A registered action returning `false` goes straight to the next slide.
- `cur`/`total` mean presses taken / presses in total; `cur < total` means the next Down stays on the slide.
- Fragments sharing a `data-fragment-index` value (including all that omit it) count as one step.
- `presenterNotes` is keyed `slideIndex + 1`; a value is a string or an object with `.text`.
- Cue strings, Korean when `document.documentElement.lang` starts with `ko`: `↓ 다음 단계 있음 (지금 n/N)`, `✓ 마지막 단계 (N/N), 누르면 다음 슬라이드`, `✓ 단계 없음, 누르면 다음 슬라이드`, `→ 다음 항목 있음 (n/N)`, `↓ 이 장에 단계가 있음`. English otherwise: `↓ more steps (now n/N)`, `✓ last step (N/N), the next press moves on`, `✓ no steps, the next press moves on`, `→ more items (n/N)`, `↓ this slide has steps`.
- New browser tests follow `tests/structure/reactive_hidden_test.py` (skip without Playwright/Chromium) with a `test-*.sh` TAP wrapper. Run suites with output redirected to a log under `/home/atomoh/.tmp`, never piped to `tail`.
- Public docs: English source plus the matching Korean page; run `npm run record:locales`, `npm run test:i18n`, `npm run check:locales` in `doc-sites/`.
- Colors come from tokens (`var(--accent, #ec7211)` in the presenter CSS), not new raw hex.

## Review Focus

- A slide whose fragments omit `data-fragment-index` reveals them together: the cue counts one step (Task 1).
- A `state()` that throws must not break the cue or the presenter window (Task 3).
- The presenter window closed and reopened, or closed while events keep firing: no listener errors, no duplicate cue boxes (Task 3).
- A note given as an object `{text, timing}`, a slide with presses but no note, and a slide with marks but no presses all compare correctly (Task 7).
- A slide that never stops accepting Down is capped at 40 presses and reported, not looped (Task 7).
- `↓` inside `[요약]`, `[출처]`, `[약어]` lines or `{...}` markers is never drawn as a badge and is flagged by the lint (Tasks 4, 6).

---

## PR 1: framework and presenter view (Tasks 1-4)

### Task 1: `deck.getStepInfo`

**Files:**
- Modify: `$P/assets/slide-framework.js` (next to `cycleInteractive`, ~line 989)
- Create: `tests/structure/reactive_step_info_test.py`, `tests/structure/test-reactive-step-info.sh`

**Interfaces:**
- Produces: `SlideFramework.getStepInfo(index = this.currentSlide) -> { kind: 'action'|'interactive'|'fragment'|'none', cur: number|null, total: number|null, more: boolean }`. Later tasks read only this.

- [ ] **Step 1: Write the failing tests** in `reactive_step_info_test.py` (fixture deck with one slide per case, opened like `reactive_hidden_test.py`). Test names and assertions:
  - `test_no_steps`: plain slide gives `{kind:'none', more:false}`.
  - `test_action_with_state`: `registerSlideAction(i,{down,up,state:()=>({cur:1,total:3})})` gives `{kind:'action',cur:1,total:3,more:true}`; with `cur:3,total:3` gives `more:false`.
  - `test_action_without_state`: gives `{kind:'action',cur:null,total:null,more:true}`.
  - `test_action_state_throwing`: a `state()` that throws behaves as without `state()`.
  - `test_fragments_group_by_index`: three `.fragment` with `data-fragment-index` 1,1,2 give `total:2`; after one `revealNextFragment()` `cur:1`; fragments with no index give `total:1`.
  - `test_tabs_then_fragments`: a slide with 3 tabs and 2 fragments reports `kind:'interactive',cur:0,total:2` first, and after the last tab `kind:'fragment'`.
  - `test_action_hides_fragments`: with a registered action, `kind` stays `'action'` and fragments are ignored.
  - `test_other_slide`: `getStepInfo(k)` for a slide not yet visited reports its initial state without changing `currentSlide`.
- [ ] **Step 2: Run** `python3 tests/structure/reactive_step_info_test.py`; expected FAIL (`getStepInfo is not a function`).
- [ ] **Step 3: Implement** `getStepInfo` per the interface. Call `initFragments(index)` when `fragmentState[index]` is missing. Derive tabs/compare counts the way `cycleInteractive` locates `.tab-btn` / `.compare-btn` (active index and button count, `total = count - 1`); a slide with `__canvasStep` is `{kind:'interactive',cur:null,total:null,more:true}`. Wrap `state()` in try/catch and require finite numbers with `total >= 1`, otherwise treat as absent.
- [ ] **Step 4: Run** the test; expected OK. Add the TAP wrapper `test-reactive-step-info.sh` (copy `test-reactive-hidden.sh` structure without the build half).
- [ ] **Step 5: Commit** `feat(reactive-presentation): add deck.getStepInfo`.

### Task 2: events `rp:slideshown` and `rp:stepchange`

**Files:**
- Modify: `$P/assets/slide-framework.js` (`showSlide` ~line 745; `revealNextFragment`, `revealPrevFragment`, `cycleInteractive`, `handleNavigationAction`)
- Test: `tests/structure/reactive_step_info_test.py` (new class `StepEventTests`)

**Interfaces:**
- Produces: `document` event `rp:slideshown` with `detail:{index}`, fired after the `.active` class is applied (end of the 350 ms transition, or immediately when there is no transition); `document` event `rp:stepchange` with `detail:{index}`; method `SlideFramework.notifyStepChange(index = this.currentSlide): void`. `rp:slidechange` timing is unchanged.

- [ ] **Step 1: Write failing tests**: `test_slideshown_fires_after_active` (record `classList.contains('active')` inside the listener; expect true, and the event arrives at least 300 ms after `rp:slidechange`); `test_slideshown_without_transition` (immediate path); `test_stepchange_on_fragment_action_and_tab` (one event per successful press, none for the press that leaves the slide); `test_notify_step_change_public` (calling it fires one event with the given index); `test_slidechange_timing_unchanged` (still fires before `.active`).
- [ ] **Step 2: Run**; expected FAIL.
- [ ] **Step 3: Implement.** Dispatch `rp:slideshown` in both branches of `showSlide`. Add a private `_emitStepChange(index)` used by `notifyStepChange` and called when a reveal or cycle returns true and after a slide action's `down()`/`up()` returns non-false (the same spot #303's `redrawAnimations()` call sits).
- [ ] **Step 4: Run** tests; expected OK.
- [ ] **Step 5: Commit** `feat(reactive-presentation): add rp:slideshown and rp:stepchange events`.

### Task 3: presenter step cue

**Files:**
- Modify: `$P/assets/presenter-view.js` (`setupPresenterControls`, `updatePresenterView`, the `pagehide` listener, presenter CSS block)
- Create: `tests/structure/reactive_step_cue_test.py`, `tests/structure/test-reactive-step-cue.sh` (model on `reactive_notes_edit_test.py` for opening the presenter popup)

**Interfaces:**
- Consumes: `deck.getStepInfo`, events `rp:slidechange`, `rp:slideshown`, `rp:stepchange` (Tasks 1-2).
- Produces: element `#p-step-cue` (`role="status"`, `data-more="1"|"0"`) inside `.presenter-nav`; method `PresenterView._renderStepCue(doc: Document): void`; pure helper `stepCueText(info, lang) -> string` using the strings in Global Constraints.

- [ ] **Step 1: Write failing tests** (Playwright, presenter popup opened with `n`): `test_cue_for_action_slide_updates_on_down` (cue reads `↓ 다음 단계 있음 (지금 0/2)`, then `1/2`, then `✓ 마지막 단계 (2/2), 누르면 다음 슬라이드` after the last press, with `lang="ko"`); `test_cue_none`; `test_cue_fragment_variant`; `test_cue_action_without_state`; `test_cue_updates_when_main_window_pressed` (press Down in the main window, cue changes without touching the presenter window); `test_cue_english_when_lang_en`; `test_cue_survives_state_throwing`; `test_no_duplicate_box_after_reopen` (close and reopen the popup: exactly one `#p-step-cue`); `test_no_errors_after_close` (close the popup, press Down in the main window, `pageerror` list empty).
- [ ] **Step 2: Run**; expected FAIL.
- [ ] **Step 3: Implement** `stepCueText` and `_renderStepCue`; create the box once under the nav buttons, set `textContent` and `data-more`, call it from `updatePresenterView`; register `document` listeners for the three events in `open()` and remove them in the `pagehide` handler and when the window is found closed.
- [ ] **Step 4: Run** tests; expected OK.
- [ ] **Step 5: Commit** `feat(reactive-presentation): presenter step cue under the arrow buttons`.

### Task 4: `↓` badge in the notes

**Files:**
- Modify: `$P/assets/presenter-view.js` (`renderRichNotes`, presenter CSS block)
- Test: `tests/structure/reactive_step_cue_test.py` (class `StepMarkBadgeTests`)

**Interfaces:**
- Produces: each `↓` in script text renders as `<span class="rp-step-mark" title="여기서 ↓">↓</span>` (title in English `press ↓ here` when lang is not `ko`) styled with `var(--accent, #ec7211)` fill, white text, bold, small radius. Lines that contain `[요약]`, `[출처]` or `[약어]`, and text inside `{...}` markers, keep a plain `↓`.

- [ ] **Step 1: Write failing tests**: `test_marks_become_badges` (note `A↓ B↓` gives two `.rp-step-mark`); `test_marks_in_meta_lines_stay_plain` (`[요약] 한 줄↓` gives none); `test_html_still_escaped` (`<b>↓</b>` shows escaped text and one badge, no injected element); `test_note_edit_still_works` (open the editor from PR #300: textarea shows the raw `↓`, saved note renders badges).
- [ ] **Step 2: Run**; expected FAIL.
- [ ] **Step 3: Implement** inside `renderRichNotes` after the existing escape step: replace `↓` per line, skipping lines and brace spans described above.
- [ ] **Step 4: Run** tests and `tests/structure/reactive_notes_edit_test.py`; expected OK.
- [ ] **Step 5: Commit** `feat(reactive-presentation): draw ↓ marks as badges in the presenter notes`.

---

## PR 2: rules, checkers and docs (Tasks 5-7)

### Task 5: authoring rules in the docs

**Files:**
- Create: `$P/references/step-guidance.md` (the one canonical home: step contract, events contract, notes mark rule, line-art defaults, how the two checkers read these)
- Modify: `$P/SKILL.md` (link and one-line rule beside the existing speaker-notes rule), `plugins/aws-content-plugin/agents/reactive-presentation-agent.md` (same rules as instructions), `$P/references/remarp-format-guide.md` ("Structured Note Schema": the `↓` rule), `$P/references/framework-contract.md` (`getStepInfo`, `state()`, the events; "listeners compare `detail.index`, never `.active`"), `$P/references/keyboard-shortcuts.md` (cue box, notes badge), `doc-sites/docs/remarp-guide/keyboard-shortcuts.md` and its Korean page, `CHANGELOG.md` (`[Unreleased]` / Added)
- Test: existing structure tests (`bash tests/run-all.sh`), locale checks

**Interfaces:** none consumed or produced in code; Tasks 6-7 cite the rule text.

- [ ] **Step 1:** Write `step-guidance.md` containing, as rules: one `↓` per press the slide takes, placed right after the sentence that finishes a step (a quick check counts one); no operating instructions in the script; no `↓` in `[요약]`/`[출처]`/`[약어]`/`{...}`; line-art defaults (one step per click or Down, first frame is the complete picture, camera still while a packet travels, works from the presenter window via #303, reduced motion follows steps with end states and camera jumps, cutting motion removes only looping animation and asks the presenter first); per-component `state()` meaning (flow scene `idx/(phases-1)`, step diagram from 0 with an OVERVIEW first step else from 1, quick check `0/1`->`1/1`, pick `0` until chosen then `i+1`, cycle `i/(n-1)`).
- [ ] **Step 2:** Link it from the files listed; keep each other file to a pointer plus the one rule that file needs.
- [ ] **Step 3:** Run `python3 scripts/sync-codex-plugins.py`, then `python3 scripts/sync-codex-plugins.py --check`; in `doc-sites/` run `npm run record:locales`, `npm run test:i18n`, `npm run check:locales`. Expected: all exit 0.
- [ ] **Step 4: Commit** `docs(reactive-presentation): step guidance rules`.

### Task 6: `check_deck.py` note lint

**Files:**
- Modify: `$P/scripts/check_deck.py` (`RULE_IDS`, new pure function, call inside the per-slide notes loop near `MISSING_NOTES`)
- Test: `tests/structure/check_deck_notes_test.py`, `tests/structure/test-check-deck-notes.sh`

**Interfaces:**
- Produces: `lint_note_text(text: str) -> list[tuple[str, str]]` returning `(rule, message)` pairs; rules `NOTE_OPERATING_INSTRUCTION` and `NOTE_MARK_IN_META`, both WARN, reported with the slide number.

- [ ] **Step 1: Write failing tests**: `test_flags_korean_operating_phrases` (each of `아래 화살표로`, `눌러 볼게요`, `버튼을 누르`, `장면을 누를 때마다` yields `NOTE_OPERATING_INSTRUCTION`); `test_flags_english_operating_phrases` (`press the down arrow`, `click the next button`); `test_plain_script_is_clean` (a note with `↓` after sentences and no phrases yields `[]`); `test_mark_in_summary_line` (`[요약] 요점↓`, `[출처] a↓`, `[약어] b↓`, `{timing: 2}↓` each yield `NOTE_MARK_IN_META`); `test_deck_level_warning_has_slide_number` (run `check_file` on a two-slide fixture; the finding carries `slide == 2`).
- [ ] **Step 2: Run**; expected FAIL.
- [ ] **Step 3: Implement** with a phrase tuple of Korean and English patterns starting from the examples above (compile once, case-insensitive for English); add the two ids to `RULE_IDS`; reuse the notes text the existing loop already collects.
- [ ] **Step 4: Run** tests; expected OK; run an existing deck through `check_deck.py` to confirm no new FAIL.
- [ ] **Step 5: Commit** `feat(reactive-presentation): lint speaker notes for operating instructions and misplaced marks`.

### Task 7: `measure_deck.py` step-mark count

**Files:**
- Modify: `$P/scripts/measure_deck.py` (module docstring check list, new function, call in `measure` before `_PREPARE_JS`)
- Test: `tests/structure/measure_step_marks_test.py`, `tests/structure/test-measure-step-marks.sh`

**Interfaces:**
- Consumes: `deck.goTo`, `deck.handleNavigationAction('down')`, `deck.presenterNotes`.
- Produces: `count_slide_presses(page, index: int, cap: int = 40) -> tuple[int, bool]` (presses that kept the slide current, and whether the cap was hit); `check_step_marks(page, block: str) -> list[dict]` returning findings with `rule='STEP_MARKS'`, `severity='WARN'`, `slide` 1-based, message `notes carry N "↓" but the slide takes M presses`.

- [ ] **Step 1: Write failing tests** (fixture decks written into a temp dir like `measure_runon_test.py`): `test_matching_marks_pass` (slide with 2 fragments and 2 `↓` in its note: no finding); `test_mismatch_warns` (3 presses, 1 mark: one `STEP_MARKS` finding); `test_marks_without_presses_warn` (0 presses, 2 marks); `test_presses_without_marks_warn` (2 presses, no note); `test_object_note_uses_text` (`{text, timing}` note); `test_last_slide_skipped`; `test_action_without_state_counted` (a registered action with no `state()` taking 3 presses, 3 marks: pass); `test_cap_reported` (an action that always returns true: finding message mentions the cap, run terminates).
- [ ] **Step 2: Run**; expected FAIL.
- [ ] **Step 3: Implement.** In JS, loop `deck.handleNavigationAction('down')` while `deck.currentSlide === i` and count presses that leave the slide current; the press that changes the slide is not counted (rule: one mark per press the slide takes). Wait for `!deck.transitioning` after each slide change, and between slides reload nothing: call `deck.goTo(i)` fresh. Run once per block on a fresh page load before `_PREPARE_JS` (that helper reveals every fragment), on the first viewport and theme only. Count `↓` in `presenterNotes[i + 1]` (string or `.text`).
- [ ] **Step 4: Run** tests; expected OK; run `measure_deck.py` on `$P/assets/example-deck/` and report any new warnings in the PR.
- [ ] **Step 5: Run the whole suite** with output to a log: `bash tests/run-all.sh > /home/atomoh/.tmp/step-guidance.log 2>&1`, then grep the log for `# Results`; expected `0 failed`. Run the sync check and the two plugin test scripts.
- [ ] **Step 6: Commit** `feat(reactive-presentation): measure_deck checks ↓ marks against real presses`.
