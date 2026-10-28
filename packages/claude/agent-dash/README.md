# agent-dash

Shows what the agents of a Claude Code session are doing without asking Claude: who is
working, who delegated to whom, and which agent is probably waiting on which. In Claude
Code it is a mod (a pane, a band above the prompt, a status line and notices). In
Codex and `claude -p`, the `agent-status` skill reports the agent-team roster as text.

## Use

Install `agent-dash@oh-my-cloud-skills` and start a new session. The mod needs Claude
Code 2.1.300 or later.

- `/agent-dash` opens the pane; `/agent-dash stop` stops watching, clears the status line and forgets the captured task, tool and message text. A notice already shown stays.
- The pane opens as a map of the agents that are working now (pending, running or
  waiting). The main loop is one line on top: how many agents work, the idle and
  finished counts when there are any, `main waits on <agent> (est.)` when it probably
  waits, and its own latest tool call, dimmed once it is older than a minute and left
  out after ten minutes. The `View: Map` and `Refresh` buttons sit right under it,
  above the cards. With nothing working the map says `No agents working`, the counts
  and `View: List shows them`.
- Each working agent gets a compact card. Its title is a headline, the agent type,
  the status with its elapsed time and an `open` button. The headline is the agent's
  name; without a name it is what the agent was asked to do (the Agent call's short
  description, unless it only repeats the type); without either it is the type. When
  two drawn cards would have the same headline, both get the last four characters of
  their agent id, for example `Discovery (a3f9)`. The type shows on every card or, when
  any title would not fit with it, on none. Below the title come the task on one line
  (left out when the headline is a description no other card shares), the latest tool
  call (`doing:`, with the time since it started), `waits on <agent> (est.)` when it
  probably waits, and the last message it sent. Waits and messages name their target
  by the headline its card shows. When agents without a name or description, or
  agents sharing one description, also share a prompt preamble, the task line drops the
  leading words they all share and shows the rest after `…`. That shared part is worked
  out over the cards drawn now, so it can change as agents start and finish.
- Cards sit in a grid of equal widths: one per line below 120 columns, two from 120
  and three from 180. A working child follows its working parent with `└` on its title
  row; in the one-column layout it is also indented. Every working card is drawn. When
  the cards are taller than the pane, focus the pane and scroll it with the arrow keys,
  PageUp/PageDown, Home/End or the mouse wheel.
- Finished and idle agents get no card: they show only in the counts, in the status
  line and in the list. The band above the prompt shows `agents: <summary>` only while
  an agent works. A count of zero is never shown. Every agent counts once: a pending or
  running agent, or one whose status says waiting with no inferred wait, counts as
  `running`; one with an estimated wait as `waiting (est.)`; then `idle` and `done`.
- `View: Map` / `View: List` (hotkey `m`) switches to the list: one line per agent,
  finished ones included, in a delegation tree with status, elapsed time and
  `waits on <agent> (est.)`; it names an agent by its name or type, not by its
  description. A foreground agent started by the main loop shows as
  `main waits on <agent> (est.)` and counts in the waiting total. In both views an
  agent's `open` button opens its conversation.
- Kiro delegation: while an agent (usually `kiro:kiro-delegate-agent`) or the main loop
  runs Kiro CLI tasks, its card lists one line per task, such as
  `kiro task 2 · running · try 2 · 4m12s`. The state is `running`, `captured`,
  `scope-checked`, `verifying`, `retrying`, `done` or `claude fallback`, and `try` counts
  the first run as 1. Once a task needed a retry or fell back to Claude, the card's
  title also reads `kiro 2/4 done · 1 retry · 1 fallback`. The list adds a short
  `kiro 2/4`, and the status line and band add `kiro n/m` while a run is active. All
  of it is inferred from the agent's own Bash calls: a `kiro-cli chat` run named by its
  `task-<id>-attempt-<n>.log` redirect or its `task-<id>` directory, the
  `task-<id>-retry-<k>` prompt files, `worktree.py capture-diff`, `scope_guard.py`,
  `git apply`, the wave's `git commit`, `worktree.py remove`, and a `claude fallback`
  or `host fallback` note whose own command names the task's path. Commands are read
  as shell words, so a command that only mentions kiro (in quotes, an argument, an
  echoed string or a heredoc) records nothing, and nothing is polled. A run in the main
  loop stops counting as active after ten minutes without a step. With
  `showDelegation` off the card shows only the counts, never the task ids.
- Notices appear when an agent finishes or fails and when a wait lasts longer than
  `longWaitMs` (120000 by default).

A map at 120 columns with three working agents (a lead, its foreground child and an
agent the main loop waits on, which has no name and is headlined by its description)
and two finished ones. Rendered from the map code:

```
main · 3 working · 2 done
main waits on Review view.ts for width bugs (est.)
doing: Agent Review view.ts for width bugs (50s ago)
m: View: Map  r: Refresh
╭─────────────────────────────────────────────────────────╮ ╭─────────────────────────────────────────────────────────╮
│ ● lead · running 80s open                               │ │ └ ● tester · running 60s open                           │
│ task: Coordinate the map review and merge the findings  │ │ task: Run the unit tests and report failures            │
│ doing: SendMessage tester: run only tests/vi… (40s ago) │ │ doing: Bash claude plugin test plugins/agent-… (8s ago) │
│ ⏳ waits on tester (est.)                               │ │                                                         │
│ → tester: "run only tests/view.test.ts first"           │ │                                                         │
╰─────────────────────────────────────────────────────────╯ ╰─────────────────────────────────────────────────────────╯
╭─────────────────────────────────────────────────────────╮
│ ● Review view.ts for width bugs · running 50s open      │
│ doing: Read agent-dash/hooks/lib/view.ts (4s ago)       │
╰─────────────────────────────────────────────────────────╯
waits are estimates from spawn and message events
```

With nothing working, the map keeps only the counts:

```
No agents working
2 done
View: List shows them
m: View: Map  r: Refresh
```

## Boundaries

- A wait is an estimate from spawn and message events, not a fact the engine reports.
- Read-only: the mod never approves, denies or rewrites a tool call or a prompt.
- Privacy: the delegated prompt, a one-line summary of each tool call and the text of
  sent messages are held in memory only, redacted (tokens, keys, passwords, credentials
  in URLs and long secret-shaped strings are masked) and clipped. Only the first 4,000
  characters of a text are read. Nothing is written to disk or sent anywhere, and an
  agent's detail is dropped when it leaves the agent list. Nothing is recorded while
  the dash is stopped; stopping also clears what was captured. Redaction is best
  effort: a secret with no key name and no recognisable shape can still show, and a
  harmless long run of mixed letters and digits, such as a git SHA or a hash-named
  directory in a path, shows as `***`.
- Terminal escape sequences, control characters and bidi overrides are stripped from
  everything the pane, band and notices draw, agent names and descriptions included.
- `showDelegation` (on by default) turns that text off: the observers then record no
  prompt, tool summary or message text, the map shows `(hidden)` in its place, and a
  card's headline is the agent's name or type, never its description.
- Opt-in model policy: with `modelPolicyEnabled` on, a subagent spawned without a model
  gets the alias mapped to its type. A model named on the call, or forced for the
  session, always wins.
- A mod is code that runs inside Claude Code with your permissions, unsandboxed.
  `claude plugin validate plugins/agent-dash` lists every event it handles.
