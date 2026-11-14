# Reactive presentation: step guidance for presenters

Status: design, approved by the maintainer in conversation (decisions marked "decided").
Component: `plugins/aws-content-plugin/skills/reactive-presentation` (`$P` below).

## Intent

A deck author using reactive-presentation often builds slides that advance in steps: Remarp
fragments, tabs, and animated scenes (flow scenes, step diagrams) driven by the Up/Down keys.
Today a presenter cannot tell from the speaker notes or the presenter window whether a slide
has steps left, or when to press Down while speaking. Scenes also misbehave when driven from the
presenter window, and a scene can be left on an old step after coming back to its slide.

A workshop deck built on this framework (repository `Atom-oh/claude-code-workshop`, PR #77,
branch `feat/20261116-step-marks`, commit `2d1cecf`; files `20261116/reactive/assets/stepviz.js`,
`flowscene.js`, `presenter-notes.js`) solved these with deck-local patches. This work rebuilds
them as framework features and authoring rules, so every deck produced by this skill gets them.
Read that commit first; port the behavior, do not copy the patches (the notes file monkey-patches
`PresenterView.prototype.renderRichNotes` at run time and says so itself).

## Scope and dependencies

- Scope, my call (the request was for guidance that deck builders follow): this work ships the contract,
  the presenter-window features, the authoring rules and the checkers. It does not ship step components.
  `stepviz.js` and `flowscene.js` stay in the workshop deck; the per-component counting rules in section 1
  are the contract an author's own `state()` follows, and the rules in section 5 are guidance for building
  scenes. Tests use a minimal scene written inside the test fixture.
- Depends on PR #303 (`AnimationLoop.drawNow()`, redraw right after a slide action, 100 ms fallback timer),
  open at the time of writing with its required checks passing. Section 5's "works from the presenter window"
  rule relies on it; do not start the presenter-view work from a base that lacks it, and do not re-implement it.
- The workshop commit named above is public to the maintainer's account; the behavior that matters is spelled
  out in "Reference behavior" below so the plan does not depend on reading it.

## Goals

1. The framework can answer "how many presses are left on this slide" for every kind of step.
2. The presenter window shows that answer under the arrow buttons and keeps it current.
3. The speaker notes mark where to press Down, and a checker confirms the marks match reality.
4. Step animations follow one default behavior that is easy to follow and does not make the
   audience dizzy.

## Non-goals and anti-goals

- No change to how slides or fragments are authored in Remarp beyond a literal `↓` in notes.
- Not a new animation library. Existing `AnimationLoop`/`TimelineAnimation` stay.
- Anti-goal: a checker that passes because it trusts a scene's own bookkeeping. The count must come
  from actually pressing the key.
- Anti-goal: cutting step animations to reduce motion. Only looping motion goes.

## Decided design

### 1. Step contract and one lookup (framework)

- A handler passed to `deck.registerSlideAction(index, { up, down, state })` may include
  `state()` returning `{ cur, total }`: `cur` is the number of presses already taken on the slide,
  `total` the number of presses the slide has. `cur < total` means the next Down stays on the slide;
  `cur === total` means the next Down leaves it. Handlers without `state()` stay valid.
