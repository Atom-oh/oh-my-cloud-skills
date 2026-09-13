---
sidebar_position: 8
title: "AWS light PowerPoint skill"
---

# AWS light PowerPoint skill

{/* Legacy section links retained after the English rewrite. */}
<span id="aws-light-fcd-skill" />
<span id="트리거-키워드" />
<span id="언제-이-스킬을-쓰나-그리고-안-쓰나" />
<span id="제공-자산" />
<span id="워크플로우" />
<span id="핵심-규칙-non-negotiable" />
<span id="제공-자산-위치" />

Create native editable PowerPoint decks with the shipped AWS light theme, Pretendard typography, gradient accents, reusable layouts, and AWS/AgentCore icon helpers.

## Use this workflow {#use-this-workflow}

Choose this skill when the deliverable must be an editable AWS light `.pptx`. Use reactive-presentation for interactive web slides and its screenshot-based export when that is the desired result.

## Build {#build}

Read the kit and reference layouts; plan a coherent narrative; use native PowerPoint shapes/text where editing matters; resolve icons through `kit.icon()`; inspect slide layout; build and embed fonts using the supplied tooling.

Run from the prepared deck workspace. Set `PPTX_SKILL` to the actual installed
`aws-light-fcd` directory so the helper retains access to its bundled fonts:

```bash
PPTX_SKILL="/absolute/path/to/installed/plugin/skills/aws-light-fcd"
NODE_PATH=$(npm root -g) node build.js
python3 "$PPTX_SKILL/scripts/check_pptx.py" deck.pptx
python3 "$PPTX_SKILL/scripts/embed_fonts.py" deck.pptx
```

The workspace contains the generated `build.js`. If the font helper is copied
elsewhere, pass `--fonts-dir` pointing to the supplied font directory; copying the
script alone does not preserve its default `assets/fonts` lookup.
Before embedding, `check_pptx.py` must score at least 80 with zero `[geometry]`
findings. Content review remains required before publication.

## Assets and verification {#assets-and-verification}

The kit provides covers, agendas, statistics, AgentCore cards, and architecture layouts. `kit.icon()` intentionally uses the sibling reactive-presentation icon library. Keep editable objects aligned, use canonical assets, inspect the exported slides, and run content review before publication.


[Skill, resources, and quality requirements](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/aws-light-fcd/SKILL.md)
