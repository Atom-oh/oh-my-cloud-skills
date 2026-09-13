---
sidebar_position: 6
title: "Speaker notes"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="발표자-노트" />
<span id="기본-문법" />
<span id="타이밍-마커" />
<span id="큐-마커" />
<span id="큐-타입-레퍼런스" />
<span id="노트-작성-가이드라인" />
<span id="권장-사항" />
<span id="품질-기준-필수" />
<span id="모범-사례" />
<span id="프레젠터-뷰" />
<span id="프레젠터-뷰-구성" />
<span id="레이아웃-조절" />
<span id="슬라이드와-동기화" />
<span id="전체-예제" />


# Speaker notes

Place speaking guidance in `:::notes`; it is available in presenter view rather than the audience slide.

```markdown
:::notes
{timing: 3min}
[요약]
- Explain the decision.
- Connect it to the measured evidence.
- Identify the remaining limitation.

Start by describing the observed failure and why it matters to the user.
Walk through the evidence supporting the selected fix, then explain what
its verification covers and which conditions still require follow-up.
{cue: question}
Ask which assumption the audience would test next.
{cue: transition}
Move to the example that exercises that assumption.
:::
```

## Exact marker and language

The current validator looks for the literal `[요약]` marker, meaning “summary,” on applicable content slides. Preserve that syntax even in an English deck. Write the bullets and spoken script in English; do not translate a required parser literal into an unsupported alias.

## Timing and cues

Use `{timing: 3min}` or `{timing: 90s}`. Cue markers such as `{cue: demo}`, `{cue: pause}`, `{cue: question}`, `{cue: transition}`, `{cue: poll}`, and `{cue: break}` mark delivery actions. Explain practical implications and transitions instead of repeating slide text.

## Validation

The source validator distinguishes missing, short, and unstructured notes, with slide-type exemptions. Its guidance recommends at least 150 characters and fuller notes where needed; the exact severity thresholds live in the validator. Keep source validation separate from the independent content-review score.

## Presenter view

P opens a separate view with current/next slide, notes, timing, and navigation. Splitters resize the slide/notes regions and store their ratios locally. The presenter and main window synchronize through the framework's channel; test that behavior with the actual generated deck.

[Notes validation rules](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py)
