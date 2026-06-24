# Delegated Implement (co-agent:harness)

How the **host designs, a cross-provider peer implements, and the host reviews + commits**.
The peer writes code **only inside an isolated git worktree** under a workspace-write
sandbox; the host owns the failing test, the verification, and every commit.

> Review-gate mechanics: `consensus-mode.md`. CLI invocation details: `ai-cli-adapters.md`.
> Implementer selection / write-mode flags: `scripts/co_agent_config.py implementer|impl-flags`.

## Trust boundary

The **hard guarantee is not the sandbox — it is that the host only ever applies the
worktree's captured, scope-guarded diff.** A git worktree isolates the *working tree*, not
the process, so a peer could in principle write via `..`/absolute paths. That cannot reach
the main tree, because the host never copies the peer's filesystem: `worktree.py
capture-diff` runs `git add -A` (which respects `.gitignore`) **inside the worktree** then
`git diff --cached`, so **only files the peer changed within the worktree** are captured;
anything written outside it is invisible to the patch. Every captured path must then pass
`scope_guard.py --plan <plan>` (out-of-scope hunks dropped), and the host applies the result
to the main branch and **runs the tests there** — never trusting a test run inside the peer's
worktree. So even a peer that escaped its cwd cannot land an out-of-worktree or out-of-scope
write. This — capture-scoped-to-worktree + scope_guard + host-applies-only-that — is what
holds the boundary; the sandbox below is defense-in-depth, not the sole guard.

**Defense-in-depth: a workspace-write sandbox with cwd = the worktree**, emitted by
`co_agent_config.py impl-flags <ai> --host <h>`. Only CLIs with a real workspace-write
sandbox are eligible implementers:

| Implementer | Write-mode flags |
|-------------|------------------|
| Codex | `-s workspace-write` (+ `-m <model>`, effort) |
| Agy | `--sandbox` (+ `--model`) |

Codex `-s workspace-write` confines writes to the working directory; **agy has a *single*
`--sandbox` mode** (no separate read-only flag like Codex's `-s read-only`), which likewise
sandboxes to the launch cwd. For **both**, the per-task loop sets **cwd = the worktree**, so
the sandbox confines writes there. The advisory (review) path instead runs agy in **`-p`
print mode** (emits text, never acts), which is why `impl-flags agy` emits the same
`--sandbox` the advisory `flags agy` would, plus `--model` — the difference is print-vs-agent
mode and the cwd. **Whether agy's `--sandbox` fully blocks `..`/absolute writes is not
something we assert as proven** — that is exactly why the capture-scoped-to-worktree backstop
above, not the sandbox, is the load-bearing guarantee. (To raise the floor, the host may run
the implementer with `worktree.py` from inside `<wt>`; if a future audit shows a sandbox does
not confine to cwd, drop that implementer from `impl-flags`.)

**Not eligible implementers:** `claude --permission-mode acceptEdits`, `kiro-cli
--trust-tools`, and `gemini --yolo` auto-accept writes but do **not** sandbox them to a cwd,
so they lack even the defense-in-depth layer — `implementer`/`impl-flags` reject them.
Default implementer: claude host → `codex`, codex host → `agy`. These write variants exist
**only** here; review / decide / ADR / plan / code-gate paths stay read-only/advisory
(`flags`, not `impl-flags`).

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
   separation) → host-implement. If **no** sandbox peer is READY, the multi-model gate
   cannot run — **block** and tell the user to run `/co-agent:setup`. Never silently block.
4. **Capture + scope.** `worktree.py capture-diff <wt>` → patch; every path must pass
   `scope_guard.py --plan <plan>`. Out-of-scope hunks are dropped and fed back.
5. **Apply + verify (host).** Apply the patch to the main branch; run `tests/run-all.sh`
   (+ project tests) **on the main tree**. Red → feed the failure back to the peer and
   loop, bounded by `harness.max_fix_rounds` (inherits `consensus.max_rounds`).
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
   `restore` only reverts files that exist in `HEAD`; a patch that **added new files** leaves
   them as untracked, so also `git clean -fd -- <task files>` (scoped to the task's file set,
   **never a bare `git clean`** — that would wipe unrelated untracked work) to remove them.
   The tree is then clean. **Then** undo the red-test commit with `git revert --no-edit
   <red-test-sha>` (a non-destructive inverse commit; revert refuses on a dirty tree, which is
   why the restore comes first). Do **not** use `git reset --soft` (keeps the red test staged)
   nor a bare `git reset --hard` (could discard unrelated work). Then `consensus_state.py set .
   status needs-human` and stop the task. Never leave a red commit or applied-but-failing
   changes on the working branch.

## Host-only-commit (non-negotiable)

External AIs never run `git commit`/`push`/`reset`. They only ever execute inside a
worktree under a write sandbox. The host applies the validated patch and performs every
commit on the working branch. Local commits only.

## Output gate

A stage advances only when its `result.json` checks out
(`consensus_state.py stage-result check <path>`): no `plan.md` → no plan gate; a task
`result.json` with `green=false` → no commit; a gate verdict of FAIL or unresolved
CRITICAL/MAJOR → `needs-human`. Timings accumulate in `stage_wall.tsv`.
