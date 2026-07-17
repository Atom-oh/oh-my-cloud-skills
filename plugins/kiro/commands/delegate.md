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

Before starting, if `python3 "${CLAUDE_PLUGIN_ROOT}/skills/kiro-delegate/scripts/kiro_setup.py" probe`
does not report `READY`, tell the user to run `/kiro:setup` first — don't attempt the
worktree/implement steps against an unusable CLI.
