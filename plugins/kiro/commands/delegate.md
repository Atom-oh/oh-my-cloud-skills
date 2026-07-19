---
description: Plan the requested change as a Kiro-native spec, then delegate implementation tasks to Kiro CLI inside isolated worktrees, verifying and committing on the host side. Falls back to writing the code directly when a task's fix loop is exhausted.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
---

# kiro: delegate

$ARGUMENTS

Invoke `kiro-delegate-agent` to run the full pipeline for this request:

1. **Plan** — write `.kiro/specs/<name>/{requirements,design,tasks.md}` per
   `skills/kiro-delegate/references/spec-format.md`. Keep tasks' `**Files:**` blocks
   complete and backtick-wrapped.
2. **Wave-plan + execute** — per task (or per disjoint-file wave, up to
   `delegate.parallel_tasks`): isolated worktree → Kiro implements → capture-diff →
   scope_guard → apply → test.
3. **Verify + bounded retry** (`delegate.max_fix_rounds`) → **Claude fallback** on
   exhaustion, never a silent skip.
4. **Commit** (host only) + tick off `tasks.md` + report the delegation rate (tasks Kiro
   finished vs. tasks Claude took over).

Before starting:

1. If `python3 "${CLAUDE_PLUGIN_ROOT}/skills/kiro-delegate/scripts/kiro_setup.py" probe`
   does not report `READY`, tell the user to run `/kiro:setup` first — don't attempt the
   worktree/implement steps against an unusable CLI.
2. **Require `.kiro/agents/kiro-implementer.json` to exist before implementing anything.**
   Without it, the implementer falls back to an ad-hoc `--trust-tools=fs_read,fs_write`
   invocation that has NO `preToolUse` write-guard (the custom agent file is what
   carries that hook — see `references/kiro-headless.md` → "Trust boundary" step 6). If
   the file is missing, run
   `python3 "${CLAUDE_PLUGIN_ROOT}/skills/kiro-delegate/scripts/kiro_setup.py" write-agents`
   first (this is exactly what `/kiro:setup` does — running it here just means the user
   skipped setup and went straight to delegate) — never silently fall through to the
   unguarded ad-hoc invocation.
3. **Require a clean tree on the plan's declared file set before implementing anything**
   (`git status --porcelain -- <files>`). If Kiro's fix loop is later exhausted for a
   task, the fallback restores/cleans that task's files — which cannot tell "Kiro's own
   half-finished patch" apart from "the user's pre-existing uncommitted edit" to the
   same file. Checking this before any task starts, not after a fallback is triggered,
   is what makes that distinction safe to skip. If any declared file is dirty, stop and
   ask the user to commit/stash it or exclude it from the plan.
