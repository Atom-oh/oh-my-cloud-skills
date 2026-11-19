# Recipes

All snippets use deck role tokens. Class prefix `sk-`. The complete working example is
`templates/sketch-opener.html`; copy from it rather than retyping.

## 1. Shared wobble filter (once per SVG)

```html
<filter id="sk-rough" x="-5%" y="-5%" width="110%" height="110%">
  <feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="7" result="n"/>
  <feDisplacementMap in="SourceGraphic" in2="n" scale="3.2" xChannelSelector="R" yChannelSelector="G"/>
</filter>
```

Apply it through `.sk-ink { filter:url(#sk-rough) }` on strokes and shapes, never on text.
Raise `scale` to 4 for a rougher look, lower to 2 for tidier. The filter is static, so it
costs nothing during animation. A CSS animation on `transform` replaces the element's `transform` attribute, so never
animate an element that is also positioned with `transform=`: put the position on an outer
`<g transform="translate(...)">` and the animated class on an inner `<g>`.

## 2. Panels, cards, stamps

- Panel: `rect rx=18`, class `sk-ink` + wash fill (`sk-wash-a|i|s`), stroke 2.
- Card: `rect rx=8`, class `sk-ink sk-thin sk-card` (fill `--surface-2`). A stack of papers
  is the same card repeated twice with a (+4, +4) offset behind it.
- Stamp: filled circle (r 15) in ink plus the number in `--surface-1`, top left of a panel.
- Document card: add a folded corner (two short lines forming a triangle) and two or three
  short bars for text.

## 3. Doodle icons (single line weight, ink only)

Draw in a local `translate()` group of about 40x40. Keep each icon under about ten
path commands.

| Meaning | Doodle |
|---|---|
| person | circle head, arc body |
| document | rect with folded corner, 3 bars |
| terminal | rounded rect, `>` and a short underscore |
| gear | small circle plus 8 ticks (the only element that may spin) |
| check | circle with a tick |
| idea | circle with 6 short rays |
| folder, box, magnifier, moon | simple rect or arc plus one detail |

## 4. Edges

- Always a shallow quadratic curve, `M x1 y1 Q cx cy x2 y2`, with a control point offset 8
  to 16 units from the straight line.
- Arrowhead: small filled triangle at the end, same ink.
- Loop around the outside: control point 100 or more units outside the bands.
- Short label on an edge: `sk-note` text, 14 to 16 px, only when the edge carries
  something specific.

## 5. Flow dots

```html
<circle class="sk-dot a" style="offset-path:path('M265 170 Q310 158 372 170')"/>
```

- The `offset-path` string must be the same path as the visible edge.
- Speed target about 110 px per second in viewBox units. With a 3 s loop, a path of about
  330 units fits one pass per loop; shorter paths use the same loop (they appear quicker
  but the template's short edges are the intended minimum, about 100 units); long arcs use
  `.slow` (2x) so they do not race.
- Stagger several dots on one path with negative `animation-delay` values.
- Colour the dot by the role of what flows (`a` accent, `i` info, `s` success).
- Skip dots on pure annotation lines.

## 6. Micro motion (two to four per picture)

- Sparkles: `sk-star` pulse, three to six total, around the headline or key idea.
- One spinning gear, one blinking cursor, or a check that draws itself with
  `stroke-dashoffset`.
- All durations are `--sk-loop` or simple fractions of it, so the picture loops cleanly
  if it is ever captured as a GIF.
- `prefers-reduced-motion: reduce` disables all of it.

## 7. Colour

- Wash: `color-mix(in srgb, var(--accent) 12%, var(--surface-1))`. Adjacent panels use
  different roles. Three to four washes at most.
- Cards stay on `--surface-2`, not washed.
- Ink is `currentColor` and is the only text colour; muted notes use `--on-surface-muted`.
- No gradients, glows, drop shadows or neon highlighters. Focus comes from sparkles and
  the headline.

## 8. Type

Font stack: `'Gaegu','Nanum Pen Script','Comic Sans MS','Segoe Print',cursive`.
No font is bundled, so a machine without the first two falls back to a system face and the
diagram must still read. Sizes in a 960 wide viewBox: headline 22 to 26, band title 26,
card label 19, edge note 14 to 16.
