---
sidebar_position: 1
title: "Remarp"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="remarp-소개" />
<span id="왜-remarp인가" />
<span id="비교표" />
<span id="핵심-장점" />
<span id="1-사람이-읽을-수-있는-마크다운" />
<span id="2-프래그먼트-애니메이션" />
<span id="3-canvas-dsl" />
<span id="4-스피커-노트--타이밍" />
<span id="5-pptx-테마-통합" />
<span id="6-멀티파일-프로젝트" />
<span id="7-인터랙티브-패턴" />
<span id="8-vscode-visual-edit" />
<span id="하위-호환성" />
<span id="다음-단계" />


# Remarp

Remarp is this repository's Markdown-to-HTML presentation format. It adds slide directives, fragments, speaker notes, simple Canvas diagrams, interactive slide types, theme extraction, and multi-file projects to ordinary Markdown.

## Authoring model

Use `.md` files with `remarp: true` frontmatter. A single file can hold a short deck; a longer session can use `_presentation.md` plus numbered block files. `.remarp.md` remains supported for existing sources and editor integration.

Slides are separated by `---`. Directives such as `@type: tabs` precede content. `{.click}` reveals fragments. `:::notes` contains speaking guidance. HTML/CSS/script blocks support layouts and interactive tools beyond the small Canvas DSL.

## Workflow

Plan → author → validate → build → browser checks → content review. Edit source and rebuild; do not treat generated HTML as the durable source unless the editor explicitly writes changes back. Marp migration is available, but generated output still needs validation and review.

## Next steps

[Quick start](/docs/remarp-guide/quick-start) · [Frontmatter](/docs/remarp-guide/syntax/frontmatter) · [Build CLI](/docs/remarp-guide/build-cli) · [Editor](/docs/remarp-guide/vscode-extension)

## Related links

- [quick start](./quick-start.md)
- [Frontmatter](./syntax/frontmatter.md)
- [vscode extension](./vscode-extension.md)
- [Canvas DSL](./syntax/canvas-dsl.md)
