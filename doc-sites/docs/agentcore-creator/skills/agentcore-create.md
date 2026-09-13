---
sidebar_position: 1
title: "AgentCore create skill"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="트리거" />
<span id="제공-리소스" />
<span id="scripts" />
<span id="references" />
<span id="워크플로우" />
<span id="phase-1-discovery" />
<span id="phase-2-design" />
<span id="phase-3-skill-first-build" />
<span id="phase-4-agentcore-convert" />
<span id="phase-5-deploy--verify" />


# AgentCore create skill

Use `agentcore-create` for a new agent or `convert <plugin-path>` for an existing plugin. The skill supports local, GitHub, and marketplace input; source resolution must identify the intended plugin before conversion.

## Design and local build

Capture purpose, users, tools, knowledge, target, and success criteria. Produce a concrete file plan. Build the skill/plugin locally and test representative requests and an edge case before cloud conversion. Codex testing needs an exposed `.agents/skills/` entry that loads the agent instructions; a Claude agent filename alone does not register a Codex worker.

## Conversion paths

Harness produces configuration for model, instructions, tools, skills, and supported managed features. Runtime produces a Strands application wrapped for AgentCore. Decide based on required orchestration, streaming, framework, and tool behavior. Model-specific request compatibility and IDs come from the converter's mapping and reference files.

## Deployment verification

Review the resource plan, account/region, identity, tool authentication, memory requirements, and dependencies. Perform only authorized resource creation, invoke the deployed agent, and record observed output. A generated configuration is not evidence of successful deployment.

[Full phases and commands](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/agentcore-creator/skills/agentcore-create/SKILL.md)
