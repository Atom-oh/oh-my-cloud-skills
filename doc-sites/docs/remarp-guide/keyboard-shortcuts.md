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
| P | Open presenter view |
| F | Toggle fullscreen |
| O | Toggle overview |
| S | Toggle sidebar outside fullscreen |
| Escape | Leave pen mode while it is on, otherwise exit overview, otherwise exit fullscreen |

Typing in an input or textarea does not navigate the deck. Touch swipes on the deck support previous/next navigation. Compare/tabs/Canvas behavior depends on the registered interaction for that slide.

## Custom mappings {#custom-mappings}

```yaml
keys:
  n: next
  Backspace: prev
```

The runtime reads a key-to-action object. Supported actions are those implemented by the navigation switch. The current default map does not bind number keys, N for a notes panel, or B for blackout; older examples that list them are not the active runtime contract.

## Pen mode {#pen-mode}

Draw on the slide while presenting. Every pen key is an Option (Alt) chord matched by QWERTY key position, so on Dvorak or AZERTY-like layouts press the key in that position (the digits use the number row positions). Plain P, O, S, Space and the arrow keys keep their meaning.

| Key | Action |
| --- | --- |
| Option+P | Laser: off turns it on in Laser; on in another mode switches to Laser; on in Laser turns it off |
| Option+O | Pen (stays on) |
| Option+I | Highlighter (translucent, wide, stays on) |
| Option+U | Eraser (removes whole strokes) |
| Option+Y | Magnifier: a round lens follows the mouse (stays on) |
| Option+T | Clear all ink on the current slide |
| Option+1 / 2 / 3 | Thin / medium / thick; in Magnifier mode 2x / 3x / 4x zoom |
| Option+4 / 5 / 6 / 7 / 8 / 9 | Red / yellow / green / blue / white / black; nothing in Magnifier mode |
| Esc | Leave pen mode |

Option+O, Option+I, Option+U and Option+Y each turn pen mode on when it is off. Clearing ink moved from Option+Y to Option+T when the Magnifier took Option+Y. The defaults are red and medium, and the Highlighter defaults to yellow. Each of Laser, Pen and Highlighter remembers its own colour. Esc leaves pen mode, and while pen mode is on it wins over an open agenda or detail panel. In Chrome and Edge, fullscreen entered with the F key locks Esc to the page: the first Esc leaves pen mode (or closes overview), the next Esc exits fullscreen, and holding Esc exits fullscreen at any time. The lock needs a secure context (https or localhost), so a deck opened from `file://` may not get it. In Safari, Firefox, and fullscreen entered from the browser menu or with Cmd+Ctrl+F or F11, the browser takes Esc first and exits fullscreen, so use Option+P to leave pen mode there; press it again from Pen, Highlighter, Eraser or Magnifier, which first switches to Laser.

While pen mode is on, the canvas takes all pointer input over the slide, so tabs, quiz buttons, compare toggles and detail tooltips need pen mode off first.

Laser strokes fade after 3 seconds. Pen and highlighter ink stays on its slide for the session and is never saved. Ink is mirrored between the deck window and the presenter window popup (opened with P): ink drawn in the presenter's current-slide preview appears on the deck window at the same slide position. Two separate deck windows or tabs sync only the slide position.

On Linux, Chrome or Firefox may reserve Alt+1 to Alt+9 for tab switching, so the thickness and colour keys may not reach the page there. On Firefox for Windows, Alt+T (Option+T, clear ink) is a menu accelerator; the pen handler calls `preventDefault()`, which should suppress the menu. Neither behaviour has been verified.

Set `pen: { fadeMs, audienceBadge }` in the `SlideFramework` options to change the laser fade time (default 3000 ms) or to hide the mode badge in the deck window with `audienceBadge: false`. The presenter window always shows the badge.

### Magnifier {#magnifier}

Option+Y turns on the Magnifier: a round lens, 28% of the slide height, follows the mouse and shows the slide under it enlarged. The zoom starts at 2x; Option+1, Option+2 and Option+3 switch it to 2x, 3x and 4x, and the badge shows the current zoom. Near an edge the lens stays inside the slide while its centre still shows the point under the mouse.

The lens is mirrored between the deck window and the presenter window: pointing at the presenter's current-slide preview shows the lens in the deck window at the same slide position, and pointing at the deck window shows it in the preview. Closing the presenter window leaves the deck lens working. The lens hides when the mouse leaves the slide, on a mode change, on a slide change (until the mouse moves again) and in overview mode.

In Magnifier mode, clicks and hover do not reach the slide. Option+P, Option+O, Option+I and Option+U only change the mode and keep pen mode on, so the canvas still takes all pointer input. Clicks and hover reach the slide only after pen mode is off: press Esc (where Esc reaches the page), or press Option+P twice (the first press switches to Laser and the second turns pen mode off).

The lens has these limits:

- Only the slide is magnified. The footer, logo and progress bar are not.
- Pen ink is copied into the lens as a bitmap, so it looks softer at 3x and 4x.
- Canvas animations are copied into the lens every frame. Iframes in the lens reload as separate copies, and videos show their poster or first frame.
- The lens refreshes on a slide change, a fragment reveal, a `class` change in the slide and a window resize. A change that only touches text, `style` or `hidden` stays stale in the lens until the next slide change or resize.
- SVG references such as `fill="url(#grad)"` and `<use href="#sym">` render in both windows when the referenced element is inside the slide. A reference to an element outside the slide renders in the deck window's lens but not in the presenter window's lens.

## Presenter and overview {#presenter-and-overview}

Use P before presenting with a second display and verify window synchronization. Use O and select a slide to navigate the overview. Test custom key mappings in the actual generated deck, particularly when they replace a default.

[Runtime key map](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/reactive-presentation/assets/slide-framework.js)
