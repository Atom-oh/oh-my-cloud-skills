# Step guidance: step contract, events, `↓` marks and step-animation defaults

Canonical home for the rules that let a presenter see how many presses a slide still has and
where in the script to press Down. Other files carry a pointer plus the one rule they need.

## 1. Step contract

`deck.registerSlideAction(index, { up, down, state })`. `state()` is optional and returns
`{ cur, total }`: `cur` = presses already taken on the slide, `total` = presses the slide has.
`cur < total` means the next Down stays on the slide; `cur === total` means the next Down leaves it.
A handler without `state()` stays valid; the presenter window then shows "this slide has steps"
(count unknown), as it does for a legacy `slide.__canvasStep` (kind `interactive`, null counts, `more: true`).

Per-component meaning of `cur/total` (every component uses the same one):

| Component | `cur / total` |
|---|---|
| Flow scene | `idx / (phases - 1)` |
| Step diagram | step counted from 0 when it opens on an OVERVIEW step, from 1 otherwise, so the count matches the visible "STEP n" label |
| Quick check | `0/1`, then `1/1` |
| Pick control | `0` while nothing is chosen, then `i + 1` |
| Cycle | `i / (n - 1)` |

`deck.getStepInfo(index = currentSlide)` is the single lookup and returns `{ kind, cur, total, more }`.
It follows the real order of Down: registered slide action, then tabs / compare / `__canvasStep`,
then fragments, then the next slide. It reports the phase Down acts on now, not a sum. Fragments that
share a `data-fragment-index` are one step; fully revealed fragments report `more: false`. Tabs or compare
buttons that are exhausted on a slide without fragments report their last step
(`{ kind: 'interactive', cur: n - 1, total: n - 1, more: false }`); `kind: 'none'` is only for a slide with
no step phase at all. The presenter window and any other consumer read only this function.

## 2. Events contract

- `rp:slidechange` (`detail.index`) fires when the slide index changes. With an animated transition
  (the default for `goTo`/`next`/`prev`) it fires about 350 ms BEFORE the slide gets the `.active`
  class; without one (`showSlide(i, false)`, the first slide at load) `.active` is already set. A
  listener compares `event.detail.index` with its own slide's index and never tests `.active` inside
  the handler (a scene that did so never reset).
- `rp:slideshown` (same `detail`) fires after `.active` is applied: at the end of the transition, or at
  the end of `showSlide` when there is none. Use it when the slide must be visible.
- Order guarantee: `rp:slidechange` always precedes `rp:slideshown` for the same change, and
  `deck.currentSlide` is already the new index when either fires.
- `rp:stepchange` (`detail.index`) means the step shown on a slide changed. The framework emits it after
  key presses and for its own tab/compare clicks. A scene that advances itself without a key press
  (its own next/prev buttons) calls `deck.notifyStepChange()` so the presenter cue refreshes.
- A scene returns to its first step when its slide is entered again: listen to `rp:slidechange`, compare
  `detail.index`, reset.

## 3. Down marks in the speaker notes

- Exactly one `↓` per press the slide takes, placed right after the sentence that finishes a step.
  A quick check counts one.
- The script never says what to press ("아래 화살표로", "눌러 볼게요", "press the down arrow"). The
  presenter window draws each `↓` as an orange badge, so the script only marks the place.
- No `↓` in a meta layer and none inside a `{...}` marker. A meta layer is a line holding `[요약]`,
  `[출처]` or `[약어]` plus the bullet lines right under it (starting with `-`, `*` or `•` after optional
  whitespace) up to the first blank or non-bullet line, so the block form (`[요약]` on its own line,
  bullets below) is covered. Only a `↓` INSIDE a `{...}` span is meta; a `↓` after the closing `}`
  (`{timing: 2}↓`) is script text and is drawn as a badge.

The presenter notes renderer and `check_deck.py` apply this one rule. Checked by (WARN): `check_deck.py`
rules `NOTE_OPERATING_INSTRUCTION` (operating phrases in the script, including navigation key-press
instructions such as "↓ 키를 눌러가며") and `NOTE_MARK_IN_META` (`↓` in a meta layer or inside `{...}`);
both read the decoded note text, so they work on decks compiled by `remarp_to_slides.py` (which writes
`\u2193` escapes). `measure_deck.py` rule `STEP_MARKS` compares the presses really taken with Down against
the `↓` count in the slide's notes; a slide whose counting throws is reported as "counting stopped at
slide N" and the pass goes on. The count comes from real presses, never from `state()`.

## 4. Presenter window

Under the arrow buttons a status box shows what the next Down does (`getStepInfo`): more steps with
`n/N`, last step, no steps, more fragment items, or "this slide has steps" for an action without
`state()` or a legacy `__canvasStep`. It follows `<html lang>` (Korean for `ko*`, English otherwise) and updates on slide change,
on `rp:stepchange` and after presses from either window. In the notes pane each `↓` of the script is an
orange `.rp-step-mark` badge with dark text; the Remarp source and PDF export are unchanged. The cue and
badge colors are presenter-scoped (`--pv-text-muted`, `--pv-on-accent`) so they stay readable on the
fixed dark presenter chrome whatever the deck theme.

## 5. Step-animation defaults (line art, scenes)

- One step per click or Down.
- The first frame is the complete picture, so PDF export and `prefers-reduced-motion` show the whole scene.
- The camera moves only when the step changes and stays still while a packet or other element travels.
- A scene keeps working when driven from the presenter window: the deck window may get no animation
  frames, so `AnimationLoop` redraws on a step (`drawNow()`, `redrawAll()`) and has a 100 ms fallback
  timer. Build scenes on `AnimationLoop` rather than a bare `requestAnimationFrame`.
- Reduced motion still follows the steps: each step shows its end state at once and the camera jumps to
  that step's frame. It must not freeze on the overview while still consuming presses.
- Cutting motion removes only looping animation; the steps stay. The agent asks the presenter before cutting.
