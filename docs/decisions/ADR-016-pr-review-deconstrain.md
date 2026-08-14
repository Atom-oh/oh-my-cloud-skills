# ADR-016: De-constrain the PR Review Gate — Collapse the Lens×Model Matrix, Bound the Chair, Trust the Model's Verdict

## Status

Accepted (2026-08-14)

## Context

PRs #141–#148 queued up unable to merge because `AI Code Review` was red, and
investigation showed the gate was failing for reasons that were not review findings:

- **#141 and #146** never received a real review. `synthesize.sh`'s chair ran with
  `--allowedTools "Read Grep Glob"` and was told to "Read CLAUDE.md + AGENTS.md for
  project context" — on diffs touching the pr-review scripts or the co-agent plugin
  tree, both the primary and fallback chair model crawled the repo until the 600s
  `CHAIR_TIMEOUT` killed them (confirmed from CI logs: both models timed out at
  exactly 600s, on both PRs). When that happens, `synthesize.sh` discarded everything
  and wrote a fabricated `VERDICT: FAIL`, indistinguishable to the PR author from an
  actual objection — and the failure reproduced deterministically on retry, since diff
  content is what triggered the crawl.
- **#143/#144/#145** were the author's own diagnostic control PRs, opened specifically
  to isolate that runaway (by diff size, by a mock-VERDICT test fixture, by the new
  file alone) — each individually blocked on a single non-runtime nitpick promoted to
  MAJOR by the chair, none of which held up as a merge blocker.
- Memory (`docs/pr-review/review-memory.md` predecessor: chat-history-only
  `pr-review-gate-convergence` note) already recorded PR #125 running 40 rounds
  without ever reaching PASS on exactly this class of finding.

Beyond the immediate incident, the harness had grown well past what frontier models
(Opus 5 / Sonnet 5 / Fable 5) need:

- **16 cells for what didn't need 16.** 4 models × 4 hardcoded lenses (L2 skill /
  L3 security / L4 correctness / L5 docs) quadrupled both the cell count and the
  chair's input — directly shrinking the chair's effective timeout budget on any
  diff large enough to make every cell's output non-trivial.
- **Lens checklists duplicated project rules already inlined in the chair prompt.**
- **The severity rule was one sentence with no definition**: `CRITICAL/MAJOR 있으면
  FAIL, 아니면 PASS`. A strong model told to find issues will label its best find
  MAJOR, and one MAJOR was fatal — with no distinction between "this breaks
  something" and "this is worth mentioning."
- **The harness overrode the model's own verdict.** `coverage-severe.flag` forced
  `VERDICT: FAIL` regardless of what the chair had concluded.
- **Two verdict parsers, deliberately kept different.** `chair_valid()` in
  `synthesize.sh` required exactly one `^VERDICT:` line and that it be the file's
  last line; the workflow gate accepted any `^VERDICT: (PASS|FAIL)$` line anywhere.
  `verdict-gate-agreement-check.sh` (107 lines) existed solely to assert the two
  parsers disagreed in the intended direction — with no caller anywhere in the repo.
- Review-comment archaeology (`"8차 리뷰 MINOR-3"`, `"17차 리뷰 MINOR-1"`, `"20차 리뷰
  MAJOR L4-1"` style citations) had accumulated to where comments outweighed the code
  they annotated.

## Options Considered

1. **Patch the timeout/severity bugs only, keep the 16-cell lens×model matrix** —
   fixes the immediate incident but leaves the chair's input 4× larger than
   necessary, which is what starved its timeout budget in the first place; the same
   class of failure remains one large diff away.
2. **Drop the external panel entirely, single Claude reviewer** — maximal
   simplification, but gives up the cross-vendor diversity ADR-011 was built for.
3. **Collapse lens×model → model-only (this ADR)** — keep the cross-vendor roster
   (Codex + Kiro×3), drop the lens split so each model does one full-scope review.
   16 cells → 4. `run-panel.sh` treats every `*.txt` in the lenses directory as one
   lens already, so this needed zero changes to `run-panel.sh`'s fan-out logic — the
   workflow just writes one prompt file instead of four.

Option 3 was chosen, confirmed with the user (chat, this session): keep the
cross-vendor panel, drop the lens dimension.

## Decision

- **Bound the chair, don't trust it to self-limit.** The chair's first attempt keeps
  `Read Grep Glob` and a `CHAIR_TIMEOUT` (300s, down from 600s). If it doesn't produce
  a usable verdict, the fallback attempt runs with **no file tools at all**
  (`CHAIR_FALLBACK_TIMEOUT`, 120s) — the diff and every panel review are already on
  stdin, so a no-tools chair is complete and cannot crawl. The chair prompt no longer
  tells the model to Read `CLAUDE.md`/`AGENTS.md` — project rules that matter are
  already inlined in the prompt; that instruction was the actual crawl trigger.
