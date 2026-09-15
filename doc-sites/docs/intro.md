---
sidebar_position: 1
slug: /intro
title: "Getting started"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="oh-my-cloud-skills-시작하기" />
<span id="플러그인-목록" />
<span id="설치-방법" />
<span id="marketplace에서-설치-권장" />
<span id="로컬에서-직접-로드" />
<span id="플러그인-구조" />
<span id="사용-예시" />
<span id="콘텐츠-생성" />
<span id="인프라-운영" />
<span id="다음-단계" />


# Getting started

This marketplace contains nine plugins for Claude Code and Codex. Plugin definitions and helper scripts are the product; this site documents their workflows.

The current release is **v2.0.0**. Read the [release notes and migration guide](/docs/releases/v2.0.0)
before updating an existing co-agent setup that selected Antigravity.

<span id="plugins" />

## Choose a plugin {#choose-a-plugin}

| Plugin | Purpose |
| --- | --- |
| [co-agent](/docs/co-agent/overview) | Second opinions, decisions, ADRs, and implementation pipelines with peer review. The current host chairs the work. |
| [kiro](/docs/kiro/overview) | Delegate implementation and optional reviews to Kiro CLI while the current host owns the plan, verification, and commits. |
| [atlas](/docs/atlas/overview) | Maintain a per-topic repository wiki with git-based drift detection and optional push-time synchronization. |
| [project-init](/docs/project-init/overview) | Initialize project instructions and structure, synchronize documentation, and create ADRs, runbooks, and reference guides for either host. |
| [aws-content-plugin](/docs/aws-content-plugin/overview) | Create web presentations, editable PowerPoint decks, diagrams, documents, workshops, brochures, and portfolio pages. |
| [aws-ops-plugin](/docs/aws-ops-plugin/overview) | Diagnose AWS and EKS incidents across compute, networking, identity, observability, storage, databases, analytics, and cost. |
| [kiro-power-converter](/docs/kiro-power-converter/overview) | Convert Claude plugin sources and individual skills into Kiro Powers, including steering, hooks, assets, and MCP configuration. |
| [agentcore-creator](/docs/agentcore-creator/overview) | Design and test an agent locally, then prepare an AgentCore harness configuration or a generated Runtime application. |
| [token-saver](/docs/token-saver/overview) | Add concise response guidance while preserving reasoning, verification, complete artifacts, and required report formats. |

<span id="quick-install" />

## Install {#install}

In Claude Code, add the repository marketplace, then install the plugins you need:

```text
/plugin marketplace add Atom-oh/oh-my-cloud-skills
/plugin install aws-content-plugin@oh-my-cloud-skills
```

In Codex, add this repository's `.agents/plugins/marketplace.json` as a marketplace source and install from `/plugins`. Start a new thread after installation. Select the installed skill in the host's skill picker or request the documented workflow in plain English.

The Claude manifests expose agents, skills, commands, and hooks. Codex manifests point to generated skill overlays and host-specific hook/MCP adapters. A Claude command becomes a skill entry in Codex; Claude subagent registration and tool names do not automatically transfer. Project-init and Atlas both have Codex packages.

## Current configuration {#current-configuration}

[Claude marketplace](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/.claude-plugin/marketplace.json) · [Codex marketplace](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/.agents/plugins/marketplace.json)

Those manifests and each plugin's source directories define the installed inventory. Generated Codex overlays may expose more skill entries because they wrap Claude commands. Model identifiers, reasoning settings, and context limits come from each plugin's configuration; this site does not maintain a second model catalog.

## Review and examples {#review-and-examples}

Content output requires the content-review quality gate before publication. Local review hooks are opt-in controls; they do not replace CI checks or repository branch protection. Review findings must be checked against the actual changed files and current configuration.

Demo embeds and downloadable artifacts are frozen examples. Their language, model names, prices, or dated claims illustrate the original output and are not current operational guidance.

## Related links {#related-links}

- [Claude Code](https://claude.ai/code)
- [Remarp Guide](/docs/remarp-guide/introduction)
