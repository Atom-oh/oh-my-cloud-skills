---
description: Inspect or change kiro plugin settings — default_delegate, delegate/review models, parallel_tasks, max_fix_rounds, review.on_commit, review.block.
allowed-tools: Bash(python3:*)
---

# kiro: configure

$ARGUMENTS

Let `SK="${CLAUDE_PLUGIN_ROOT}/skills/kiro-delegate/scripts"` and
`ROOT="$(git rev-parse --show-toplevel)"` — **always pass `--root "$ROOT"`**.
`kiro_config.py` defaults its root to the cwd, but `.claude/kiro.local.json` lives at the
repo root and the pre-commit hook reads it from there (`git rev-parse --show-toplevel`).
Running this command from a subdirectory without `--root` would write the setting to
`<subdir>/.claude/kiro.local.json`, which nothing else reads — e.g. `set review
on_commit on` would look accepted while the hook silently keeps reading off.

With no arguments, show the effective config:

```bash
python3 "$SK/kiro_config.py" show --root "$ROOT"
```

Otherwise forward the arguments to `kiro_config.py` (it validates each value and reports
errors on exit 2). Pass each argument as its **own quoted argv token** — e.g.
`python3 "$SK/kiro_config.py" set review model "gpt-5.6-sol" --root "$ROOT"` — never
splice the raw `$ARGUMENTS` string into the command line unquoted. `$ARGUMENTS` can
contain shell metacharacters (`;`, `$(...)`, backticks, newlines); pasting it unquoted
would let the shell re-interpret them **before** `kiro_config.py` ever validates the
value. Split the user's request into the intended `set <section> <key> <value>` (or
`show`) tokens yourself and quote each one:

```bash
# example — substitute the actual section/key/value the user asked for, each quoted:
python3 "$SK/kiro_config.py" set review model "gpt-5.6-sol" --root "$ROOT"
```

If the request doesn't map cleanly to a known `set`/`show` form, ask the user to
clarify rather than forwarding an unparsed string.

Common examples:

| Command | Effect |
|---------|--------|
| `set default_delegate on` | Route implementation work to Kiro automatically, no trigger phrase needed |
| `set default_delegate off` | Only delegate when explicitly asked |
| `set delegate model <m>` | Implementer model (flat-rate credits — no per-token cost trade-off; pick whatever finishes tasks correctly) |
| `set review model <m>` | Reviewer model — keep this Kiro's strongest/newest, even if the delegate model is lighter |
| `set delegate parallel_tasks <n>` | Max concurrent tasks per wave (default 3; `1` = sequential) |
| `set delegate max_fix_rounds <n>` | Retries before falling back to Claude implementing the task (default 2) |
| `set review on_commit on` | Enable the pre-commit review hook (off by default — the reviewer's `fs_read` isn't scoped to just the diff file; only enable for diffs you trust the authorship of, typically your own commits) |
| `set review on_commit off` | Disable it again |
| `set review block <critical\|warning\|none>` | Which finding severities block the commit — `warning` blocks warning+critical, `suggestion` never blocks under any level (default `critical`) |
| `set review timeout <seconds>` / `set delegate timeout <seconds>` | Per-call wall-clock budget |

Settings are layered: `kiro.defaults.json` (committed) ← `.claude/kiro.local.json`
(gitignored, this repo only) — `set` always writes the local override.
