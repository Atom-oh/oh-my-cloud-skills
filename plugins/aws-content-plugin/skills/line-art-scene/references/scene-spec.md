# Scene spec

`mount(selector, spec)` takes one plain object. Everything but `phases` is optional. Strings in
`say` are inserted as HTML so you can use `<b>`; all other strings are escaped. The spec is
authored content, never user input.

## World

| Field | Meaning |
|---|---|
| `aria` | One sentence describing the whole flow (the SVG `aria-label`) |
| `W`, `H` | viewBox size, default 900 x 520. Match the stage aspect (about 1.5) so content fills it |
| `K`, `OX`, `OY` | Projection scale and origin. Screen x = `OX + x*K + y*K*0.5`, screen y = `OY - y*K*0.3 - z*K` |
| `zones` | Ground slabs: `{ box:[x,y,z,w,d,h], label, labelAt:[x,y,z], icon?, sub? }`. `icon` is a literal icon URL |
| `parts` | Named things: `{ id: { boxes:[[x,y,z,w,d,h]], clouds:[[[x,y,z],rx,ry,label]], pipes:[[a,b]], rings:[[[x,y,z],rx,ry]] } }` |
| `icons` | Icons standing on parts: `{ part, at:[x,y,z], src, size? }`. `src` is a literal URL |
| `wires` | `{ id: { pts:[[x,y,z],...], cls? } }`. `cls` `fs-alt` dashes the wire, `fs-bad` marks a forbidden path |
| `callouts` | Numbered labels: `{ id, n, anchor:[x,y,z], at:[screenX, screenY], title, sub? }` |
| `marks` | An X shown when a `block` packet stops: `{ id, at:[x,y,z] }` |
| `tags` | Text on the scene: `{ id, at:[x,y,z], text, show:[phaseKeys], overview?:false, cls?, anchor? }` |
| `figures` | Small people, see below |

Icon URLs must be the literal form `./common/aws-icons/<category>/<file>.svg` where category is
`services`, `groups`, `categories` or `resources`. The build scans the page for that pattern and
copies only the referenced files.

## Figures

`{ at:[x,y,z], dir?:1|-1, scale?:0.9, colour?, pose?:'stand'|'type', busy?, sound?, glyphs?, gait?:'walk'|'shuffle'|'run', goto?:{phaseKey:x}, act?:{phaseKey:'type'|'raise'} }`

- `goto` makes the figure walk along x to a target while that phase is active, feet planted.
  Under reduced motion it appears at the target at once.
- `act` per phase: `type` puts both hands on a keyboard, `raise` lifts a hand.
- `busy` adds nodding, a sweat drop and floating glyphs; `sound` is the word that flickers beside
  the typist (any language, default none); `glyphs` is the list of floating strings. Reduced
  motion hides these effects.

## Side panel

| Field | Meaning |
|---|---|
| `overview` | `{ label, title, say, lines? }` for step 0 |
| `code` | Lines shown in the panel; phases highlight them by 1 based number in `lines` |
| `checks`, `checksDoneAfter` | A checklist that lights up during a phase with `checks: true`; stays lit after the phase key given |
| `hint` | Text for the hint line, default English |

## Phases

Each item of `phases` is one Down press:

| Field | Meaning |
|---|---|
| `key`, `label`, `title`, `say` | Identity and text of the step |
| `focus` | Part ids to highlight, others dim; the camera frames them. First id is emphasised |
| `badge` | Callout id to highlight |
| `packet` | `{ wire, span:[from,to], mode?, colour?, hold?, stopAt?, waitAt?, mark? }` |
| `lines` | Panel code lines to highlight |
| `checks` | `true` lights the checklist during this step |
| `d`, `lead` | Duration (default 3 s) and seconds before the packet starts (default 0.9); the camera moves only during the lead |
| `cam`, `zoom`, `segment` | Frame these ids instead of `focus`; minimum frame width fraction; `false` stops the frame growing to fit the packet path |

Packet modes: default travels `span[0]` to `span[1]`; `pingpong` goes and returns; `wait` pauses
at `waitAt` until `hold` then continues; `block` stops at `stopAt`, turns `--danger` and shows
`mark`.

## Hooks and mode

`frame(ctx)` is called every draw with `{ parts, marks, tags, wires, svg, lit, ph, u, t, all }`
for custom per frame tweaks. `mode: 'auto'` plays the phases as one looping film (a click pauses)
instead of stepping; use it only where there is no presenter.
