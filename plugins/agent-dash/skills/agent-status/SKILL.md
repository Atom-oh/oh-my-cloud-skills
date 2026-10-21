---
name: agent-status
description: Report which agents of a Claude Code agent team are working, from the team roster files, as text — "agent status", "에이전트 상태", "팀원 상태", "who is working". Read-only; use when the agent-dash pane is unavailable (Codex, claude -p) or the user wants the answer in the conversation.
---

# Agent status

Report the agents of one Claude Code agent team without changing anything. This is
the text form of the agent-dash pane. The pane, the wait estimates and the model
policy are a Claude Code mod; hosts that cannot run it get only the roster facts
below.

## Workflow

Find the team → read the roster → read the task list → report. Use only files; run
no command that starts, stops or messages an agent.

### Step 1: Find the roster

A team's config is `~/.claude/teams/<team>/config.json`; its `members` array holds
each member's `name`, `agentId` and `agentType`. The lead's entry has agent type
`team-lead`. Claude Code removes the directory when the session ends, so a missing
directory means no team is running: say so and stop. If several teams exist, report
the most recently modified one and name the others.

### Step 2: Read the task list

Tasks live in `~/.claude/tasks/<team>/`, one file per task with a state of
`pending`, `in_progress` or `completed` and any dependencies. This directory stays on
disk after the session ends: label tasks from an ended session as historical.

### Step 3: Report

Give one line per member (name, agent type) and one line per task (state, owner,
blocked-by). Say plainly that the roster does not record who is waiting on whom:
a wait is only an estimate in the agent-dash pane, and this text form gives none.
Do not edit the roster or task files.
