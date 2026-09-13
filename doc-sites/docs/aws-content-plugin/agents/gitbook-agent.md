---
sidebar_position: 5
title: "GitBook agent"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="핵심-기능" />
<span id="프로젝트-구조" />
<span id="설정-파일" />
<span id="gitbookyaml" />
<span id="summarymd-navigation" />
<span id="gitbook-컴포넌트" />
<span id="hints-callouts" />
<span id="tabs" />
<span id="code-blocks" />
<span id="expandable-sections" />
<span id="images" />
<span id="페이지-템플릿" />
<span id="네비게이션-베스트-프랙티스" />
<span id="다이어그램-통합" />
<span id="drawio-png-static-architecture" />
<span id="animated-svg-dynamic-diagrams" />
<span id="출력물" />
<span id="사용-예시" />
<span id="협업-워크플로우" />


# GitBook agent

Creates navigable GitBook documentation with README.md, SUMMARY.md, .gitbook.yaml, topic pages, assets, and cross-references.

## Workflow

Plan navigation before writing pages. Use GitBook hints, tabs, titled code blocks, expandable sections, images, downloads, and embeds where they help the reader. Match SUMMARY.md to actual files and verify links. Add language trees only when requested and keep their content aligned.

## Output and verification

Return the editable source, rendered output, relevant build commands, and verification evidence. The content-review gate applies before completion/publication; a successful file write alone is not a passing review.

[Agent contract](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/agents/gitbook-agent.md) · [Skill guide](/docs/aws-content-plugin/skills/gitbook)
