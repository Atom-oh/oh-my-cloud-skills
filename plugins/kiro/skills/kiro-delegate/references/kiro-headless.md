# Kiro CLI headless adapter

How `/kiro:delegate` and `/kiro:review` actually call `kiro-cli`. Distilled from
`kiro.dev/blog/introducing-headless-mode` and co-agent's `ai-cli-adapters.md` (same
underlying CLI, different role here: **implementer**, not advisory-only).

## Detection & auth

```bash
command -v kiro-cli >/dev/null 2>&1 && echo "kiro-cli ok"
```

Usable via an interactive login session **or** `$KIRO_API_KEY` (Pro/Pro+/Pro Max/Power) —
don't require the env var, an unauthenticated CLI just errors at call time.
`kiro_setup.py probe` runs a real headless call and classifies the result
(`READY`/`AUTH`/`TIMEOUT`/`ERROR`/`ABSENT`) — run it from `/kiro:setup` before relying on
delegation.

⚠️ **Capture stdout/stderr to files, not pipes.** Kiro can refresh auth over the host fds
it was launched with (`--auth=acp-callback`, host-mediated refresh); a `subprocess.PIPE`
severs that callback and the call hangs to the full timeout. `kiro_setup.py` and
`kiro_review.py` both redirect to temp files for this reason — do the same in any new
caller.

## Implement (write-mode)

```bash
kiro-cli chat "Read .kiro/task-prompt.md via fs_read — it has your task and any spec \
file pointers — then implement exactly what it describes. Do not touch files outside \
the task's declared file set." --agent-engine v3 --mode default --no-interactive \
  --wrap never --require-mcp-startup --agent kiro-implementer [--effort low] [--model <m>]
```

`--effort` is `delegate.effort` (`kiro_config.py delegate-effort`, default **`low`** — the
plan is already written, so applying it is mechanical; omit the flag when the accessor
prints nothing). `--require-mcp-startup` turns a silently-dead MCP server into **exit 3**
up front instead of a task that runs without a tool it was planned around and then fails
the tests for an unrelated-looking reason — treat exit 3 as infrastructure failure, not a
fix-round-worthy task failure.

**Fix rounds resume, they don't restart.** After the first call, record the session with
`kiro_run.py session-id <wt>` and re-run round 2 as
`kiro-cli chat "<the same fixed sentence>" --agent-engine v3 --resume-id <id> …`, having rewritten
`<wt>/.kiro/task-prompt.md` to hold **only the failing test output**. The session already
has the task, the spec, and Kiro's own first attempt; re-sending them costs a full context
re-read and invites redoing finished work. No id found (exit 1) → fall back to a fresh
call carrying task + failure. Details: `agents/kiro-delegate-agent.md` steps 3-4.

