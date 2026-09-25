# Running this plugin in Codex

This is a Codex entry point to shared procedures. Read the source linked by the
entry skill, using these host adaptations. Apply them to nested references too.
**Read this file once per session, not once per skill invocation** — nothing here
changes between skills in the same session; re-reading it on every entry only adds
fixed weight without adding information.

## Installed files and the target repository

The installed plugin root is three directories above the directory containing
this entry `SKILL.md`: `<plugin>/.codex-plugin/skills/<name>/SKILL.md`.
Resolve that root from the actual loaded skill path. Do not guess a cache version,
search a different installation, or assume the consumer has `plugins/` in its repo.

- `${CLAUDE_PLUGIN_ROOT}` in shared Markdown is a placeholder for that absolute
  plugin root. Codex does not render it in skill text. Substitute the resolved,
  shell-quoted path before executing an example; do not run the placeholder empty.
- Resolve Markdown links relative to the **source document**, not this entry.
  Bare `scripts/`, `references/`, `assets/` and `templates/` in a skill refer to that
  source skill directory. A source command's `plugins/<this-plugin>/...` is likewise
  a package path. User project files (`docs/`, output artifacts, plans, `.claude`
  state) belong to the user's target repository instead.
- Keep the shell working directory at the target repository. Plugin assets and
  templates are inputs; write generated output to the requested project directory.
  Shell variables do not necessarily persist between tool calls.
- Run a bundled Python or Bash helper with the installed adapter when convenient:

  ```text
  python3 "<plugin-root>/.codex-plugin/run.py" skills/<skill>/scripts/<helper>.py <args>
  ```

  It preserves cwd, stdin, arguments and exit status, supplies the installed root
  to child scripts, and sets `CO_AGENT_HOST=codex` for co-agent. Pass user text as
  an argument or stdin, never as shell code. The helper may still need an explicit
  `--root <target-repository>` according to its own CLI.

## Tools, commands and specialists

- `Read`, `Grep`, `Glob`, `Bash`, `Write` and `Edit` mean the available Codex file,
  search, shell and patch tools. `AskUserQuestion` means the current host's user
  input mechanism, only for information or authorization still missing.
- A `/plugin:command` or `Skill` invocation is an instruction to load the matching
  installed skill. It is not a shell executable. `$ARGUMENTS` means the user's
  invocation arguments, not an environment variable to expand.
  `inventory.json` maps source commands to installed names; project-init
  health-check uses `source-command-health-check` to share Codex's automatic
  migration name.
- Claude command context snippets prefixed with `!` have not been expanded in
  Codex. Gather their context by running the underlying read-only commands in the
  target repository when needed.
- `Task`, `Agent`, `subagent_type`, and names under `agents/` describe specialist
  procedures. Load the matching skill or linked agent body. When delegation is
  appropriate and available, pass the procedure, task and installed paths to an
  available general-purpose agent. Otherwise execute the procedure in this host.
  Do not register a made-up native agent type or treat a source file as executed.
- Claude `model`, `effort`, `memory`, `tools` and `allowed-tools` frontmatter is not
  a Codex configuration or permission boundary. Use supported host capabilities
  and actual permissions. Do not translate `opus` or `sonnet` into guessed model
  names, or promise persistent agent memory just because a source declares it.
  Enforce a procedure's required read-only planning or host-state protection with
  an actual sandbox/tool boundary before delegating. If the available agent
  interface cannot enforce it, perform that phase inline in this host.
- **Cost consequence of the point above**: a generated agent-sourced entry names its
  source's `model`/`effort` intent in a prose line (never a manifest field — Codex's
  plugin validator has no per-skill model/effort slot to put one in). It is advisory
  only. Without it, delegating this procedure silently runs at the current session's
  model/effort, at that spend, regardless of how strong or light the source intended
  it — the gap is real cost, not just a naming mismatch. When it matters, either
  raise/lower the session for the procedure or delegate explicitly
  (`codex exec -m <model> -c model_reasoning_effort="<effort>"`).
- Any procedure this host delegates onward — a subagent, a peer AI, a worktree
  implementer — should have its RETURNED output bounded the same way the source
  skill's own output-budget guidance intends (see the linked procedure's own
  references, e.g. token-saver's `agent-output-budget.md` where installed): verdict
  first, `file:line` over pasted code, no restating the task back to the caller.
- Internal worker entries require explicit selection; canonical workflow skills
  retain automatic routing. The `delegate` command remains an explicit alias for
  Kiro's canonical `kiro-delegate` workflow.
- Discover MCP tools from the current session. A missing optional tool may use
  a documented CLI equivalent; missing credentials or required capabilities must
  be reported, not silently counted as a successful check.

Use the current user's requested scope and existing authorization. A shared
procedure's default to publish, deploy, commit or seek confirmation does not add
authorization or override an already specified workflow.

## Hooks and evidence

When this package's manifest declares `hooks`, its command hooks are connected
through `.codex-plugin/hooks.json`; otherwise it has no plugin command hooks.
A `project-template/.codex/` tree requires separate installation into the consumer
project. For configured file matchers, the adapter translates Codex `apply_patch`
into affected paths, including renames, while retaining shell-hook decisions.
Installation alone does not establish that hooks ran: Codex requires hook trust
and the runtime must support the event. Run the procedure's substantive checks
explicitly when needed. Report actual review and validation evidence; an absent
hook, specialist or external reviewer is not a passing result.
