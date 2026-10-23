# ADR-029: Consolidate co-agent roles at execution boundaries

## Status
Accepted (2026-10-22)

## Context
Co-agent registered five agents. Its coordinator repeated the canonical skill's
host-owned orchestration, while `harness-analyst` served only an optional H5
retrospective. Neither needs a separate persona to preserve its procedure.
The other three roles have materially different permissions and output contracts.

## Options Considered
1. Keep five agents: preserve native entry points, but duplicate coordination and routing.
2. Merge all roles: simplify discovery, but mix judgment, read-only planning and writes.
3. Keep three specialists and move the other procedures to existing entries: reduce
   duplication without widening specialist permissions.

## Decision
Choose option 3. Keep `gate-chair`, `pr-autofix-planner` and
`pr-autofix-implementer` separate with their existing tools and model/effort settings.
Remove the `co-agent` agent wrapper; `/co-agent` and Codex `$co-agent` retain the skill.
Move retrospective analysis to host-owned `/co-agent:configure analyze [session-dir]`.
It stays read-only, requires three recorded runs before proposals, and never applies
settings or calls peers. The Python config helper gains no `analyze` subcommand.
Keep the dynamic decision-reconcile workflow's per-run lenses, provider roster and
review gates unchanged; its lenses are not registered agent personas.

## Consequences
Registered agents decrease from five to three; generated Codex entries from twelve
to eleven because the same-name coordinator skill/agent previously shared an entry.
Native coordinator callers must invoke the skill in the current host; analyst callers
must use `configure analyze`. Host-owned procedures do not inherit the retired agents'
pinned model/effort or persistent memory. Existing memory directories stay untouched;
any migration needs explicit authorization. Codex procedures are not native roles or
permission sandboxes. Public guide routes remain stable while explaining the migration.

## References
- [Canonical skill](../../plugins/co-agent/skills/co-agent/SKILL.md)
- [Analysis contract](../../plugins/co-agent/skills/co-agent/references/harness-analysis.md)
- [Claude assignments](../../hosts/claude/co-agent/agents.json) and [Codex execution](../../hosts/codex/co-agent/execution.json)
