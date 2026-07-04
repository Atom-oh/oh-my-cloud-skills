---
description: Host-designs / peer-implements / panel-reviews orchestrator. The host owns the design, the failing test, and every commit; ONE cross-provider implementer writes code as parallel per-task subagents in isolated git worktrees under a workspace-write sandbox; a hybrid gate reviews (parallel find → chair triage → parallel verify). Opt-in, local commits only.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
argument-hint: "<adr|spec|plan|task>  [--implementer codex|agy]"
---

# co-agent: harness

Autonomous **design → delegated-implement → review** with cross-provider role separation.
The **host** (Claude in Claude Code, Codex in Codex) designs, writes the failing test, and
is the **only committer**. A **peer implementer** writes code **only inside an isolated git
worktree** under a workspace-write sandbox. Review runs the **hybrid gate** by default —
parallel find → chair triage (the chair keeps only meaningful findings) → parallel verify
of the curated digest (`harness.review_mode`: `hybrid` | `relay` | `parallel`).
Implementation stays with **one** implementer AI but fans out as **parallel per-task
subagents** in separate worktrees (`harness.parallel_tasks`, default 3).

> Trust boundary, per-task loop + parallel waves, fallback chain, output gate:
> **`references/delegated-implement.md`**. Review-gate mechanics: **hybrid**
> `references/hybrid-gate.md` (default) · relay `references/relay-chain-gate.md` ·
> parallel `references/consensus-mode.md`. CLI details: `references/ai-cli-adapters.md`.
> Want the host itself to write the code instead (no peer, no worktree)? Use
> `/co-agent:consensus`. Side-by-side comparison: `SKILL.md` → "Consensus vs harness".

Argument: `$ARGUMENTS`

Let `SK="${CLAUDE_PLUGIN_ROOT}/skills/co-agent/scripts"` and
`HOST="${CO_AGENT_HOST:-claude}"`.

## H0 — Detect & consent
1. **Consent + cost**: resolve `MODE=$(python3 "$SK/co_agent_config.py" review-mode)`; the
   `hybrid` default fans out **twice** per round (find + verify), so show
   `python3 "$SK/co_agent_config.py" matrix --host "$HOST" $([ "$MODE" = hybrid ] && echo --phases 2)`
   — passing `--phases 2` only for hybrid keeps the displayed max-calls total accurate for
   whichever gate mode is actually configured. Confirm sending context to third-party AIs.
2. Resolve roles: panel = `co_agent_config.py panel --host "$HOST"`; implementer =
   `co_agent_config.py implementer --host "$HOST"` (user-selectable:
   `set harness implementer codex|agy`). Only **sandbox CLIs** (codex, agy) are valid
   implementers — kiro-cli stays review-panel-only (no worktree-scoped write sandbox);
   default is claude host → codex, codex host → agy. Never equals the host. Tell the user
   panel + implementer + wave concurrency (`co_agent_config.py parallel-tasks`).
3. **Consult readiness** (`.claude/co-agent-panel.local.json` from `/co-agent:setup`):
   `check_panel.py fresh` (re-run `/co-agent:setup` if `stale`), then `check_panel.py
   gate-eligible <peer>` — keep for the **review panel** only peers returning `true`
   (`status==READY` **and** `raw_cli`), **not** bare `status` (the fan-out calls raw CLIs only,
   so a plugin-only peer yields zero panel output). The **implementer** must be gate-eligible
   **plus** a sandbox CLI (codex/agy). (A peer with BOTH the plugin and a raw CLI is
   `access: plugin` yet `raw_cli: true` → still eligible; only `raw_cli:false` is out.) No
   implementer-eligible peer → host-implement; **no gate-eligible peer** at all → **block** and
   run `/co-agent:setup`. Absent summary → run `/co-agent:setup` first.
4. **Clean tree required**: refuse to start on a dirty tree — `test -z "$(git -C . status --porcelain)"`.
   `git worktree prune` to reap orphans. (`consensus_state.py verify`/`rebind` are for **resume**,
   after a session exists — they are run in H1+, not here, since `verify` fails when no session
   has been `init`'d yet.)

## H1 — Design (host)
Detect input: `consensus_state.py detect . <doc...>`. A **plan** doc → `parse_plan.py` (no
regen). An **adr/spec** → generate a TDD plan (`docs/superpowers/plans/`), then parse it.
`consensus_state.py init .` from the doc(s); allowed file set = `parse_plan.py <plan> --files`.

## H2 — Plan gate
Run the review gate on the plan; iterate ≤ `consensus.max_rounds` to no CRITICAL/MAJOR.
**Gate mechanics = `co_agent_config.py review-mode`**: `hybrid` (default) → **parallel
find → chair triage → parallel verify** (`references/hybrid-gate.md`) — the whole panel
reviews at once, the chair keeps only the meaningful findings and sends that curated
digest back to the panel for confirmation; `relay` → the sequential chain
(`references/relay-chain-gate.md`); `parallel` → the one-shot independent fan-out
(`references/consensus-mode.md`). Record `…/plan-gate/result.json` via
`consensus_state.py stage-result`. Unresolved → `set . status needs-human` and stop.

## H3 — Delegated implement (parallel waves) — see `references/delegated-implement.md`
**One implementer, N concurrent task subagents**: group tasks into waves of
pairwise-disjoint file sets (≤ `co_agent_config.py parallel-tasks` per wave; overlapping
tasks fall to the next wave; `parallel_tasks 1` = the sequential loop). Per wave: host
writes **and commits** ALL the wave's failing tests as one red commit → `worktree.py add`
per task → run the implementer **concurrently** in each worktree (`&` + `wait`) → capture
+ scope per task → apply patches serially on main (per-patch gate: that task's tests green,
no previously-green test broken) → full suite green → **one `--amend` fold per wave**.
Task-level abort restores that task's files before the fold and marks it `needs-human`
without sinking the wave.

The exact git mechanics — red-commit message convention + crash recovery, the per-peer-run
`MAIN0` escape bracket (incl. fix-round re-runs), the `--amend -m` fold that rewrites the
transient subject, and the scope-guarded abort/all-abort restore order — are authoritative
in **`references/delegated-implement.md`** (both the sequential per-task loop and the
parallel-wave adaptation). Do not re-derive them here; follow that file. Fallback chain:
counterpart → other peer → host-implement. External AIs never commit; the host is the only
committer.

## H4 — Final gate
`consensus_state.py cumulative-diff . --plan <plan> --base <trunk>` → review gate
(same `review-mode` as H2: hybrid find→triage→verify by default) →
fix ≤ `consensus.max_rounds`, require tests green. Record `…/code-gate/result.json`.

## H5 — Report
`consensus_state.py set . status done` then `report .` (writes
`.claude/co-agent-consensus/report.md`, gitignored) — include the implementer attribution
and per-stage `result.json` / `stage_wall.tsv`. Present to the user. Resumable via
`consensus_state` (`phase`/`task_index`).
