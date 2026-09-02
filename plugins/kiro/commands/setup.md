---
description: Detect kiro-cli, probe real usability, list available models, write the .kiro/agents/*.json custom agents delegate/review/websearch use, and set default_delegate / review.on_commit / websearch.enabled.
allowed-tools: Bash(python3:*), AskUserQuestion
---

# kiro: setup

Let `SK="${CLAUDE_PLUGIN_ROOT}/skills/kiro-delegate/scripts"`. `kiro_config.py` and
`kiro_setup.py` resolve the repo root themselves (`git rev-parse --show-toplevel`) when
`--root` is omitted, so `.claude/kiro.local.json` and `.kiro/agents/` land at the repo
root even from a subdirectory — pass `--root` only to target a DIFFERENT repo than the
cwd's.

1. Detect and probe (`probe` checks PATH presence itself — no separate `command -v`
   call, which this command's `Bash(python3:*)` scope wouldn't auto-approve anyway):
   ```bash
   python3 "$SK/kiro_setup.py" probe
   ```

   | Probe result | What to do |
   |--------------|------------|
   | `READY` | Continue to step 2 |
   | `ABSENT` | Tell the user to install Kiro CLI (`https://kiro.dev`) and stop — nothing else can proceed |
   | `AUTH` | Run `kiro-cli` interactively to log in, or set `KIRO_API_KEY`, then re-run `/kiro:setup` |
   | `NO_INGEST` | kiro-cli ran but didn't echo the probe's sentinel — report "responded but couldn't be verified usable" and offer one retry (some builds do this transiently) |
   | `TIMEOUT` / `ERROR` | Report the reason and offer one retry (cold-start CLIs can be slow on the first call) |

2. On `READY`, list models and help pick two — a delegate (implement) model and a
   review model:
   ```bash
   python3 "$SK/kiro_setup.py" list-models
   ```
   Use `AskUserQuestion` to offer the review-model choice explicitly — the plugin's whole
   point is a strong reviewer behind a cost-efficient implementer:
   - **Review model** — recommend the newest/strongest listed (e.g. `gpt-5.6-sol` if
     present) — first option, `(Recommended)`.
   - **Delegate model** — any model that reliably finishes tasks; default/CLI-routed is
     fine (flat-rate credits, no cost trade-off to reason about).
   Save with:
   ```bash
   python3 "$SK/kiro_config.py" set review model "<chosen review model>"
   python3 "$SK/kiro_config.py" set delegate model "<chosen delegate model>"   # or skip to keep CLI default
   ```

3. **Trust decision — ask before granting shell access (`AskUserQuestion`, mandatory,
   never default this on silently):** worktree isolation + capture-diff + scope_guard
   only guarantee what reaches the main git tree; they do nothing to confine a shell
   command's host-side side effects (reading credentials, deleting files outside the
   worktree, network calls) while it runs. Explain this plainly, then ask:
   - **No shell access (Recommended to start)** — the implementer gets
     `fs_read`/`fs_write` only; tasks that genuinely need a shell command fall back to
     Claude implementing them directly.
   - **Grant `execute_bash`** — auto-approved shell commands, with the host-side risk
     above. Only for users comfortable extending that trust to `kiro-cli` the way they
     would to any agentic CLI with shell access on this machine.

4. Write the custom agents Kiro uses in headless mode, per the answer to step 3:
   ```bash
   python3 "$SK/kiro_setup.py" write-agents [--enable-bash]
   ```
   These land at `.kiro/agents/kiro-implementer.json` (fs_read/fs_write, plus
   execute_bash only if granted; worktree-write-only via a preToolUse hook),
   `.kiro/agents/kiro-reviewer.json` (fs_read only), and
   `.kiro/agents/kiro-websearch.json` (web_search only — no filesystem, no shell). Re-run
   with `--force` to regenerate (e.g. after changing the step 3 answer).

5. Ask (`AskUserQuestion`) about the three delegation/review toggles. Each is a consent
   gate: state the egress plainly before offering it.
   - **Default delegation** — route implementation work to Kiro automatically, no
     trigger phrase:
     - **Off (Recommended to start)** — delegate only when explicitly asked.
     - **On** — `python3 "$SK/kiro_config.py" set default_delegate on`
   - **Pre-commit review hook** (off by default) — sends staged diff CONTENT to Kiro's
     backend on every `git commit`. The step-4 `kiro-reviewer` agent confines `fs_read`
     to the isolated diff dir, and both the hook and manual `/kiro:review` fail open and
     SKIP entirely if that file goes missing/tampered (never an unguarded fallback
     without explicit pre-confirmed opt-in) — but the diff content itself still leaves
     the machine:
     - **Off (Recommended to start)** — use `/kiro:review` on demand instead.
     - **On (only for diffs whose authorship you trust — typically your own commits)** —
       `python3 "$SK/kiro_config.py" set review on_commit on`; blocks on `critical`
       findings only.
   - **Pre-push lens gate** (off by default, a separate opt-in) — a 3-lens pass
     (correctness/security/scope, in parallel) over the push range, sent to Kiro's
     backend THREE times per push. Before asking, best-effort check whether co-agent's
     `push_gate` is already on (`python3
     "${CLAUDE_PLUGIN_ROOT}/../co-agent/skills/co-agent/scripts/co_agent_config.py" show
     --root . 2>/dev/null | grep push_gate` — co-agent may not be installed; ignore a
     failure silently) and, if so, say in the option text that both firing means every
     push runs two independent gates:
     - **Off (Recommended to start)** — use
       `/kiro:review --range --lenses correctness,security,scope` on demand.
     - **On** — `python3 "$SK/kiro_config.py" set review on_push on`; `critical` is a
       plain BLOCKED, a `warning`-only set at/above `review.push_block` (default
       `warning`) is framed CHAIR JUDGMENT REQUIRED — read from stderr and judged, not
       auto-vetoed.

6. Ask (`AskUserQuestion`) whether to enable **web search delegation** — routing web
   searches through kiro-cli's native `web_search` when this session has no `WebSearch`
   tool (the common case on Bedrock). State plainly that each search sends the QUERY
   TEXT to Kiro's backend — nothing else leaves the machine (the `kiro-websearch` agent
   is search-only: no `fs_read`/`fs_write`/`execute_bash`, and `kiro_websearch.py`
   refuses to run against a tampered agent file).
   - **On (Recommended for Bedrock users)** — closes the no-WebSearch gap.
     `python3 "$SK/kiro_config.py" set websearch enabled on`
   - **Off** — WebSearch-less sessions skip web searches and say so.

7. Show the final effective config:
   ```bash
   python3 "$SK/kiro_config.py" show
   ```
