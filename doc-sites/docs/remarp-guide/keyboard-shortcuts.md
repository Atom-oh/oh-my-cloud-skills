---
sidebar_position: 13
title: "Keyboard shortcuts"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="키보드-단축키" />
<span id="기본-네비게이션" />
<span id="프래그먼트--스텝" />
<span id="인터랙티브-슬라이드" />
<span id="뷰-모드" />
<span id="프레젠터-뷰" />
<span id="오버뷰-모드" />
<span id="터치-제스처-모바일" />
<span id="키보드-커스터마이징" />
<span id="커스터마이즈-가능한-키" />
<span id="퀵-레퍼런스" />
<span id="발표-시작-전" />
<span id="발표-중" />
<span id="네비게이션" />


# Keyboard shortcuts

The defaults below come from the current `SlideFramework.getKeyAction()` implementation. A deck can override them with its own key-to-action map.

| Key | Action |
| --- | --- |
| Right, Space, PageDown | Reveal next fragment, then advance |
| Left, PageUp | Hide previous fragment where available, then go back |
| Down / Up | Registered slide action, interactive cycling, then fragment/slide navigation |
| Home / End | First / last slide |
| N | Open presenter view (notes) |
| F | Toggle fullscreen |
| G | Toggle overview |
| S | Toggle sidebar outside fullscreen |
| T | Toggle the dark/light theme for the whole deck (slides pinned with `@theme` keep theirs). The choice is stored in this browser only |
| H | Hide or unhide the current slide. Arrow keys and Space skip hidden slides; the sidebar (eye icon on each thumbnail), overview, search and `#N` still reach them. The presenter window has a Hide slide button. The choice is stored in this browser only |
| Escape | Leave pen mode while it is on, otherwise exit overview, otherwise exit fullscreen |

Typing in an input or textarea does not navigate the deck. Touch swipes on the deck support previous/next navigation. Compare/tabs/Canvas behavior depends on the registered interaction for that slide.

## Custom mappings {#custom-mappings}

```yaml
keys:
  n: next
  Backspace: prev
```

