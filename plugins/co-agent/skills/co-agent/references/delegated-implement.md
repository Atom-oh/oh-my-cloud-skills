# Delegated Implement (co-agent:harness)

How the **host designs, a cross-provider peer implements, and the host reviews + commits**.
The peer writes code **only inside an isolated git worktree** under a workspace-write
sandbox; the host owns the failing test, the verification, and every commit.

> Review-gate mechanics: **hybrid** `hybrid-gate.md` (harness default) · relay
> `relay-chain-gate.md` · parallel `consensus-mode.md` (`harness.review_mode`). CLI
> invocation details: `ai-cli-adapters.md`. Implementer selection / write-mode flags:
> `scripts/co_agent_config.py implementer|impl-flags`; wave concurrency:
> `co_agent_config.py parallel-tasks` (see "Parallel waves" below).

## Trust boundary

The **hard guarantee is the host applies only the worktree's captured, scope-guarded
diff** — not the sandbox. A git worktree isolates the *working tree*, not the process, so a
peer could in principle write via `..`/absolute paths; that never reaches the main tree
because the host never copies the peer's filesystem. `worktree.py capture-diff` runs
`git add -A` (respects `.gitignore`) **inside the worktree** then `git diff --cached`, so
**only files changed within the worktree** are captured; out-of-worktree writes are invisible.
Each captured path must pass `scope_guard.py --plan <plan>` (out-of-scope hunks dropped), and
the host applies the result and **runs the tests on the main tree** — never trusting a test
run inside the worktree. Capture-scoped-to-worktree + scope_guard + host-applies-only-that is
the load-bearing guarantee; the sandbox is defense-in-depth.

**Defense-in-depth: a workspace-write sandbox with cwd = the worktree** (`co_agent_config.py
impl-flags <ai> --host <h>`). Only CLIs with a real workspace-write sandbox are eligible:

| Implementer | Write-mode flags |
|-------------|------------------|
| Codex | `-s workspace-write` (+ `-m <model>`, effort) |
| Agy | `--sandbox` (+ `--model`) |

