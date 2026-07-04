---
description: Host-designs / peer-implements / panel-reviews orchestrator. The host owns the design, the failing test, and every commit; a cross-provider peer writes code only inside an isolated git worktree under a workspace-write sandbox; a sequential relay-chain gate reviews (parallel fan-out optional). Opt-in, local commits only.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
argument-hint: "<adr|spec|plan|task>  [--implementer codex|agy]"
---

# co-agent: harness

Autonomous **design → delegated-implement → review** with cross-provider role separation.
The **host** (Claude in Claude Code, Codex in Codex) designs, writes the failing test, and
is the **only committer**. A **peer implementer** writes code **only inside an isolated git
worktree** under a workspace-write sandbox. Review runs a **sequential relay-chain gate**
by default (peers build on each other's findings for one vetted result), or the parallel
fan-out when `harness.review_mode == "parallel"`.

> Trust boundary, per-task loop, fallback chain, output gate: **`references/delegated-implement.md`**.
> Review-gate mechanics: **relay chain** `references/relay-chain-gate.md` (default) ·
> parallel `references/consensus-mode.md`. CLI details: `references/ai-cli-adapters.md`.
> Want the host itself to write the code instead (no peer, no worktree)? Use
> `/co-agent:consensus`. Side-by-side comparison: `SKILL.md` → "Consensus vs harness".

Argument: `$ARGUMENTS`

Let `SK="${CLAUDE_PLUGIN_ROOT}/skills/co-agent/scripts"` and
`HOST="${CO_AGENT_HOST:-claude}"`.

## H0 — Detect & consent
1. **Consent + cost**: confirm sending context to third-party AIs; show
   `python3 "$SK/co_agent_config.py" matrix --host "$HOST"`.
2. Resolve roles: panel = `co_agent_config.py panel --host "$HOST"`; implementer =
   `co_agent_config.py implementer --host "$HOST"`. Only **sandbox CLIs** (codex, agy) are
   valid implementers (claude/kiro-cli have no worktree-scoped write sandbox); default is
   claude host → codex, codex host → agy. Never equals the host. Tell the user panel + implementer.
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
**Gate mechanics = `co_agent_config.py review-mode`**: `relay` (default) → the sequential
**relay chain** (`references/relay-chain-gate.md`) — peers review one at a time, each
building on the prior findings, so the panel converges on one vetted result in a single
pass; `parallel` → the independent fan-out (`references/consensus-mode.md`). Record
`…/plan-gate/result.json` via `consensus_state.py stage-result`. Unresolved → `set . status
needs-human` and stop.

## H3 — Delegated implement (per task) — see `references/delegated-implement.md`
Per task: host writes **and commits** the failing test (so the `--base HEAD` worktree
contains it) → `worktree.py add` (under a gitignored path) → run the
implementer with `co_agent_config.py impl-flags <ai> --host "$HOST"` **inside the worktree**
→ `worktree.py capture-diff` → `scope_guard.py` (drop out-of-scope) → apply patch to main +
`tests/run-all.sh` **on main** → bounded fix loop (`harness.max_fix_rounds`) → `stage-result`
→ **host commits once**: before H3a, record the pre-task checkpoint SHA
(`CKPT=$(git rev-parse HEAD)`); on green, fold the red-test commit and the implementation
into **one passing commit**. **Only when H3a actually made a red-test commit** (i.e. not a
`test_required:false` task, §11/§12), `git commit --amend` onto that red-test commit (no
`reset`/`rebase` — consistent with the "never reset/rebase autonomously" constraint) so the
branch never carries a committed-but-red test. For a `test_required:false` task there is **no
red-test commit**, so make a **fresh `git commit`** — never `--amend` (it would rewrite an
unrelated prior commit). Then `worktree.py remove`. Fallback chain: counterpart → other peer → host-implement.
**On exhausted fix loop / abort**: **first discard the applied implementation patch**
(scoped to the task files: `git restore --staged --worktree -- <task files>`, then
`git clean -fd -- <task files>` to remove any **new files** the patch added — scoped, never
bare. Use a bash **array** + count guard so a whitespace-only value can't pass and spaced
filenames don't word-split: `[ ${#FILES[@]} -gt 0 ] && git clean -fd -- "${FILES[@]}"`
(an empty pathspec makes `git clean -fd --` wipe *all* untracked files). So the tree is clean,
**then** undo the red-test commit with `git revert --no-edit <red-test-sha>` — a
non-destructive inverse commit (revert refuses on a dirty tree, so restore first; do **not**
use `git reset --soft`, which keeps the red test staged, nor a bare `git reset --hard`, which
could discard unrelated work) — then
`set . status needs-human`. External AIs never commit.

## H4 — Final gate
`consensus_state.py cumulative-diff . --plan <plan> --base <trunk>` → review gate
(same `review-mode` as H2: relay chain by default, else parallel fan-out) →
fix ≤ `consensus.max_rounds`, require tests green. Record `…/code-gate/result.json`.

## H5 — Report
`consensus_state.py set . status done` then `report .` (writes
`.claude/co-agent-consensus/report.md`, gitignored) — include the implementer attribution
and per-stage `result.json` / `stage_wall.tsv`. Present to the user. Resumable via
`consensus_state` (`phase`/`task_index`).
