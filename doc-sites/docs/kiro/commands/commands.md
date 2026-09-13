---
sidebar_position: 1
title: "Kiro commands"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="kiro-명령" />


# Kiro commands

## /kiro:setup

Detect and probe Kiro CLI, inspect available model settings, and prepare the implementer, reviewer, and optional search agents. Setup keeps default delegation, commit/push review, web search, and shell-tool consent separate.

## /kiro:delegate

Provide a concrete implementation request or approved plan. The host plans, Kiro implements in task worktrees, and the host validates captured changes and tests before committing. The result reports delegation and any host fallback.

## /kiro:review

Review the selected scope on demand using the same review engine as the optional hooks. Confirm suspected issues against code and configuration. Invalid reviewer agent configuration must not silently expand tool access.

## /kiro:configure

Show effective settings and their source, or update the supported delegation, review, and web-search fields. Models may be null in defaults and resolved during setup; use actual configuration rather than copying a stale model name.

[Exact keys and defaults](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/kiro/skills/kiro-delegate/kiro.defaults.json)

Commit/push hooks are local opt-in controls. Repository-required CI, review coverage, and branch protection continue to apply independently. Codex exposes the command workflows as generated skills.
