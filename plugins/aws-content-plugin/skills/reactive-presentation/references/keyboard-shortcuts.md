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
| Esc | Close search or detail / exit fullscreen / dismiss notes panel / exit overview |
| Home/End | First/Last slide |
| 1-9 | Jump to slide number |

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
