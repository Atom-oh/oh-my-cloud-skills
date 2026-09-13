---
sidebar_position: 1
title: "MCP integrations"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="mcp-서버" />
<span id="개요" />
<span id="서버-상세" />
<span id="awsdocs-번들" />
<span id="awsapi-번들" />
<span id="awsknowledge-deploy-on-aws" />
<span id="awspricing-deploy-on-aws" />
<span id="awsiac-deploy-on-aws" />
<span id="에이전트별-mcp-사용" />
<span id="트러블슈팅" />
<span id="uvx-명령을-찾을-수-없음" />
<span id="mcp-서버-타임아웃" />
<span id="aws-자격-증명-오류" />
<span id="로그-레벨-조정" />


# MCP integrations

The AWS operations plugin declares two MCP servers in its Claude manifest: `awsdocs` for AWS documentation and `awsapi` for AWS API operations. Codex uses the generated MCP configuration referenced by its manifest. Additional tools mentioned in agent references are optional host integrations, not automatically bundled servers.

## Setup

The declared servers run through `uvx`. Prepare that executable and the authentication/configuration required by each server. Inspect the actual manifest for package names, arguments, environment settings, and timeouts instead of copying an independently maintained server list.

[Claude server configuration](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/.claude-plugin/plugin.json) · [Codex package configuration](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/.codex-plugin/plugin.json)

## Diagnose connection failures

Confirm the process starts, inspect its local logs, check the selected account/region and credential expiry, and distinguish MCP transport failures from service permission failures. Documentation search needs a working server but does not establish AWS API authorization.

The AWS API MCP package is an upstream legacy integration. Evaluate migration to AWS MCP separately using the upstream migration guide; this documentation change does not replace the configured server.

[AWS API MCP migration guide](https://github.com/awslabs/mcp/blob/main/src/aws-api-mcp-server/MIGRATION.md)
