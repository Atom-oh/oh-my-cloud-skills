# Delegated Implement (co-agent:harness)

How the **host designs, a cross-provider peer implements, and the host reviews + commits**.
The peer writes code **only inside an isolated git worktree** under a workspace-write
sandbox; the host owns the failing test, the verification, and every commit.

> Review-gate mechanics: `consensus-mode.md`. CLI invocation details: `ai-cli-adapters.md`.
> Implementer selection / write-mode flags: `scripts/co_agent_config.py implementer|impl-flags`.

## Trust boundary

A git worktree isolates the *working tree*, **not** the process — a peer can still write
via `..`/absolute paths. So writes are confined by a **workspace-write sandbox scoped to
the worktree**, emitted by `co_agent_config.py impl-flags <ai> --host <h>`. Only CLIs with
a real workspace-write sandbox are valid implementers:

| Implementer | Write-mode flags |
|-------------|------------------|
| Codex | `-s workspace-write` (+ `-m <model>`, effort) |
| Agy | `--sandbox` (+ `--model`) |

**Not valid implementers:** `claude --permission-mode acceptEdits`, `kiro --trust-tools`,
and `gemini --yolo` auto-accept writes but do **not** confine them to the worktree, so the
trust boundary would not hold — `implementer`/`impl-flags` reject them. Default implementer:
claude host → `codex`, codex host → `agy`. These write variants exist **only** here; review /
decide / ADR / plan / code-gate paths stay read-only/advisory (`flags`, not `impl-flags`).

**Trust only the tracked diff.** `worktree.py capture-diff` runs `git add -A` (which
respects `.gitignore`) then `git diff --cached`, so new source files are captured and
`.gitignore`'d files are excluded *by construction* — a hidden ignored file can never reach
the main tree. The host applies that patch to the main branch and **runs the tests there**,
never trusting a test run performed inside the peer's worktree.

## Per-task loop

For each plan task (`scope_guard.py` enforces the plan's file set throughout):

1. **Red (host).** Host writes **and commits** the failing test on the working branch
   (host is the only committer, so this is consistent). Committing first is **required**:
   the worktree is created at `HEAD`, so an uncommitted red test would not exist inside it
   and the peer would implement blind. (Skip the whole step if the task declares
   `test_required:false`, e.g. a pure refactor with existing coverage.)
2. **Worktree.** `worktree.py add <wt> --base HEAD` — create the isolated tree at the
   red-test commit, so the peer sees the failing test. Put `<wt>` under a gitignored path
   (e.g. `.claude/co-agent-consensus/worktrees/<task>`).
3. **Implement (peer).** Run the implementer with `impl-flags` **inside `<wt>`**, scoped to
   the task's files. Fallback chain on missing/error/timeout: configured implementer →
   next installed peer (keep provider separation) → host-implement. Never block.
4. **Capture + scope.** `worktree.py capture-diff <wt>` → patch; every path must pass
   `scope_guard.py --plan <plan>`. Out-of-scope hunks are dropped and fed back.
5. **Apply + verify (host).** Apply the patch to the main branch; run `tests/run-all.sh`
   (+ project tests) **on the main tree**. Red → feed the failure back to the peer and
   loop, bounded by `harness.max_fix_rounds` (inherits `consensus.max_rounds`).
6. **Review gate (optional).** Per-task multi-model review is **off by default** — the H4
   cumulative gate is the review of record. Enable it only when a task warrants it.
7. **Record + commit.** `consensus_state.py stage-result write …/tasks/<i>/result.json
   --stage task-<i> --verdict … --green true --in-scope true --implementer <ai>`; then the
   **host is the only committer** — one commit for the task. `worktree.py remove <wt>`.
8. **Escalate** when the fix loop is exhausted: `consensus_state.py set . status needs-human`
   and stop the task (do not commit a red task).

## Host-only-commit (non-negotiable)

External AIs never run `git commit`/`push`/`reset`. They only ever execute inside a
worktree under a write sandbox. The host applies the validated patch and performs every
commit on the working branch. Local commits only.

## Output gate

A stage advances only when its `result.json` checks out
(`consensus_state.py stage-result check <path>`): no `plan.md` → no plan gate; a task
`result.json` with `green=false` → no commit; a gate verdict of FAIL or unresolved
CRITICAL/MAJOR → `needs-human`. Timings accumulate in `stage_wall.tsv`.
