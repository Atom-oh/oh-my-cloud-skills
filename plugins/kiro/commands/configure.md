---
description: Inspect or change kiro plugin settings — default_delegate, delegate/review/websearch models and effort, parallel_tasks, max_fix_rounds, review.on_commit, review.on_push, review.block, review.push_block, websearch.enabled.
allowed-tools: Bash(python3:*)
---

# kiro: configure

$ARGUMENTS

Let `SK="${CLAUDE_PLUGIN_ROOT}/skills/kiro-delegate/scripts"`. `kiro_config.py` resolves
the repo root itself (`git rev-parse --show-toplevel`, run as a python3 subprocess — not
a `Bash` tool call, so it stays inside this command's `Bash(python3:*)` allowed-tools
scope) whenever `--root` is omitted, so `.claude/kiro.local.json` — which lives at the
repo root, and which the pre-commit hook also reads from there — gets written/read
correctly even when this command runs from a subdirectory. Pass `--root` explicitly
only if you need to point at a DIFFERENT repo than the cwd's.

With no arguments, show the effective config:

```bash
python3 "$SK/kiro_config.py" show
```

Otherwise forward the arguments to `kiro_config.py` (it validates each value and reports
errors on exit 2). Pass each argument as its **own quoted argv token** — e.g.
`python3 "$SK/kiro_config.py" set review model "gpt-5.6-sol"` — never splice the raw
`$ARGUMENTS` string into the command line unquoted. `$ARGUMENTS` can contain shell
metacharacters (`;`, `$(...)`, backticks, newlines); pasting it unquoted would let the
shell re-interpret them **before** `kiro_config.py` ever validates the value. Split the
user's request into the intended `set <section> <key> <value>` (or `show`) tokens
yourself and quote each one:

```bash
# example — substitute the actual section/key/value the user asked for, each quoted:
python3 "$SK/kiro_config.py" set review model "gpt-5.6-sol"
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
| `set delegate effort <low\|medium\|high\|xhigh\|max>` | kiro-cli `--effort` for the implementer (default `low` — Claude already wrote the spec, so applying it is mechanical; raise it only if tasks keep exhausting the fix loop). `default` omits the flag |
| `set review effort <low\|medium\|high\|xhigh\|max>` | Same flag for the reviewer, default `high` — the opposite end on purpose: the blocking verdict IS this call's product, so a missed critical finding costs more than the extra reasoning. Applies to the commit pass and each push lens |
| `set delegate parallel_tasks <n>` | Max concurrent tasks per wave (default 3; `1` = sequential) |
| `set delegate max_fix_rounds <n>` | Retries before falling back to Claude implementing the task (default 2) |
| `set review on_commit on` | Enable the pre-commit review hook (off by default — the staged diff CONTENT is sent to Kiro's backend; the reviewer's `fs_read` IS confined to the isolated diff dir by a tool-layer guard when the plugin-generated `kiro-reviewer` agent is present, but this still only reviews diffs whose authorship you trust, typically your own commits) |
| `set review on_commit off` | Disable it again |
| `set review block <critical\|warning\|none>` | Which finding severities block the commit — `warning` blocks warning+critical, `suggestion` never blocks under any level (default `critical`) |
| `set review on_push on` | Enable the pre-push review hook — a 3-lens pass (correctness/security/scope, run in parallel) over the commit range about to be pushed, sent to Kiro's backend 3 times. Off by default; enabling is consent to that egress. **Don't also enable co-agent's `push_gate`** for the same repo — `set` warns if it detects that, since both firing means every push runs two independent gates |
| `set review on_push off` | Disable it again |
| `set review push_block <critical\|warning\|none>` | Which severities block the PUSH (default `warning` — one tier stricter than the commit gate's `critical`, since this is the last checkpoint before content leaves the machine). A `critical` finding is a plain block; a `warning`-only set (no critical) is framed as "CHAIR JUDGMENT REQUIRED" — read the findings in stderr and decide, then bypass if acceptable |
| `set review timeout <seconds>` / `set delegate timeout <seconds>` | Per-call wall-clock budget (also the pre-push gate's per-lens timeout) |
| `set websearch enabled on` | Delegate web searches to kiro-cli's `web_search` when this session has no WebSearch tool (e.g. Claude Code on Bedrock) — only the query text is sent to Kiro's backend; the `kiro-websearch` agent is search-only (no filesystem/shell) |
| `set websearch enabled off` | Disable it (WebSearch-less sessions just skip web searches, saying so) |
| `set websearch model <m>` / `set websearch timeout <seconds>` | Search model (default: CLI-routed) and per-search budget (default 60s) |

Settings are layered: `kiro.defaults.json` (committed) ← `.claude/kiro.local.json`
(gitignored, this repo only) — `set` always writes the local override.
