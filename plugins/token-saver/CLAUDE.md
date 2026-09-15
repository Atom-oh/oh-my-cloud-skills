# token-saver

Shared response-style guidance for Claude Code and Codex. The maintained policy is
`skills/concise-responses/references/policy.md`; the session hook and manual skill
use that same file.

The hook only emits session context. Keep it deterministic and small: no model
calls, telemetry, transcript reads, output rewriting, or user/project settings
edits. Reasoning, verification, complete artifacts and required output schemas
take priority over prose brevity. Host hook trust and enablement still apply.

Edit the maintained source and regenerate the Codex package with
`python3 scripts/sync-codex-plugins.py --plugin token-saver` from the repository root.
