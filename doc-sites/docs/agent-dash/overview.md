---
sidebar_position: 0
title: "agent-dash overview"
---
# agent-dash

See which agents of a Claude Code session are working, who delegated to whom, and
which agent is probably waiting on which, without asking Claude. In Claude Code,
`agent-dash` is a mod: a pane, a one-line band above the prompt, a status line, and
notices. In Codex and other places that cannot draw, its `agent-status` skill
reports the agent-team roster as text.

## What it shows {#what-it-shows}

The pane lists the session's subagents, teammates and workflow agents as a delegation
tree. Each row shows the agent's name, type, status and how long it has been in that
status. A row whose agent is waiting adds `waits on <agent> (est.)`. Each row has an
`open` button that opens that agent's conversation in the main view. A summary line
such as `3 running · 1 waiting (est.) · 2 done` also appears in the status line and in
a band above the prompt.

A wait is an estimate. agent-dash infers it from spawn and message events: a parent
waits on a child it started in the foreground, and a sender waits on a message target
that has neither changed state nor replied. The engine reports no such fact, so every
surface labels it `est.`. A teammate that runs in its own terminal pane has no loop
in the session, so its status can be stale.

## How it runs {#how-it-runs}

Run `/agent-dash` to open the pane, or `/agent-dash stop` to stop watching and clear
the status line. The mod refreshes every 5 seconds and when an agent is spawned, a
message is sent, or a turn completes. It raises a notice when an agent finishes, fails
or is stopped, and when a wait lasts longer than `longWaitMs` (120000 by default). In
the VS Code chat panel and in `claude -p`, where nothing may draw, `/agent-dash`
returns the summary as text.

## Model policy {#model-policy}

An opt-in policy can choose the model of a subagent spawn. It is off by default. When
`modelPolicyEnabled` is on, a spawn that names no model gets the alias that
`modelPolicyMap` (a JSON object of subagent type to `opus`, `sonnet` or `haiku`)
gives its type. An empty setting uses a built-in map that follows the repository's
role tiers; an empty object (`{}`) disables every mapping; a value that is not a JSON
object is ignored and the built-in map stays. A model named on the call, and a model
the session forces for every subagent, always win over the policy. This is the only
place agent-dash changes anything.

## Limits {#limits}

agent-dash observes. It never approves, denies or rewrites a tool call or a prompt,
and it never changes a message sent between agents. Its row buttons only switch the
view. A mod is code that runs inside Claude Code with your permissions;
`claude plugin validate` lists every event it handles, and `--safe-mode` turns it off.
An organization's `allowManagedModsOnly` setting blocks mods installed from a
marketplace that is not managed.

## Get started {#get-started}

Install it with `/plugin install agent-dash@oh-my-cloud-skills` and start a new
session. The mod needs Claude Code 2.1.300 or later. In Codex, select
`agent-dash:agent-status` from the skill picker; it reads the agent-team roster and
task files and reports them without changing anything. The source lives under
`plugins/agent-dash/`.
