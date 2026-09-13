---
description: Host-designs / panel-reviews orchestrator. The host owns design, tests and commits; an eligible peer implements in isolated worktrees, or the host explicitly handles implementation when no eligible writer is ready. Helper calls retain the setup root. External review remains required. Opt-in, local commits only.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
argument-hint: "<adr|spec|plan|task>  [--implementer <ai>]"
---

# co-agent: harness

Autonomous **design → delegated-implement → review** with cross-provider role separation:
the **host** (Claude in Claude Code, Codex in Codex) designs, writes the failing test, and
is the **only committer**, while a **peer implementer** writes code only inside isolated
git worktrees under a workspace-write sandbox, and a review gate (hybrid by default) judges
the result. The product is a locally committed, gate-approved implementation with clear
attribution of who wrote what. Excellent means the trust boundary never blurs — external
AIs propose patches, the host applies, tests, and commits them.

Implementation stays with **one** implementer AI but fans out as **parallel per-task
subagents** in separate worktrees (`harness.parallel_tasks`, default 3). Gate mode:
`harness.review_mode` — `hybrid` (default: parallel find → chair triage → parallel verify)
| `relay` | `parallel`.

> Trust boundary, per-task loop + parallel waves, fallback chain, output gate:
> **`references/delegated-implement.md`**. Review-gate mechanics: **hybrid**
> `references/hybrid-gate.md` (default) · relay `references/relay-chain-gate.md` ·
> parallel `references/consensus-mode.md`. CLI details: `references/ai-cli-adapters.md`.
> Want the host itself to write the code instead (no peer, no worktree)? Use
> `/co-agent:consensus`. Side-by-side comparison: `SKILL.md` → "Consensus vs harness".

Argument: `$ARGUMENTS`

Capture the absolute orchestration/setup root before creating or entering task worktrees:

```bash
ORCH_ROOT=$(git rev-parse --show-toplevel) || exit 1
SK="${CLAUDE_PLUGIN_ROOT}/skills/co-agent/scripts"
HOST=$(python3 "$SK/co_agent_config.py" host --root "$ORCH_ROOT") || exit 1
```

Retain `ORCH_ROOT` and `HOST` in the task/retry context; never recompute the root from
a task worktree. Its checkout lacks the setup project's ignored readiness and local
overrides. Keep orchestration/state/commit commands in `ORCH_ROOT`; all configuration,
readiness, planning and flag calls use `--root "$ORCH_ROOT" --host "$HOST"`.

## H0 — Detect & consent
1. **Consent + cost**: resolve `MODE=$(python3 "$SK/co_agent_config.py" review-mode --root "$ORCH_ROOT" --host "$HOST")`; the
   `hybrid` default fans out **twice** per round (find + verify), so show
   `python3 "$SK/co_agent_config.py" matrix --root "$ORCH_ROOT" --host "$HOST" $([ "$MODE" = hybrid ] && echo --phases 2)`
   — passing `--phases 2` only for hybrid keeps the displayed max-calls total accurate for
   whichever gate mode is actually configured. Confirm sending context to third-party AIs.
2. Resolve the panel with `co_agent_config.py panel --root "$ORCH_ROOT" --host "$HOST"` and inspect
   `show` with the same root/host for configured providers. `implementer --root "$ORCH_ROOT" --host "$HOST"` reports the
   configured/default writer; it does not establish readiness. Use the JSON planner
   in step 3 to resolve execution mode. Never invoke the current host as its own peer.
   Writer eligibility comes from the helper's sandbox allowlist, not panel membership.
   Antigravity is retired (ADR-022). If `implementer` exits 3 with no stdout, resolve
   the explicit planner mode below; exit 2 requires fixing configuration.
3. **Consult readiness** (`$ORCH_ROOT/.claude/co-agent-panel.local.json`):
   `check_panel.py fresh --root "$ORCH_ROOT" --host "$HOST"`, then
   `check_panel.py gate-eligible <peer> --root "$ORCH_ROOT" --host "$HOST"` —
   keep for the **review panel** only peers returning `true`
   (`status==READY` **and** `raw_cli`), **not** bare `status` (the fan-out calls raw CLIs only,
   so a plugin-only peer yields zero panel output). The **implementer** must be gate-eligible
   **plus** a supported sandbox CLI accepted by `impl-flags`. (A peer with BOTH the plugin and a raw CLI is
   `access: plugin` yet `raw_cli: true` → still eligible; only `raw_cli:false` is out.) No
   implementer-eligible peer → consider explicit host implementation; **no gate-eligible peer** at all → **block** and
   run `/co-agent:setup` for `ORCH_ROOT`. Missing/stale evidence must be refreshed
   there with `check_panel.py report --root "$ORCH_ROOT" --host "$HOST"`.
   Resolve `co_agent_config.py implementation-plan --root "$ORCH_ROOT" --host "$HOST"` after setup.
   It emits JSON with `mode`, `implementer` and the enabled READY `reviewers`.
   Exit 3 requires an explicit host-mode choice: if that implementation is already
   authorized by the requested workflow, rerun with `--allow-host-implementation`.
   Exit 2 requires fixing configuration/readiness. Do not treat it as permission
   to continue. Report the selected mode, reviewers and wave concurrency.
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
**Gate mechanics = `co_agent_config.py review-mode --root "$ORCH_ROOT" --host "$HOST"`**: `hybrid` (default) → parallel find →
chair triage (the chair keeps only meaningful findings) → parallel verify of the curated
digest (`references/hybrid-gate.md`); `relay` → the sequential chain
(`references/relay-chain-gate.md`); `parallel` → the one-shot independent fan-out
(`references/consensus-mode.md`). Record `…/plan-gate/result.json` via
`consensus_state.py stage-result`. Unresolved → `set . status needs-human` and stop.

## H3 — Delegated implement (parallel waves) — see `references/delegated-implement.md`
For `mode: host`, the current host uses its native tools in the task worktrees,
keeping the same scoped capture, tests, checkpoints and host-owned commits. Do not
call `impl-flags` with a null writer or launch the host CLI as its own peer. H2/H4
external review remains required. The peer invocation steps below apply only to
`mode: peer`.

**One implementer, N concurrent task subagents**: group tasks into waves of
pairwise-disjoint file sets (≤ `co_agent_config.py parallel-tasks --root "$ORCH_ROOT" --host "$HOST"` per wave; overlapping
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
parallel-wave adaptation). Do not re-derive them here; follow that file. Re-resolve
`implementation-plan --root "$ORCH_ROOT" --host "$HOST"` after writer failure.
Only the writer launch uses the task worktree as cwd; helper calls retain the setup
root. Native host mode requires the explicit flag and READY external review.
External AIs never commit; the host is the only committer.

## H4 — Final gate
`consensus_state.py cumulative-diff . --plan <plan> --base <trunk>` → review gate
(same `review-mode` as H2: hybrid find→triage→verify by default) →
fix ≤ `consensus.max_rounds`, require tests green. Record `…/code-gate/result.json`.

## H5 — Report
`consensus_state.py set . status done` then `report .` (writes
`.claude/co-agent-consensus/report.md`, gitignored) — include the implementer attribution
and per-stage `result.json` / `stage_wall.tsv`. Present to the user. Resumable via
`consensus_state` (`phase`/`task_index`). Optionally offer the **`harness-analyst`**
subagent (`agents/harness-analyst.md`) to mine the accumulated records for
`/co-agent:configure` proposals — advisory only; below 3 recorded runs it reports
observations without proposals.
