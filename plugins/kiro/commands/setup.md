---
description: Detect kiro-cli, probe real usability, list available models, write the .kiro/agents/*.json custom agents delegate/review use, and set default_delegate / review.on_commit.
allowed-tools: Bash(python3:*), AskUserQuestion
---

# kiro: setup

Let `SK="${CLAUDE_PLUGIN_ROOT}/skills/kiro-delegate/scripts"`.

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

3. Write the custom agents Kiro uses in headless mode:
   ```bash
   python3 "$SK/kiro_setup.py" write-agents
   ```
   These live at `.kiro/agents/kiro-implementer.json` (fs_read/fs_write/execute_bash,
   worktree-write-only via a preToolUse hook) and `.kiro/agents/kiro-reviewer.json`
   (fs_read only). Re-run with `--force` if the user wants to regenerate them.

4. Ask (`AskUserQuestion`) whether to turn on **default delegation** — routing
   implementation work to Kiro automatically without a trigger phrase:
   - **Off (Recommended to start)** — delegate only when explicitly asked
     (`/kiro:delegate` or a trigger phrase).
   - **On** — `python3 "$SK/kiro_config.py" set default_delegate on`
   And whether to keep the **pre-commit review hook** on (default is on):
   - **On (Recommended)** — review every `git commit`'s staged diff, block on `critical`
     findings only.
   - **Off** — `python3 "$SK/kiro_config.py" set review on_commit off`

5. Show the final effective config:
   ```bash
   python3 "$SK/kiro_config.py" show
   ```
