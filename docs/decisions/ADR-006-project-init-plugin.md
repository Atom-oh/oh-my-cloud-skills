# ADR-006: project-init Plugin Introduction

## Status

Accepted (2026-04-20)

## Context

The commands for project initialization (generating CLAUDE.md, managing ADRs, syncing documentation) were scattered at the root level, making reuse and maintenance difficult. Multiple projects were repeatedly recreating the same pattern (CLAUDE.md, docs/decisions/, CHANGELOG.md).

## Decision

Split the `project-init` plugin out as an independent plugin:
- 1 agent (`doc-sync-checker`): documentation sync analysis and quality scoring
- 1 skill (`project-scaffolder`): Claude Code project structure patterns
- 8 commands: `/init-project`, `/sync-docs`, `/add-adr`, `/add-module`, `/add-runbook`, `/generate-readme`, `/generate-changelog`, `/health-check`

## Consequences

- Documentation sync status can be quantified on a 100-point scale
- `/sync-docs` automatically detects missing CLAUDE.md files, version mismatches, and missing ADRs
- Can be used directly as a plugin in other projects

## References

- Commit: 375ac6e
- Plugin path: `plugins/project-init/`
