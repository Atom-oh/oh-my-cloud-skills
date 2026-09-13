---
sidebar_position: 1
title: "AgentCore creator"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="agentcore-creator-개요" />
<span id="구성-요소" />
<span id="에이전트-1개" />
<span id="스킬-1개" />
<span id="사전-요구사항" />
<span id="워크플로우" />
<span id="5-phase-상세" />
<span id="agentcore-구성-요소" />
<span id="auto-invocation-키워드" />


# AgentCore creator

Design and test an agent locally, then prepare an AgentCore harness configuration or a generated Runtime application.

## Five phases

| Phase | Result |
| --- | --- |
| Discovery | Purpose, users, capabilities, tools, knowledge, and success criteria |
| Design | Approved component plan and harness/Runtime target |
| Skill-first build | Locally tested plugin or host-accessible skill |
| Conversion | Harness configuration or generated Strands/Runtime code |
| Deploy and verify | Authorized resource creation and smoke-test evidence |

An existing plugin path enters at conversion; a new idea starts with discovery. Harness configuration attaches skills and tools to the managed loop. Runtime generation supplies a Strands application when the design requires custom orchestration or runtime behavior.

## Components and integration

The package exposes agentcore-creator-agent and agentcore-create. The workflow can map tools through Gateway and plan Memory where needed. Keep `.claude-plugin/plugin.json` as the conversion input on either host; Codex local testing additionally needs a host-visible skill that loads the relevant instructions.

Model mapping and compatibility rules are defined in the converter and references. Resolve model availability for the actual deployment rather than copying an invented or stale catalog ID. Resource creation is a separate authorized phase after the candidate is reviewable.

[Workflow contract](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/agentcore-creator/skills/agentcore-create/SKILL.md) · [Converter and model mapping](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/agentcore-creator/skills/agentcore-create/scripts/convert_plugin_to_agentcore.py)
