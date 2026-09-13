---
sidebar_position: 1
title: "Frontmatter"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="글로벌-frontmatter" />
<span id="필드-레퍼런스" />
<span id="기본-필드" />
<span id="speaker-객체" />
<span id="blocks-배열" />
<span id="theme-객체" />
<span id="transition-객체" />
<span id="keys-객체" />
<span id="블록-파일-frontmatter" />
<span id="로컬-frontmatter-필드" />
<span id="pptx-테마-소스" />
<span id="예제-완전한-글로벌-frontmatter" />


# Frontmatter

Place YAML frontmatter at the beginning of a single-file deck or in `_presentation.md` for a multi-file project.

```yaml
---
remarp: true
version: 1
title: "Architecture review"
speaker:
  name: "Alex Morgan"
  title: "Engineer"
  company: "Example team"
audience: "Platform engineers"
level: "300"
quiz: true
duration: 30
lang: en
blocks:
  - name: fundamentals
    title: "Fundamentals"
    duration: 15
  - name: patterns
    title: "Patterns"
    duration: 15
theme:
  source: "./company-template.pptx"
  footer: auto
  pagination: true
  logo: auto
transition:
  default: slide
  duration: 400
---
```

## Metadata

`remarp: true` identifies source. `title`, `speaker`, `audience`, `level`, `quiz`, and `duration` describe the talk and its planning requirements. `version`, `date`, `event`, and `lang` carry optional format/event metadata. Use the `speaker` object; legacy `author` is only a fallback where supported.

## Blocks

Each block has a name, title, and duration; the project can also declare the source file. Local block frontmatter supplies `remarp: true`, `block`, and an optional title. Keep the block name consistent with the global list and total duration consistent with the plan.

## Theme

`theme` supports source, primary/accent/font/codeTheme, footer, pagination, and logo settings. A source can be a PPTX path or an extracted theme directory. PDF paths are recognized, but PDF extraction is currently unimplemented. Brand CSS uses `--pptx-*` input variables; semantic surface/text roles belong to the framework's light/dark scopes.

## Transitions and keys

Transition metadata supplies a default effect and duration. Key configuration is passed to the runtime as a key-to-action map, for example:

```yaml
keys:
  n: next
  p: presenter
```

Use actual keyboard event keys and runtime actions; action-to-array examples are not the current runtime contract. [Keyboard reference](/docs/remarp-guide/keyboard-shortcuts) lists supported defaults.
