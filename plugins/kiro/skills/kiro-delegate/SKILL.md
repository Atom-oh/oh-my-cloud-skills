---
name: kiro-delegate
description: "Claude plans and verifies, Kiro CLI implements and reviews on its own flat-rate subscription credits — a cost-savings delegation workflow, not a second opinion (see co-agent for that). Kiro implements inside an isolated git worktree; only the captured, scope-guarded diff ever reaches the main tree. Triggers on 'kiro한테 시켜', 'kiro로 구현', 'kiro한테 위임', 'kiro 위임', 'delegate to kiro', 'kiro implement', 'kiro가 구현' (all → /kiro:delegate, write-capable), and 'kiro가 리뷰'/'kiro review' (→ /kiro:review ONLY, read-only — never the write-capable delegate pipeline below)."
triggers:
  # Canonical trigger set — kept identical (same wording, same order) across this
  # frontmatter, this file's own description above, agents/kiro-delegate-agent.md's
  # description, and CLAUDE.md's Skill/Auto-Invocation tables — EXCEPT
  # agents/kiro-delegate-agent.md intentionally drops the two review triggers below
  # (that agent is write-capable: plan → implement → commit; it must never be reached
  # by a review-only request). Deliberately excludes informational phrasings like
  # "kiro credits" or "비용 절감 kiro" — those read as a question about the plugin, not
  # a request to act, and routing them into a write-capable pipeline would be a
  # false-positive activation.
  - "kiro한테 시켜"        # → /kiro:delegate (write)
  - "kiro로 구현"          # → /kiro:delegate (write)
  - "kiro한테 위임"        # → /kiro:delegate (write)
  - "kiro 위임"            # → /kiro:delegate (write)
  - "delegate to kiro"     # → /kiro:delegate (write)
  - "kiro implement"       # → /kiro:delegate (write)
  - "kiro가 구현"          # → /kiro:delegate (write)
  - "kiro가 리뷰"          # → /kiro:review ONLY (read-only) — NOT kiro-delegate-agent
  - "kiro review"          # → /kiro:review ONLY (read-only) — NOT kiro-delegate-agent
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

**Routing within this skill's trigger set is NOT one path.** "kiro review"/"kiro가
리뷰" route to the **read-only** `/kiro:review` command (`kiro_review.py`) — never to
`kiro-delegate-agent`, which is a write-capable orchestrator that plans, implements, and
**commits**. `kiro-delegate-agent.md`'s own description explicitly excludes the review
triggers for this reason. Every other trigger in the list above ("kiro한테 시켜", "kiro
로 구현", "delegate to kiro", …) routes to `kiro-delegate-agent` / `/kiro:delegate`.

## What "safe" means here — and what it doesn't (co-agent can't allow this at all)

`co-agent:harness` refuses Kiro as an implementer (`SANDBOX_IMPLEMENTERS = codex, agy`
only) because Kiro has no cwd-confined write sandbox. This plugin narrows the claim
rather than pretending the sandbox exists: **only a change captured from inside the
assigned worktree, and within the plan's declared file set, can ever reach the main
tree** — that is enforced by `worktree.py capture-diff` + `scope_guard.py` (the latter
checks the plan-wide union of every task's files, not a single task in isolation, so
per-task boundaries during a wave come from serializing implementer runs per file set,
not from `scope_guard.py` itself). It does **not** constrain what an auto-approved
`execute_bash` call can do to the rest of the host while Kiro is running (read
credentials, delete files outside the worktree) — running Kiro with `execute_bash`
trusted is a decision you make about `kiro-cli` itself, independent of this pipeline's
worktree/capture/scope-guard layers. See `plugins/kiro/CLAUDE.md` → "Trust decision"
before enabling `default_delegate`. Kiro never commits.

## Commands

| Command | Purpose |
|---------|---------|
| `/kiro:setup` | Detect `kiro-cli`, probe real usability, list available models, write `.kiro/agents/{kiro-implementer,kiro-reviewer}.json`, set `default_delegate`/`review.on_commit` |
| `/kiro:delegate <request>` | Plan → spec → Kiro implements per task → Claude verifies + commits → delegation-rate report |
| `/kiro:review [paths...]` | Run the same Kiro-powered review the pre-commit hook runs, on demand (default: staged changes) |
| `/kiro:configure` | Inspect/change `default_delegate`, delegate/review models, `parallel_tasks`, `max_fix_rounds`, `review.on_commit`, `review.block` |

## Pre-commit review (opt-in)

`review.on_commit` is **off by default** — the reviewer's `fs_read` tool isn't scoped
to just the diff file, so a prompt-injection payload in an untrusted staged diff could
direct it to read an unrelated absolute path and leak it into the review response sent
to Kiro's backend. Turn it on (`/kiro:setup`, or `/kiro:configure set review on_commit
on`) only for diffs you trust the authorship of — typically your own commits. Once on, a
`PreToolUse(Bash)` hook runs before every `git commit`: it sends the staged diff to Kiro
on the configured **review model** (meant to be Kiro's strongest/newest —
`/kiro:setup` helps you pick one, e.g. `gpt-5.6-sol`) and blocks the commit (exit 2) only
on `critical` findings by default (`review.block`: `critical` | `warning` | `none`). It
**fails open** — a missing/timed-out/unauthenticated Kiro never blocks a commit; the
review is skipped and a warning is printed instead. Bypass a single commit with
`KIRO_REVIEW=off`, or turn it off persistently with `/kiro:configure set review
on_commit off`.

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