- Every component uses that one meaning (decided; it replaces the workshop's mix of conventions):
  flow scene `idx / (phases - 1)`; step diagram `step` counted from 0 when it opens on an OVERVIEW
  step, from 1 otherwise, so the count matches the visible "STEP n" label; quick check `0/1` then `1/1`;
  pick control `0` while nothing is chosen (index -1), then `i + 1`; cycle `i / (n - 1)`.
- `deck.getStepInfo(index)` (name decided) is the single lookup. It folds fragments, tabs/compare
  cycling and registered slide actions into one result, including a kind (fragment, interactive, action,
  none) and a `more` flag. A registered action with no `state()` is reported as "has steps, count unknown".
  The presenter window and any other consumer read only this function.
- The order in which phases are consulted is Down's real order, given under "Reference behavior". The workshop
  cue checked fragments first; the framework does not copy that.

### 2. Slide events (framework)

- `rp:slidechange` fires when the slide index changes, about 350 ms before the slide gets the `.active`
  class (`slide-framework.js`, `showSlide`). Keep that timing. The contract states that listeners compare
  `event.detail.index` with their own slide and must not test `.active` inside the handler (a scene that
  did so never reset, because `.active` was not set yet).
- Add `rp:slideshown`, same `detail`, dispatched after `.active` is applied (at the end of the transition
  timeout, or immediately when there is no transition). Scenes that need the slide to be visible use it.

### 3. Presenter step cue (presenter view)

- A status box under the arrow buttons in the presenter window, built into `presenter-view.js` (not a
  run-time patch). Text, decided: `↓ 다음 단계 있음 (지금 n/N)` while `cur < total`;
  `✓ 마지막 단계 (N/N), 누르면 다음 슬라이드` at the end; `✓ 단계 없음, 누르면 다음 슬라이드` when there are none;
  a fragment variant `→ 다음 항목 있음 (n/N)`; an action without `state()` shows `↓ 이 장에 단계가 있음`.
  (My call: when the deck language is not Korean, show the English equivalents of the same strings.)
- It updates on slide change, after any step press (including from the presenter window's buttons and keys),
  and when the presenter clicks in the main window.

### 4. Down marks in the notes (presenter view)

- A `↓` in the spoken script is drawn as an orange badge in the presenter notes. Done inside the
  framework's notes rendering, after HTML escaping, only in script text. The source Remarp and exported PDF
  are unchanged.
- Authoring rule, decided: exactly one `↓` per press, placed where in the script the presenter presses; the
  script never contains operating instructions ("press the down arrow", "아래 화살표로", "눌러 볼게요").
  `↓` is not allowed in the structured lines `[요약]`, `[출처]`, `[약어]` or `{...}` markers.

### 5. Authoring defaults for step animations (rules in the skill and agent docs)

- One step per click or Down.
- The first frame is the complete picture, so the PDF export and `prefers-reduced-motion` show the whole scene.
- The camera moves only when the step changes and stays still while a packet or other element travels.
- A scene keeps working when driven from the presenter window (the deck window may get no animation
  frames; `AnimationLoop` already redraws on a step and has a fallback timer, PR #303).
- Reduced motion still follows the steps: each step shows its end state at once and the camera jumps to
  that step's frame. It must not freeze on the overview while still consuming presses.
- Cutting motion removes only looping animation; the steps stay. The agent asks the presenter before cutting.

### 6. Checkers

- `scripts/check_deck.py` (static, WARN): lint script lines for operating-instruction phrases; flag `↓`
  inside `[요약]`, `[출처]`, `[약어]` and `{...}` lines.
- `scripts/measure_deck.py` (Tier 2, browser, WARN), decided: for each slide except the last, `deck.goTo(i)`,
  then call `handleNavigationAction('down')` until `currentSlide` changes (cap 40) and count the presses.
  Compare with the number of `↓` in `deck.presenterNotes[i + 1]` (a string, or the `.text` of an object).
  A mismatch is a WARNING. The count comes from real presses, not from `state()`, because only pressing is
  right for handlers without `state()`, fragments and tabs/compare cycling together. The workshop maintainers
  ran this approach over six decks; every slide matched (207 + 114 marks).

## Reference behavior (stand-alone summary of the workshop code)

- What Down does today (`handleNavigationAction('down')` in `slide-framework.js`), in this order: a registered
  slide action's `down()`; otherwise tabs, compare toggles or a legacy `__canvasStep` (`cycleInteractive`);
  otherwise the next fragment; otherwise the next slide. A registered action that returns `false` goes straight
  to the next slide, so fragments after it are reachable with Right/Space only. Fragments sharing a
  `data-fragment-index` appear together and count as one step. `deck.getStepInfo` follows this order and reports
  the phase Down will act on now, not a sum across phases (my call). The workshop cue listed fragments first
  because its fragment slides were driven with Right; the framework follows Down's real order instead.
  Cue text for a phase: `cur < total` is "more" with `cur/total`; `cur === total` is the "last step" text; a
  registered action without `state()` is "this slide has steps"; no phase at all is "no steps". The checker in
  section 6 still counts every Down press on the slide, whatever its phase.
- A registered handler returns `true` when it consumed the key and `false` to let the deck move on
  (`handleNavigationAction`); this is how a scene's last step hands over to the next slide.
- Notes badge: each `↓` becomes an inline span with a light-orange fill, dark text, small padding and radius,
  bold weight, tooltip text "여기서 ↓". The workshop used raw colors; here they come from tokens.
- Scene reset: a scene returns to its first step when its slide is entered again. It listens to
  `rp:slidechange`, compares `detail.index` with its own slide's index, and resets.

## Answers to builder questions (my calls unless marked)

- Language: the cue strings follow `document.documentElement.lang`; Korean when it starts with `ko`, English
  otherwise (my call). English strings: `↓ more steps (now n/N)`, `✓ last step (N/N), the next press moves on`,
  `✓ no steps, the next press moves on`, `→ more items (n/N)`, `↓ this slide has steps`.
- `presenterNotes` is keyed `index + 1` (1-based); the measure check runs in the main deck window only, and a
  slide with no registered actions is still measured (zero presses). A slide whose notes hold `↓` but whose
  presses are zero is a mismatch like any other, so it warns (my call, following "differs means WARNING").
- `rp:slideshown` and the step-change notification mechanism belong in the first pull request (framework and
  presenter view), because the cue's update rule needs them.
- The `check_deck.py` rule ids, the operating-instruction phrase list (Korean and English, starting from the
  examples in section 6) and its false-positive tests are the builder's. Public docs: update the existing
  keyboard-shortcuts and authoring pages in English and Korean rather than adding a page.

## Constraints

- Source of truth is `plugins/`; regenerate `packages/` with `python3 scripts/sync-codex-plugins.py`.
- Public docs in `doc-sites/` need English source and a matching Korean page; run the locale checks.
- Colors and spacing come from design tokens, not raw hex (repository rule); the workshop code used raw values.
- Tests are Playwright browser tests in `tests/structure/` with a `test-*.sh` wrapper that skips when
  Playwright is missing, like the existing reactive tests.

## Left to the builder

- Exact fragment and tabs/compare indexing so `cur`/`total` read as "presses taken / presses in total".
- How scene-internal clicks (a scene's own next/prev buttons) tell the framework to refresh the cue
  (for example a `rp:stepchange` event or a `deck.notifyStepChange()` call).
- Where the rules live in the docs (SKILL.md, the agent file, `remarp-format-guide.md`, canvas guide) and how to
  split the work into pull requests (suggested: framework and presenter view first, then checkers and docs).
- The rule id names for the new checks.
- Whether `deck-nav`/sidebar listeners that depend on `rp:slidechange` timing need adjusting.
