---
name: kiro-delegate
description: "Claude plans and verifies, Kiro CLI implements and reviews on its own flat-rate subscription credits — a cost-savings delegation workflow, not a second opinion (see co-agent for that). Kiro implements inside an isolated git worktree; only the captured, scope-guarded diff ever reaches the main tree. Triggers on 'kiro한테 시켜', 'kiro로 구현', 'delegate to kiro', 'kiro 위임', 'kiro가 리뷰', 'kiro credits'."
triggers:
  - "kiro한테 시켜"
  - "kiro로 구현"
  - "kiro한테 위임"
  - "kiro 위임"
  - "delegate to kiro"
  - "kiro implement"
  - "kiro가 구현"
  - "kiro가 리뷰"
  - "kiro review"
  - "kiro credits"
  - "비용 절감 kiro"
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - AskUserQuestion
---

# kiro-delegate — Cost-Savings Implementation Delegation

Claude (or Codex, in the Codex-plugin variant) plans, decomposes, and verifies. **Kiro
CLI does the token-expensive part** — writing the code and reviewing diffs — running on
its own flat-rate subscription credits instead of this session's budget. This is
deliberately **not** a multi-AI review/consensus tool (that's `co-agent` — different
goal: diversity of opinion, not cost). Kiro is delegated to because it's cheaper for the
work, not because a second opinion is wanted.

> Full trust-boundary rationale, CLI adapter detail, and spec format: see
> `references/kiro-headless.md` and `references/spec-format.md`. The orchestration
> agent (`agents/kiro-delegate-agent.md`) carries the authoritative step-by-step pipeline
> — this file routes intent and covers the commands.

## Why Kiro can be trusted with write access here (co-agent can't allow it)

`co-agent:harness` refuses Kiro as an implementer (`SANDBOX_IMPLEMENTERS = codex, agy`
only) because Kiro has no cwd-confined write sandbox. This plugin makes it safe anyway:
Kiro only ever runs with cwd = a throwaway git worktree, and the host applies **only**
what `worktree.py capture-diff` captured from inside it, after `scope_guard.py` drops
anything outside the current task's declared file set. Kiro never commits.

## Commands

| Command | Purpose |
|---------|---------|
| `/kiro:setup` | Detect `kiro-cli`, probe real usability, list available models, write `.kiro/agents/{kiro-implementer,kiro-reviewer}.json`, set `default_delegate`/`review.on_commit` |
| `/kiro:delegate <request>` | Plan → spec → Kiro implements per task → Claude verifies + commits → delegation-rate report |
| `/kiro:review [paths...]` | Run the same Kiro-powered review the pre-commit hook runs, on demand (default: staged changes) |
| `/kiro:configure` | Inspect/change `default_delegate`, delegate/review models, `parallel_tasks`, `max_fix_rounds`, `review.on_commit`, `review.block` |

## Pre-commit review (automatic)

When `review.on_commit` is on (default), a `PreToolUse(Bash)` hook runs before every
`git commit`: it sends the staged diff to Kiro on the configured **review model**
(meant to be Kiro's strongest/newest — `/kiro:setup` helps you pick one, e.g.
`gpt-5.6-sol`) and blocks the commit (exit 2) only on `critical` findings by default
(`review.block`: `critical` | `any` | `none`). It **fails open** — a missing/timed-out/
unauthenticated Kiro never blocks a commit; the review is skipped and a warning is
printed instead. Bypass a single commit with `KIRO_REVIEW=off`, or turn it off
persistently with `/kiro:configure set review on_commit off`.

## Delegate vs. review — different models, on purpose

- **Delegate (implement) model** — `delegate.model`. Flat-rate CLI, so no per-token cost
  trade-off; point it at whatever finishes tasks correctly (fewer fix-rounds = pure
  wall-clock savings).
- **Review model** — `review.model`. Deliberately kept at Kiro's *strongest* available
  model even if the delegate model is lighter — the review is the safety net behind
  whatever the implementer produced, so it shouldn't be the weak link.

## Default-delegate mode

`default_delegate` (off by default) routes implementation requests through this
pipeline automatically, without needing a "delegate to kiro" trigger phrase — falling
back to Claude writing the code whenever Kiro is unavailable or exhausts its fix loop.
Set it from `/kiro:setup` or `/kiro:configure set default_delegate on`.

## Never

- Never run Kiro with cwd = the repo root (or anything other than its assigned worktree)
  in write mode.
- Never apply an uncaptured or unscoped patch to the main tree.
- Never let Kiro run `git commit`/`push`/`reset`.
- Never let a stuck task silently drop work — it becomes a reported Claude fallback.

## References

- `references/kiro-headless.md` — CLI invocation, auth, trust boundary, model tiering
- `references/spec-format.md` — Kiro spec structure + `tasks.md` format the scripts parse
- `scripts/worktree.py`, `scripts/scope_guard.py`, `scripts/parse_plan.py` — copied
  verbatim from co-agent (the isolation/scoping mechanics are identical; only the
  implementer CLI differs)
- `scripts/kiro_config.py` — layered settings (`kiro.defaults.json` ← `.claude/kiro.local.json`)
- `scripts/kiro_review.py` — the Kiro-run review used by `/kiro:review` and the hook
- `scripts/kiro_setup.py` — probe, model listing, `.kiro/agents/*.json` generation
