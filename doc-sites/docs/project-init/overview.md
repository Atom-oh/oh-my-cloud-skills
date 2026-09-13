---
sidebar_position: 1
title: "Project init"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="project-init-개요" />
<span id="구성-요소" />
<span id="에이전트-1개" />
<span id="스킬-1개" />
<span id="명령-9개" />
<span id="워크플로우" />
<span id="프로젝트-초기화" />
<span id="문서-동기화" />
<span id="생성되는-구조" />
<span id="health-check-점수" />


# Project init

Initialize project instructions and structure, synchronize documentation, and create ADRs, runbooks, and reference guides for either host.

## Host-specific setup {#host-specific-setup}

Claude Code uses the source plugin's commands, project-scaffolder knowledge skill, and doc-sync-checker agent. Codex uses generated overlays that adapt initialization to AGENTS.md, `.agents/skills/`, and available host tools. Do not install Claude hook JSON as if it were Codex configuration.

## Workflows {#workflows}

| Entry | Result |
| --- | --- |
| `init-project` | Detect the stack and add missing project structure |
| `sync-docs` | Compare maintained documentation with code and settings |
| `add-adr` | Number and draft an architecture decision |
| `add-module` | Add module instructions and update architecture references |
| `add-runbook` | Create an operational runbook |
| `add-reference-doc` | Create implementation reference material under docs/reference |
| `generate-readme` | Create or refresh a user-facing README |
| `generate-changelog` | Update the release record |
| `health-check` | Inspect project setup and documentation quality |

## Adaptation and quality {#adaptation-and-quality}

Existing projects keep their detected language, framework, source layout, and user-authored instructions. Generated files should describe real commands and boundaries. Follow the user's language requirement; bilingual templates are an optional output capability, not a requirement to duplicate all documentation.

Health checks report missing setup, instruction quality, architecture coverage, and actionable repairs. Read the actual command rubric before interpreting a numeric score. PR autofix and decision reconciliation belong to co-agent.

[Codex package](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/project-init/.codex-plugin/plugin.json) · [Source structure reference](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/project-init/skills/project-scaffolder/SKILL.md)
