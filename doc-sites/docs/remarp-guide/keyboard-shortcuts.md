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
| Escape | Exit overview or fullscreen; leaves pen mode first while it is on |

Typing in an input or textarea does not navigate the deck. Touch swipes on the deck support previous/next navigation. Compare/tabs/Canvas behavior depends on the registered interaction for that slide.

## Custom mappings {#custom-mappings}

```yaml
keys:
  n: next
  Backspace: prev
```

The runtime reads a key-to-action object. Supported actions are those implemented by the navigation switch. The current default map does not bind number keys, N for a notes panel, or B for blackout; older examples that list them are not the active runtime contract.

## Pen mode {#pen-mode}

Draw on the slide while presenting. Every pen key is an Option (Alt) chord matched by physical key, so plain P, O, S, Space and the arrow keys keep their meaning.

| Key | Action |
| --- | --- |
| Option+P | Laser: off turns it on in Laser; on in another mode switches to Laser; on in Laser turns it off |
| Option+O | Pen (stays on) |
| Option+I | Highlighter (translucent, wide, stays on) |
| Option+U | Eraser (removes whole strokes) |
| Option+Y | Clear all ink on the current slide |
| Option+1 / 2 / 3 | Thin / medium / thick |
| Option+4 / 5 / 6 / 7 / 8 / 9 | Red / yellow / green / blue / white / black |
| Esc | Leave pen mode |

Option+O, Option+I and Option+U each turn pen mode on when it is off. The defaults are red and medium; the Highlighter uses yellow until you choose a colour. Plain Esc is consumed only while pen mode is on, so it does not also exit fullscreen, and it wins over an open agenda or detail panel in that case.

Laser strokes fade after 3 seconds. Pen and highlighter ink stays on its slide for the session and is never saved. Ink drawn in the presenter window's current-slide preview appears on the audience window at the same slide position.

On Linux, Chrome or Firefox may reserve Alt+1 to Alt+9 for tab switching, so the thickness and colour keys may not reach the page there. This has not been verified.

Set `pen: { fadeMs, audienceBadge }` in the `SlideFramework` options to change the laser fade time (default 3000 ms) or to hide the mode badge in the deck window with `audienceBadge: false`. The presenter window always shows the badge.

## Presenter and overview {#presenter-and-overview}

Use P before presenting with a second display and verify window synchronization. Use O and select a slide to navigate the overview. Test custom key mappings in the actual generated deck, particularly when they replace a default.

[Runtime key map](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/reactive-presentation/assets/slide-framework.js)
