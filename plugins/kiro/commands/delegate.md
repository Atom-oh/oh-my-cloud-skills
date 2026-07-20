---
description: Plan the requested change as a Kiro-native spec, then delegate implementation tasks to Kiro CLI inside isolated worktrees, verifying and committing on the host side. Falls back to writing the code directly when a task's fix loop is exhausted.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
---

# kiro: delegate

$ARGUMENTS

Invoke `kiro-delegate-agent` to run the full pipeline for this request:

1. **Plan** — write `"$ROOT/.kiro/specs/<name>/"{requirements,design,tasks}.md` (never a
   cwd-relative `.kiro/specs/…` — see the `$ROOT` note below) per
   `skills/kiro-delegate/references/spec-format.md`. Keep tasks' `**Files:**` blocks
   complete and backtick-wrapped.
2. **Wave-plan + execute** — per task (or per disjoint-file wave, up to
   `delegate.parallel_tasks`): isolated worktree → Kiro implements → capture-diff →
   scope_guard → apply → test.
3. **Verify + bounded retry** (`delegate.max_fix_rounds`) → **Claude fallback** on
   exhaustion, never a silent skip.
4. **Commit** (host only) + tick off `tasks.md` + report the delegation rate (tasks Kiro
   finished vs. tasks Claude took over).

Before starting (let `ROOT="$(git rev-parse --show-toplevel)"` — every root-sensitive
call below passes `--root "$ROOT"`, same rule as configure/setup/review: these scripts
default their root to the cwd, and a subdirectory invocation without `--root` would
read/write `.kiro/agents/` and the config from the wrong place). **`$ROOT` applies to
every plain `.kiro/…` path too, not just the scripts' own `--root` flag** — the agent's
own pipeline (step 1's spec, step 3's `cp` sources, the clean-tree `git status` below)
must anchor every `.kiro/…` reference to `"$ROOT/.kiro/…"`, or a subdirectory invocation
would read/write specs and copy files from the wrong location while `verify-agents
--root "$ROOT"` above still correctly checked the real one — a silent divergence, not a
hard failure, which makes it worse (see `agents/kiro-delegate-agent.md`'s `$ROOT` note
at the top of its "Pipeline" section for the full rationale):

1. If `python3 "${CLAUDE_PLUGIN_ROOT}/skills/kiro-delegate/scripts/kiro_setup.py" probe`
   does not report `READY`, tell the user to run `/kiro:setup` first — don't attempt the
   worktree/implement steps against an unusable CLI.
2. **Require a plugin-generated `.kiro/agents/kiro-implementer.json` before implementing
   anything** — run
   `python3 "${CLAUDE_PLUGIN_ROOT}/skills/kiro-delegate/scripts/kiro_setup.py" verify-agents --root "$ROOT"`:
   - exit 2 (missing): run `... kiro_setup.py write-agents --root "$ROOT"` first (what
     `/kiro:setup` does). Without the file, the implementer falls back to an ad-hoc
     `--trust-tools=fs_read,fs_write` invocation with NO `preToolUse` write-guard (the
     custom agent file carries that hook — `references/kiro-headless.md` → "Trust
     boundary" step 6). Never fall through to that.
   - exit 1 (tampered / hand-edited): do NOT run it — the pipeline copies it into a
     worktree and runs its `preToolUse.runCommand` hook (a host command). Regenerate
     with `... kiro_setup.py write-agents --force --root "$ROOT"`, or ask the user,
     before delegating.
   - exit 0: proceed.
3. **Require a clean tree on the plan's declared file set before implementing anything**
   (`git -C "$ROOT" --literal-pathspecs status --porcelain -- <files>` — `-C "$ROOT"` so
   this reads the real repo root regardless of cwd; `--literal-pathspecs` is the same
   flag as the restore/clean fallback, so a pathspec is interpreted identically by
   both). If Kiro's
   fix loop is later exhausted for a
   task, the fallback restores/cleans that task's files — which cannot tell "Kiro's own
   half-finished patch" apart from "the user's pre-existing uncommitted edit" to the
   same file. Checking this before any task starts, not after a fallback is triggered,
   is what makes that distinction safe to skip. If any declared file is dirty, stop and
   ask the user to commit/stash it or exclude it from the plan.
