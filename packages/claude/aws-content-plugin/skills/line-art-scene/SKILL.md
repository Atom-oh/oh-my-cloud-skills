---
name: line-art-scene
description: "Build a stepped, hand-drawn line-art scene for a reactive-presentation slide: a sketched cutaway with a moving camera, a glowing packet that follows real paths, numbered callouts, small line-art people, and a side panel with step title, code lines and checks, advanced with the slide's Down and Up keys. Use for 'line art scene', 'flow scene', 'animated walkthrough slide', 'step-by-step animated architecture', '선화 애니메이션', '단계별 흐름 장면'. Not for a quick friendly overview (use sketch-diagram) and not for exact AWS architecture records (use architecture-diagram)."
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - AskUserQuestion
---

# Line-art scene

A slide component for walking an audience through a flow one step at a time. The scene is
drawn live in SVG with one thin pen on paper, so it stays crisp at any size, retints with the
deck theme, and can be stepped, reset and exported. Everything is data: one scene object in,
one stepped slide out.

Style and structure ideas were studied from the MIT-licensed `line-art-animation` skill
(JDhruv14); nothing is copied. The modules in `assets/` are written for this plugin.

## When to use it

| Situation | Use |
|---|---|
| Walk through a request, pipeline or protocol, one step per press, with a camera and callouts | **line-art-scene** |
| Friendly one-screen overview at the start of a section | `sketch-diagram` |
| Exact AWS boundaries and official layouts as a record | `architecture-diagram` |
| Explorable diagram the audience can pan and zoom | Remarp `:::archify` |

## Workflow

1. **Write the story as steps.** Name 3 to 8 steps. For each: what is highlighted, what
   travels, what the presenter says. Step 0 is always the full picture.
2. **Lay out the world** in the cabinet projection (x right, y into the screen, z up) as zones,
   parts, wires and callouts. Place parts on the ground slab, wires through named waypoints.
3. **Write the scene object** following `references/scene-spec.md`. Start from
   `templates/scene-example.remarp.md`, a generic request walkthrough that builds as is.
4. **Embed it** per `references/slide-embedding.md` (`@fit: off`, `:::html` host, `:::script`
   mount, one `↓` per press in the notes).
5. **Build and look at it**: validate, build, serve over http, step through every phase in light
   and dark (`references/verification.md`). Fix what you see before showing it.

```bash
python3 skills/reactive-presentation/scripts/remarp_to_slides.py validate deck.remarp.md
python3 skills/reactive-presentation/scripts/remarp_to_slides.py build deck.remarp.md -o out
python3 -m http.server 8000 --directory out   # modules need http, file:// blocks them
```

## Output

A slide with a host element (inside `:::html`) and a mount call (inside `:::script`). The build copies `assets/` to
`common/line-art-scene/` and copies each referenced AWS icon to `common/aws-icons/`:

```html
<div id="scene-request"></div>

:::script
import('./common/line-art-scene/flowscene.js').then(m => m.mount('#scene-request', SPEC));
:::
```

## House rules

- **Step 0 is the whole picture**, so PDF export and reduced motion show everything. One step
  per Down press; Up goes back; the scene resets when its slide is entered again.
- **The camera moves only when the step changes**, never while the packet travels.
- **Theme tokens only.** Ink is `currentColor`, paper is `--surface-1`. No hex, no rgba.
- **Figures** are drawn in their own space (about 95 units tall, feet on y = 120), walk with
  planted feet (`gait`), and attach springs to anything that swings. No free sines on a body.
- **Reduced motion keeps the steps** and shows each end state at once; it never freezes on the
  overview while still consuming presses.
- **Official AWS icons** come from the plugin's bundle by literal `./common/aws-icons/...` URLs
  so the build copies them. Do not draw substitutes.
- Copy style applies: no em dashes or middle dots in any label, step text or note.

## Common problems

| Symptom | Cause | Fix |
|---|---|---|
| Scene is a small box with the side panel cut off | slide fit engine shrank the content | add `@fit: off` to the slide |
| Nothing renders, console says a module failed | page opened from `file://` | serve over http (GitHub Pages, `python3 -m http.server`) |
| Icons are broken images | icon URL is not the literal `./common/aws-icons/<category>/<file>.svg` | use the literal path so the build can find and copy it |
| Down skips the scene or leaves the slide early | `registerSlideAction` index mismatch or scene mounted on another slide | mount inside the slide that holds the host element |
| Presenter window shows no step count | `state()` missing | keep the default handlers, do not replace them |
| Camera frames look cropped | focus ids not in `parts`, `callouts` or `tags` | list valid ids in `focus` or give an explicit `cam` |

## References

- `references/scene-spec.md`: every field of the scene object
- `references/style.md`: pen, paper, proportions, what to avoid
- `references/motion.md`: gait, springs, packet modes, camera and timing
- `references/slide-embedding.md`: Remarp slide, notes marks, build and icon copy
- `references/verification.md`: checks and a stepping script
- `templates/scene-example.remarp.md`: working generic example
