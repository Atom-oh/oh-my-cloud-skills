---
sidebar_position: 4
title: "GitBook skill"
---

# GitBook skill

{/* Legacy section links retained after the English rewrite. */}
<span id="trigger-keywords" />
<span id="use-cases" />
<span id="provided-resources" />
<span id="references" />
<span id="project-structure" />
<span id="component-patterns-detail" />
<span id="hints-callouts" />
<span id="tabs" />
<span id="code-blocks" />
<span id="basic-code-block" />
<span id="code-with-title-and-line-numbers" />
<span id="supported-languages-40" />
<span id="expandable-sections" />
<span id="embedded-content" />
<span id="file-download" />
<span id="video-embed" />
<span id="external-page-embed" />
<span id="images-with-caption" />
<span id="sized-image" />
<span id="summarymd-writing-guide" />
<span id="basic-structure" />
<span id="syntax-rules" />
<span id="multi-level-hierarchy-example" />
<span id="best-practices" />
<span id="multi-language-setup" />
<span id="directory-structure-for-koreanenglish" />
<span id="gitbookyaml-for-multi-language" />
<span id="content-parity-rules" />
<span id="diagram-integration" />
<span id="drawio-png" />
<span id="animated-svg-iframe" />
<span id="mermaid-inline" />
<span id="korean-heading-anchors" />
<span id="quick-start-commands" />
<span id="usage-example" />
<span id="quality-review-required" />

Build a structured documentation site with navigable topic pages and rich GitBook components.

## Structure {#structure}

Use README.md for the entry page, SUMMARY.md for navigation, .gitbook.yaml for source configuration, and topic directories for the actual pages. Keep navigation depth shallow enough to scan and ensure every listed path exists.

## Components {#components}

Use hints for warnings and tips, tabs for alternatives, titled code fences for commands/files, expandable sections for detail, and images with useful captions and alt text. Downloads, videos, and external embeds must have valid targets. Integrate static Draw.io exports, supported animated embeds, or Mermaid diagrams according to the output format.

## Language and anchors {#language-and-anchors}

Use the language requested by the user. For a deliberately multilingual site, create explicit language roots and align navigation/content. Preserve published anchors during renames; exact syntax or historical example text can remain quoted with an English explanation.

## Validate {#validate}

Check SUMMARY.md, relative paths, component syntax, image references, and cross-links. Run the site's build and inspect important pages before content review and authorized publication.


[Skill, resources, and quality requirements](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/gitbook/SKILL.md)
