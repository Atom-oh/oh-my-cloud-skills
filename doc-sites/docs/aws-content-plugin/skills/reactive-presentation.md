---
sidebar_position: 1
title: "Reactive presentation skill"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="trigger-keywords" />
<span id="provided-resources" />
<span id="assets" />
<span id="scripts" />
<span id="references" />
<span id="icons" />
<span id="key-features" />
<span id="remarp-format-recommended" />
<span id="pptx-theme-extraction" />
<span id="data-visualization-patterns" />
<span id="typography-hierarchy" />
<span id="css-only-charts" />
<span id="kpi-card-layout" />
<span id="chartjs-integration" />
<span id="canvas-vs-html-decision-guide" />
<span id="the-4-box-rule" />
<span id="decision-matrix" />
<span id="html-architecture-pattern" />
<span id="remarp-workflow-detail" />
<span id="step-1-theme-setup-optional" />
<span id="step-2-content-planning" />
<span id="step-3-create-project-structure" />
<span id="step-4-write-remarp-content" />
<span id="step-5-build-html" />
<span id="step-6-review--iterate" />
<span id="step-7-enhancement" />
<span id="step-8-quality-review" />
<span id="step-9-deploy" />
<span id="interactive-pattern-guide" />
<span id="simulator-pattern" />
<span id="calculator-pattern" />
<span id="dashboard-pattern" />
<span id="speaker-notes-writing-guide" />
<span id="requirements" />
<span id="structure-template" />
<span id="good-example" />
<span id="bad-example-what-not-to-do" />
<span id="slide-types" />
<span id="keyboard-shortcuts" />
<span id="usage-example" />
<span id="quality-review-required" />


# Reactive presentation skill

Build interactive HTML decks from Remarp, with speaker notes, keyboard navigation, light/dark themes, quizzes, tabs, diagrams, and optional PowerPoint theme extraction.

## Workflow

Plan the audience, message, blocks, and timing. Use `_presentation.md` for shared metadata and numbered `.md` files with `remarp: true` for blocks. Author slide directives, fragments, notes, and references; validate; build; inspect the rendered deck; revise; run content review before publication.

## Content and interaction

Supported slide forms include content, code, compare, Canvas, quiz, tabs, timeline, and checklist. Use native HTML/CSS grids for KPI cards, charts, grouped architectures, and readable layouts. Use `:::script` for calculators or simulators with real input/output state. Canvas is limited to simple linear diagrams with at most four boxes/icons; groups and branches use HTML/CSS.

## Design and notes

Use semantic tokens and class-based themes. Brand input uses `--pptx-*` variables consumed by the framework. Keep type hierarchy and contrast clear, use the shared AWS icon library, and include useful notes explaining the message, practical implications, audience cues, and transition.

## Tools and exports

The source directory contains the converter, theme extractor, export helpers, framework assets, icons, and reference patterns. `build`, `sync`, `migrate`, `issues`, and `validate` are converter subcommands. Browser exports and the screenshot-based PPTX helper are distinct from native editable PowerPoint generation.

[Build CLI](/docs/remarp-guide/build-cli) · [Syntax](/docs/remarp-guide/syntax/frontmatter) · [Design tokens](/docs/remarp-guide/themes/css-variables)


[Skill, resources, and quality requirements](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/reactive-presentation/SKILL.md)
