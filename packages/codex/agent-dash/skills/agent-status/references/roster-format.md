# Agent team files

What the `agent-status` skill reads, and how far that is documented. Source: the
Claude Code agent teams guide (code.claude.com/docs/en/agent-teams), architecture
section. Verify against the installed Claude Code version before relying on a field.

## Documented

| Path | Holds | Lifetime |
|---|---|---|
| `~/.claude/teams/<team>/config.json` | Runtime team state; a `members` array with each member's name and agent id | Removed when the session ends |
| `~/.claude/tasks/<team>/` | The shared task list | Stays on disk after the session; cleaned up after `cleanupPeriodDays` |
| `~/.claude/teams/<team>/inboxes/<agent>.json` | One mailbox per agent | Messages between agents; do not read |

`<team>` is `session-` followed by the first eight characters of the session id.
The lead's member entry has agent type `team-lead`; a teammate's carries the type the
lead named when spawning it, or none.

## Not documented

- The exact field names of a task file. Report what is visible, and say when a field
  is missing.
- Who waits on whom. No file records it.
- The status of a teammate in its own terminal pane: the config keeps only the last
  state written, and a pane that dies leaves it standing.

## Rules

- Read, never write: the config holds runtime state and is overwritten on the next
  update.
- Print the roster fields only; the file also holds session and terminal pane ids.
