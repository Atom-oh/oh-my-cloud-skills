# Embedding in a Remarp slide

```markdown
---
@type: content
@fit: off
## One request, four stops

:::html

<div id="scene-request">
<p>One sentence that tells the whole flow.</p>
<ol>
<li>Step one in a few words</li>
<li>Step two in a few words</li>
</ol>
</div>
:::

:::script
import('./common/line-art-scene/flowscene.js').then(function (m) {
  m.mount('#scene-request', { /* scene spec, see scene-spec.md */ });
});
:::

:::notes
{timing: 2min}
[요약]
• ...
Sentence that finishes step one.↓ Sentence that finishes step two.↓
:::
```

1. **`@fit: off`** is required. The fit engine would otherwise shrink the whole body and the side
   panel is clipped. The scene sizes itself to the slide body.
2. **Host**: a `<div id="...">` in `:::html` (blank lines around it) that holds a static
   fallback: one `<p>` telling the whole flow and an `<ol>` with one short item per step. The
   module replaces the fallback with the stage and side panel when it mounts. PDF export needs
   it: the print view copies only each slide's markup and runs no `:::script`, so without a
   fallback the slide body is blank. Use plain `<p>`, `<ol>` and `<li>`, with no extra `<div>`,
   no inline style and no `fs-` classes (their styles are not loaded in the print view). Keep the
   host id unique per slide.
3. **Mount**: in `:::script`, using a dynamic `import()` so a failed load does not break the deck.
   The module finds the deck's `registerSlideAction`, so Down and Up step the scene and the
   presenter window shows the step count.
4. **Assets**: when the built page contains `common/line-art-scene/`, the build copies this
   skill's `assets/*.js` and `flowscene.css` there. Each icon URL written as
   `./common/aws-icons/<category>/<file>.svg` is copied by the existing icon pass. No manual
   copy is needed. The ZIP export (`ExportUtils.downloadZIP`, the ZIP buttons in `toc.html`) is
   not a runnable copy of such a deck: it skips `common/line-art-scene/` and the icon URLs inside
   the spec, and it stores `common/` beside the deck folder while a built page loads `./common/`
   from its own folder. An unpacked ZIP shows the static fallback and the console reports a
   failed module import. To share or re-host a deck with a scene, publish or copy the whole build
   output directory.
5. **Notes**: exactly one `↓` per press, right after the sentence that finishes a step, never
   saying what to press (see reactive-presentation `references/step-guidance.md`). The count
   equals the number of `phases`. Voice follows "Spoken script voice" in the Remarp format guide.
6. **Serve over http.** Module imports are blocked on `file://`. GitHub Pages and
   `python3 -m http.server` are fine. A failed import leaves the static fallback in place, so
   check the console.
7. **Order of slides**: a scene replaces a slide's whole body. Do not put other `:::html` content
   next to it.

Without a deck on the page (a standalone preview) the module binds ArrowDown and ArrowUp itself.
