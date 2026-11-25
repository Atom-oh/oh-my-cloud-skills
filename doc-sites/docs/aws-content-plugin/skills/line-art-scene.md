---
sidebar_position: 10
title: "Line-art scene skill"
---

# Line-art scene skill

Walk an audience through a flow one step per key press, in a hand-drawn scene with a moving camera, a packet that follows real paths, numbered callouts, small line-art people, and a side panel.

## When to use it {#when-to-use-it}

Use it to explain a request path, pipeline, or protocol in several steps. For a quick overview at the start of a section, use [sketch-diagram](/docs/aws-content-plugin/skills/sketch-diagram). For exact AWS boundaries as a record, use architecture-diagram, and for a diagram the audience can pan and zoom, use the Remarp `:::archify` block.

## What you write {#what-you-write}

The scene is data: one object that lists zones, parts, wires, callouts, figures, and the phases. Step 0 is always the full picture. Each Down press plays the next phase once and holds its end state, Up goes back, and leaving and re-entering the slide resets to step 0. The shipped template, a generic request walkthrough, builds as is.

## Embedding and limits {#embedding-and-limits}

The slide uses `@fit: off` and a `:::html` host element that holds a static fallback: one sentence and a numbered list of the steps. The scene mounts from a `:::script` block and replaces the fallback. PDF export runs no slide scripts, so a PDF shows the fallback. The build copies the scene modules and referenced AWS icons into the deck, and the page must be served over http because browsers block module imports from `file://`. The ZIP export from the table of contents does not carry the scene, so share or host the whole build directory instead.

## Verify {#verify}

Validate and build the deck, serve it, and step through every phase in light and dark. With reduced motion on, each press shows the step's end state at once and nothing keeps moving.

[Skill, references, and template](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/line-art-scene/SKILL.md)