- **An infra failure is not a review finding.** When both chair attempts fail to
  produce a usable verdict, `synthesize.sh` sets `chair_error=1` (via `GITHUB_ENV`).
  The workflow gate checks this before checking the verdict and posts a distinct
  `Status: ERROR` badge — "the chair produced no output, re-run, don't chase this as
  content" — instead of `Status: BLOCKED — CRITICAL/MAJOR`.
- **Collapse the lens×model matrix to model-only.** One full-scope prompt, shared by
  all 4 models, replaces the four lens-restricted prompts. `run-panel.sh` and
  `panel_config.py` are unchanged — the fan-out is driven by however many `*.txt`
  files sit in the lenses directory, so writing one file instead of four collapses
  the matrix without touching the fan-out code.
- **Define blocking, then get out of the way.** The chair prompt replaces
  `CRITICAL/MAJOR 있으면 FAIL, 아니면 PASS` with an impact test: FAIL only for a
  finding that would actually break something, leak a credential, or violate a
  stated project contract if merged as-is, stated in one line at the Verdict
  section. Advisory/style findings alone are never sufficient for FAIL.
- **One verdict parser, shared by both sides.** `lib.sh` gains `verdict_of()`: the
  last `^VERDICT: (PASS|FAIL)` match in the file wins, wherever it sits, trailing
  text on that line tolerated. `chair_valid()` and the workflow gate both call it —
  the two-parser divergence and its accompanying commentary are gone, and
  `verdict-gate-agreement-check.sh` (orphaned, no caller) is deleted.
- **Stop overriding the model's verdict.** `coverage-severe.flag` (surviving vendor
  count ≤1) still surfaces as a banner — "cross-vendor confirmation didn't hold for
  this review" — but no longer forces `VERDICT: FAIL`. The verdict is the chair's.
- **The review-memory loop (ADR-015) is preserved, moved to stdin.** The chair used
  to be told to `Read` the memory file's path directly; that instruction is gone
  along with the other Read-project-files instruction, so the memory excerpt is now
  inlined into the chair's stdin instead (`CHAIR_MEMORY_CAP`, 8000B) — both the
  tool-bearing primary attempt and the no-tools fallback see it. The
  `### 🧠 MEMORY CANDIDATES` / `### PANEL QUALITY` output contract is unchanged.
- **Trim the archaeology.** Comments that encoded a load-bearing invariant (scrub
  before cap, file-based `head -c` to dodge SIGPIPE under `pipefail`, argv-vs-stdin
  for the 128KiB single-arg limit, run-scoped workdir) stay, condensed to one line.
  Round-by-round narration of resolved review cycles does not belong in the scripts
  it was annotating.

## Consequences

- Chair input drops ~4× (4 cells vs. 16) and the chair can no longer spend its
  timeout budget crawling the repo — the exact failure mode that blocked #141/#146
  cannot recur, whatever the diff.
- A genuine Bedrock/CI outage now reads as `Status: ERROR` with an honest "re-run,
  this isn't content" message, instead of a fabricated `Status: BLOCKED —
  CRITICAL/MAJOR` that sends the PR author looking for a defect in their own diff.
- The severity bar moved from "did a strong model find *something*" to "does this
  actually break something" — fewer PRs should hit the PR #125-style 40-round
  non-convergence class this ADR's Context describes, though this is a qualitative
  judgment call handed back to the chair model, not a mechanical guarantee.
- Coverage-collapse (≤1 surviving vendor) no longer force-fails a PR whose chair
  otherwise reached PASS — it's visible in the comment, not fatal.
- `pull_request_target` checks out **base**, so this change only takes effect for
  PRs opened/synchronized after it merges — it cannot review its own PR with the new
  harness. This PR's own check ran the *old* gate (and hit the exact chair-crawl
  timeout this ADR fixes) — the merge decision rested on the local test suite
  (`tests/pr-review/*.sh`, `tests/run-all.sh`) instead.
- Tests updated: `tests/pr-review/test-synthesize.sh` (e)/(g)/(h) — coverage-severe
  no longer forces FAIL, the single-parser semantics, and the new infra-error path
  (`chair_error=1` via `GITHUB_ENV`, distinct from a real BLOCKED). `tests/pr-review/
  test-lib.sh` gains `verdict_of()` coverage. `tests/pr-review/test-run-panel.sh`
  needed no changes — its lens-matrix mechanism is generic and untouched; only the
  workflow now feeds it one prompt file instead of four.

## References

- ADR-011 (lens×model matrix — this ADR reverses its lens dimension, keeps its
  cross-vendor panel and L1 pre-check), ADR-015 (review-memory loop — preserved,
  delivery mechanism changed)
- `.github/workflows/pr-review.yml`, `scripts/pr-review/{synthesize,lib,run-panel}.sh`
- `docs/ci-pr-review.md`, `docs/ci-pr-review-runbook.md`
- `tests/pr-review/{test-synthesize,test-lib}.sh`
- PRs #141, #146 (the incident), #143/#144/#145 (the author's own diagnostic
  controls, closed as superseded by this root-cause fix)
