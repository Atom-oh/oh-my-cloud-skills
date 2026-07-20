---
name: kiro-delegate
description: "Claude plans and verifies, Kiro CLI implements on its own flat-rate subscription credits — a cost-savings implementation-delegation workflow, not a second opinion (see co-agent for that). Kiro implements inside an isolated git worktree; only the captured, scope-guarded diff ever reaches the main tree. Triggers on 'kiro한테 시켜서 구현', 'kiro로 구현', 'kiro한테 구현 위임', 'delegate implementation to kiro', 'kiro implement this'. For read-only review of a diff, use the /kiro:review command instead — this skill is write-capable (it commits) and deliberately does NOT own review triggers."
triggers:
  # This skill is WRITE-CAPABLE (allowed-tools below include Write/Edit/Bash; the
  # pipeline plans → implements → commits). Its trigger set therefore contains ONLY
  # explicit implementation-delegation phrasings — never a review phrasing, because a
  # trigger match loads this skill (and its write tools). Read-only review has its own
  # entry point, the `/kiro:review` command, which needs no skill trigger to be
  # reachable; routing "review" here would be a write-capable activation for a
  # read-only request. Also excludes informational phrasings ("kiro credits", "비용
  # 절감 kiro") — those are questions about the plugin, not requests to act. This set is
  # kept identical to agents/kiro-delegate-agent.md's description and CLAUDE.md's
  # Skill/Auto-Invocation tables.
  - "kiro한테 시켜서 구현"
  - "kiro로 구현"
  - "kiro한테 구현 위임"
  - "delegate implementation to kiro"
  - "kiro implement this"
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

**This skill covers implementation delegation only; review is a separate command.**
This skill (and `kiro-delegate-agent`) is write-capable — it plans, implements, and
**commits** — so its triggers are all explicit *implementation*-delegation phrasings.
Read-only review of a diff is the **`/kiro:review`** command (`kiro_review.py`), a
distinct entry point that never loads this write-capable skill. That separation is
structural (the review triggers are simply not in this skill's `triggers:` set), not a
prose convention — so a "review this with kiro" request can't accidentally activate the
implement-and-commit pipeline.

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

`review.on_commit` is **off by default** — the staged diff CONTENT is sent to Kiro's
backend, so enabling is a deliberate choice. The plugin-written `kiro-reviewer` agent
carries a tool-layer `preToolUse` guard that confines `fs_read` to the isolated temp
dir holding only the diff (a prompt-injection payload in an untrusted diff can't make
it read an unrelated path); if that agent file is missing or tampered, `kiro_review.py`
**fails open and skips the review entirely by default** rather than falling back
unguarded — this applies to both the automatic hook and the manual `/kiro:review`
command, since a warning printed right before an already-unguarded call runs isn't a
real chance to object to it. `/kiro:review` can still run unguarded, but only via an
explicit `--allow-unguarded` the command gates behind an `AskUserQuestion` confirmation
first. Turn the hook on via `/kiro:setup` or
`/kiro:configure set review on_commit on`. Once on, a
`PreToolUse(Bash)` hook runs before every `git commit`: it sends the staged diff to Kiro
on the configured **review model** (meant to be Kiro's strongest/newest —
`/kiro:setup` helps you pick one, e.g. `gpt-5.6-sol`) and blocks the commit (exit 2) only
on `critical` findings by default (`review.block`: `critical` | `warning` | `none`). It
**fails open** — a missing/timed-out/unauthenticated Kiro never blocks a commit; the
review is skipped and a warning is printed instead. Bypass a single commit with an
**inline** `KIRO_REVIEW=off git commit ...` prefix — the hook recognizes this literal
prefix in the command text itself (not the hook process's own environment, which a
same-line assignment never reaches; a separately-`export`ed value from a prior command
also won't help, since shell state doesn't persist between Bash tool calls) — or turn
it off persistently with `/kiro:configure set review on_commit off`.

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
- `scripts/kiro_config.py` — layered settings (`kiro.defaults.json` ← `.claude/kiro.local.json`,
  gitignored by convention; if a consumer repo commits it anyway, its
  `default_delegate`/`review.on_commit` values are ignored and fall back to off — a
  committed file can't silently opt an installing user into diff egress or
  auto-delegation)
- `scripts/kiro_review.py` — the Kiro-run review used by `/kiro:review` and the hook
- `scripts/kiro_setup.py` — probe, model listing, `.kiro/agents/*.json` generation
