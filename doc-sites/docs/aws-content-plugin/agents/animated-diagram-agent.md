---
sidebar_position: 3
title: "Animated diagram agent"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="핵심-기능" />
<span id="아키텍처-패턴" />
<span id="색상-코딩-표준" />
<span id="워크플로우" />
<span id="step-1-requirements-analysis" />
<span id="step-2-static-background" />
<span id="step-3-animation-layer" />
<span id="step-4-interactive-legend" />
<span id="애니메이션-타이밍-가이드라인" />
<span id="interactive-animation-pattern" />
<span id="시나리오-템플릿" />
<span id="출력물" />
<span id="사용-예시" />
<span id="협업-워크플로우" />


# Animated diagram agent

Adds visible traffic flow, scaling, deployment, and failover behavior to architecture diagrams. SMIL suits repeated SVG motion; JavaScript/CSS state machines suit controls, scenario changes, and resource lifecycle simulation.

## Workflow {#workflow}

Build a readable static architecture first, then add motion, a legend, labels, and controls. Keep semantic colors consistent, stagger events so their order is clear, and verify reset/replay behavior. Review both the still frame and the animated result.

## Output and verification {#output-and-verification}

Return the editable source, rendered output, relevant build commands, and verification evidence. The content-review gate applies before completion/publication; a successful file write alone is not a passing review.

[Agent contract](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/agents/animated-diagram-agent.md) · [Skill guide](/docs/aws-content-plugin/skills/animated-diagram)
