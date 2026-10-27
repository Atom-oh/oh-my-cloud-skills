# agent-dash

Shows what the agents of a Claude Code session are doing without asking Claude: who is
working, who delegated to whom, and which agent is probably waiting on which. In Claude
Code it is a mod (a pane, a band above the prompt, a status line and notices). In
Codex and `claude -p`, the `agent-status` skill reports the agent-team roster as text.

## Use

Install `agent-dash@oh-my-cloud-skills` and start a new session. The mod needs Claude
Code 2.1.300 or later.

- `/agent-dash` opens the pane; `/agent-dash stop` stops watching and clears the status line. A notice already shown stays.
- The pane opens as a map. The main loop sits on top; under it each agent gets a card,
  headed by the first line of what it was delegated. A card shows the agent's status
  and elapsed time, its task (two lines at most), its latest tool call (`doing:`, shown
  while it runs, with the time since it started) and up to two earlier ones (`recent:`), `waits on <agent> (est.)` when it probably
  waits, and the last two messages it sent. Children are indented under their parent;
  cards that do not fit collapse into `+N more`.
- `View: Map` / `View: List` (hotkey `m`) switches to the list: one line per agent in a
  delegation tree with status, elapsed time and `waits on <agent> (est.)`. A foreground
  agent started by the main loop shows as `main waits on <agent> (est.)` and counts in
  the waiting total. In both views an agent's `open` button opens its conversation.
- Notices appear when an agent finishes or fails and when a wait lasts longer than
  `longWaitMs` (120000 by default).

A map with the main loop and one agent:

```
╭──────────────────────────────────────────────────────────────╮
│ main · 1 delegation · 1 running · 0 waiting (est.) · 0 done  │
│ doing: Grep buildTree (0s ago)                               │
╰──────────────────────────────────────────────────────────────╯
│ "Find the config loader"
╭──────────────────────────────────────────────────────────────╮
│ ● helper · Explore · running 0s                         open │
│ task: Find the config loader and list every caller of it     │
│ doing: (no tool calls yet)                                   │
╰──────────────────────────────────────────────────────────────╯
waits are estimates from spawn and message events
View: Map  Refresh
```

## Boundaries

- A wait is an estimate from spawn and message events, not a fact the engine reports.
- Read-only: the mod never approves, denies or rewrites a tool call or a prompt.
- Privacy: the delegated prompt, a one-line summary of each tool call and the text of
  sent messages are held in memory only, redacted (tokens, keys, passwords, credentials
  in URLs and long secret-shaped strings are masked) and clipped. Only the first 4,000
  characters of a text are read. Nothing is written to disk or sent anywhere, and an
  agent's detail is dropped when it leaves the agent list. Nothing is recorded while
  the dash is stopped. Redaction is best effort: a secret with no key name and no
  recognisable shape can still show, and a harmless long run of mixed letters and
  digits, such as a git SHA or a hash-named directory in a path, shows as `***`.
- Terminal escape sequences, control characters and bidi overrides are stripped from
  everything the pane, band and notices draw, agent names and descriptions included.
- `showDelegation` (on by default) turns that text off: the observers then record no
  prompt, tool summary or message text, and the map shows `(hidden)` in its place.
- Opt-in model policy: with `modelPolicyEnabled` on, a subagent spawned without a model
  gets the alias mapped to its type. A model named on the call, or forced for the
  session, always wins.
- A mod is code that runs inside Claude Code with your permissions, unsandboxed.
  `claude plugin validate plugins/agent-dash` lists every event it handles.
