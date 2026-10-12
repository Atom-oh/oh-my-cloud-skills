---
sidebar_position: 0
title: "pr-dash overview"
---
# pr-dash

See a pull request's CI checks and AI review result without asking Claude. In
Claude Code, `pr-dash` is a mod: a pane, a status line under the prompt, and toasts.
In Codex and other places that cannot draw, its `pr-status` skill reports the same
facts as text.

## What it shows {#what-it-shows}

The pane lists the PR's title, state, branches and head commit, one row per check,
and the AI review status with its Critical, Major, and Minor findings. It marks
whether the review covers the current head commit or an older one, and links to the
PR and the review comment.

## How it runs {#how-it-runs}

Run `/pr-dash` for the current branch's PR, `/pr-dash <number>` for another one,
or `/pr-dash stop` to stop watching. After Claude runs `gh pr create` or
`git push` successfully, pr-dash starts watching that branch's PR. It checks every
60 seconds, keeps the status line current, and shows a toast when the checks
finish or the review result changes. It stops after the PR is merged or closed.

Press `r` to refresh. When the review has findings, `f` asks Claude to fix them with
co-agent's pr-autofix skill. When every check passed and a PASSED review covers the
current head, `m` asks Claude to re-check and merge under the repository's rules.

## Limits {#limits}

pr-dash only reads GitHub through `gh pr view`. Its buttons hand a prompt to
Claude; they never merge, push, or approve anything themselves, so Claude's
permission prompts and the repository's merge rules still apply. The pane is a
display, and CI remains the merge gate. It trusts only the review comment posted by
`github-actions` with the repository's review marker.

The pane draws in the Claude Code terminal and the Desktop app. The VS Code chat
panel and `claude -p` get a one-line summary instead. A mod is code that runs
inside Claude Code with your permissions; `claude plugin validate` lists what it
does, and `--safe-mode` turns it off.

## Get started {#get-started}

Install it with `/plugin install pr-dash@oh-my-cloud-skills`, sign in to the GitHub
CLI with `gh auth login`, and start a new session. The mod needs Claude Code
2.1.287 or later. In Codex, select `pr-dash:pr-status` from the skill picker. The
source lives under `plugins/pr-dash/`.
