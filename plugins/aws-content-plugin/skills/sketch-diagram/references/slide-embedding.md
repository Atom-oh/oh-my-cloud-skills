# Embedding in a Remarp slide

1. Copy the `<svg>` from the finished template into a `:::html` block (blank lines before
   and after, so it is not wrapped in a `<p>`).
2. Put the `sk-*` rules in a `<style>` element at the top of the same `:::html` block. Do
   not use `:::css`: that block is only for per-slide `<target>` overrides of built-in
   elements and silently drops ordinary rules. Delete the PREVIEW-ONLY token block: the
   deck already provides `--surface-*`, `--on-surface*` and the role colours.
3. Keep `max-height: 500px` on the wrapper (already in `.sk-wrap`); the slide body already
   has padding.
4. Give the slide a short assertive title, as for any slide, and let the diagram carry the
   picture. A sketch diagram does not replace the explanatory text the audience needs; say
   the point in the title and the notes.
5. Notes: follow "Spoken script voice" in the reactive-presentation format guide. Describe
   what the dots are doing in plain words ("여기서 질문이 문서랑 만나고요").
6. Run `remarp_to_slides.py validate`. The hex values in the preview token block are the
   usual cause of `RAW_HEX`; remove them. Inline `style="offset-path:..."` is the only
   inline style in the diagram, because each dot needs its own path.

```markdown
---
@type: content
## 한 번 돌면 다음은 쉬워져요

:::html

<style>
.sk-wrap { ... }
</style>
<div class="sk-wrap"> <svg class="sk-svg" viewBox="0 0 960 450" ...> ... </svg> </div>
:::

:::notes
{timing: 1min}
[요약]
• 질문이 맥락을 만나 판단과 실행을 거쳐 결과로 모인다
• 부족하면 처음으로 돌아가는 고리가 있다
:::
```

## Fonts

A Hangul handwriting face (for example Gaegu or Nanum Pen Script) looks best but is not
bundled. If the deck must be self-contained, subset the font to the glyphs used and inline
it as a data URI woff2 in the slide's `<style>`; otherwise rely on the fallback stack.

## Choosing sketch versus other diagram forms

Use sketch-diagram for a quick, friendly overview at the start of a section. Use
`line-art-scene` when the audience should be walked through steps with a moving camera,
callouts and a side panel, and `:::archify` when they must explore a precise architecture.
