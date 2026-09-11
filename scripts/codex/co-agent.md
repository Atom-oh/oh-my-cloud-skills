# Co-agent host selection

The current host is Codex. Pass `--host codex` where supported and use the bundled
`run.py` adapter so child processes receive `CO_AGENT_HOST=codex`. For a direct
shell invocation, set that variable on the same invocation; do not rely on it
persisting across tools. Codex chairs; Claude CLI, Kiro CLI and Agy may be peers.
Never launch Codex as its own external panel member.

Use `configure`, `setup`, `sync-context`, `consensus`, `harness`, `pr-autofix` and
`decision-reconcile` entry skills for those workflows. An official Claude Code
peer plugin is not installed in Codex merely because its files exist; use the
working CLI adapter when that Claude-only route is unavailable.

Missing, failed or incomplete required review coverage is not a clean verdict.
Preserve the latest-HEAD review and verification rules of the active task.
