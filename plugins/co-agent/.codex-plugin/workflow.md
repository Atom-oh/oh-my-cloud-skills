# Co-agent host selection

The current host is Codex. Pass `--host codex` where supported and use the bundled
`run.py` adapter so child processes receive `CO_AGENT_HOST=codex`. For a direct
shell invocation, set that variable on the same invocation; do not rely on it
persisting across tools. Codex chairs; resolve configured external peers with `co_agent_config.py panel --host codex`.
Never launch Codex as its own external panel member.

Use `configure`, `setup`, `sync-context`, `consensus`, `harness`, `pr-autofix` and
`decision-reconcile` entry skills for those workflows. An official Claude Code
peer plugin is not installed in Codex merely because its files exist; use the
working CLI adapter when that Claude-only route is unavailable.

Missing, failed or incomplete required review coverage is not a clean verdict.
Preserve the latest-HEAD review and verification rules of the active task.

## PR auto-fix execution

For `pr-autofix`, select the Codex path before reading any Claude dispatch example.
`pr-autofix-planner` and `pr-autofix-implementer` are procedures, not native Codex agent types.
Fable/Opus aliases and Claude `tools:` frontmatter are not Codex prerequisites or
permission grants. Use supported session capabilities, not guessed model aliases.

Read the shared skill and `references/land-delta-pipeline.md` → "Host execution"
for the phase decision: inline planning is supported; delegation requires an actual
sandbox/tool boundary for read-only planning or edit-only worktree implementation,
including host-state protection. A general-purpose agent is usable only if those
controls exist. Otherwise execute that phase inline and report the specific missing
control, not merely the absence of a Claude model or named specialist.

Keep implementation in the pipeline's isolated worktree and preserve every
`land_delta.sh` gate and host-only state/commit/push responsibility. This local
execution choice does not replace required external review or weaken latest-HEAD
acceptance. Never claim an unavailable tool restriction was enforced.
