---
sidebar_position: 2
title: "Quick start"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="빠른-시작" />
<span id="1-파일-만들기" />
<span id="2-html-빌드" />
<span id="3-브라우저에서-열기" />
<span id="기본-조작법" />
<span id="핵심-문법-요약" />
<span id="슬라이드-구분" />
<span id="디렉티브" />
<span id="프래그먼트" />
<span id="컬럼-레이아웃" />
<span id="다음-단계" />


# Quick start

## Create the source {#create-the-source}

Save this as `my-talk.md`. The literal `[요약]` marker means “summary” and is checked by the current structured-notes validator (`NOTE_STRUCTURE` is a warning when the marker is missing); the notes themselves remain English.

```markdown
---
remarp: true
title: "Build with evidence"
speaker:
  name: "Alex Morgan"
  title: "Engineer"
  company: "Example team"
audience: "Project contributors"
level: "200"
quiz: false
duration: 5
lang: en
---

# Build with evidence

A short introduction to the review loop.

:::notes
{timing: 2min}
[요약]
- Introduce the review loop.
- Connect each change to observable behavior.
- Explain how the checks support the conclusion.

Introduce the example and ask the audience to keep one recent change in mind.
Explain that the next slide separates reading the code, exercising its behavior,
and recording what the result proves. This keeps the review concrete and gives
the next reviewer enough evidence to reproduce the conclusion.
:::

---
@type: content

## Verify each change

- Read the affected code {.click order=1}
- Run the relevant checks {.click order=2}
- Record the result {.click order=3}

:::notes
{timing: 3min}
[요약]
- Start from the changed behavior.
- Choose checks that exercise it.
- Report evidence and limits.

Explain why a successful build alone may not exercise the changed behavior.
Walk through one relevant test and describe what its passing result proves.
{cue: transition}
Next, use the same method when reviewing a teammate's change.
:::

```

## Validate and build {#validate-and-build}

Run from the marketplace repository root:

```bash
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py validate my-talk.md
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py build my-talk.md -o /var/tmp/my-talk --lang en
mkdir -p /var/tmp/my-talk/common
cp -R plugins/aws-content-plugin/skills/reactive-presentation/assets/. /var/tmp/my-talk/common/
```

Single-file builds emit HTML only; the copy step supplies the CSS and JavaScript referenced from `common/`. Open `/var/tmp/my-talk/default.html` and exercise the fragments. Right/Space advances; Left reverses; P opens presenter view. Run content review before publication.

## Extend the deck {#extend-the-deck}

Use `@type` for compare/tabs/quiz/checklist/timeline/Canvas slides, `@layout` for columns, and `:::notes` for speaking guidance. For multi-file decks put shared frontmatter in `_presentation.md`. See the syntax and CLI reference for exact supported fields and commands.

## Related links {#related-links}

- [Frontmatter](./syntax/frontmatter.md)
- [directives](./syntax/directives.md)
- [fragments](./syntax/fragments.md)
- [Canvas DSL](./syntax/canvas-dsl.md)
