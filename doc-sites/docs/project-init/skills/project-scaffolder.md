---
sidebar_position: 1
title: "Project scaffolder"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="project-scaffolder-skill" />
<span id="제공-리소스" />
<span id="references-12개-템플릿" />
<span id="프로젝트-타입-감지" />


# Project scaffolder

The knowledge skill explains project structure, scoped instructions, documentation, and host integrations. It detects the language and framework from real dependency/build files and adapts its templates to the existing repository.

## Placement {#placement}

Keep concise repository instructions at the root and module-specific context beside the module. Put architecture guides, ADRs, runbooks, onboarding, and implementation references under docs. Skills, commands, agents, hooks, and MCP configuration use the current host's supported directories and formats.

Claude source templates describe CLAUDE.md and `.claude/`. Codex overlays adapt applicable workflows to AGENTS.md and `.agents/skills/`; Claude-specific hooks are not implicitly portable.

## Template selection {#template-selection}

References cover instruction quality, settings and hooks, skills and agents, documentation, MCP, setup scripts, testing, and editor configuration. Create only the files the project needs. Preserve user content, use executable project commands, exclude secrets, and keep the requested language consistent.

[Template directory](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/project-init/skills/project-scaffolder/references/)
