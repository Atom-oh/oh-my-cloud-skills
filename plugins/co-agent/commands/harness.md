---
description: Host-designs / peer-implements / panel-reviews orchestrator. The host owns the design, the failing test, and every commit; a cross-provider peer writes code only inside an isolated git worktree under a workspace-write sandbox; the consensus gate reviews. Opt-in, local commits only.
allowed-tools: Read, Glob, Grep, Bash, AskUserQuestion
argument-hint: "<adr|spec|plan|task>  [--implementer codex|claude|agy]"
---

# co-agent: harness

Autonomous **design → delegated-implement → review** with cross-provider role separation.
The **host** (Claude in Claude Code, Codex in Codex) designs, writes the failing test, and
is the **only committer**. A **peer implementer** writes code **only inside an isolated git
worktree** under a workspace-write sandbox. Review reuses the consensus gate.

> Trust boundary, per-task loop, fallback chain, output gate: **`references/delegated-implement.md`**.
> Review-gate mechanics: `references/consensus-mode.md`. CLI details: `references/ai-cli-adapters.md`.

Argument: `$ARGUMENTS`

Let `SK="${CLAUDE_PLUGIN_ROOT:-plugins/co-agent}/skills/co-agent/scripts"` and
`HOST="${CO_AGENT_HOST:-claude}"`.

## H0 — Detect & consent
1. **Consent + cost**: confirm sending context to third-party AIs; show
   `python3 "$SK/co_agent_config.py" matrix --host "$HOST"`.
2. Resolve roles: panel = `co_agent_config.py panel --host "$HOST"`; implementer =
   `co_agent_config.py implementer --host "$HOST"`. Only **sandbox CLIs** (codex, agy) are
   valid implementers (claude/kiro-cli/gemini have no worktree-scoped write sandbox); default is
   claude host → codex, codex host → agy. Never equals the host. Tell the user panel + implementer.
3. **Clean tree required**: `python3 "$SK/consensus_state.py" verify .`
   (`rebind` after an intentional manual commit when resuming). `git worktree prune` to reap orphans.

## H1 — Design (host)
Detect input: `consensus_state.py detect . <doc...>`. A **plan** doc → `parse_plan.py` (no
regen). An **adr/spec** → generate a TDD plan (`docs/superpowers/plans/`), then parse it.
`consensus_state.py init .` from the doc(s); allowed file set = `parse_plan.py <plan> --files`.

## H2 — Plan gate
Run the consensus gate on the plan (`consensus-mode.md`); iterate ≤ `consensus.max_rounds`
to no CRITICAL/MAJOR. Record `…/plan-gate/result.json` via `consensus_state.py stage-result`.
Unresolved → `set . status needs-human` and stop. (Works with the current gate; benefits
from the adversarial/escalation upgrades when present — not required.)

## H3 — Delegated implement (per task) — see `references/delegated-implement.md`
Per task: host writes **and commits** the failing test (so the `--base HEAD` worktree
contains it) → `worktree.py add` (under a gitignored path) → run the
implementer with `co_agent_config.py impl-flags <ai> --host "$HOST"` **inside the worktree**
→ `worktree.py capture-diff` → `scope_guard.py` (drop out-of-scope) → apply patch to main +
`tests/run-all.sh` **on main** → bounded fix loop (`harness.max_fix_rounds`) → `stage-result`
→ **host commits once** → `worktree.py remove`. Fallback chain: counterpart → other peer →
host-implement. Exhausted fix loop → `needs-human`. External AIs never commit.

## H4 — Final gate
`consensus_state.py cumulative-diff . --plan <plan> --base <trunk>` → consensus gate →
fix ≤ `consensus.max_rounds`, require tests green. Record `…/code-gate/result.json`.

## H5 — Report
`consensus_state.py set . status done` then `report .` (writes
`.claude/co-agent-consensus/report.md`, gitignored) — include the implementer attribution
and per-stage `result.json` / `stage_wall.tsv`. Present to the user. Resumable via
`consensus_state` (`phase`/`task_index`).
