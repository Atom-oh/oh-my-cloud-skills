# ADR-022: Retire Antigravity from co-agent

## Status

Accepted (2026-09-13), per the repository owner's request. Supersedes the active
Antigravity peer and implementation paths described by ADR-010. Historical records
remain evidence of earlier behavior.

## Context

The owner requested Antigravity removal. Stored overrides, probes and writer
fallbacks make disabling a default insufficient.

## Decision

- Co-agent supports Kiro CLI, Claude CLI and Codex CLI, excluding the current host.
  The active candidates are Kiro plus the opposite host CLI.
- Remove Antigravity from defaults, selection, flag emission, setup, local hooks,
  model fan-out and implementation fallbacks. Retired `agy`, `antigravity` and
  `gemini` settings produce migration guidance and cannot re-enable a provider.
- Keep Codex as the only supported external sandbox writer when Claude hosts.
  With no eligible external writer, the host must explicitly select the documented
  host-implementation plan after fresh setup. A READY external reviewer remains
  required. Claude and Kiro do not gain delegated write permissions.
- Keep review quorums, input limits, secret checks and required CI coverage intact.
  The repository CI roster already excludes Agy, so this decision changes no
  required CI reviewer and is not a response to missing CI coverage.
- Preserve historical review data and audit residual legacy context files. Do not
  delete handwritten context or unrelated provider credentials as part of removal.

## Consequences

Migrate old settings and refresh setup. Codex-host harness uses explicit native
host implementation while retaining READY external review.

## References

- [Earlier Antigravity decision](ADR-010-antigravity-supersedes-gemini.md)
- [Configuration helper](../../plugins/co-agent/skills/co-agent/scripts/co_agent_config.py)
- [Readiness](../../plugins/co-agent/skills/co-agent/scripts/check_panel.py)
- [Harness workflow](../../plugins/co-agent/commands/harness.md)
