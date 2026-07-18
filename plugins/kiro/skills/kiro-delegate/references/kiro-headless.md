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
kiro-cli chat "<TASK PROMPT>" --mode default --no-interactive \
  --trust-tools=fs_read,fs_write --wrap never \
  [--model <m>] [--agent kiro-implementer]
```

- **Prompt is a positional argv `[INPUT]`** — Kiro ignores stdin in `chat`. For anything
  beyond a one-line prompt, don't embed large context in argv (`ps` exposure + `ARG_MAX`);
  point Kiro at the spec files with a short instruction and let it `fs_read` them itself
  (it already has the tool via `--trust-tools`/the custom agent's `allowedTools`).
- **`--agent kiro-implementer`** (once `/kiro:setup` has written
  `.kiro/agents/kiro-implementer.json`) scopes the run to that custom agent's
  `tools`/`allowedTools`/hooks instead of the ad-hoc `--trust-tools` flag — prefer it once
  set up; `--trust-tools=fs_read,fs_write` is the fallback when it hasn't been written
  yet. **`execute_bash` is NOT in either default** — it's off unless `/kiro:setup`'s
  explicit trust-decision question was answered yes (`kiro_setup.py write-agents
  --enable-bash`); a task needing a shell command falls back to Claude implementing it
  directly rather than silently granting shell access.
- **cwd MUST be the task's worktree** (`worktree.py add <wt> --base HEAD`), never the main
  checkout — this is the actual isolation boundary. See "Trust boundary" below.
- **`--v3` narrows the model catalog** and can reject some model ids
  (`INVALID_MODEL_ID` — reproduced with pre-rename model names; see co-agent's ADR-012).
  Drop `--v3` whenever an explicit `--model` is set; only use `--v3`+no-model for the
  CLI's own default routing.

## Review (read-only)

```bash
kiro-cli chat "<instruction to fs_read the diff file and report findings>" \
  --mode default --no-interactive --trust-tools=fs_read --wrap never \
  [--model <m>] [--agent kiro-reviewer]
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
4. Every captured path must pass `scope_guard.py --plan <tasks.md-derived plan>` — a path
   outside the **plan's whole declared file set** (the union across every task, not the
   single task currently running — this script has no per-task filter, verbatim from
   co-agent) is dropped. It cannot by itself stop one task's run from touching a file
   another task in the same wave declared; that separation instead comes from
   wave-planning only ever batching pairwise-**disjoint** file sets into one wave.
5. The host applies **only** the captured, scope-guarded patch to the main tree and runs
   tests there — never inside the worktree.
6. The `kiro-implementer` custom agent's `preToolUse` hook (written by
   `kiro_setup.py write-agents`) additionally refuses an `fs_write` whose path is absolute
   or contains `..`, as defense-in-depth on top of 1-5 — it narrows the blast radius
   *before* capture, but 3-5 remain the actual guarantee even if a write slips past it.

**What 1-6 do NOT cover: `execute_bash`.** All of the above governs `fs_write` and the
main tree only. `execute_bash` is **off by default** in
`.kiro/agents/kiro-implementer.json` (`kiro_setup.py write-agents`) — `/kiro:setup`
explicitly asks (`AskUserQuestion`) before ever granting it, and only writes it into the
agent file if the user opts in (`--enable-bash`). If granted, Kiro auto-approves it
(`--trust-tools`/`allowedTools`) and a shell command it runs is **not confined to the
worktree at the process level**: it can read files anywhere the OS user can read
(credentials, SSH keys), delete files outside the worktree, or make outbound network
calls, and none of steps 1-6 will see or stop it because they only ever look at the git
diff *afterward*. This is not a gap this plugin can close with more
worktree/capture/scope_guard machinery — those layers are about what lands in the repo,
not what a shell command can do to the host while it runs. Granting `execute_bash` is an
explicit trust decision about `kiro-cli` (same category of trust as running any other
agentic CLI with shell access locally); without it, some tasks Kiro would otherwise
finish (ones that genuinely need a shell command) fall back to Claude implementing them
directly instead.

**Reviewer `fs_read` is not path-restricted either.** `kiro-reviewer.json` grants only
`fs_read` (no `fs_write`/`execute_bash`), but that tool is not scoped to the diff file
`kiro_review.py` points it at — a diff can contain attacker-influenced content (this is
someone's staged code change), and a prompt-injection payload in it could instruct the
reviewer to `fs_read` an unrelated absolute path (e.g. `~/.aws/credentials`) and include
its contents in the review response, which is sent to Kiro's backend. `_sanitized_env()`
strips credential-shaped environment variables from the reviewer's process env, but that
protects only `os.environ` — it does nothing for the filesystem. Do not run
`/kiro:review` (or rely on the pre-commit hook) against a diff you don't trust the
author of on a machine where `fs_read` could reach something sensitive; there is
currently no filesystem allowlist enforcing "only the diff file" at the tool layer.

## Model tiering

- **Delegate (implementer) model** — `delegate.model` in `kiro.local.json`. Kiro is a
  flat-rate subscription CLI, so unlike a metered peer, there's no per-token cost to
  weigh — point it at whichever model actually finishes tasks correctly; fewer fix-rounds
  is pure wall-clock savings, same reasoning as co-agent's `implementer_model` guidance.
- **Review model** — `review.model`, meant to be Kiro's **strongest/newest** available
  model (the user's own example: `gpt-5.6-sol`). `/kiro:setup` runs
  `kiro-cli chat --list-models --format json` and helps pick one.
- List available models: `kiro_setup.py list-models`.
