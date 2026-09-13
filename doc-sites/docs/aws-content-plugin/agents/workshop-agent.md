---
sidebar_position: 6
title: "Workshop agent"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="핵심-기능" />
<span id="디렉토리-구조" />
<span id="front-matter-필수" />
<span id="workshop-studio-디렉티브" />
<span id="잘못된-예-hugo" />
<span id="올바른-예-workshop-studio" />
<span id="alert" />
<span id="code" />
<span id="tabs" />
<span id="image" />
<span id="mermaid-diagrams" />
<span id="베스트-프랙티스" />
<span id="do" />
<span id="dont" />
<span id="이중언어-콘텐츠-가이드라인" />
<span id="출력물" />
<span id="사용-예시" />
<span id="협업-워크플로우" />


# Workshop agent

Creates AWS Workshop Studio projects with contentspec.yaml, ordered modules/labs, frontmatter, directives, and optional infrastructure templates.

## Workflow

Explain prerequisites, expected results, validation, and cleanup in every lab. Use Workshop Studio alert, code, tabs, image, expand, and Mermaid syntax; do not use Hugo shortcodes or chapter:true. Keep required resources and IAM permissions specific. Produce language pairs only when the brief requests them.

## Output and verification

Return the editable source, rendered output, relevant build commands, and verification evidence. The content-review gate applies before completion/publication; a successful file write alone is not a passing review.

[Agent contract](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/agents/workshop-agent.md) · [Skill guide](/docs/aws-content-plugin/skills/workshop-creator)
