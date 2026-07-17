# kiro Plugin — Claude Code Configuration

Cost-savings delegation: **Claude plans and verifies, Kiro CLI implements and reviews**
on its own flat-rate subscription credits. Not a second opinion — `co-agent` covers that
(multi-AI review/decision/ADR); this plugin exists purely to move token-expensive work
(writing code, reviewing diffs) off this session's budget and onto Kiro's.

**Prerequisite**: `kiro-cli` (+ interactive login or `KIRO_API_KEY`). Run `/kiro:setup`
first — it probes real usability, lists models, and writes the `.kiro/agents/*.json`
custom agents the delegate/review paths invoke. Without a `READY` peer, `/kiro:delegate`
tells the user to run setup rather than silently falling back (falling back mid-pipeline,
per-task, is expected and reported; falling back for the *entire* run because Kiro was
never set up is not).

---

## Agents

| Agent | Purpose |
|-------|---------|
| `kiro-delegate-agent` | Orchestrates plan → spec → per-task Kiro implement (isolated worktree) → verify → commit → delegation-rate report |

## Skill

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `kiro-delegate` | "kiro한테 시켜", "kiro로 구현", "delegate to kiro", "kiro 위임", "kiro가 리뷰", "kiro credits" | Cost-savings implementation + review delegation to Kiro CLI |

## Commands

| Command | Purpose |
|---------|---------|
| `/kiro:setup` | Detect + probe kiro-cli, list models, write `.kiro/agents/*.json`, toggle default-delegate / review-on-commit |
| `/kiro:delegate <request>` | Run the full plan → delegate → verify → commit pipeline |
| `/kiro:review [paths]` | On-demand Kiro review (same engine as the pre-commit hook) |
| `/kiro:configure` | Inspect/change settings |

## Trust boundary (why Kiro can write here when co-agent's harness refuses it)

Kiro has no cwd-confined write sandbox, so co-agent's harness excludes it as an
implementer (`SANDBOX_IMPLEMENTERS = codex, agy`). This plugin makes it safe anyway: Kiro
only ever runs with cwd = a throwaway git worktree; the host applies **only** what
`worktree.py capture-diff` captured from inside that worktree, after `scope_guard.py`
drops anything outside the current task's declared file set. Kiro never commits — Claude
is the only committer. Detail: `skills/kiro-delegate/references/kiro-headless.md`.

## Pre-commit review (PreToolUse hook)

`hooks/pre-commit-review.sh` matches `git commit` at a command boundary and runs
`kiro_review.py --staged` before it. **Fails open** on any internal error, missing/
unauthenticated `kiro-cli`, or `review.on_commit=false` — a broken reviewer must never
wedge a commit. Blocks (exit 2) only on findings at/above `review.block` (default
`critical`). Bypass one commit with `KIRO_REVIEW=off`; disable persistently via
`/kiro:configure set review on_commit off`.

## Model tiering

- **Delegate (implement) model** — flat-rate credits, no per-token cost trade-off; point
  it at whatever model finishes tasks correctly.
- **Review model** — deliberately kept at Kiro's strongest/newest available model (e.g.
  `gpt-5.6-sol`), even when the delegate model is lighter — the review is the safety net
  behind the implementer's output.

## Scripts reused from co-agent (unmodified)

`skills/kiro-delegate/scripts/worktree.py`, `scope_guard.py`, `parse_plan.py` are copied
verbatim from `plugins/co-agent/skills/co-agent/scripts/` — the isolation/scoping
mechanics (worktree capture, plan-scoped file allowlist) are identical; only the
implementer CLI differs. `kiro_config.py`/`kiro_review.py`/`kiro_setup.py` are new,
scoped to this plugin's single peer.

## Auto-Invocation Keywords

| 한국어 | English |
|--------|---------|
| kiro한테 시켜 | delegate to kiro |
| kiro로 구현 | kiro implement |
| kiro 위임 | delegate to kiro |
| kiro가 리뷰 | kiro review |

## Workflow

```
/kiro:setup     → detect kiro-cli, probe, list models, write .kiro/agents/*.json
/kiro:delegate  → Claude plans (Kiro-native spec) → wave-plan tasks
                → per task: worktree → Kiro implements → capture-diff → scope_guard
                → Claude applies + tests → bounded retry → Claude fallback if exhausted
                → Claude commits → delegation-rate report
git commit      → PreToolUse hook → kiro_review.py (fail-open, blocks only on `critical`)
/kiro:review    → same review engine, on demand
```
