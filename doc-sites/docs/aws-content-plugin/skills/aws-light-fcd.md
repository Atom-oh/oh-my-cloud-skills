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

## Use this workflow

Choose this skill when the deliverable must be an editable AWS light `.pptx`. Use reactive-presentation for interactive web slides and its screenshot-based export when that is the desired result.

## Build

Read the kit and reference layouts; plan a coherent narrative; use native PowerPoint shapes/text where editing matters; resolve icons through `kit.icon()`; inspect slide layout; build and embed fonts using the supplied tooling.

```bash
NODE_PATH=$(npm root -g) node build.js
python3 scripts/embed_fonts.py deck.pptx
```

These commands run from a prepared deck workspace containing the generated build script and supplied font helper. Check the skill for setup and paths.

## Assets and verification

The kit provides covers, agendas, statistics, AgentCore cards, and architecture layouts. `kit.icon()` intentionally uses the sibling reactive-presentation icon library. Keep editable objects aligned, use canonical assets, inspect the exported slides, and run content review before publication.


[Skill, resources, and quality requirements](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/aws-light-fcd/SKILL.md)
