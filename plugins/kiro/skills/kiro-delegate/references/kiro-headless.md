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
the task's declared file set." --mode default --no-interactive --wrap never \
  --require-mcp-startup --agent kiro-implementer [--effort low] [--model <m>]
```

`--effort` is `delegate.effort` (`kiro_config.py delegate-effort`, default **`low`** — the
plan is already written, so applying it is mechanical; omit the flag when the accessor
prints nothing). `--require-mcp-startup` turns a silently-dead MCP server into **exit 3**
up front instead of a task that runs without a tool it was planned around and then fails
the tests for an unrelated-looking reason — treat exit 3 as infrastructure failure, not a
fix-round-worthy task failure.

**Fix rounds resume, they don't restart.** After the first call, record the session with
`kiro_run.py session-id <wt>` and re-run round 2 as
`kiro-cli chat "<the same fixed sentence>" --resume-id <id> …`, having rewritten
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
- **`--v3` narrows the model catalog** and can reject some model ids
  (`INVALID_MODEL_ID` — reproduced with pre-rename model names; see co-agent's ADR-012).
  Drop `--v3` whenever an explicit `--model` is set; only use `--v3`+no-model for the
  CLI's own default routing.

## The real headless flag surface (measured on kiro-cli 2.11.1, 2026-07)

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
| `--mode default\|spec`, `--wrap never`, `--agent`, `--model` | already in use throughout |

`-d/--delete-session`, `--session-source v1\|v2`, `--agent-engine`, `--v3` also exist;
`--v3` narrows the model catalog (see the `INVALID_MODEL_ID` note above).

### What is genuinely missing: turn-level event streaming

There is **no `--output-format stream-json`** equivalent — a `chat` turn's output is the
same human-readable text a terminal user sees (`--format json` applies to the
`--list-models`/`--list-sessions` **list** flags, not to a turn). Upstream requests:
`--output-format json` + `--progress-file <path>` NDJSON (kiro#5423) and headless
session-id/credit JSON (kiro#9066). Note the narrower claim than before: `--resume-id`,
`--effort` and session JSON all exist today — only the live event stream doesn't, and
kiro#9066's session-id ask is already worked around by reading the session store.

The credit figure from that same wish-list is likewise scrapeable rather than absent:
kiro-cli prints a `Credits: <n>` turn footer into the log the caller already redirects, so
`kiro_run.py credits <log>...` sums it for the delegation-rate report — best-effort, and
the report omits the line rather than guessing if the footer format changes.

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
  kiro-cli chat "<the fixed instruction sentence>" --mode default --no-interactive \
    --wrap never --agent kiro-implementer > /tmp/kiro-delegate-<task>.log 2>&1
  ```

  Outside `<wt>` because anything written inside it lands in `capture-diff`'s scope; and
  **`> file`, never `| tee`** — a pipe severs the auth callback and hangs the call to the
  full timeout, which is the failure this whole section is meant to avoid.

## Review (read-only)

```bash
kiro-cli chat "<instruction to fs_read the diff file and report findings>" \
  --mode default --no-interactive --trust-tools=fs_read --wrap never \
  [--effort high] [--model <m>] [--agent kiro-reviewer]
```

Same argv/stdin rules as implement, but `--trust-tools=fs_read` only (or the
`kiro-reviewer` custom agent, which has no `fs_write`/`execute_bash` at all) — the
reviewer must never be able to write. `kiro_review.py` is the concrete implementation
(diff → temp file → `fs_read` instruction → JSON findings contract).

## Trust boundary (mirrors co-agent's delegated-implement.md) — and its actual limits

The **hard guarantee is narrow: the host applies only the worktree's captured,
scope-guarded diff to the main git tree** — not `--trust-tools`, not the custom agent's
`allowedTools`, and not a claim that Kiro is sandboxed in any general sense. Kiro has
**no cwd-confined write sandbox** (unlike Codex's `-s workspace-write` or Agy's
`--sandbox`), which is exactly why co-agent's `co_agent_config.py` refuses it as a
harness implementer (`SANDBOX_IMPLEMENTERS = ("codex", "agy")`). This plugin makes
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
`preToolUse` exit-2 blocking; (c) `_sanitized_env()` additionally strips
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
