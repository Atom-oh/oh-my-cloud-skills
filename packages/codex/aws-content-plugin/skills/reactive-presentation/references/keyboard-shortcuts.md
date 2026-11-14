# Keyboard Shortcuts (runtime)

Shortcuts the generated slideshow supports at viewing time.

| Key | Action |
|-----|--------|
| ← → | Previous / Next slide |
| Space | Next slide |
| ↑ ↓ | Cycle tabs/compare options on current slide; step animation if registered |
| Cmd+K / Ctrl+K | Open slide search |
| / | Open slide search when focus is not in a form control |
| F | Toggle fullscreen |
| N | Open presenter view / notes (new window with notes, timer, slide sync; clicks in its current-slide preview are forwarded to the audience window, and the preview follows text-only changes) |
| G | Toggle overview mode (slide grid thumbnails) |
| S | Toggle slide sidebar (non-fullscreen only) |
| T | Toggle dark/light theme for the whole deck (slides pinned with `@theme` keep theirs). Stored per deck in localStorage; works in the presenter window too |
| H | Hide/unhide the current slide (also the eye icon on each sidebar thumbnail and the presenter window's "Hide slide" button; skipped by arrows/Space; still reachable from sidebar, overview, search). Stored per deck in localStorage; works in the presenter window too |
| Esc | Close search or detail / exit overview / leave pen mode while it is on / exit fullscreen when nothing else is open (see Pen mode for fullscreen) |
| Home/End | First/Last slide |

Plain `P`, `O`, `I`, `U`, `Y`, `C` and the digits `1`-`9` belong to the pen (see below);
the pen handler runs first, so a deck cannot remap them through `window.__remarpKeys`.
`B` has no default binding.

## Pen mode

`deck-pen.js` draws ink over the slide. Every pen key is a plain key (no Option/Alt, no
Shift) matched by QWERTY key position, so on Dvorak or AZERTY-like layouts press the key
in that position (digits use the number row positions). The keys also work while a
Korean or Japanese IME is active. Alt and Shift chords are left to the browser. Pen keys
are ignored while focus is in a text field.
`N`, `G`, `F`, `S`, `H`, `T`, Space and the arrow keys keep their meaning.

| Key | Action |
|-----|--------|
| P | Laser: off -> on in Laser; on in another mode -> Laser; on in Laser -> off |
| O | Pen (stays on) |
| I | Highlighter (translucent, wide, stays on) |
| U | Eraser (removes whole strokes) |
| Y | Magnifier: a round lens follows the mouse (stays on) |
| C | Clear all ink on the current slide |
| 1 / 2 / 3 | Thin / medium / thick; in Magnifier mode 2x / 3x / 4x zoom |
| 4 / 5 / 6 / 7 / 8 / 9 | Red / yellow / green / blue / white / black; nothing in Magnifier mode |
| Esc | Leave pen mode (see the fullscreen note below) |

- `O`, `I`, `U` and `Y` each turn pen mode on when it is off.
- Clearing ink is `C`.
- Defaults are red, medium. The Highlighter defaults to yellow. Each of Laser, Pen and
  Highlighter remembers its own colour; the eraser has none.
- Esc leaves pen mode, and while pen mode is on it wins over an open agenda or detail
  panel. In Chrome and Edge, fullscreen entered with the F key locks Esc to the page
  (Keyboard Lock): the first Esc leaves pen mode (or closes overview), the next Esc
  exits fullscreen, and holding Esc exits fullscreen at any time. Keyboard Lock needs
  a secure context (https or localhost), so a deck opened from `file://` may not get
  it. While focus is in a form control (a range input, a text field, an embedded
  iframe), Esc does nothing in locked fullscreen; hold Esc, or click the slide
  background first, to exit. Fullscreen entered from the browser menu or with
  Cmd+Ctrl+F or F11 is not changed by the lock; whether Esc reaches the page there
  depends on the browser (not verified). In Safari and Firefox, Esc in
  Fullscreen-API fullscreen exits fullscreen before the page sees it. `P` always
  leaves pen mode; press it again from Pen, Highlighter, Eraser or Magnifier, which
  first switches to Laser.
- While pen mode is on the canvas takes all pointer input over the slide, so tabs, quiz
  buttons, compare toggles and detail tooltips need pen mode off first.
- Laser strokes fade after 3 seconds (`pen.fadeMs`). Pen and highlighter ink stays per
  slide for the session and is never saved.
- Ink is mirrored between the deck window and the presenter window popup (opened with
  `N`): ink drawn in the presenter's current-slide preview shows on the deck window at
  the same slide position. Two separate deck windows or tabs sync only the slide position.

### Magnifier

- The lens is a circle 28% of the slide height. The zoom defaults to 2x and stays as
  chosen for the session; the badge shows it (for example `Magnifier 3x`). Near an edge
  the lens stays inside the slide and its centre still shows the point under the mouse.
- The lens position is shared: pointing at the presenter's current-slide preview shows
  the lens in the deck window at the same slide position, and pointing at the deck
  window shows it in the preview. Closing the presenter window leaves the deck lens
  working; reopening it shows the lens there again.
- The lens hides when the mouse leaves the slide, on a mode change, on a slide change
  (until the mouse moves again) and in overview mode.
- In Magnifier mode clicks and hover do not reach the slide: no stroke, no slide
  change, no tooltip. `P`, `O`, `I` and `U` only change the mode and keep pen mode on,
  and the canvas still takes all pointer input. Clicks and hover reach the slide only
  after pen mode is off: press Esc (where Esc reaches the page) or press `P` twice (the first
  press switches to Laser, the second turns pen mode off).

Magnifier limits:

- Only the slide is magnified; the footer, logo and progress bar are not.
- Pen ink is copied into the lens as a bitmap, so it looks softer at 3x and 4x.
- Canvas animations are copied into the lens every frame. Iframes in the lens are
  separate copies that reload, and videos show their poster or first frame.
- The lens copy refreshes on slide change, fragment reveal, `class` changes in the slide
  and window resize. A change that only touches text, `style` or `hidden` stays stale in
  the lens until the next slide change or resize.
- The lens copy carries no `id` attributes. SVG references such as `fill="url(#grad)"`
  and `<use href="#sym">` still render in both windows: in the deck window they resolve
  to the live slide, and in the presenter window to the current-slide preview, which
  keeps the ids (verified in Chromium by `test_lens_svg_id_references_in_both_windows`).
  A reference to an id that exists only outside the slide does not render in the
  presenter window's lens.

Configure with `new SlideFramework({ pen: { fadeMs: 3000, audienceBadge: true } })`.
`audienceBadge: false` hides the mode badge in the deck window only; the presenter
window always shows it.

## Editing Speaker Notes (presenter window)

The presenter window's Speaker Notes pane is editable, so a stiff sentence can be softened or an
example added without asking Claude again or rebuilding the deck.

- Click **Edit notes** or double-click the notes to open a text box with the current note.
- **Ctrl+Enter** (Cmd+Enter), clicking **Save notes**, or leaving the box saves. **Esc** cancels.
- A saved note renders with the same formatting as authored notes (`**bold**`, `` `code` ``, `-` lists).
- An edited slide shows an **Edited** badge and a **Reset to original** button that restores the authored note.
- Edits are stored in this browser only (`localStorage`, key `rp-notes:<page path>`), per slide. Only a
  difference from the authored note is stored. The Remarp source and the audience window are not changed;
  cues and timing keep their authored values. Exporting edits back to the source is not supported.
- While the box has focus, plain-key shortcuts (N, G, H, C, T, pen keys) and arrows type text instead of acting.
- Changing slide or closing the presenter window while editing saves the edit first.

## Step cue and `↓` marks (presenter window)

- A status box under the arrow buttons shows what the next Down does on the current slide (`deck.getStepInfo`):
  `↓ more steps (now n/N)`, `✓ last step (N/N), the next press moves on`, `✓ no steps, the next press moves on`,
  `→ more items (n/N)` for fragments, `↓ this slide has steps` for an action without `state()`. Korean text when
  `<html lang>` starts with `ko`. It updates on slide change, after any step press and on `rp:stepchange`.
- Each `↓` in the script is drawn as an orange badge in the notes pane (tooltip: press ↓ here). The source and PDF
  keep the plain character. Authoring rule: [step-guidance.md](step-guidance.md#3-down-marks-in-the-speaker-notes).

## Deck Overlay Navigation

- Hover the top-right viewport corner to open the agenda.
- Agenda block and slide links call `SlideFramework.goTo(index)`.
- Search covers slide titles, visible content and detail text. Speaker notes are excluded.
- Arrow keys choose a search result and Enter opens it.
- Search shortcuts are ignored while focus is in an input, textarea, select or editable region.
- Agenda, search and detail UI exist only in the deck window and are hidden in overview and capture paths.

## Tab/Step Navigation (↑↓)

The ↑↓ arrow keys control interactive elements on the current slide:

- **↓ key**: Next tab, next compare option, or next animation step
- **↑ key**: Previous tab, previous compare option, or previous animation step

Detection priority:
1. **Registered slide action** (`deck.registerSlideAction(index, { up, down })`) — takes priority. Used for animation step control where JS state can't be auto-detected from DOM.
2. **Auto-detect `.tab-bar`** on current slide — cycles through `.tab-btn` elements
3. **Auto-detect `.compare-toggle`** on current slide — cycles through `.compare-btn` elements
4. **No interactive element** — does nothing

Register animation step control:
```javascript
deck.registerSlideAction(SLIDE_INDEX, {
  down: () => timeline.nextStep(),
  up: () => timeline.prevStep(),
});
```
