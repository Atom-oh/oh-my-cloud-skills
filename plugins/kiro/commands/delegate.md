---
description: Plan the requested change as a Kiro-native spec, then delegate implementation tasks to Kiro CLI inside isolated worktrees, verifying and committing on the host side. Falls back to writing the code directly when a task's fix loop is exhausted.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, AskUserQuestion
---

# kiro: delegate

$ARGUMENTS

Invoke `kiro-delegate-agent` (via the `Agent` tool) to run the full pipeline for this
request — that agent's step-by-step pipeline (preflight, `$ROOT`-anchoring, symlink
refusals, per-wave commits) governs execution; the summary below is this command's entry
point, not a substitute for loading it:

1. **Plan** — write `"$ROOT/.kiro/specs/<name>/"{requirements,design,tasks}.md` per
   `skills/kiro-delegate/references/spec-format.md`, with every task's `**Files:**`
   entries backtick-wrapped.
2. **Wave-plan + execute** — per task (or per disjoint-file wave, up to
   `delegate.parallel_tasks`): isolated worktree → Kiro implements → capture-diff →
   scope_guard → apply → test.
3. **Verify + bounded retry** (`delegate.max_fix_rounds`) → **Claude fallback** on
   exhaustion, never a silent skip.
4. **Commit** (host only) + tick off `tasks.md` + report the delegation rate.

Before starting, let `ROOT="$(git rev-parse --show-toplevel)"` and pass `--root "$ROOT"`
to every script call below. **Anchor every plain `.kiro/…` path to `"$ROOT/.kiro/…"` as
well** — from a subdirectory, a cwd-relative path reads/writes specs and support files
somewhere preflight never verified, a silent divergence rather than a hard failure (full
rationale: the `$ROOT` note atop `agents/kiro-delegate-agent.md` → "Pipeline").

1. If `python3 "${CLAUDE_PLUGIN_ROOT}/skills/kiro-delegate/scripts/kiro_setup.py" probe`
   does not report `READY`, tell the user to run `/kiro:setup` first — don't attempt the
   worktree/implement steps against an unusable CLI.
2. Run
   `python3 "${CLAUDE_PLUGIN_ROOT}/skills/kiro-delegate/scripts/kiro_setup.py" verify-agents --root "$ROOT"`:
   - exit 2 (missing): run `... kiro_setup.py write-agents --root "$ROOT"` first. Never
     fall through to an ad-hoc `--trust-tools=fs_read,fs_write` invocation — the custom
     agent file is what carries the `preToolUse` write-guard
     (`references/kiro-headless.md` → "Trust boundary" step 6).
   - exit 1 (tampered / hand-edited): do NOT run it — the pipeline copies it into a
     worktree and its `preToolUse.runCommand` is a host command that executes.
     Regenerate with `... kiro_setup.py write-agents --force --root "$ROOT"`, or ask
     the user, before delegating.
   - exit 0: proceed.
3. Require a clean tree on the plan's declared file set:
   `git -C "$ROOT" --literal-pathspecs status --porcelain -- <files>` must be empty
   (`--literal-pathspecs` matches the fallback's restore/clean, so both interpret every
   pathspec identically). The fallback restore/clean cannot tell Kiro's half-finished
   patch from the user's pre-existing uncommitted edit — checking before any task starts
   is what makes that safe. If any declared file is dirty, stop and ask the user to
   commit/stash it or exclude it from the plan.
