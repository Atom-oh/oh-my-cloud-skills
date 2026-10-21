# agent-dash

Shows what the agents of a Claude Code session are doing without asking Claude: who is
working, who delegated to whom, and which agent is probably waiting on which. In Claude
Code it is a mod (a pane, a band above the prompt, a status line and notices). In
Codex and `claude -p`, the `agent-status` skill reports the agent-team roster as text.

## Use

Install `agent-dash@oh-my-cloud-skills` and start a new session. The mod needs Claude
Code 2.1.300 or later.

- `/agent-dash` opens the pane; `/agent-dash stop` stops watching and clears the status line. A notice already shown stays.
- The pane lists agents as a delegation tree with status, elapsed time and, when one is
  waiting, `waits on <agent> (est.)`. A foreground agent started by the main loop shows
  as `main waits on <agent> (est.)` above the tree and counts in the waiting total.
  Pressing a row's button opens that agent's conversation.
- Notices appear when an agent finishes or fails and when a wait lasts longer than
  `longWaitMs` (120000 by default).

## Boundaries

- A wait is an estimate from spawn and message events, not a fact the engine reports.
- Read-only: the mod never approves, denies or rewrites a tool call or a prompt.
- Opt-in model policy: with `modelPolicyEnabled` on, a subagent spawned without a model
  gets the alias mapped to its type. A model named on the call, or forced for the
  session, always wins.
- A mod is code that runs inside Claude Code with your permissions, unsandboxed.
  `claude plugin validate plugins/agent-dash` lists every event it handles.