The runtime reads a key-to-action object. Supported actions are those implemented by the navigation switch. Plain digits 1-9 and the pen letters P, O, I, U, Y and C are handled by the pen first, so mapping them has no effect. N already opens the presenter view and G the overview (the `n: next` example above replaces N's default); the default map has no blackout key B, and older examples that list one are not the active runtime contract.

## Pen mode {#pen-mode}

Draw on the slide while presenting. Every pen key is a plain key (no Option/Alt and no Shift) matched by QWERTY key position, so on Dvorak or AZERTY-like layouts press the key in that position (the digits use the number row positions). The keys also work while a Korean or Japanese IME is active and are ignored while focus is in a text field. N, G, F, S, H, T, Space and the arrow keys keep their meaning.

| Key | Action |
| --- | --- |
| P | Laser: off turns it on in Laser; on in another mode switches to Laser; on in Laser turns it off |
| O | Pen (stays on) |
| I | Highlighter (translucent, wide, stays on) |
| U | Eraser (removes whole strokes) |
| Y | Magnifier: a round lens follows the mouse (stays on) |
| C | Clear all ink on the current slide |
| 1 / 2 / 3 | Thin / medium / thick; in Magnifier mode 2x / 3x / 4x zoom |
| 4 / 5 / 6 / 7 / 8 / 9 | Red / yellow / green / blue / white / black; nothing in Magnifier mode |
| Esc | Leave pen mode |

O, I, U and Y each turn pen mode on when it is off. Clearing ink is C. Plain 1-9 always belong to the pen, so a deck cannot remap them. The defaults are red and medium, and the Highlighter defaults to yellow. Each of Laser, Pen and Highlighter remembers its own colour. Esc leaves pen mode, and while pen mode is on it wins over an open agenda or detail panel. In Chrome and Edge, fullscreen entered with the F key locks Esc to the page: the first Esc leaves pen mode (or closes overview), the next Esc exits fullscreen, and holding Esc exits fullscreen at any time. The lock needs a secure context (https or localhost), so a deck opened from `file://` may not get it. While focus is in a form control (a range input, a text field, an embedded iframe), Esc does nothing in locked fullscreen; hold Esc, or click the slide background first, to exit. Fullscreen entered from the browser menu or with Cmd+Ctrl+F or F11 is not changed by the lock; whether Esc reaches the page there depends on the browser (not verified). In Safari and Firefox, Esc in Fullscreen-API fullscreen exits fullscreen before the page sees it. P always leaves pen mode; press it again from Pen, Highlighter, Eraser or Magnifier, which first switches to Laser.

While pen mode is on, the canvas takes all pointer input over the slide, so tabs, quiz buttons, compare toggles and detail tooltips need pen mode off first.

Laser strokes fade after 3 seconds. Pen and highlighter ink stays on its slide for the session and is never saved. Ink is mirrored between the deck window and the presenter window popup (opened with N): ink drawn in the presenter's current-slide preview appears on the deck window at the same slide position. Two separate deck windows or tabs sync only the slide position.


Set `pen: { fadeMs, audienceBadge }` in the `SlideFramework` options to change the laser fade time (default 3000 ms) or to hide the mode badge in the deck window with `audienceBadge: false`. The presenter window always shows the badge.

### Magnifier {#magnifier}

Y turns on the Magnifier: a round lens, 28% of the slide height, follows the mouse and shows the slide under it enlarged. The zoom starts at 2x; 1, 2 and 3 switch it to 2x, 3x and 4x, and the badge shows the current zoom. Near an edge the lens stays inside the slide while its centre still shows the point under the mouse.

The lens is mirrored between the deck window and the presenter window: pointing at the presenter's current-slide preview shows the lens in the deck window at the same slide position, and pointing at the deck window shows it in the preview. Closing the presenter window leaves the deck lens working. The lens hides when the mouse leaves the slide, on a mode change, on a slide change (until the mouse moves again) and in overview mode.

In Magnifier mode, clicks and hover do not reach the slide. P, O, I and U only change the mode and keep pen mode on, so the canvas still takes all pointer input. Clicks and hover reach the slide only after pen mode is off: press Esc (where Esc reaches the page), or press P twice (the first press switches to Laser and the second turns pen mode off).

The lens has these limits:

- Only the slide is magnified. The footer, logo and progress bar are not.
- Pen ink is copied into the lens as a bitmap, so it looks softer at 3x and 4x.
- Canvas animations are copied into the lens every frame. Iframes in the lens reload as separate copies, and videos show their poster or first frame.
- The lens refreshes on a slide change, a fragment reveal, a `class` change in the slide and a window resize. A change that only touches text, `style` or `hidden` stays stale in the lens until the next slide change or resize.
- SVG references such as `fill="url(#grad)"` and `<use href="#sym">` render in both windows when the referenced element is inside the slide. A reference to an element outside the slide renders in the deck window's lens but not in the presenter window's lens.

## Presenter and overview {#presenter-and-overview}

Use N before presenting with a second display and verify window synchronization. Use G and select a slide to navigate the overview. Test custom key mappings in the actual generated deck, particularly when they replace a default.

## Step cue and Down marks {#step-cue}

The presenter window shows a status box under the arrow buttons that says what the next Down press does on the current slide: ↓ more steps (now n/N), ✓ last step (N/N), the next press moves on, ✓ no steps, the next press moves on, → more items (n/N) while fragments remain, or ↓ this slide has steps when a scene does not report its count. The text is Korean when the deck's `lang` starts with `ko`, English otherwise. The box follows slide changes, key presses in either window and a scene's own next/previous buttons.

In the notes pane, every `↓` in the spoken script is drawn as an orange badge. Write exactly one `↓` per press the slide takes, right after the sentence that finishes a step (a quick check counts one). Do not write what to press, such as "press the down arrow", and do not put `↓` in the `[요약]`, `[출처]` or `[약어]` lines, in the bullets right under them, or inside `{...}` markers. The Remarp source and the exported PDF keep the plain character.

## Editing speaker notes {#edit-speaker-notes}

The Speaker Notes pane of the presenter window is editable. Click **Edit notes** or double-click the notes, change the text, then press Ctrl+Enter (Cmd+Enter) or click **Save notes**; leaving the box also saves, and Esc cancels. Saved text uses the same formatting as authored notes. A slide with an edit shows an **Edited** badge and a **Reset to original** button.

Edits are stored in this browser only, per slide, and only when they differ from the authored note. The Remarp source and the audience window do not change, and cues and timing keep their authored values. While the text box has focus, shortcut keys and arrows type text instead of acting. Changing slide or closing the presenter window while editing saves the edit first.

[Runtime key map](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/reactive-presentation/assets/slide-framework.js)
