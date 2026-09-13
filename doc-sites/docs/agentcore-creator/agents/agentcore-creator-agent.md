---
sidebar_position: 1
title: "AgentCore creator agent"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="트리거-키워드" />
<span id="기능" />
<span id="사용-예시" />
<span id="새-에이전트-설계-및-배포" />
<span id="기존-플러그인-변환" />
<span id="출력물" />


# AgentCore creator agent

Guides an agent from an idea or existing plugin to a locally validated design and an AgentCore deployment candidate.

## Responsibilities

Discover requirements; design skills, references, tools, and state; select harness configuration or Runtime generation; build and test locally; convert; then deploy and smoke-test within the user's authorization. Keep the file/resource plan concrete and record the result of each phase.

For an existing plugin, inspect its manifest, skills, agent instructions, MCP tools, references, and hooks. Do not imply that host-specific hooks automatically become managed harness behavior. Choose Runtime when the required custom orchestration cannot be expressed by the selected harness path.

## Output

Return generated configuration/code, dependencies, tool and memory mappings, local test results, and the proposed deployment commands. After an authorized deployment, report resource identifiers and actual invocation results without exposing credentials.

[Agent definition](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/agentcore-creator/agents/agentcore-creator-agent.md)
