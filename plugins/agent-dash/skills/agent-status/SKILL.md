---
name: agent-status
description: Report which agents of a Claude Code agent team are working, from the team roster files, as text — "agent status", "에이전트 상태", "팀원 상태", "who is working". Read-only; use when the agent-dash pane is unavailable (Codex, claude -p) or the user wants the answer in the conversation.
---

# Agent status

Report the agents of one Claude Code agent team without changing anything. This is
the text form of the agent-dash pane. The pane, its wait estimates and the model
policy are a Claude Code mod; hosts that cannot run it get only the roster facts
below. The documented file layout and what is not documented are in
[references/roster-format.md](references/roster-format.md).

## Workflow

Find the team → read the roster → read the task files → report. Use only file reads;
run nothing that starts, stops or messages an agent, and do not read mailbox files
(`inboxes/`), which hold the agents' messages.

### Step 1: Find the team

A running team has a directory under `~/.claude/teams/`. Claude Code removes it when
the session ends, so a missing or empty directory means no team is running: say so
and stop. With several teams, take the one whose `config.json` was modified most recently (the
directory's own time does not change when the roster is rewritten) and name the others.
Each path printed below names its team directory.

```bash
ls -t "$HOME"/.claude/teams/*/config.json 2>/dev/null
```

### Step 2: Read the roster

The team's `config.json` holds a `members` array with each member's name, agent id
and agent type. The lead's entry has agent type `team-lead`; a teammate's entry omits
the type when none was named.

```bash
python3 -I -c 'import json,sys; d=json.load(open(sys.argv[1])); [print(m.get("name"), "|", m.get("agentType") or "-") for m in d.get("members", [])]' "$HOME/.claude/teams/<team>/config.json"
```

Do not print any other field of this file: it holds runtime state such as session and
terminal pane identifiers.

### Step 3: Read the task files

Tasks live in `~/.claude/tasks/<team>/`. This directory stays on disk after the
session ends, so label tasks from an ended session as historical. The file format is not documented. Read each file and report only these fields: title or
subject, status (pending, in progress or completed), owner, and blocked by. Say so when one
is absent, and do not print any other field, even when present.

```bash
ls -l "$HOME/.claude/tasks/<team>/"
```

### Step 4: Report

| Situation | What to say |
|---|---|
| No team directory | "No agent team is running." Stop. |
| Team found, no task files | Give the roster only and say there are no tasks. |
| Task from an ended session | Mark it historical; do not call the agent working. |
| Asked who waits on whom | The roster does not record it. The agent-dash mod estimates waits from events and labels them `est.`; this text form gives none. |

## Output

One line per member (name, agent type), then one line per task (status, owner,
blocked by) with the fields as read. End with one sentence on what the answer cannot
show: live status and waits are in the agent-dash pane, available only in Claude Code.
Never edit the roster or the task files.
