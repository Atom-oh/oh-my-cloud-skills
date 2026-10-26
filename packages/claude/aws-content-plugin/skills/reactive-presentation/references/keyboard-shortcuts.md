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
| N | Toggle speaker notes panel (bottom 20% overlay) |
| P | Open presenter view (new window with notes, timer, slide sync) |
| O | Toggle overview mode (slide grid thumbnails) |
| S | Toggle slide sidebar (non-fullscreen only) |
| B | Blackout screen |
| Esc | Close search or detail / exit fullscreen / dismiss notes panel / exit overview / leave pen mode while it is on |
| Home/End | First/Last slide |

There is no default digit-key slide jump; plain `1`-`9` do nothing unless a deck
maps them through `keys` (verified against `getKeyAction()` in `slide-framework.js`).

## Pen mode

`deck-pen.js` draws ink over the slide. Every pen key is an Option (Alt) chord matched
by physical key, so plain `P`, `O`, `S`, Space and the arrow keys keep their meaning.

| Key | Action |
|-----|--------|
| Option+P | Laser: off -> on in Laser; on in another mode -> Laser; on in Laser -> off |
| Option+O | Pen (stays on) |
| Option+I | Highlighter (translucent, wide, stays on) |
| Option+U | Eraser (removes whole strokes) |
| Option+Y | Clear all ink on the current slide |
| Option+1 / 2 / 3 | Thin / medium / thick |
| Option+4 / 5 / 6 / 7 / 8 / 9 | Red / yellow / green / blue / white / black |
| Esc | Leave pen mode |

- Option+O, I and U each turn pen mode on when it is off.
- Defaults are red and medium. The Highlighter uses yellow until a colour is chosen.
- Plain Esc is consumed only while pen mode is on, so it does not also exit fullscreen,
  and it wins over an open agenda or detail panel in that case.
- Laser strokes fade after 3 seconds (`pen.fadeMs`). Pen and highlighter ink stays per
  slide for the session and is never saved.
- Ink drawn in the presenter window's current-slide preview shows on the audience
  window at the same slide position.
- Linux caveat (not verified here): Chrome or Firefox on Linux may reserve Alt+1-9 for
  tab switching, so the thickness and colour keys may not reach the page there.

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
