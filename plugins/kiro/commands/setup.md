---
description: Detect kiro-cli, probe real usability, list available models, write the .kiro/agents/*.json custom agents delegate/review use, and set default_delegate / review.on_commit.
allowed-tools: Bash(python3:*), AskUserQuestion
---

# kiro: setup

Let `SK="${CLAUDE_PLUGIN_ROOT}/skills/kiro-delegate/scripts"`. `kiro_config.py` and
`kiro_setup.py` resolve the repo root themselves (`git rev-parse --show-toplevel`, run
as a python3 subprocess — not a `Bash` tool call, so it stays inside this command's
`Bash(python3:*)` allowed-tools scope) whenever `--root` is omitted, so
`.claude/kiro.local.json` and `.kiro/agents/` — which live at the repo root, and which
the pre-commit hook / delegate pipeline also read from there — land in the right place
even when this command runs from a subdirectory. No need to compute or pass `--root`
below unless you want to target a DIFFERENT repo than the cwd's.

1. Detect and probe (`kiro_setup.py probe` already checks PATH presence itself — no
   separate `command -v` call needed, and one avoids a permission prompt this command's
   `Bash(python3:*)` allowed-tools scope wouldn't auto-approve):
   ```bash
   python3 "$SK/kiro_setup.py" probe
   ```
   If `ABSENT`: tell the user to install Kiro CLI (`https://kiro.dev`) and stop here —
   nothing else in this command can proceed without it.
   If `AUTH`: tell them to run `kiro-cli` interactively to log in, or set `KIRO_API_KEY`,
   then re-run `/kiro:setup`.
   If `NO_INGEST`: kiro-cli ran but didn't echo the probe's sentinel back — report this
   as "kiro-cli responded but couldn't be verified usable" and offer to retry once before
   treating it as a real problem (some CLI builds behave this way transiently).
   If `TIMEOUT`/`ERROR`: report the reason and offer to retry once (cold-start CLIs can be
   slow on the first call).

2. On `READY`, list models and help pick two — a delegate (implement) model and a review
   model:
   ```bash
   python3 "$SK/kiro_setup.py" list-models
   ```
   Use `AskUserQuestion` to offer the review-model choice explicitly, since the plugin's
   whole point is a strong reviewer behind a cost-efficient implementer:
   - **Review model** — recommend the newest/strongest listed model (e.g. `gpt-5.6-sol`
     if present) — first option, `(Recommended)`.
   - **Delegate model** — any model that reliably finishes tasks; default/CLI-routed is
     fine if the user has no preference (flat-rate credits mean there's no cost trade-off
     to reason about here, unlike a metered API).
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
   - **No shell access (Recommended to start)** — the implementer gets `fs_read`/
     `fs_write` only. Some tasks that genuinely need a shell command (installing a
     dependency, running a generator script) will fall back to Claude implementing them
     directly instead of Kiro.
   - **Grant `execute_bash`** — the implementer can run shell commands, auto-approved,
     with the host-side risk above. Only choose this if you're comfortable extending that
     trust to `kiro-cli` the same way you would to any other agentic CLI with shell
     access on this machine.

4. Write the custom agents Kiro uses in headless mode, per the answer to step 3:
   ```bash
   python3 "$SK/kiro_setup.py" write-agents [--enable-bash]
   ```
   These live at `.kiro/agents/kiro-implementer.json` (fs_read/fs_write, plus
   execute_bash only if granted in step 3; worktree-write-only via a preToolUse hook)
   and `.kiro/agents/kiro-reviewer.json` (fs_read only). Re-run with `--force` if the
   user wants to regenerate them (e.g. after changing the step 3 answer).

5. Ask (`AskUserQuestion`) whether to turn on **default delegation** — routing
   implementation work to Kiro automatically without a trigger phrase:
   - **Off (Recommended to start)** — delegate only when explicitly asked
     (`/kiro:delegate` or a trigger phrase).
   - **On** — `python3 "$SK/kiro_config.py" set default_delegate on`
   And whether to turn on the **pre-commit review hook** (**off by default**) — note
   that this hook sends staged diff CONTENT to Kiro's backend. The `kiro-reviewer`
   agent written in step 4 carries a tool-layer `fs_read` guard confining reads to the
   isolated diff dir (a prompt-injecting untrusted diff can't make it read an unrelated
   file); still mention that the diff content itself leaves the machine, and that the
   guard depends on the step-4 agent file staying in place (this and the manual
   `/kiro:review` command both fail open and SKIP the review entirely by default if
   that file goes missing/tampered — neither falls back to an unguarded invocation
   without an explicit, pre-confirmed opt-in):
   - **Off (Recommended to start)** — no automatic review; use `/kiro:review` on demand
     when you do want one.
   - **On (only for diffs you trust the authorship of — typically your own commits)** —
     `python3 "$SK/kiro_config.py" set review on_commit on`; review every `git commit`'s
     staged diff, block on `critical` findings only.

6. Show the final effective config:
   ```bash
   python3 "$SK/kiro_config.py" show
   ```
