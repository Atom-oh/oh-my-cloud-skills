# ADR-015: PR Review Memory Loop — One Committed File, Written Only by the Local Host

## Status

Accepted (2026-07-31)

## Context

15 review-lineage agents declare `memory: project|user`, but there is not a single `MEMORY.md`
anywhere in the repo, and the CI PR review (`.github/workflows/pr-review.yml`) neither **reads
nor writes** accumulated knowledge. The result: the same real problem gets rediscovered from
scratch every time, the same false positive gets flagged again on every PR, and even when a
given cell's judgment quality is poor, no evidence accumulates anywhere — the evidence used in
ADR-012 to drop `kimi-k2.5` (e.g. "7 dismissed findings vs. 0") existed only in chat history.

**Reusing the same agent across CI runs is not possible.** The chair runs as `claude -p …
--disallowedTools "… Task"`, so it cannot spawn subagents; the panel cells are Codex/Kiro CLIs,
not Claude agents; and `agent-memory` lives in the workspace, which disappears on every
`pull_request_target` + `clean: true` checkout. So **what gets shared must be a single committed
file, not an agent**.

The actual loop in practice is **CI review FAIL → local `/co-agent:pr-autofix`**. So the memory
must be something pr-autofix can reference, and the next CI run must see the same thing.

## Options Considered

1. **Have CI auto-commit the memory file** — rejected. This is self-modification that bypasses
   review, and it opens an injection path where PR body/diff text goes straight into commit
   content.
2. **Accumulate in a runner-local TSV** — rejected. `actions/checkout`'s `clean: true` wipes the
   workspace on every run, and the existence/persistence of a path outside the runner has not
   been confirmed on this repo's runner (an unverified assumption, same as `docs/ci-pr-review.md`'s
   "Path B"). Also, interactive agents cannot read it.
3. **Auto-disable a cell that exceeds a threshold** — rejected. Automatic exclusion leads to
   coverage collapse, and `run-panel.sh`'s severe gate could then permanently fail-closed a PR.

## Decision

- **The single source is one committed file** — `docs/pr-review/review-memory.md`. Fixed into 3
  sections (recurring real problems / known false-positive patterns / panel cell judgment
  quality) plus a data-handling header.
- **Multiple readers**: `memory_excerpt` (`scripts/pr-review/lib.sh`) inlines an excerpt into the
  lens prompts (`MEMORY_CAP` default 4000B, fail-open, excludes the "panel cell judgment quality"
  table); the chair receives the path and reads it directly via `Read`; the interactive
  `gate-chair`/`content-review-agent` also read the same file.
- **A single local host is the only writer**: only `/co-agent:pr-autofix`'s host (Claude) updates
  it. The planner / implementer are **forbidden** from writing to this file — since the
  implementer processes untrusted review text, letting it write to a file that later gets loaded
  into future review prompts would open an injection path.
- **Roster exclusion is only a recommendation**: if a cell has `unsupported >= 5` and
  `unsupported/total >= 0.5`, `panel_config.py set <cell> enabled false --root .` + an ADR are
  **recommended**. Automatic application is forbidden (a human still commits it, exactly as in
  the ADR-012 precedent).

## Consequences

- The PR head cannot tamper with the memory used to review itself — since `pull_request_target`
  checks out the base ref, this is not an injection surface. The trade-off is that **updates only
  take effect starting from the PR after they merge** (the same delay characteristic as a roster
  change).
- Memory updates do not go through the `land_delta.sh` pipeline (they're a host edit outside the
  worktree). Since that script's `commit` stage only stages landed files via pathspec, a memory
  update is a **separate host commit** made right after landing.
- Review works normally even if the file is missing or a section is empty (fail-open on every
  path) — the absence of memory never blocks a review.
- The caps (30 lines per section, 200 lines per file) must be enforced by humans. There is no automatic pruning.

## References

- `docs/pr-review/review-memory.md` — the memory file itself
- `scripts/pr-review/lib.sh` (`memory_excerpt`), `scripts/pr-review/synthesize.sh` (chair prompt)
- `.github/workflows/pr-review.yml` — the excerpt append in the "Build lens prompts" step
- `plugins/co-agent/skills/pr-autofix/SKILL.md` — marker interpretation + memory read/write + threshold recommendation
- ADR-009 (CI multi-AI review), ADR-011 (lens×model matrix), ADR-012 (roster-exclusion precedent),
  ADR-013 (Kiro diff delivery / removal of `fs_read`)
