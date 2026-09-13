---
sidebar_position: 1
title: "AWS content plugin"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="aws-content-plugin-개요" />
<span id="구성-요소" />
<span id="에이전트-9개" />
<span id="스킬-9개" />
<span id="워크플로우" />
<span id="프레젠테이션-워크플로우" />
<span id="다이어그램-워크플로우" />
<span id="애니메이션-다이어그램-워크플로우" />
<span id="문서-워크플로우" />
<span id="gitbook-워크플로우" />
<span id="workshop-워크플로우" />
<span id="quality-gate-필수" />
<span id="판정-기준" />
<span id="리뷰-루프" />
<span id="다이어그램-에이전트-선택-가이드" />
<span id="aws-아이콘" />


# AWS content plugin

Create web presentations, editable PowerPoint decks, diagrams, documents, workshops, brochures, and portfolio pages.

## Choose a workflow {#choose-a-workflow}

| Output | Skill or agent |
| --- | --- |
| Interactive HTML slides | reactive-presentation |
| Native editable AWS light PowerPoint | aws-light-fcd |
| AWS Draw.io architecture | architecture-diagram |
| Animated traffic or scenario diagram | animated-diagram |
| Technical report or comparison | document-agent |
| GitBook documentation | gitbook |
| Workshop Studio labs | workshop-creator |
| Product/solution landing page | brochure |
| Personal profile/portfolio | gh-home |
| Remarp issue annotations | slide-fix |

The presentation dispatcher selects web or native PowerPoint based on the requested format. Static diagrams use Draw.io; complex architecture inside a web slide uses HTML/CSS; small linear sequences can use Canvas. An external Archify composition can be embedded as an artifact, but Archify is not an additional bundled marketplace plugin.

## Build and review {#build-and-review}

Plan the audience and story; create editable source; validate the relevant format; build or export; inspect the result; then run content-review-agent. The quality gate requires PASS before publishing. Diagram exports additionally need valid XML and a layout score of at least 80.

## Shared assets {#shared-assets}

Use the shipped icon library and canonical diagram tokens. Native PowerPoint's `kit.icon()` resolves the sibling reactive-presentation library; do not duplicate it. Asset counts and current templates are discoverable from their source directories.

[Claude component manifest](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/.claude-plugin/plugin.json) · [Codex package](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/.codex-plugin/plugin.json) · [Diagram tokens](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/architecture-diagram/references/design-tokens.md)
