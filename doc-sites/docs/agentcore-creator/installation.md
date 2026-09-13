---
sidebar_position: 2
title: "Install agentcore-creator"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="설치" />
<span id="marketplace에서-설치" />
<span id="로컬에서-직접-로드" />
<span id="사전-요구사항" />
<span id="mcp-서버" />
<span id="aws-권한" />
<span id="제거" />


# Install agentcore-creator

## Claude Code

```text
/plugin marketplace add Atom-oh/oh-my-cloud-skills
/plugin install agentcore-creator@oh-my-cloud-skills
```

For local development from a repository checkout:

```bash
claude --plugin-dir ./plugins/agentcore-creator
```

## Codex

Install `agentcore-creator` from this repository's Codex marketplace using `/plugins`, then start a new thread. The package loads its generated `.codex-plugin/skills/` entries. Use the installed skill picker or describe the desired operation; the slash commands shown in this guide name the corresponding Claude workflows.

## Setup and verification

Prepare the AgentCore tooling described by the skill and AWS access for the selected account/region. Local generation and cloud deployment are separate phases; review the generated plan before creating resources.

For a source checkout, validate both host packages from the repository root:

```bash
python3 scripts/test-plugins.py
python3 scripts/test-codex-plugins.py
```

Inspect the plugin's manifest and generated overlay if an expected entry is missing. Do not treat a successful installation as proof that external credentials, peer CLIs, or cloud permissions work.

## Remove

Use `/plugin uninstall agentcore-creator@oh-my-cloud-skills` in Claude Code or uninstall the entry through Codex `/plugins`.
