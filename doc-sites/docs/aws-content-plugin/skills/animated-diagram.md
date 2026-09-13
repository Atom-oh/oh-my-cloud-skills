---
sidebar_position: 3
title: "Animated diagram skill"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="trigger-keywords" />
<span id="use-cases" />
<span id="provided-resources" />
<span id="references" />
<span id="templates" />
<span id="architecture" />
<span id="color-standards" />
<span id="smil-animation-patterns" />
<span id="traffic-dots-animatemotion" />
<span id="pulsing-glow-effect" />
<span id="sequential-stagger" />
<span id="dashed-line-flow-animation" />
<span id="sequential-highlight-step-by-step" />
<span id="interactive-scenario-patterns" />
<span id="scaling-scenario-eksasg" />
<span id="bluegreen-deployment-scenario" />
<span id="failover-simulation-scenario" />
<span id="smil-vs-css-animation-comparison" />
<span id="when-to-use-smil" />
<span id="when-to-use-javascript--css" />
<span id="decision-guide" />
<span id="animation-timing-guidelines" />
<span id="interactive-legend" />
<span id="usage-example" />
<span id="output-usage" />
<span id="quality-review-required" />
<span id="validation-checklist" />
<span id="smil-animation" />
<span id="interactive-animation" />


# Animated diagram skill

Visualize request traffic, autoscaling, blue/green deployment, failover, and other service interactions using SVG motion or interactive HTML.

## Select the motion model

SMIL `animateMotion`, opacity/glow, dash offsets, and staggered highlights suit repeating flow demonstrations. JavaScript state machines and CSS transitions suit start/pause/reset controls, changing replica counts, migrations, and failure recovery.

Keep the underlying architecture readable as a still image. Use consistent semantic colors, a legend, stable labels, and enough spacing for motion. Sequence related events deliberately and keep timing in a single scenario model.

## Verify

Exercise each scenario, reset, and replay; inspect reduced viewport sizes; check console errors and animation overlap. Embed the result as SVG or HTML where the target supports it and provide a static export where motion is unavailable.

The skill's references and templates define traffic dots, glow, sequential highlights, scaling, deployment, and failover patterns.


[Skill, resources, and quality requirements](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/animated-diagram/SKILL.md)
