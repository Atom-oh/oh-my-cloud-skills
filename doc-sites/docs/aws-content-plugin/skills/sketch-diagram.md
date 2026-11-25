---
sidebar_position: 9
title: "Sketch diagram skill"
---

# Sketch diagram skill

Create a light, hand-drawn animated concept diagram for a slide opener or a friendly explainer: wobbly ink lines, pale washes, doodle icons, and small dots that travel along the real flow.

## When to use it {#when-to-use-it}

Use it for the first picture of a section, where the audience needs the whole idea at a glance: a loop, a pipeline, a hub with spokes, a comparison, or a timeline. For exact AWS boundaries and official icons, use architecture-diagram or animated-diagram. For a walkthrough that advances one step per key press, use [line-art-scene](/docs/aws-content-plugin/skills/line-art-scene).

## What it produces {#what-it-produces}

One self-contained block: a `<style>` element and an inline SVG with an `aria-label` that tells the flow in one sentence. The hand-drawn look comes from one shared SVG displacement filter plus gently bowed paths, and the colors come from the deck's theme tokens, so it reads in both light and dark themes.

## Rules that keep it readable {#rules-that-keep-it-readable}

Choose the layout from the natural shape of the topic instead of a default row of boxes. Write the flow in one sentence first (what moves, where it forks, merges or loops) and put moving dots on every path that carries it. Keep labels short, use one doodle icon per card, and keep sparkles to a handful. With `prefers-reduced-motion` the animation is off and the still picture must remain complete.

## Embed and verify {#embed-and-verify}

Put the styles and the SVG together in one `:::html` block of a Remarp slide. A `:::css` block only accepts per-slide target overrides and drops ordinary rules, so do not use it for this. Validate the deck, open the result in both themes, and write the speaker notes in the presenter's natural voice.

[Skill, layouts, recipes, and template](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/sketch-diagram/SKILL.md)
