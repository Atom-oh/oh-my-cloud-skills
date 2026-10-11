## Check the requested target first

The maintained migration command upgrades legacy **Claude Code** project files:
`.claude/settings.json`, `.claude/hooks/` and `.claude/agents/`. It does not migrate
or repair `.codex/hooks.json` and does not register native Codex agents.

For a Claude Code target, follow the linked source migration with the current
user's authorization and installed template paths. Preserve unrelated host files.
For a Codex target, inspect the existing `.codex/` hook definitions and apply the
native installation/merge, JSON validation, project trust and hook-trust sequence
in this plugin's workflow guide. Diagnose or repair only the requested configuration.
Do not import Claude permissions, replace custom hooks, execute untrusted hooks,
or claim that a migration ran merely because no `.claude/` tree exists.

If there are no legacy Claude files, report that no Claude migration is applicable.
When the requested target is Codex, state separately what native configuration
was actually inspected or changed and which trust/runtime checks remain unverified.
