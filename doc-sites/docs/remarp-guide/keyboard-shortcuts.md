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
| Escape | Exit overview or fullscreen |

Typing in an input or textarea does not navigate the deck. Touch swipes on the deck support previous/next navigation. Compare/tabs/Canvas behavior depends on the registered interaction for that slide.

## Custom mappings {#custom-mappings}

```yaml
keys:
  n: next
  Backspace: prev
```

The runtime reads a key-to-action object. Supported actions are those implemented by the navigation switch. The current default map does not bind number keys, N for a notes panel, or B for blackout; older examples that list them are not the active runtime contract.

## Presenter and overview {#presenter-and-overview}

Use P before presenting with a second display and verify window synchronization. Use O and select a slide to navigate the overview. Test custom key mappings in the actual generated deck, particularly when they replace a default.

[Runtime key map](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/reactive-presentation/assets/slide-framework.js)
