---
sidebar_position: 10
title: "Well-Architected agent"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="well-architected-framework-review-agent" />
<span id="트리거-키워드" />
<span id="6-pillar-평가" />
<span id="스코어링" />
<span id="전문-에이전트-위임" />
<span id="사용-예시" />
<span id="전체-리뷰" />
<span id="특정-필러-집중" />
<span id="출력-형식" />
<span id="mcp-연동" />


# Well-Architected agent

Review operational excellence, security, reliability, performance efficiency, cost optimization, and sustainability.

## Diagnostic approach

Collect evidence for each pillar, score against the source rubric, rank findings by severity and impact, and propose an AS-IS to TO-BE roadmap with owners, prerequisites, verification, and sequencing. Do not score absent evidence as a verified control.

## Evidence and handoff

Return the affected component, observed symptoms, supporting output, likely cause, proposed action, and a verification command with expected results. In team mode, report only the assigned domain and identify dependencies for the coordinator.

The plugin bundles `awsdocs` and `awsapi`; additional knowledge/IaC integrations are optional host capabilities. Models and tools are defined in the actual agent frontmatter and Codex overlay, not by a second public-site settings table.

[Agent commands and decision tree](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/agents/wellarchitected-agent.md)
