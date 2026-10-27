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
| P | Open presenter view (new window with notes, timer, slide sync; clicks in its current-slide preview are forwarded to the audience window, and the preview follows text-only changes) |
| O | Toggle overview mode (slide grid thumbnails) |
| S | Toggle slide sidebar (non-fullscreen only) |
| Esc | Close search or detail / exit overview / leave pen mode while it is on / exit fullscreen when nothing else is open (see Pen mode for fullscreen) |
| Home/End | First/Last slide |

There is no default binding for plain `N`, `B` or the digits `1`-`9`; they do nothing
unless a deck remaps them to an existing action (verified against `getKeyAction()` in
`slide-framework.js` and a search of the other runtime scripts).

## Pen mode

`deck-pen.js` draws ink over the slide. Every pen key is an Option (Alt) chord matched
by QWERTY key position, so on Dvorak or AZERTY-like layouts press the key in that
position (digits use the number row positions). Plain `P`, `O`, `S`, Space and the arrow keys
keep their meaning.

| Key | Action |
|-----|--------|
| Option+P | Laser: off -> on in Laser; on in another mode -> Laser; on in Laser -> off |
| Option+O | Pen (stays on) |
| Option+I | Highlighter (translucent, wide, stays on) |
| Option+U | Eraser (removes whole strokes) |
| Option+Y | Magnifier: a round lens follows the mouse (stays on) |
| Option+T | Clear all ink on the current slide |
| Option+1 / 2 / 3 | Thin / medium / thick; in Magnifier mode 2x / 3x / 4x zoom |
| Option+4 / 5 / 6 / 7 / 8 / 9 | Red / yellow / green / blue / white / black; nothing in Magnifier mode |
| Esc | Leave pen mode (see the fullscreen note below) |

- Option+O, I, U and Y each turn pen mode on when it is off.
- Clearing ink moved from Option+Y to Option+T when the Magnifier took Option+Y.
- Defaults are red, medium. The Highlighter defaults to yellow. Each of Laser, Pen and
  Highlighter remembers its own colour; the eraser has none.
- Esc leaves pen mode, and while pen mode is on it wins over an open agenda or detail
  panel. In Chrome and Edge, fullscreen entered with the F key locks Esc to the page
  (Keyboard Lock): the first Esc leaves pen mode (or closes overview), the next Esc
  exits fullscreen, and holding Esc exits fullscreen at any time. Keyboard Lock needs
  a secure context (https or localhost), so a deck opened from `file://` may not get
  it. In Safari, Firefox, and fullscreen entered from the browser menu or with
  Cmd+Ctrl+F or F11, the browser takes Esc first and exits fullscreen, so use Option+P
  to leave pen mode there; press it again from Pen, Highlighter, Eraser or Magnifier,
  which first switches to Laser.
- While pen mode is on the canvas takes all pointer input over the slide, so tabs, quiz
  buttons, compare toggles and detail tooltips need pen mode off first.
- Laser strokes fade after 3 seconds (`pen.fadeMs`). Pen and highlighter ink stays per
  slide for the session and is never saved.
- Ink is mirrored between the deck window and the presenter window popup (opened with
  `P`): ink drawn in the presenter's current-slide preview shows on the deck window at
  the same slide position. Two separate deck windows or tabs sync only the slide position.
- Linux and Windows caveat (not verified here): Chrome or Firefox on Linux may reserve
  Alt+1-9 for tab switching, so the thickness and colour keys may not reach the page
  there. On Firefox for Windows, Alt+T (Option+T, clear ink) is a menu accelerator; the
  pen handler calls `preventDefault()`, which should suppress the menu, but this was not
  verified.

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
  change, no tooltip. Option+P, O, I and U only change the mode and keep pen mode on,
  and the canvas still takes all pointer input. Clicks and hover reach the slide only
  after pen mode is off: press Esc (where Esc reaches the page) or press Option+P twice (the first
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
