---
sidebar_position: 2
title: "Architecture diagram agent"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="핵심-기능" />
<span id="캔버스-크기" />
<span id="aws-그룹-박스-스타일" />
<span id="aws-cloud" />
<span id="region" />
<span id="vpc" />
<span id="aws-아이콘-카테고리-색상" />
<span id="parent-계층-규칙" />
<span id="워크플로우" />
<span id="아이콘-그리드-배치" />
<span id="출력물" />
<span id="사용-예시" />
<span id="협업-워크플로우" />


# Architecture diagram agent

Creates AWS Draw.io diagrams through the YAML layout generator or hand-authored XML for unsupported structures. Outputs editable .drawio plus a reviewed PNG or SVG export.

## Workflow

Use canonical design tokens for icon size, subnet colors, fonts, and spacing. Vertex parents follow Cloud → Region → VPC → Subnet → service; edges stay under parent="1". Validate XML and cell counts, require layout score at least 80, export, and inspect the render for truncation or overlap.

## Output and verification

Return the editable source, rendered output, relevant build commands, and verification evidence. The content-review gate applies before completion/publication; a successful file write alone is not a passing review.

[Agent contract](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/agents/architecture-diagram-agent.md) · [Skill guide](/docs/aws-content-plugin/skills/architecture-diagram)

[Canonical diagram tokens](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/architecture-diagram/references/design-tokens.md)