Codex `-s workspace-write` confines writes to the cwd; **agy has a *single* `--sandbox` mode**
(no separate read-only flag like Codex's `-s read-only`) that likewise sandboxes to the launch
cwd — the per-task loop sets cwd = the worktree for both. The advisory path instead runs agy
in **`-p` print mode** (emits text, never acts), so `impl-flags agy` differs from `flags agy`
only by print-vs-agent mode (same `--sandbox`). We do **not** assert agy's `--sandbox`
provably blocks `..`/absolute writes — which is exactly why the capture backstop above, not
the sandbox, is load-bearing (if an audit shows a sandbox doesn't confine to cwd, drop that
implementer from `impl-flags`).

**Not eligible:** `claude --permission-mode acceptEdits` and `kiro-cli --trust-tools`
auto-accept writes but don't sandbox them to a cwd — `implementer`/`impl-flags`
reject them. Default: claude host → `codex`, codex host → `agy`. These write variants exist
**only** here; review/decide/ADR/plan/code-gate paths stay advisory (`flags`, not `impl-flags`).

## Per-task loop

For each plan task (`scope_guard.py` enforces the plan's file set throughout):

1. **Red (host).** Host writes **and commits** the failing test on the working branch
   (host is the only committer, so this is consistent). Committing first is **required**:
   the worktree is created at `HEAD`, so an uncommitted red test would not exist inside it
   and the peer would implement blind. This red-test commit is **transient** — step 7
   squashes it into a single passing commit, and step 8 reverts it on abort, so the branch
   never retains a committed-but-red test. (Skip the whole step if the task declares
   `test_required:false`, e.g. a pure refactor with existing coverage.)
2. **Worktree.** `worktree.py add <wt> --base HEAD` — create the isolated tree at the
   red-test commit, so the peer sees the failing test. Put `<wt>` under a gitignored path
   (e.g. `.claude/co-agent-consensus/worktrees/<task>`).
3. **Implement (peer).** Pick the implementer from peers that are **READY** AND
   **`raw_cli: true`** (a usable raw write CLI) AND a sandbox CLI (codex/agy) — consult
   `.claude/co-agent-panel.local.json` (written by `/co-agent:setup`). Gate on `raw_cli`,
   NOT `access`: a peer with BOTH the official plugin and a raw CLI is `access: plugin` yet
   `raw_cli: true` → still eligible. Only a peer with **no raw CLI** (`raw_cli: false`) can't
   run `impl-flags` and is ineligible. Run the implementer with
   `impl-flags` **inside `<wt>`**, scoped to the task's files. Fallback chain on
   missing/error/not-READY/timeout: configured implementer → next READY peer (keep provider
   separation) → **host-implement**. No-implementer vs no-reviewer differ (matches harness H3):
   **no implementer-eligible peer → host-implement** (don't block — the host can write the
   code); **block** only when **no gate-eligible peer** remains for the review panel, since
   then the multi-model gate can't run — tell the user to run `/co-agent:setup`. Never silently block.
4. **Capture + scope.** `worktree.py capture-diff <wt>` → patch; every path must pass
   `scope_guard.py --plan <plan>`. Out-of-scope hunks are dropped and fed back.
5. **Apply + verify (host).** Snapshot the main tree before the peer runs
   (`MAIN0=$(git -C . status --porcelain)`) and re-check after — **abort if it changed**
   (a peer that escaped its cwd and wrote into the main checkout out-of-band, which the
   captured diff would miss). Backs the trust claim with a check, not just the sandbox. Then
   apply the captured patch to the main branch; run `tests/run-all.sh` (+ project tests) **on
   the main tree**. Red → feed the failure back and loop, bounded by `harness.max_fix_rounds`.
6. **Review gate (optional).** Per-task multi-model review is **off by default** — the H4
   cumulative gate is the review of record. Enable it only when a task warrants it.
7. **Record + commit.** Record the pre-task checkpoint SHA before H3a's red commit
   (`CKPT=$(git rev-parse HEAD)`). `consensus_state.py stage-result write
   …/tasks/<i>/result.json --stage task-<i> --verdict … --green true --in-scope true
   --implementer <ai>`; then the **host is the only committer** — fold the red-test commit
   and the green implementation into **one passing commit**. **Only when step 1 made a
   red-test commit** (not a `test_required:false` task), `git commit --amend` onto it (no
   `reset`/`rebase` — matches the "never reset/rebase autonomously" constraint) so the branch
   never carries a committed-but-red test. For a `test_required:false` task there is **no
   red-test commit**, so make a **fresh `git commit`** — never `--amend` (it would rewrite an
   unrelated prior commit). `worktree.py remove <wt>`.
8. **Escalate / abort** when the fix loop is exhausted: **first discard the applied
   implementation patch** that step 5 put in the working tree, scoped to the task's files —
   `git restore --staged --worktree -- <task files>` (or `git checkout -- <task files>`).
   `restore` only reverts `HEAD`-tracked files; a patch that **added new files** leaves them
   untracked, so also `git clean -fd -- <task files>` (scoped — **never a bare `git clean`**).
   ⚠️ **Guard the pathspec first**: if `<task files>` is empty, `git clean -fd --` deletes
   **every** untracked file in the tree. Use a bash **array** (not a string) and a count guard,
   so a whitespace-only value can't pass and filenames with spaces don't word-split:
   `[ ${#FILES[@]} -gt 0 ] && git clean -fd -- "${FILES[@]}"` — build `FILES=(...)` from the
   plan's task set, never an unquoted glob that can expand to nothing. The tree is then clean. **Then** undo the red-test commit with `git revert --no-edit
   <red-test-sha>` (a non-destructive inverse commit; revert refuses on a dirty tree, which is
   why the restore comes first). Do **not** use `git reset --soft` (keeps the red test staged)
   nor a bare `git reset --hard` (could discard unrelated work). Then `consensus_state.py set .
   status needs-human` and stop the task. Never leave a red commit or applied-but-failing
   changes on the working branch.

## Parallel waves — one implementer, N concurrent task subagents

The panel deliberates in numbers, but **implementation stays with ONE implementer AI**
(`co_agent_config.py implementer`, user-selectable via `set harness implementer codex|agy`)
— cross-AI implementation diversity belongs in the review gate, not in the diff. Throughput
comes from running **that one implementer as parallel subagent instances**, one per task,
each in its own worktree. `harness.parallel_tasks` (default 3; `1` = the sequential
per-task loop above) caps how many run at once.

**Wave planning.** Take the plan's task list (`parse_plan.py`) with each task's file set
(`parse_plan.py --files` scope). Greedily group tasks into **waves** of pairwise-**disjoint**
file sets, at most `parallel_tasks` per wave; a task whose files overlap an earlier task in
the wave falls to the next wave. Tasks in a wave run concurrently; waves run sequentially.
(Overlap check is on the plan's declared file scopes — the same sets `scope_guard.py`
enforces — so two tasks that could write the same file never run in the same wave.)

**Per wave** (adapts steps 1–8 of the sequential loop):

1. **Red (host).** Write the failing tests for every task in the wave that does NOT
   declare `test_required:false`, and commit them as **one** red-test commit
   (`RED_MADE=true` if this commit was made; `RED_MADE=false` if every task in the wave is
   `test_required:false`, so there is nothing to commit here — same condition the
   sequential loop's step 1 already checks per task, just OR'd across the wave). One
   commit, not N: the wave is folded into passing commits by amending, and only a single
   transient red commit can be cleanly amended/reverted without rebase.
2. **Worktrees.** `worktree.py add <wt_i> --base HEAD` per task — every worktree sees the
   whole wave's red tests.
3. **Implement (parallel).** Snapshot main before starting (`MAIN0=$(git -C . status
   --porcelain)`) — the host makes no changes to main while implementers run, so this is
   the one point where an out-of-band write is unexpected. Run the implementer with
   `impl-flags` in **each** worktree concurrently (`&` + `wait`, one background job per
   task, capped by `parallel_tasks`). Each prompt is scoped to ITS task + files and must
   say: *"other failing tests in this tree belong to parallel tasks — do not touch them or
   their files."* `scope_guard.py` drops any out-of-scope hunk regardless. After `wait`,
   re-check main against `MAIN0` **once** — abort the whole wave if it changed (a peer
   escaped its worktree and wrote into the main checkout out-of-band). From this point on,
   main changes on every apply below **by design** — do not re-run this check mid-apply.
4. **Capture + scope** per task, as in step 4 of the sequential loop.
5. **Apply + verify (host, serial).** Apply the captured patches **one at a time** — each
   apply is an intentional, host-driven change to main, not an anomaly to detect. After
   each apply, the gate is: **that task's tests pass and no previously-green test breaks**
   — full-suite green is NOT expected mid-wave (sibling tasks' red tests are still
   unimplemented). A failing task gets the bounded fix loop (`harness.max_fix_rounds`) in
   its own worktree without blocking siblings already applied.
6. **Fold (host).** When every surviving task in the wave is applied, require the **full
   suite green on main**. **Only if `RED_MADE=true`** (step 1 made a red-test commit this
   wave), `git commit --amend` onto it — one passing commit per wave (same
   no-reset/no-rebase constraint, and the same guard the sequential loop's step 7 applies
   per task: never amend when there is no red commit to amend onto, or the amend silently
   rewrites an unrelated prior commit instead). **If `RED_MADE=false`** (every task in the
   wave was `test_required:false`), make a **fresh `git commit`** instead. `worktree.py
   remove` all.
7. **Abort a task, keep the wave.** If one task exhausts its fix loop: restore **that
   task's files** (implementation patch AND its red tests, if any) to their pre-wave state
   — scoped `git restore`/`git checkout` + guarded `git clean -fd -- "${FILES[@]}"` exactly
   as in step 8 of the sequential loop — then proceed to the fold; when `RED_MADE=true` the
   amend rewrites the red commit to the current tree, so the aborted task's tests drop out
   of the folded commit cleanly. Mark the task `needs-human` in state. If **every** task in
   the wave aborts: `git revert --no-edit` the red-test commit if `RED_MADE=true`; if
   `RED_MADE=false` there is no commit to revert — just discard the tree changes above and
   skip the fold entirely (no commit for this wave).

Waves inherit everything else unchanged: host is the only committer, external AIs never
commit, `stage-result` per task, resume via `consensus_state` (`task_index` advances by
completed task, so a resumed run re-plans waves from the remaining tasks).

**When NOT to parallelize.** Plans whose tasks are deliberately sequential (each builds on
the last's code) declare overlapping file sets and will naturally serialize into 1-task
waves — do not force-split them. If in doubt, `set harness parallel_tasks 1`.

## Host-only-commit (non-negotiable)

External AIs never run `git commit`/`push`/`reset`. They only ever execute inside a
worktree under a write sandbox. The host applies the validated patch and performs every
commit on the working branch. Local commits only.

## Output gate

A stage advances only when its `result.json` checks out
(`consensus_state.py stage-result check <path>`): no `plan.md` → no plan gate; a task
`result.json` with `green=false` → no commit; a gate verdict of FAIL or unresolved
CRITICAL/MAJOR → `needs-human`. Timings accumulate in `stage_wall.tsv`.
