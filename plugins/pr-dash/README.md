# pr-dash

Shows a pull request's CI checks and AI review result without asking Claude. In
Claude Code it is a mod: a pane, a status line under the prompt and toasts. In
Codex, the VS Code chat panel and `claude -p`, the `pr-status` skill reports the
same facts as text.

## Use

Install `pr-dash@oh-my-cloud-skills` (`/plugin install pr-dash@oh-my-cloud-skills`)
and start a new session. The mod needs Claude Code 2.1.287 or later; both parts need
an authenticated GitHub CLI (`gh auth status`).

- `/pr-dash` opens the pane for the current branch's PR. `/pr-dash 253` picks a PR;
  `/pr-dash stop` stops watching and clears the status line. The command also runs
  while Claude is working.
- After Claude runs `gh pr create` or `git push` successfully, pr-dash starts
  watching that branch's PR: it polls every 60 seconds, keeps the status line
  current, and shows a toast when the checks finish or the review result changes.
  Watching stops once the PR is merged or closed.
- Pane keys: `r` refreshes. `f` (shown when the review has findings) asks Claude
  to apply them with co-agent's pr-autofix skill. `m` (shown only when every check
  passed and a PASSED review covers the current head) asks Claude to re-check and
  merge under the repository's rules. Esc closes the pane.
- `/pr-dash:pr-status` (Claude Code) or `pr-dash:pr-status` (Codex) prints the
  status as text.

Where it looks: `gh pr view` runs in the session's directory, or in the directory of
a `git -C <dir> push` or `cd <dir> && git push` that Claude ran (a `~` or `$VAR`
directory is not expanded and is ignored). Outside a git repository pr-dash stays
silent: no warning, no toast, no status line, polling stops, and `/pr-dash` or the
pane says `not in a git repository`.

The pane draws in the terminal and the Desktop app. Elsewhere `/pr-dash` returns a
one-line summary.

## Boundaries

- Read-only toward GitHub: the mod runs only `gh pr view … --json …`. Buttons hand
  a prompt to Claude; they never merge, push, comment or approve a tool call. Claude's
  turn, its permission prompts and the repository's merge rules still decide.
- It trusts only the newest `github-actions` comment carrying
  `<!-- oh-my-cloud-skills-pr-review -->`, and the first `**Status:**` line outside
  quotes, code fences and HTML comments. The pane is a display; CI remains the gate.
- A mod is code that runs inside Claude Code with your permissions, unsandboxed.
  `claude plugin validate plugins/pr-dash` lists every event it handles and every
  call it makes. `--safe-mode` or `disableAllHooks` turns it off.

## Development

From `plugins/pr-dash`: `claude plugin validate .` and `claude plugin test`.
Try it live with `claude --plugin-dir ./plugins/pr-dash` from the repository root;
the module reloads on save. Tested with Claude Code 2.1.296.