**The task prompt argument above is a FIXED STRING, not per-task interpolated text —
this is deliberate, not a simplification.** An earlier draft put the actual task
description directly in this argv position (`kiro-cli chat "<TASK PROMPT>"`), built by
substituting task/spec-derived text into a shell double-quoted string. That text can
include content this pipeline doesn't fully control (spec/plan content, or anything
folded into the task description while decomposing a request against a hostile/consumer
repo) — a `$(...)`, backtick, or unescaped `"` inside it would be interpreted by the
HOST shell that runs this command **before `kiro-cli` ever sees it**, executing as
whatever permissions ran the command — completely outside the worktree/`execute_bash`
restrictions this plugin's trust boundary depends on. Writing the real task content to
`.kiro/task-prompt.md` and letting the implementer `fs_read` it (exactly the pattern
`kiro_review.py`'s `_PROMPT_INSTR` already uses for untrusted diff content) means the
shell command line never contains anything but this one fixed sentence, for every task,
every time — nothing to inject into.

**`--agent kiro-implementer` is REQUIRED, not preferred.** `/kiro:delegate`'s preflight
(`agents/kiro-delegate-agent.md` step 0) refuses to implement anything until
`.kiro/agents/kiro-implementer.json` exists — running `kiro_setup.py write-agents`
first if it's missing. This is because the custom agent file is what carries the
`preToolUse` write-guard hook (step 6 below); there is no equivalent hook available via
a plain `--trust-tools=...` flag. An older draft of this plugin allowed
`--trust-tools=fs_read,fs_write` as a fallback when the agent file hadn't been written
yet — that fallback has NO write-guard and is no longer used by this pipeline; if you
see it in an older note, treat the agent-file requirement above as authoritative.

- **Prompt is a positional argv `[INPUT]`** — Kiro ignores stdin in `chat`. Never embed
  task/spec-derived text directly in this argv position (`ps` exposure + `ARG_MAX`, and —
  the load-bearing reason — shell metacharacter injection on the host, see the fixed-string
  rationale above); write it to `.kiro/task-prompt.md` **inside the worktree** instead and
  point Kiro at it (path **relative to `<wt>`** — the implementer's `fs_read` is
  cwd-confined, see "Trust boundary" below) with the one fixed instruction sentence, letting
  it `fs_read` the file itself (it already has the tool via the custom agent's
  `allowedTools`). Same for the spec files.
- **`execute_bash` is NOT in the implementer's default tool set** — it's off unless
  `/kiro:setup`'s explicit trust-decision question was answered yes (`kiro_setup.py
  write-agents --enable-bash`); a task needing a shell command falls back to Claude
  implementing it directly rather than silently granting shell access.
- **cwd MUST be the task's worktree** (`worktree.py add <wt> --base HEAD`), never the main
  checkout — this is the actual isolation boundary. See "Trust boundary" below.
- **Verify that `--model` took effect.** kiro-cli 2.24.0 printed `[warn] failed to set
  model '<id>': Method not found` for every id, then ran the turn on the global
  `chat.defaultModel` with exit 0; 2.29.1 applies the flag. `kiro_run.py model-check
  <log>` detects the warning for delegate runs, and `kiro_review.py`, `kiro_websearch.py`
  and the `kiro_setup.py probe` turn it into an error. The fix is `kiro-cli update`.
- **Pass `--agent-engine v3` on every implementer call**, first attempt and fix round
  alike. The delegate and review paths run on the V3 engine with the universal-format
  agent files `write-agents` generates; websearch stays on the default V2 engine. See
  "Engine selection" below.

## The real headless flag surface (measured on kiro-cli 2.11.1, 2026-07; rechecked on 2.29.1, 2026-10)

**Read this before assuming a lever doesn't exist.** The public headless blog post lists
only four flags (`--no-interactive`, `--trust-all-tools`, `--trust-tools`,
`--require-mcp-startup`), and an earlier version of this section repeated that list as if
it were exhaustive — which is why this plugin shipped for a while without `--effort` or
fix-round resumption, both of which were available the whole time. `kiro-cli chat --help`
is the authoritative source; re-run it after a CLI upgrade rather than trusting prose:

| Flag | Used here |
|------|-----------|
| `--effort low\|medium\|high\|xhigh\|max` | `delegate.effort` (default `low`) / `review.effort` (default `high`) — `kiro_config.py delegate-effort\|review-effort` |
| `--resume-id <SESSION_ID>` (also `-r`, `--resume-picker`) | fix-round chaining — `kiro_run.py session-id <wt>` |
| `-l/--list-sessions` + `-f json\|json-pretty` | how `session-id` finds that id (grouped by `cwd`, so a per-task worktree identifies its session unambiguously) |
| `--list-models --format json` | `kiro_setup.py list-models` |
| `--require-mcp-startup` (exit **3**) | delegate invocation — a silently-dead MCP server fails fast instead of failing the tests later for an unrelated-looking reason |
| `--agent-engine v1\|v2\|v3` | `v3` on delegate (implementer) and review calls and the setup probe; websearch omits it and runs on the default `v2` — see "Engine selection" |
| `--mode default\|spec`, `--wrap never`, `--agent`, `--model` | already in use throughout |

`-d/--delete-session`, `--session-source v1\|v2`, `--v3`, `--v2` and
`--output-format text\|stream-json` also exist. The plugin uses none of them; it selects
the engine with `--agent-engine` only.

### Turn-level event streaming (available since the 2.11.1 measurements)

kiro-cli 2.11.1 had no structured turn output: a `chat` turn printed the same text a
terminal user sees, and `--format json` applied only to the `--list-models` /
`--list-sessions` list flags (upstream asks: kiro#5423, kiro#9066). On 2.29.1,
`--output-format stream-json` emits the run's ACP events as JSON Lines on both engines.
They include the session id, the credits used (V2 `meteringUsage`; V3
`session_info_update.promptTurnSummaries`), every tool call with its status, and a final
`runFinished` with `status` and `finalText`. The plugin still reads the text log, the
session store and the credits footer described below. Moving to stream-json is open work.

The credit figure from that same wish-list is scrapeable only on the V2 engine: there
kiro-cli prints a `Credits: <n>` turn footer into the log the caller already redirects, so
`kiro_run.py credits <log>...` sums it — best-effort, and the delegation-rate report omits
the line rather than guessing if the footer format changes. The V3 engine prints no
footer, so for the V3 delegate and review paths `credits` exits 1 and the report omits
the figure. V3 records it in its session store instead (see "Engine selection").

## Engine selection (measured on kiro-cli 2.29.1, 2026-10)

The delegate path (the implementer, first attempt and `--resume-id` fix rounds) and all
three review forms (`kiro-reviewer` agent, the confirmed `--allow-unguarded`
`--trust-tools=fs_read` fallback, and Codex's tool-free `kiro-review-notools` agent) pass
`--agent-engine v3`, and so does the `kiro_setup.py probe`. `kiro_websearch.py` omits the
flag and runs on the default V2 engine: its agent file stays in the V2 format, because
`kiro-cli agent upgrade` would add a `web` (fetch URL) tool next to `web_search`. On
2.11.1 the V3 catalog's default routing also blocked `web_search`.

- **Agent format.** V3 refuses V2-format agent files (`needs upgrading for this agent
  engine`, exit **4**). `write-agents` generates `kiro-implementer` and `kiro-reviewer` in
  the universal format `kiro-cli agent upgrade <dir>` produces, which V2 and V3 both load
  (`agent upgrade --dry-run` reports them `already universal`). `tools` uses the universal
  names (`read`, `shell`, `write`, in that order), `allowedTools` keeps the V2 names
  (`fs_read`, `fs_write`, `execute_bash`), `hooks` is a list of entries such as
  `{"name": "preToolUse-0", "trigger": "preToolUse", "matcher": "write", "action":
  {"type": "command", "command": <guard>}, "timeout": 10}` (implementer: `write` then
  `read`; reviewer: one `read`), and `permissions.rules` allows `fs_read`, `fs_write` and,
  with `--enable-bash`, `shell`. An agent with no hooks has `"hooks": []` and
  `"permissions": {"rules": []}`, as in `kiro-review-notools`. `verify-agents` and
  `kiro_review.py`'s reviewer check accept only these universal shapes. An unedited V2
  file matching the previous generator's output is recognized and upgraded by plain
  `write-agents` (it prints `upgraded (plugin-generated V2 agent): <path>`), keeping
  that file's `execute_bash` choice; any other existing file still needs `--force`.
- **Wider hook matchers.** `read` also matches `grep`, `glob`, `code`, `introspect` and
  `tool_search`; `write` also matches `code`.
- **Hook payloads.** Top-level keys are `cwd`, `hook_event_name`, `session_id`,
  `tool_input` and `tool_name`. Tool inputs: `read_file` {`path`, `offset`, `limit`},
  `list_directory` {`path`, `explanation`, `depth`}, `fs_write` {`path`, `text`},
  `str_replace` {`path`, `oldStr`, `newStr`, `replace_all`}, `grep_search` {`query`,
  `caseSensitive`, `excludePattern`, `explanation`, `includePattern`} and `file_search`
  {`query`, `explanation`, `excludePattern`, `includeIgnoredFiles`}. The last two carry no
  path.
- **Search-tool guard rule.** The guard lets `grep_search` and `file_search` through
  without a path under two allowlists, because the glob engine interprets patterns: a
  literal denylist let brace expansion (`{/etc,src}/*`), escapes (`.\./x`), character
  classes (`[.][.]/x`) and an unknown `directory` key through. Keys: every `tool_input`
  key must be in the measured set for that tool (`grep_search`: `query`,
  `caseSensitive`, `excludePattern`, `explanation`, `includePattern`; `file_search`:
  `query`, `explanation`, `excludePattern`, `includeIgnoredFiles`), so a `path`,
  `directory` or newly added field is refused. Patterns: `includePattern` and
  `excludePattern` must be `null` or a string that fully matches `[A-Za-z0-9_.*?/!-]*`
  (no braces, brackets, backslash, comma, `$`, `~`, colon, whitespace or NUL), does not
  start with `/`, is not `os.path.isabs` and contains no `..`. Everything else is
  refused, as is every other path-less payload (`introspect`, `tool_search`, ...). This
  is defense in depth over V3's own confinement below. V2's `operations[]` handling is
  unchanged.
- **V3's own workspace limit.** Independently of the hook, V3 confines `grep_search` and
  `file_search` to the workspace (an `includePattern` of `../*` or an absolute outside
  path finds nothing, and symlinks are not followed), refuses `list_directory ..`, and
  refuses `read_file` through a symlink that points outside
  (`kiro-scope:workspace-escape`). Neither engine confines `execute_bash`, which stays off
  unless setup ran with `--enable-bash`; with shell access granted, `cat` reads any file
  the user can read.
- **Hook refusals need stderr.** V3 ignores a `preToolUse` exit 2 when the hook's stderr is
  empty and runs the tool anyway; V2 blocks either way. The guard always prints a reason.
  A refused call is recorded in the session store as `"status": "denied"`.
- **No credits footer.** V3 text output prints no `Credits:` footer, so `kiro_run.py
  credits` exits 1 on a V3 log and the delegation report omits the credits line. The
  session store (`~/.kiro/sessions/<dir>/<session-id>/messages.jsonl`) records each turn's
  `usage_summary.promptTurnSummaries[].usage`; reading it, or stream-json, is open work.
  The redirected log also carries KAS (Kiro Agent Server) `[INFO]` lines such as
  `kas.server.starting`, and a Node `ExperimentalWarning` tagged `[ERROR]`; neither is a
  failure.
- **Invalid `--model`.** V3 fails with exit 1 (`The model '<id>' is not available`) rather
  than substituting another model. `--model claude-sonnet-5.5 --effort low` works.
- **Cost.** One user measured 1.5–2.7x more credits per short prompt on V3 than on V2.
- **Unchanged.** `--resume-id`, `--list-sessions` (sessions are tagged `"source": "v3"`;
  `kiro_run.py session-id` finds them), `--require-mcp-startup`, `--effort`,
  `--mode default`, `--model` and an agent-less `--trust-tools=fs_read` all work on V3.

## Watching a run

What *is* available today is that text, live. Since every caller here already redirects
stdout to a **file** (mandatory, see the auth-callback warning above), tailing that file
turns a blind wait into visible progress with no protocol support at all:

- **`/kiro:review`** — pass `--progress`: `kiro_review.py` tails kiro's stdout to its own
  stderr line-by-line, prefixed `[kiro:<lens>]` (so the 3 parallel lenses stay
  distinguishable), ANSI stripped, plus a 15s "still running, Ns elapsed" heartbeat. Run
  it in a **background** Bash and poll — a foreground Bash call shows nothing until it
  returns, which is exactly the wait being fixed. The hooks deliberately don't pass it:
  their stderr only reaches anyone after the call has already finished.
- **Implement (delegate)** — Claude runs `kiro-cli` directly, so do the same thing by
  hand: redirect to a log **outside `<wt>`** and launch it in the background, then
  `tail -n 20` that log between polls.

  ```bash
  kiro-cli chat "<the fixed instruction sentence>" --agent-engine v3 --mode default \
    --no-interactive --wrap never --agent kiro-implementer \
    > /tmp/kiro-delegate-<task>.log 2>&1
  ```

  Outside `<wt>` because anything written inside it lands in `capture-diff`'s scope; and
  **`> file`, never `| tee`** — a pipe severs the auth callback and hangs the call to the
  full timeout, which is the failure this whole section is meant to avoid.

## Review (read-only)

```bash
kiro-cli chat "<instruction to fs_read the diff file and report findings>" \
  --mode default --no-interactive --wrap never --agent kiro-reviewer \
  --agent-engine v3 [--effort high] [--model <m>]
```

Same argv/stdin rules as implement, with the `kiro-reviewer` custom agent, which has no
`fs_write`/`execute_bash` at all — the reviewer must never be able to write. Only after a
confirmed `--allow-unguarded` does `kiro_review.py` replace `--agent kiro-reviewer` with
the unguarded `--trust-tools=fs_read`. Codex's tool-free review instead passes
`--trust-tools=` with a temporary `kiro-review-notools` agent and embeds the diff in the
prompt. All three forms pass `--agent-engine v3`. `kiro_review.py` is the concrete
implementation (diff → temp file → `fs_read` instruction → JSON findings contract).

## Trust boundary (mirrors co-agent's delegated-implement.md) — and its actual limits

The **hard guarantee is narrow: the host applies only the worktree's captured,
scope-guarded diff to the main git tree** — not `--trust-tools`, not the custom agent's
`allowedTools`, and not a claim that Kiro is sandboxed in any general sense. Kiro has
**no cwd-confined write sandbox** (unlike Codex's `-s workspace-write`), which is
why co-agent's `co_agent_config.py` refuses it as a
harness implementer (`SANDBOX_IMPLEMENTERS = ("codex",)`). This plugin makes
delegating to Kiro anyway acceptable **for changes that reach the main tree**, by making
the **worktree isolation + capture + scope_guard** path load-bearing for that one thing:

1. `worktree.py add <wt> --base HEAD` — Kiro only ever sees `<wt>` as its cwd.
2. Kiro implements inside `<wt>` (it may write anywhere it can reach — `..`, absolute
   paths — nothing stops it at the process level).
3. `worktree.py capture-diff <wt>` stages `git add -A` **inside `<wt>` only**, then diffs
   against the recorded base SHA. Anything Kiro wrote outside `<wt>` is invisible here —
   it was never captured, so it can never reach the main tree.
4. Every captured path must pass `scope_guard.py --plan <tasks.md-derived plan> --
   <path>...` (candidates go after a literal `--`) — a path
   outside the **plan's whole declared file set** (the union across every task, not the
   single task currently running — this script has no per-task filter, verbatim from
   co-agent) is dropped. It cannot by itself stop one task's run from touching a file
   another task in the same wave declared; that separation instead comes from
   wave-planning only ever batching pairwise-**disjoint** file sets into one wave.
5. The host applies **only** the captured, scope-guarded patch to the main tree and runs
   tests there — never inside the worktree.
6. The `kiro-implementer` custom agent's `preToolUse` hooks (written by
   `kiro_setup.py write-agents`) additionally refuse an `fs_write` **or `fs_read`** whose
   path **resolves** (via `os.path.realpath` — so a symlink inside the worktree that
   points outside it is followed and caught, and Windows drive/UNC absolute paths are
   handled by `isabs`) outside the launch cwd (the worktree), as defense-in-depth on top
   of 1-5 — it narrows the blast radius *before* capture (for writes) and closes a
   confidentiality leak (for reads: a prompt-injection payload reachable from the task
   prompt or spec content can no longer direct the implementer to `fs_read` an
   out-of-worktree absolute path like `~/.aws/credentials` and surface its contents in
   Kiro's response). The pipeline copies the spec files *into* the worktree
   (`agents/kiro-delegate-agent.md` step 3) specifically so the implementer never needs
   an absolute read outside it. 3-5 remain the actual guarantee for what reaches the
   main tree even if a write slips past the hook.

   The guard checks every path in the payload: V2's `fs_write` sends `tool_input.path`,
   and V2's `fs_read` sends `tool_input.operations[]` (each `path`, or `image_paths` in
   Image mode). It refuses a path that starts with `~` or contains `$`, because kiro-cli
   expands both. It also refuses a payload with no path or with a path-like key it does
   not read, and it writes the reason to stderr. Before the 2026-10 fix, the guard read
   only `tool_input.path`: every V2 read passed, and so did `~/…` and `$HOME/…` paths for
   reads and writes (measured on kiro-cli 2.29.1). Agent files generated before the fix
   fail `verify-agents`; regenerate them with `write-agents --force`.

   On the V3 engine, `read_file`, `list_directory`, `fs_write` and `str_replace` send a
   top-level `path`, which the same check covers. `grep_search` and `file_search` send no
   path; the guard allows them only under the key and pattern allowlists in "Engine
   selection".

**What 1-6 do NOT cover: `execute_bash`.** All of the above governs `fs_write`/`fs_read`
and the main tree only. `execute_bash` is **off by default** in
`.kiro/agents/kiro-implementer.json` (`kiro_setup.py write-agents`) — `/kiro:setup`
explicitly asks (`AskUserQuestion`) before ever granting it, and only writes it into the
agent file if the user opts in (`--enable-bash`). If granted, Kiro auto-approves it
(`--trust-tools`/`allowedTools`) and a shell command it runs is **not confined to the
worktree at the process level**: it can read files anywhere the OS user can read
(credentials, SSH keys), delete files outside the worktree, or make outbound network
calls, and none of steps 1-6 will see or stop it because they only ever look at
`fs_read`/`fs_write` tool calls and the git diff *afterward* — a shell command bypasses
both. This is not a gap this plugin can close with more worktree/capture/scope_guard
machinery — those layers are about what lands in the repo, not what a shell command can
do to the host while it runs. Granting `execute_bash` is an explicit trust decision
about `kiro-cli` (same category of trust as running any other agentic CLI with shell
access locally); without it, some tasks Kiro would otherwise finish (ones that genuinely
need a shell command) fall back to Claude implementing them directly instead.

**Reviewer `fs_read` is cwd-confined via the same guard.** `kiro-reviewer.json` grants
only `fs_read` (no `fs_write`/`execute_bash`), and carries a `preToolUse` hook applying
the same realpath containment to READS: `kiro_review.py` runs the reviewer with cwd = an
isolated temp dir containing only the diff file, so "reads confined to cwd" is exactly
"the reviewer can read the diff and nothing else". A prompt-injection payload in an
untrusted diff that tells the reviewer to `fs_read ~/.aws/credentials` (or any absolute
path, `../` escape, or symlink out) is refused at the tool layer (exit 2), not just
discouraged in prose. Residual caveats, still worth knowing: (a) the guard only applies
when the plugin-generated `kiro-reviewer.json` exists and is untampered —
`kiro_review.py` verifies its shape before using it; if verification fails, the DEFAULT
(no flag needed) is to fail open and **skip** the review entirely rather than falling
back unguarded — this is the same for the automatic pre-commit hook AND the manual
`/kiro:review` command (run `/kiro:setup` to fix that state). A prior version of this
plugin let the manual path fall back unguarded automatically, with only a printed
warning; that warning arrived right before the unguarded call ran, so it was never a
real chance to object — `/kiro:review` now requires an explicit `--allow-unguarded`,
which `commands/review.md` only passes after asking the user first via
`AskUserQuestion`; (b) the guard is a kiro-cli hook, so it presumes kiro-cli honors
`preToolUse` exit-2 blocking (V2 does; V3 honors it only when the hook writes to stderr,
which the guard does); (c) `_sanitized_env()` additionally strips
credential-shaped env vars from the reviewer's process env. Treat authorship trust as
defense-in-depth on top of the guard, not the other way around.

## Model + effort tiering

- **Delegate (implementer) model** — `delegate.model` in `kiro.local.json`. Kiro is a
  flat-rate subscription CLI, so unlike a metered peer, there's no per-token cost to
  weigh — point it at whichever model actually finishes tasks correctly; fewer fix-rounds
  is pure wall-clock savings, same reasoning as co-agent's `implementer_model` guidance.
- **Delegate effort** — `delegate.effort`, default **`low`**. Claude has already written
  the spec and the per-task file set; the implementer is applying an approved plan, and
  the DeepSWE-style observation that deeper reasoning buys nothing on a mechanical
  application applies here the same way it does to this repo's own
  `pr-autofix-implementer` tier. Raise it if a specific repo's tasks keep exhausting the
  fix loop — that's a wall-clock signal, not a cost one.
- **Review model** — `review.model`, meant to be Kiro's **strongest/newest** available
  model (the user's own example: `gpt-5.6-sol`). `/kiro:setup` runs
  `kiro-cli chat --list-models --format json` and helps pick one.
- **Review effort** — `review.effort`, default **`high`**, deliberately the opposite end
  of the ladder from delegate: this call's blocking verdict *is* its product, and a missed
  critical finding costs more than the extra reasoning. Applies to the single-pass commit
  gate and to each of the 3 parallel push lenses alike.
- List available models: `kiro_setup.py list-models`.
