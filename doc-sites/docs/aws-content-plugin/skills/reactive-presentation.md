---
sidebar_position: 1
title: "Reactive presentation skill"
---

# Reactive presentation skill

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

Build interactive HTML decks from Remarp, with speaker notes, keyboard navigation, light/dark themes, quizzes, tabs, diagrams, and optional PowerPoint theme extraction.

## Workflow {#workflow}

Plan the audience, message, blocks, and timing. Use `_presentation.md` for shared metadata and numbered `.md` files with `remarp: true` for blocks. Author slide directives, fragments, notes, and references; validate; build; inspect the rendered deck; revise; run content review before publication.

## Content and interaction {#content-and-interaction}

Supported slide forms include content, code, compare, Canvas, quiz, tabs, timeline, and checklist. Use native HTML/CSS grids for KPI cards, charts, grouped architectures, and readable layouts. Use `:::script` for calculators or simulators with real input/output state. Canvas is limited to simple linear diagrams with at most four boxes/icons; groups and branches use HTML/CSS.

## Navigation and detail layers {#navigation-and-detail-layers}

Hover the top-right corner to open the deck agenda. Press Cmd+K, Ctrl+K, or `/`
to search slide titles, visible content, and detail text. Search excludes speaker
notes. Agenda and search are available in the deck window and are hidden from
overview, presenter previews, measurement, and export captures.

Use a tooltip for a short explanation:

```markdown
[UDP 8472]{tip="Cilium VXLAN port"}
```

Use a slide-scoped detail block for longer content:

```markdown
[UDP 8472]{detail=vxlan-8472}

:::detail vxlan-8472 "Why UDP 8472 is required"
tip: Cilium VXLAN tunnel port between hybrid nodes

The port carries VXLAN traffic between nodes.
:::
```

The detail block must be at the top level of the same slide. Duplicate IDs and
missing references are CRITICAL `DETAIL_REF` findings. Tooltips work on hover and
keyboard focus; tip-only terms also support touch. Move onto the tooltip to keep
reading, or press Esc to dismiss it. The detail panel opens by click, Enter, or
Space and closes with Esc, an outside click, or a slide change.

## Audience-aware explanations {#audience-aware-explanations}

Explain unfamiliar terminology, industry jargon, and acronyms at their first
meaningful use in each independently viewable block. Do not assume API, JSON,
EKS, or S3 is familiar just because it is common in the industry. Repeat an
explanation after a long gap when readers would otherwise lose context, rather
than annotating every occurrence.

For **L100–200** (`level: 100`/`200`, or `beginner`/`intermediate`), give the full
name, a plain-language meaning, and a practical example or reason it matters.
Use a short, useful hover summary and put multi-sentence teaching in a detail
panel. L300–400 can be more concise but still needs explanations for unfamiliar
domain-specific terms. Speaker notes are not a substitute for these audience-facing
explanations.

```markdown
[API]{detail=api}

:::detail api "How an API connects applications"
tip: API (Application Programming Interface): an agreed way for programs to request data or actions.

An API defines which requests a program accepts and what it returns.
For example, a weather app requests a forecast instead of collecting sensor data itself.
:::
```

- **Charts:** add a nearby “How to read this chart” trigger explaining the axes,
  units, population/timeframe, comparison baseline, takeaway, and limitations or
  source as applicable to the chart and data. Use an accessible text caption, not
  the chart image itself, as the detail trigger.
- **Quotations:** preserve the quoted text and show its attribution. Add a
  “Quote context” trigger with the source/context and why the quote matters.
  Mark illustrative or unverified quotes explicitly; never invent a citation.
- **Static exports:** keep essential claims, chart labels/units, the takeaway,
  and attribution visible. Hover and detail layers are not included in exported
  slide images.

Content review checks explanation coverage and suitability for the audience;
the compiler checks annotation structure, not jargon recognition or factual quality.

## Copy gates {#copy-gates}

`EM_DASH`, `AI_TONE` and `AUDIENCE_TONE` are source validation warnings that must be resolved in
the authoring loop. `SENTENCE_RUNON` is a rendered measurement warning. Keep each
card description to one claim line plus an optional reason line, then put
additional explanation in `:::detail`.

## Design and notes {#design-and-notes}

Use semantic tokens and class-based themes. Brand input uses `--pptx-*` variables consumed by the framework. Keep type hierarchy and contrast clear, use the shared AWS icon library, and include useful notes explaining the message, practical implications, audience cues, and transition.

## Tools and exports {#tools-and-exports}

The source directory contains the converter, theme extractor, export helpers, framework assets, icons, and reference patterns. `build`, `sync`, `migrate`, `issues`, and `validate` are converter subcommands. Browser exports and the screenshot-based PPTX helper are distinct from native editable PowerPoint generation.

[Build CLI](/docs/remarp-guide/build-cli) · [Syntax](/docs/remarp-guide/syntax/frontmatter) · [Design tokens](/docs/remarp-guide/themes/css-variables)


[Skill, resources, and quality requirements](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/reactive-presentation/SKILL.md)
