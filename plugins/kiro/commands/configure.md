---
description: Inspect or change kiro plugin settings — default_delegate, delegate/review/websearch models and effort, parallel_tasks, max_fix_rounds, review.on_commit, review.on_push, review.block, review.push_block, websearch.enabled.
allowed-tools: Bash(python3:*)
---

# kiro: configure

$ARGUMENTS

Let `SK="${CLAUDE_PLUGIN_ROOT}/skills/kiro-delegate/scripts"`. `kiro_config.py` resolves
the repo root itself (`git rev-parse --show-toplevel`) when `--root` is omitted, so
`.claude/kiro.local.json` lands at the repo root even from a subdirectory — pass `--root`
only to target a DIFFERENT repo than the cwd's.

With no arguments, show the effective config:

```bash
python3 "$SK/kiro_config.py" show
```

Otherwise forward to `kiro_config.py` (it validates values, exit 2 on error). **Pass each
argument as its own quoted argv token — never splice the raw `$ARGUMENTS` string in
unquoted.** It can carry shell metacharacters (`;`, `$(...)`, backticks, newlines) that
the shell would re-interpret before `kiro_config.py` ever validates them. Split the
request into `set <section> <key> <value>` (or `show`) tokens yourself:

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
| `set delegate model <m>` | Implementer model (flat-rate credits — pick whatever finishes tasks correctly) |
| `set review model <m>` | Reviewer model — keep this Kiro's strongest/newest, even if the delegate model is lighter |
| `set delegate effort <low\|medium\|high\|xhigh\|max>` | kiro-cli `--effort` for the implementer (default `low` — the spec is already written; raise only if tasks keep exhausting the fix loop). `default` omits the flag |
| `set review effort <low\|medium\|high\|xhigh\|max>` | Same flag for the reviewer, default `high` — the blocking verdict IS this call's product. Applies to the commit pass and each push lens |
| `set delegate parallel_tasks <n>` | Max concurrent tasks per wave (default 3; `1` = sequential) |
| `set delegate max_fix_rounds <n>` | Retries before falling back to Claude implementing the task (default 2) |
| `set review on_commit on` | Enable the pre-commit review hook (off by default — the staged diff CONTENT is sent to Kiro's backend; the reviewer's `fs_read` is confined to the isolated diff dir when the plugin-generated `kiro-reviewer` agent is present, but only review diffs whose authorship you trust) |
| `set review on_commit off` | Disable it again |
| `set review block <critical\|warning\|none>` | Which finding severities block the commit — `warning` blocks warning+critical, `suggestion` never blocks (default `critical`) |
| `set review on_push on` | Enable the pre-push review hook — a 3-lens pass (correctness/security/scope, in parallel) over the push range, sent to Kiro's backend 3 times. Off by default; enabling is consent to that egress. `set` warns if co-agent's `push_gate` is also on (two independent gates per push) |
| `set review on_push off` | Disable it again |
| `set review push_block <critical\|warning\|none>` | Which severities block the PUSH (default `warning` — one tier stricter than the commit gate, the last checkpoint before content leaves the machine). A `critical` finding is a plain block; a `warning`-only set is framed "CHAIR JUDGMENT REQUIRED" — read the stderr findings and decide |
| `set review timeout <seconds>` / `set delegate timeout <seconds>` | Per-call wall-clock budget (also the pre-push gate's per-lens timeout) |
| `set websearch enabled on` | Delegate web searches to kiro-cli's `web_search` when this session has no WebSearch tool (e.g. Claude Code on Bedrock) — only the query text is sent to Kiro's backend; the `kiro-websearch` agent is search-only (no filesystem/shell) |
| `set websearch enabled off` | Disable it (WebSearch-less sessions just skip web searches, saying so) |
| `set websearch model <m>` / `set websearch timeout <seconds>` | Search model (default: CLI-routed) and per-search budget (default 60s) |

Settings are layered: `kiro.defaults.json` (committed) ← `.claude/kiro.local.json`
(gitignored, this repo only) — `set` always writes the local override.
