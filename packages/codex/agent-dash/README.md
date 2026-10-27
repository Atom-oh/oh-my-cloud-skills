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
  waits, and its own latest tool call. Each working agent gets a compact card: its
  status and elapsed time, its task on one line, its latest tool call (`doing:`, shown
  while it runs, with the time since it started), `waits on <agent> (est.)` when it
  probably waits, and the last message it sent. A working child is indented under its
  working parent; cards that do not fit collapse into `+N more`. With nothing working
  the map says `No agents working` and the counts.
- Finished and idle agents get no card: they show only in the counts, in the status
  line and in the list. The band above the prompt shows `agents: <summary>` only while
  an agent works. A count of zero is never shown.
- `View: Map` / `View: List` (hotkey `m`) switches to the list: one line per agent,
  finished ones included, in a delegation tree with status, elapsed time and
  `waits on <agent> (est.)`. A foreground agent started by the main loop shows as
  `main waits on <agent> (est.)` and counts in the waiting total. In both views an
  agent's `open` button opens its conversation.
- Notices appear when an agent finishes or fails and when a wait lasts longer than
  `longWaitMs` (120000 by default).

A map with three working agents (a lead, its foreground child and an agent the main
loop waits on) and two finished ones:

```
main · 3 working · 2 done
main waits on reviewer (est.)
doing: Agent Review the map change (50s ago)
╭──────────────────────────────────────────────────────────────╮
│ ● lead · team-lead · running 80s open                        │
│ task: Coordinate the map review and merge the findings       │
│ doing: SendMessage tester: run only tests/view.te… (40s ago) │
│ ⏳ waits on tester (est.)                                    │
│ → tester: "run only tests/view.test.ts first"                │
╰──────────────────────────────────────────────────────────────╯
  ╭────────────────────────────────────────────────────────────╮
  │ └ ● tester · general-purpose · running 60s open            │
  │ task: Run the unit tests and report failures               │
  │ doing: Bash claude plugin test plugins/agent-dash (8s ago) │
  ╰────────────────────────────────────────────────────────────╯
╭──────────────────────────────────────────────────────────────╮
│ ● reviewer · code-reviewer · running 50s open                │
│ task: Review hooks/lib/view.ts for width bugs                │
│ doing: Read agent-dash/hooks/lib/view.ts (4s ago)            │
╰──────────────────────────────────────────────────────────────╯
waits are estimates from spawn and message events
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
  prompt, tool summary or message text, and the map shows `(hidden)` in its place.
- Opt-in model policy: with `modelPolicyEnabled` on, a subagent spawned without a model
  gets the alias mapped to its type. A model named on the call, or forced for the
  session, always wins.
- A mod is code that runs inside Claude Code with your permissions, unsandboxed.
  `claude plugin validate plugins/agent-dash` lists every event it handles.
