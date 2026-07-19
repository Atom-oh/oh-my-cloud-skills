---
description: Detect kiro-cli, probe real usability, list available models, write the .kiro/agents/*.json custom agents delegate/review use, and set default_delegate / review.on_commit.
allowed-tools: Bash(python3:*), AskUserQuestion
---

# kiro: setup

Let `SK="${CLAUDE_PLUGIN_ROOT}/skills/kiro-delegate/scripts"` and
`ROOT="$(git rev-parse --show-toplevel)"`. **Every `kiro_config.py` / `write-agents`
call below passes `--root "$ROOT"`** — these scripts default their root to the cwd, but
`.claude/kiro.local.json` and `.kiro/agents/` live at the repo root and the pre-commit
hook / delegate pipeline read them from there. Run from a subdirectory without `--root`
and the settings/agents land in `<subdir>/...`, which nothing else reads — a toggle the
user just turned on would silently not apply.

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
   python3 "$SK/kiro_config.py" set review model "<chosen review model>" --root "$ROOT"
   python3 "$SK/kiro_config.py" set delegate model "<chosen delegate model>" --root "$ROOT"   # or skip to keep CLI default
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
   python3 "$SK/kiro_setup.py" write-agents --root "$ROOT" [--enable-bash]
   ```
   These live at `.kiro/agents/kiro-implementer.json` (fs_read/fs_write, plus
   execute_bash only if granted in step 3; worktree-write-only via a preToolUse hook)
   and `.kiro/agents/kiro-reviewer.json` (fs_read only). Re-run with `--force` if the
   user wants to regenerate them (e.g. after changing the step 3 answer).

5. Ask (`AskUserQuestion`) whether to turn on **default delegation** — routing
   implementation work to Kiro automatically without a trigger phrase:
   - **Off (Recommended to start)** — delegate only when explicitly asked
     (`/kiro:delegate` or a trigger phrase).
   - **On** — `python3 "$SK/kiro_config.py" set default_delegate on --root "$ROOT"`
   And whether to turn on the **pre-commit review hook** (**off by default**) — note
   that this hook sends staged diff CONTENT to a `fs_read`-capable reviewer with no path
   restriction beyond the diff file itself, so an untrusted diff (e.g. reviewing a
   contributor's PR branch) could in principle prompt-inject the reviewer into reading
   an unrelated file; mention this plainly, not just the block-severity behavior:
   - **Off (Recommended to start)** — no automatic review; use `/kiro:review` on demand
     when you do want one.
   - **On (only for diffs you trust the authorship of — typically your own commits)** —
     `python3 "$SK/kiro_config.py" set review on_commit on --root "$ROOT"`; review every `git commit`'s
     staged diff, block on `critical` findings only.

6. Show the final effective config:
   ```bash
   python3 "$SK/kiro_config.py" show --root "$ROOT"
   ```
