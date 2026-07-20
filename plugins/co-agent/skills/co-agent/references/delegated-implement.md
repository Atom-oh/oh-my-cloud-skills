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

**Role tiering:** `impl-flags` resolves its model/effort from
`harness.implementer_models.<ai>`/`implementer_efforts.<ai>` first, falling back to the
panel's `model`/`effort` (`/co-agent:configure` → "모델 티어링"). The overrides are
**stored per implementer, keyed by the explicit `harness.implementer` at set time**
(setting them with no implementer configured is refused) — model names don't encode a
provider, so only per-AI keying survives both the host-dependent default fallback
(claude-host→codex, codex-host→agy) AND an explicit `set harness implementer` switch
without handing, e.g., a codex model to `agy --model`; a non-current implementer's
entry stays dormant (and is reused on switch-back). `impl-flags` also re-validates the
merged model/effort at emit time (fail-closed, exit 2) since its argv feeds a
write-enabled sandbox and the local/user JSON can be hand-edited. This splits the
WRITE path from the review path: the same CLI can implement on a different
generation model than its review/gate calls (`flags`) use. Which direction to
split depends on the cost model (configure.md "모델 티어링" → 비용 모델 전제):
on a flat-rate subscription CLI (the default assumption) point `implementer_model`
at that CLI's **strongest** generation model — fewer fix rounds is pure wall-clock
savings; only on metered API keys drop to a cost-efficient model and let the
hybrid gate behind it catch the generation mistakes.
`implementer_effort` is codex-only (storing it while the implementer is agy is
refused — agy's headless CLI has no effort flag).

**Not eligible:** `claude --permission-mode acceptEdits` and `kiro-cli --trust-tools`
auto-accept writes but don't sandbox them to a cwd — `implementer`/`impl-flags`
reject them. Default: claude host → `codex`, codex host → `agy`. These write variants exist
**only** here; review/decide/ADR/plan/code-gate paths stay advisory (`flags`, not `impl-flags`).

## Per-task loop

For each plan task (`scope_guard.py` enforces the plan's file set throughout):

1. **Red (host).** First record `CKPT=$(git rev-parse HEAD)` (step 8's abort restores from
   it). Host then writes **and commits** the failing test on the working branch (host is the
   only committer, so this is consistent). Committing first is **required**: the worktree is
   created at `HEAD`, so an uncommitted red test would not exist inside it and the peer would
   implement blind. This red-test commit is **transient** — step 7 squashes it into a single
   passing commit, and step 8 reverts it on abort, so the branch never retains a
   committed-but-red test. (Skip the whole step if the task declares `test_required:false`,
   e.g. a pure refactor with existing coverage.)
   **Red-commit message convention (crash recovery)** — same rule as the wave loop, keyed
   per task: the subject MUST start with `harness: task <i> red test (transient)`, and
   step 7's fold **rewrites** it to a green subject. `CKPT` is shell-only, so this marker is
   the durable record that HEAD is an unfolded red commit. On resume, if
   `git log -1 --format=%s` matches the marker **and** HEAD is genuinely red (`git show
   --stat HEAD` touches only test files, or the suite still fails), `git revert --no-edit
   HEAD` on a clean tree and redo the task; never stack a new red commit on the orphan.
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
   the main tree**. Red → feed the failure back and loop, bounded by `harness.max_fix_rounds`
   — **each fix-round peer re-run gets its own snapshot/re-check bracket** (re-snapshot just
   before that run so the host's already-applied patch doesn't false-trip it); a single
   pre-first-run snapshot would leave every fix-round re-run as an undetected escape window.
6. **Review gate (optional).** Per-task multi-model review is **off by default** — the H4
   cumulative gate is the review of record. Enable it only when a task warrants it.
7. **Record + commit.** (`$CKPT` was already recorded in step 1, BEFORE the red commit —
   do NOT re-run `git rev-parse HEAD` here: HEAD is now the transient red commit, and
   clobbering `$CKPT` with the red SHA would make any later CKPT-based restore re-instate
   the failing tests.) `consensus_state.py stage-result write
   …/tasks/<i>/result.json --stage task-<i> --verdict … --green true --in-scope true
   --implementer <ai>`; then the **host is the only committer** — fold the red-test commit
   and the green implementation into **one passing commit**. **First STAGE the applied
   work** — step 5's `git apply` left it unstaged/untracked and commit reads only the index,
   so without staging the fold commits the red tree and drops the implementation (amend →
   "green"-labelled but red; fresh commit → "nothing to commit"). Stage scoped with the
   guarded array: `[ ${#FILES[@]} -gt 0 ] && git add -- "${FILES[@]}"` (the task's file set,
   incl. its red test; never bare `git add -A`). Then, **only when step 1 made a
   red-test commit** (not a `test_required:false` task), `git commit --amend -m "harness:
   task <i> green"` onto it — **always an explicit `-m` that REPLACES the transient red
   subject** (never `--amend --no-edit`, which would leave the `… red test (transient)`
   marker on the green commit and trip step 1's recovery into reverting completed work); no
   `reset`/`rebase` (matches the "never reset/rebase autonomously" constraint) so the branch
   never carries a committed-but-red test. For a `test_required:false` task there is **no
   red-test commit**, so make a **fresh `git commit`** — never `--amend` (it would rewrite an
   unrelated prior commit). `worktree.py remove <wt>`.
8. **Escalate / abort** when the fix loop is exhausted: **first discard the applied
   implementation patch** that step 5 put in the working tree, scoped to the task's files.
   ⚠️ **Partition the pathspec by tracked-now FIRST** (`git ls-files --error-unmatch <f>`):
   `git restore` fatals ATOMICALLY (`pathspec did not match`, restoring **nothing**) if even
   one untracked path is in its argument list — so run
   `git --literal-pathspecs restore --staged --worktree -- "${TRACKED[@]}"` on tracked
   files only, and remove the patch-added **untracked** files with
   `git --literal-pathspecs clean -fd -- "${UNTRACKED[@]}"` (scoped — **never a bare
   `git clean`**). Passing the full unpartitioned task file set would leave the tree
   dirty and make the revert below refuse. **`--literal-pathspecs` on every restore/clean
   call in this section, not just this one**: plan file entries are ordinary strings a
   plain `--` only ends OPTION parsing with, not git's own pathspec MAGIC syntax
   (`:(glob)`, `:(top)`, …) — an entry containing that syntax could widen a
   restore/clean's scope past the intended file set and destroy unrelated work; the flag
   forces every pathspec argument to be treated as a literal path, magic syntax and all.
   ⚠️ **Guard the pathspec first**: if `<task files>` is empty, `git clean -fd --` deletes
   **every** untracked file in the tree. Use a bash **array** (not a string) and a count guard,
   so a whitespace-only value can't pass and filenames with spaces don't word-split:
   `[ ${#FILES[@]} -gt 0 ] && git --literal-pathspecs clean -fd -- "${FILES[@]}"` — build
   `FILES=(...)` from the plan's task set, never an unquoted glob that can expand to
   nothing. The tree is then clean. **Then** undo the red-test commit with `git revert --no-edit
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

1. **Red (host).** First record the pre-wave checkpoint: `CKPT=$(git rev-parse HEAD)`
   — step 7's abort path restores from it, so it must be taken BEFORE the red commit.
   Then write the failing tests for every task in the wave that does NOT declare
   `test_required:false`, and commit them as **one** red-test commit
   (`RED_MADE=true` if this commit was made; `RED_MADE=false` if every task in the wave is
   `test_required:false`, so there is nothing to commit here — same condition the
   sequential loop's step 1 already checks per task, just OR'd across the wave). One
   commit, not N: the wave is folded into passing commits by amending, and only a single
   transient red commit can be cleanly amended/reverted without rebase.
   **Red-commit message convention (crash recovery):** the commit subject MUST start with
   `harness: wave red tests (transient)`. `RED_MADE`/`CKPT` live only in the session's
   shell, so this marker is the ONLY durable record that HEAD is a transient red commit.
   **Step 6's fold rewrites this subject** to a green subject, so a surviving marker
   reliably means the commit was never folded (without the rewrite, a headless
   `--amend --no-edit` would leave the transient marker on the *green* folded commit and
   this recovery would revert completed work). **On resume** (`consensus_state.py`
   `phase`/`task_index` point mid-implement), check `git log -1 --format=%s`: if it matches
   the marker **and** HEAD is genuinely red (belt-and-braces: `git show --stat HEAD` touches
   only test files, or re-running the suite fails), then with a clean tree
   `git revert --no-edit HEAD` it and re-plan the wave from the remaining tasks (never stack
   a new red commit on top of an orphaned one); a dirty tree on top of it is the
   interrupted-wave state → `set . status needs-human`.
2. **Worktrees.** `worktree.py add <wt_i> --base HEAD` per task — every worktree sees the
   whole wave's red tests.
3. **Implement (parallel).** The escape check brackets **every peer execution**, not the
   wave: snapshot main immediately before running any implementer
   (`MAIN0=$(git -C . status --porcelain)`), and re-check right after it finishes —
   the host makes no changes to main **while a peer is running**, so any diff across that
   bracket is an out-of-band write (a peer escaped its worktree via `..`/absolute path —
   the one threat capture-diff cannot see). For the initial batch: snapshot once, run the
   implementers concurrently in their worktrees (`&` + `wait`, one background job per
   task, capped by `parallel_tasks`), re-check after `wait` — abort the whole wave on a
   mismatch. The same bracket applies to **every fix-round re-run in step 5**: snapshot
   just before that peer run (the snapshot then already includes the host's own applied
   patches, so they don't false-trip it), re-check when it finishes, abort the task on a
   mismatch. The host's own applies between peer runs are intentional changes, never
   compared against a stale snapshot. Each prompt is scoped to ITS task + files and must
   say: *"other failing tests in this tree belong to parallel tasks — do not touch them or
   their files."* `scope_guard.py` drops any out-of-scope hunk regardless.
4. **Capture + scope** per task, as in step 4 of the sequential loop.
5. **Apply + verify (host, serial).** Apply the captured patches **one at a time**. After
   each apply, the gate is: **that task's tests pass and no previously-green test breaks**
   — full-suite green is NOT expected mid-wave (sibling tasks' red tests are still
   unimplemented). A failing task gets the bounded fix loop (`harness.max_fix_rounds`) in
   its own worktree without blocking siblings already applied — **each fix-round peer run
   gets its own step-3 snapshot/re-check bracket** (fix rounds are peer executions too;
   without the bracket they would be the one window where a worktree escape lands
   undetected). **Run fix-round peer executions one at a time** — never two concurrently,
   and never apply a sibling patch while any peer run is in flight — so each bracket's diff
   attributes to exactly one peer (overlapping runs would make an escape ambiguous, and a
   sibling apply mid-run would false-trip the bracket).
6. **Fold (host).** When every surviving task in the wave is applied, require the **full
   suite green on main**. **First STAGE the applied work** — step 5 applied each captured
   patch to the *worktree* (plain `git apply`, so the changes are unstaged/untracked), and
   `git commit --amend`/`git commit` commit **only the index**, so without staging the fold
   would commit the red tree and silently drop every implementation (an `--amend` produces a
   "green"-labelled commit that is actually red; a fresh commit fatals "nothing to commit").
   Stage the surviving wave's files **scoped** with the guarded-array discipline —
   `[ ${#WAVE_FILES[@]} -gt 0 ] && git add -- "${WAVE_FILES[@]}"` (the plan's file set for the
   **applied-and-surviving (non-aborted)** tasks, incl. their red-test files so they fold in;
   never a bare `git add -A`). An aborted task's files must be EXCLUDED even though its patch
   was applied in step 5: step 7's restore already removed them from index and worktree, and
   `git add` on a now-nonexistent path fatals ATOMICALLY (`pathspec did not match`), staging
   nothing — which would fold a commit without the survivors' implementations. Then:
   **Only if `RED_MADE=true`** (step 1 made a red-test commit this wave), fold with
   `git commit --amend -m "harness: wave <n> green (<task ids>)"` onto it — **always an
   explicit `-m` that REPLACES the transient red subject** (never `--amend --no-edit`: that
   keeps `harness: wave red tests (transient)` on the now-green commit, and step 1's recovery
   would then revert this completed wave on the next resume). One passing commit per wave
   (same no-reset/no-rebase constraint, and the same guard the sequential loop's step 7
   applies per task: never amend when there is no red commit to amend onto, or the amend
   silently rewrites an unrelated prior commit instead). **If `RED_MADE=false`** (every task
   in the wave was `test_required:false`), make a **fresh `git commit -m "harness: wave <n>
   green (<task ids>)"`** instead. `worktree.py remove` all.
7. **Abort a task, keep the wave.** If one task exhausts its fix loop, restore **that
   task's files** to their pre-wave state **from `$CKPT`, never from HEAD** — HEAD is the
   wave's red-test commit and still CONTAINS the task's red tests, so a HEAD-relative
   `git restore`/`git checkout` would restore the failing tests instead of removing them,
   deadlocking step 6's full-suite-green precondition. Partition the task's files by whether
   git tracks them **now** (both the red-test files, tracked in the red commit, and any
   pre-existing project files the patch modified are tracked; only patch-**added** source
   files are untracked, since the host applied that patch to the worktree without
   committing):
   - **tracked** (`git ls-files --error-unmatch <f>` succeeds):
     `git --literal-pathspecs restore --source="$CKPT" --staged --worktree -- "${TRACKED[@]}"`.
     This already stages a **deletion** for any path that did not exist at `$CKPT` (e.g.
     the new red-test files) — no separate `git rm` is needed, and mixing an untracked
     path into `git rm` would make it fail atomically and remove nothing.
   - **untracked** (patch-added new files): the sequential loop's step-8 guarded array —
     `[ ${#UNTRACKED[@]} -gt 0 ] && git --literal-pathspecs clean -fd -- "${UNTRACKED[@]}"`
     (never a bare `git clean`). `--literal-pathspecs` here too, same reason as step 8:
     a plan-declared path containing git pathspec magic syntax must not widen this
     destructive call's scope.

   Then proceed to the fold; when `RED_MADE=true` the amend rewrites the red commit to the
   current tree, so the aborted task's tests genuinely drop out of the folded commit. Mark
   the task `needs-human` in state. If **every** task in the wave aborts, do NOT restore
   from `$CKPT` first — `git revert` refuses on a dirty tree, so mirror the sequential
   loop's step 8 order: **discard the applied patches back to HEAD**, partitioned by
   tracked-now exactly as in step 8
   (`git --literal-pathspecs restore --staged --worktree -- "${TRACKED[@]}"` from HEAD
   for tracked files + the guarded
   `git --literal-pathspecs clean -fd -- "${UNTRACKED[@]}"` for untracked patch-added
   files — an unpartitioned pathspec makes `git restore` fatal
   atomically and restore nothing) so the tree is clean at the red HEAD, **then** `git revert --no-edit`
   the red-test commit if `RED_MADE=true` — the revert itself removes the red tests. If
   `RED_MADE=false` there is no commit to revert — just discard the tree changes and skip
   the fold entirely (no commit for this wave).

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
