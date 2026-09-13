---
sidebar_position: 1
title: "Project init commands"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="project-init-명령" />


# Project init commands

In Claude Code these are slash commands. In Codex use the corresponding generated skill; `source-command-health-check` disambiguates the project setup check from AWS health checks.

## /init-project

Detect the repository's language, framework, commands, and existing layout. Create missing instructions, documentation, skills, and supported host integration files without overwriting handwritten content.

## /sync-docs

Audit maintained documents against source and configuration; update stale commands, counts, paths, and architectural statements. Keep one authoritative statement for details that change frequently.

## /add-adr

Create a numbered decision record with context, alternatives, decision, and consequences. Link superseded records when appropriate.

## /add-module

Add a module directory and scoped instructions, then update architecture documentation to describe its role and dependencies.

## /add-runbook

Create a runbook with prerequisites, operations, expected output, verification, and recovery steps.

## /add-reference-doc

Add implementation reference material for selected layers under `docs/reference/` and link it from the owning instructions.

## /generate-readme

Describe the project's actual purpose, installation, usage, development commands, and contribution path. Follow the requested language.

## /generate-changelog

Record release changes under the project's versioning and changelog conventions. Describe shipped behavior and avoid inventing release dates.

## /health-check

Validate files, hooks, permissions, instruction quality, and configuration. Report the rubric, evidence, and fixes; a health score is not a replacement for the required test suite.
