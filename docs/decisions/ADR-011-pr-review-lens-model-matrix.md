# ADR-011: PR Review — L1 Deterministic Gate + Lens×Model Matrix

## Status

Accepted (2026-07-05)

## Context

ADR-009's multi-AI panel (Codex + Kiro×3) diversified reviewers by vendor, but all four AIs
reviewed the diff with the **same "look at everything" prompt**. In this structure, the only
axis of diversity is the vendor, so if one model misses a particular review area (e.g. version
consistency, dangling references), the other models — using the same prompt — are also likely
to miss that same area. There was also no verification stage to filter review results, so false
positives went straight into comments unfiltered. In addition, items that can be verified
deterministically (JSON validity, dangling references, version consistency) were being handled
via AI calls, creating unnecessary cost, latency, and room for false positives.

## Options Considered

1. **Keep the current setup (broadcast the same prompt)** — simple, but diversity has only one axis (vendor), so blind spots repeat.
2. **One model dedicated per lens (1 model : 1 lens)** — trades vendor diversity for lens cross-checking; if a given CLI is absent, that whole lens goes empty.
3. **Full lens×model matrix + separate deterministic pre-check** (Adopted) — maximizes both vendor diversity and lens (perspective) diversity at once, and pulls out anything that can be verified deterministically into a script, ahead of AI.

## Decision

Restructure `.github/workflows/pr-review.yml` into a two-tier gate
(design: `docs/superpowers/specs/2026-07-05-pr-review-hybrid-lens-design.md`):

- **L1 (deterministic, no AI calls)** — `scripts/pr-review/precheck.sh` extracts the PR head
  tree via `git archive` **as data only** (never executed), and against the base (trusted)
  checkout's `scripts/test-plugins.py --root <tree>` **and `scripts/test-codex-plugins.py
  --root <tree>`**, verifies manifest JSON validity, dangling references, and version
  consistency across both the `.claude-plugin` manifests and the `.codex-plugin`/`.agents`
  manifests. (An early revision ran only `test-plugins.py`, leaving a coverage gap where
  `.codex-plugin` manifests skipped both L1 and AI re-review — this was found as a MAJOR
  finding in the CI's own self-review and fixed within the same PR.) On failure, the AI panel
  is never invoked and the job immediately reports `VERDICT: FAIL` — deterministic problems
  don't spend AI budget.
- **L2–L5 (lens×model matrix)** — once L1 passes, 4 models (Codex + Kiro×3) × 4 lenses
  (L2 = Skill/Agent quality, L3 = security, L4 = code correctness, L5 = documentation
  consistency) = 16 independent find agents all run in parallel (`&`+`wait`). Each cell reviews
  only its own single lens — the narrower scope shortens each cell's response, and given the
  parallel execution, wall-clock time is plausibly even shorter than the current setup (4 calls,
  full scope) (worst-of-16 (narrow scope) < worst-of-4 (broad scope)).
- **Chair**: Claude Fable 5 (→ Opus 4.8 fallback, per ADR-009) synthesizes the 16 cells by
  lens. `CHAIR_TIMEOUT` was raised from 120s to 600s (#105, progressed in parallel and
  independently of this PR). Measured basis: in a separate run on the same runner image/service
  account, an older script version without a timeout spent 286 seconds normally synthesizing a
  357-line diff — the 120s value (later reviewed at 180s) was force-killing a chair that was
  still responding normally, every time, and misattributing it as "empty response → FAIL" (a
  timeout misconfiguration, not a Bedrock outage). Since the matrix has more input (4→16
  outputs), the timeout was kept generously at 600s.
- **The chair call passes the diff+panel content via stdin rather than argv.** Linux has a hard
  ~128 KiB limit on a single argv argument (exec fails immediately beyond it); the old structure
  (4 calls) only broke once each cell exceeded roughly ~31 KB, but with 16 calls the average per
  cell only needs to exceed roughly ~8 KB to hit the limit — this prevents the paradox where the
  more detailed a review is (= the longer its output), the more likely the exec itself fails,
  resulting in "empty response → VERDICT: FAIL." A per-cell byte cap (`PANEL_CELL_CAP`, default
  20000) was also added as belt-and-braces. For the same reason, the Kiro cell was also switched
  from embedding the diff as text in argv to referencing only the file path via `fs_read`
  (reusing a pattern already documented in co-agent's `ai-cli-adapters.md`; the previous
  revision's `--trust-tools=read,grep` was an invalid flag — the actual tool name is `fs_read`).
- **The residual risk of switching Kiro to `fs_read` is mitigated the same way as co-agent's PR
  gate.** Granting `fs_read` actual file-read permission means that prompt injection embedded in
  an untrusted PR diff could induce it to "instead of that path, read this job's other
  credentials (GH_TOKEN, Codex/chair's Bedrock Pod Identity `AWS_*`) and include them in the
  response," and that response could then be exposed in a public PR comment via the chair's
  synthesis, or leaked outside the region to Kiro, an external service (found as a CRITICAL
  finding in the CI's own self-review — see Appendix for detail). The same mitigation used in
  `consensus_hooks.py`'s `_review_one`/`_sanitized_env` is applied only to the Kiro cell:
  (1) an isolated cwd (`$WORK/kiro-cwd`, not the repo) — so relative-path reads can't reach repo
  files (the diff path is already absolute, so this doesn't matter for it); (2) an env allowlist
  — only `KIRO_API_KEY` plus non-sensitive variables (PATH/HOME/LANG/TMPDIR) are passed through;
  GH_TOKEN/AWS_* etc. are blocked. Codex is not given the same isolation because it actually
  needs that `AWS_*` itself for Bedrock authentication (Pod Identity injection) (out of scope —
  this isn't a risk newly opened by this diff, but a structural property of the existing Bedrock
  auth model). The risk of inducing an absolute-path read (e.g. `~/.aws/credentials`) remains as
  long as `fs_read` is read-capable — the same limitation is documented in the co-agent docs.
  **This residual risk is an explicit accepted risk** — if an induced absolute-path read
  succeeds, its content is **already sent to the external service (Kiro) before** the local
  `scrub_secrets()` is applied (the egress leg cannot be blocked by scrubbing). Mitigating
  factors: the workflow only runs same-repo PRs via the `head.repo.full_name ==
  github.repository` gate, so the threat actor is already narrowed to a collaborator with write
  access, and the env allowlist plus isolated cwd/HOME have removed the env-/`~`-based attack
  surface through actual testing (raised as CRITICAL by the panel in round 15 → the chair
  downgraded it to MINOR based on this very documented fact, and it was reconfirmed). A
  process/container-level FS sandbox (e.g. exposing only the diff file via bubblewrap or a
  read-only mount on the runner image) is the only way to structurally close this residual risk —
  left as an operational follow-up item. **HOME is also isolated** (`$KIRO_CWD`, not the actual
  runner's `$HOME`) to reduce the effective attack surface of cases induced via `~` notation
  (this runner's Kiro auth relies only on `KIRO_API_KEY`, not on credential files under HOME —
  found as MAJOR in the CI's own self-review and fixed within the same PR).
- **Coverage floor**: if a kiro-cli flag such as `--v3 --mode default --trust-tools=fs_read` is
  invalidated on this runner, or the binary is missing, all of that model's lenses fall back to a
  graceful skip, and the matrix could silently shrink (e.g. only Codex's 4 cells remain) while
  still producing `VERDICT: PASS` (found as MAJOR in the CI's own self-review). When an entire
  model's row is empty, `run-panel.sh` logs `::warning::` plus `degraded-models.txt`, and
  `synthesize.sh` puts that list in an explicit banner at the top of the review (this doesn't
  force VERDICT to FAIL — it's judged that intermittent rate limits are common too, and since the
  matrix itself provides cross-checking per lens, it isn't a total blind spot; instead, it's made
  visible so a human doesn't miss it). If the surviving vendor count collapses to 1 or fewer
  (i.e. (total-1) or more models are degraded), this warn-only premise itself breaks, so only in
  that case is it forcibly escalated to `VERDICT: FAIL` (detail: Appendix, round 5). Actual
  `fs_read` smoke verification on the runner image is left as an operational follow-up that
  cannot be done in this repository's development environment. Also added to the same
  operational follow-up list: explicit tracking of the lens-column blind spot (only per-model
  row checks exist; the case where a single lens is simultaneously empty across all models is not
  detected — a judgment already noted in the runbook as "considered low-probability") (round 16,
  MINOR-3 — the description itself was accurate, but it was missing from this list, hurting
  traceability).
- **Cost is not treated as a constraint** (user decision) — the actual ceiling is only the
  runner's concurrency/API rate limits, defended against with the job's `timeout-minutes` (50m).
- The remaining invariants of ADR-009 (security: base-checkout + no fork-PR execution, data
  residency: Kiro's external transmission as accepted risk, fail-closed VERDICT, comment-upsert
  marker) remain unchanged.

## Consequences

- Coverage is systematized from "diversifying reviewers" to a "reviewer×perspective matrix" — reducing blind spots.
- Manifest/version problems that can be verified deterministically are blocked immediately with 0 false positives and 0 AI cost.
- The number of AI calls increases from 1×panel (4) to up to 4×panel (16) — an intended trade-off (cost unconstrained).
- Phase V (verify, the fully-formed hybrid gate) is not included in this implementation — the matrix itself already provides 4-way cross-checking per lens, which is judged to absorb a substantial share of false positives; it will be added if real false positives become a problem.
- Tests: newly created `tests/pr-review/test-run-panel.sh` (matrix fan-out) + `tests/pr-review/
  test-precheck.sh` (L1) + `tests/pr-review/test-synthesize.sh` (chair synthesis) + `tests/
  pr-review/test-lib.sh` (scrub_secrets/ensure_slots), and a pass/fail bridge was added to
  `tests/run-all.sh` to include `tests/pr-review/*.sh` in CI aggregation (previously an
  uncounted gap). Detailed round-by-round coverage is in the Appendix.
- **A limit of self-verification, and real progress achieved within it**: this redesign is itself
  unable to self-verify under the base-script model (ADR-009), but **this PR itself went through
  two actual CI review passes**. The first pass (the old 4-panel structure, commit 01cf9d4)
  caught C1 (missing Kiro env/cwd isolation) and M2 (harness `set -e` contamination), both fixed
  within the same PR. After #105 (`CHAIR_TIMEOUT` 120s→600s — diagnosed from a separate root
  cause, see below), which merged into main in parallel, was reflected, a second review (commit
  9ee2d99) actually ran to completion, catching and fixing an additional `.codex-plugin` manifest
  L1 coverage gap (M1), the absence of a coverage floor (M2), and the missing HOME scratch
  isolation (M3), all within the same PR. Conversely, some items raised by that review were
  actually disproven through direct verification (a claim that `KIRO_API_KEY` quoting was
  insufficient — directly reproduced and confirmed that the `env -i` conditional expansion was
  already safe, so it was not applied) — an example of not blindly applying panel feedback, but
  verifying it against the code/reproduction before adopting it. This pattern (raised → checked
  against diff/code → fixed if confirmed, rejected with a documented reason if disproven) recurred
  identically across the following 14 rounds — see the Appendix for round-by-round detail.
- **The actual root cause of CHAIR_TIMEOUT 120s→600s (#105)**: separately from the "argv 128 KiB
  limit" this PR diagnosed, #105, started in parallel, found a more fundamental cause — in a
  separate run on the same runner image/service account, an older script version without a
  timeout normally spent 286 seconds synthesizing a 357-line diff. In other words, most of the
  observed "chair empty response" failures were not Bedrock outages or ARG_MAX, but rather **the
  timeout value itself — 120s (later reviewed at 180s) — being too short and killing normal
  responses**. The two fixes (switching to stdin + raising the timeout) target different failure
  modes and are not mutually exclusive — switching to stdin prevents the hard exec()-level
  failure, while raising the timeout saves normal-but-slow responses.

## References

- ADR-009 (the original multi-AI panel decision, amended by this ADR), ADR-010 (Antigravity removal)
- `docs/superpowers/specs/2026-07-05-pr-review-hybrid-lens-design.md` (design proposal)
- `.github/workflows/pr-review.yml`, `scripts/pr-review/{precheck,run-panel,synthesize,lib}.sh`,
  `scripts/test-plugins.py --root`, `scripts/test-codex-plugins.py --root`
- `docs/ci-pr-review.md`, `docs/ci-pr-review-runbook.md`
- `tests/pr-review/{test-run-panel,test-precheck,test-lib,test-synthesize}.sh`
- PR #103 (this redesign), #104 (co-agent model tiering, unrelated parallel merge), #105
  (`CHAIR_TIMEOUT` 120s→600s — root cause diagnosed independently of this PR)

## Appendix: Round-by-Round Review Log

> This appendix is the history of findings, verification, and fixes produced across 15 rounds of
> self-CI review before PR #103 was merged. The Decision/Consequences above hold only the durable
> final decisions; the process leading to them (what was raised, how it was verified, and why it
> was or wasn't adopted) is preserved here. Rounds 11–14 repeatedly noted that "the Decision body
> is also doubling as a revision log, hurting readability," and splitting off this appendix
> addresses that feedback.

- **Round 3 fix (CI self-review, after commit 5c56d7f)**: (1) added one more layer of
  belt-and-braces to the above absolute-path-read residual risk — `lib.sh::scrub_secrets()` now
  applies detection of the co-agent `_SECRET_RE` patterns (AWS/GitHub/Slack/OpenAI·Anthropic/
  Google + generic key=value) and JWTs (Pod Identity token shape) *before* the per-cell cap is
  applied, substituting any value leaked via an absolute-path read before it actually reaches the
  chair's stdin (this only works once the value has already appeared in a cell's output — it
  still cannot prevent the read itself, a remaining limitation). (2) synced
  `docs/ci-pr-review.md`/runbook, which had drifted from the L1 implementation by not mentioning
  `test-codex-plugins.py`. (3) fixed a mislabel where the L1-fail comment header attached
  "lens×model matrix" even on paths where the matrix never ran. (4) added a guard for all three
  `precheck.sh` arguments being empty strings, raised the L1 step to `set -euo pipefail`, fixed
  `synthesize.sh`'s cell iteration to use `LC_ALL=C sort` (removing locale-dependent ordering), and cleaned up stale comments.
- **Round 4 fix (CI self-review, after commit 27ab2de) — this time including an actual crash bug**:
  (1) **M1 confirmed by direct reproduction**: in `synthesize.sh`, `printf '%s' "$SCRUBBED" |
  head -c "$CAP"` had a bug where, if a scrubbed cell exceeded the cap, `head` would exit first →
  `printf` would receive SIGPIPE (141) → `set -euo pipefail` would kill the entire script, so not
  even `review.md` would be produced (a regression introduced in round 3 when scrubbing was
  layered onto a pipe; directly reproduced with a 100KB→20000B cap and confirmed exit 141, and
  confirmed it does not reproduce once routed through a file instead). Removed the pipe and had
  the scrub result written to a temp file, read via `head -c file` — with no inter-process pipe,
  SIGPIPE itself cannot occur. (2) also fixed, after direct confirmation, 2 coverage gaps in
  `scrub_secrets()`: unquoted `KEY=value` (the most common credential-file shape) wasn't being
  caught, and a PEM's header line was substituted but its body (the actual key) was left intact
  (a line-oriented sed cannot handle multi-line blocks — switched to an awk state machine that
  substitutes the entire BEGIN..END block). (3) minor: updated the workflow's timeout-estimation
  comment to reflect the 600s baseline, added a numeric-format guard for `pr_number` in
  `precheck.sh`, and replaced all of the tests' hardcoded `/tmp/*.log` paths with `mktemp`
  (removing interference between parallel runs). **Deliberately not adopted**: a suggestion to
  update the design spec's Status to "Implemented" — per `docs/superpowers/CLAUDE.md`'s
  convention, a spec is a historical artifact that freezes the intent at the time it was written,
  and the durable current state is the ADR's job (already Accepted); rewriting a spec's Status to
  match later reality is explicitly forbidden by that convention.

- **Round 5 fix (after commit 14a6686)**: (1) MAJOR — `run-panel.sh`'s skip-diagnostic block was
  piping the last 25 lines of a failed cell's stderr straight into the public CI log via `tail
  -25 "$e" >&2`, unscrubbed. `docs/ci-pr-review.md` explicitly states that "raw stderr is never
  exposed via comments/logs," and the actual implementation did not match that documentation;
  combined with the Kiro `fs_read` threat model (prompt injection embedded in the diff inducing
  credentials to be routed to stderr), this was an actual leak path. CONFIRMED by code review —
  fixed to `tail -25 "$e" | scrub_secrets >&2`, and confirmed no new SIGPIPE risk is introduced,
  since both `tail` and the awk/sed inside `scrub_secrets` fully consume input to EOF (unlike the
  SIGPIPE pattern caught in rounds 3/4, there is no early-exit stage here). (2) MAJOR — because
  the coverage floor is warn-only, if an entire vendor dies at once (e.g. all 3 Kiro models fail
  simultaneously due to a new flag-combination bug), the matrix could still silently produce
  `VERDICT: PASS` using only the remaining vendor (Codex), weakening the fail-closed contract —
  CONFIRMED by direct reproduction (mocking a scenario where 3/4 models die). The review's
  suggestion of "force FAIL if even one dies" was not adopted (that would over-block even a single
  model's transient rate limit, when that lens still has 3-way cross-checking) — instead
  implemented a middle ground that forces FAIL only when `TOTAL_MODELS - 1` (i.e. ≤1 surviving
  vendor, meaning no lens retains any cross-checking at all): `run-panel.sh` writes a
  `coverage-severe.flag`, and when `synthesize.sh` sees that flag, it deletes whatever
  `VERDICT:` line the chair already wrote via `sed -i '/^VERDICT:/d'` and leaves only the single
  forced-FAIL line (the comment step only looks at the file's last line, so leaving the original
  PASS in place would visually contradict the BLOCKED badge). Both the 3/4-dead scenario (flag on
  + chair PASS → forced FAIL, only 1 VERDICT line remains) and the 1/4-dead scenario (flag off +
  chair PASS preserved as-is) were directly reproduced via mocks and locked in with tests
  (`test-run-panel.sh` (f)/(g), `test-synthesize.sh` (e)). **Disproven**: a claim raised in the
  same round that "the JWT pattern could be injected across a newline" was disproven by direct
  testing — confirmed that `scrub_secrets` operates line-by-line without `sed -z`, so
  `[[:space:]]` cannot match across a newline; not adopted.

- **Round 6 fix (after commit 1132c1d, PASSED — 0 CRITICAL/MAJOR, MINOR only)**: with 3/3 panel
  consensus, no CRITICAL/MAJOR was confirmed (the 2 items raised were downgraded to MINOR after
  cross-checking against the diff — unscrubbed L1-failure output, and the `kiro_env`
  function-as-command pattern); of the remaining 4 MINOR items, the low-cost ones with real
  hardening value were folded into this round too: (1) the "Write L1 failure as review" step in
  `pr-review.yml` was posting `precheck.sh`'s output straight into the PR comment without
  `scrub_secrets` — while agreeing with the panel's analysis that the current L1 inputs have no
  real credential-leak source, the mismatch with `docs/ci-pr-review.md`'s "never expose raw
  output" principle was real, so `lib.sh` is now sourced to pass the output through
  `scrub_secrets`. (2) `precheck.sh`'s tar extraction was leaving symlinks from the PR tree
  intact — the current validators don't echo parse failures, so there is no leak today, but as
  defense-in-depth against a future risk that could combine with (1), added `find "$TREE" -type l
  -delete`. (3) `run-panel.sh`'s `DIFF="$(realpath "$1" 2>/dev/null || echo "$1")"` fallback was
  silently leaking into a blind review, where, on realpath failure, it passed through the
  original (relative) path, which Kiro's isolated cwd could not find — switched to fail-fast
  (`|| exit 1`). Directly reproduced that realpath succeeds (exit 0) as long as the parent
  directory exists, even if the target file doesn't, then reproduced an actual failure using a
  path whose parent directory itself doesn't exist, and locked it in with a test. (4) aligned an
  asymmetry where `test-plugins.py` only omitted `.resolve()` when `--root` wasn't given, matching
  `test-codex-plugins.py` (cosmetic). **Not adopted**: the `kiro_env` function-as-command pattern,
  which the panel confirmed as "not a defect," was left unrefactored since it's confirmed to work
  correctly today via subshell inheritance (noted only as a caution for future refactors); the
  unquoted heredoc lens prompt was also left unchanged since `$COMMON` expansion is an intended
  part of the design. New tests: `test-run-panel.sh` (i) (realpath fail-fast),
  `test-precheck.sh` (k) (symlink removal) — full suite 586 passed (+4), the same 17 pre-existing unrelated failures remain.

- **Round 7 fix (after commit e59c0ff, BLOCKED — 1 MAJOR)**: the panel didn't respond
  (Claude solo), so it was the chair alone cross-checking against the diff, but the finding was
  CONFIRMED — of the state files `run-panel.sh` newly creates, only `coverage-severe.flag` was
  not reset at the start of a run. `responded.txt` (`: >`), `degraded-models.txt` (`: >`), and
  `pr-tree` (`rm -rf`) are all reinitialized on every run, but this flag was missing from that
  set — if the self-hosted runner preserves `/tmp` across jobs (the current workflow only does
  `mkdir -p` and never cleans up — the ephemeral assumption is never stated anywhere in the code),
  a single instance of 3/4 models dying would poison state so that even a subsequent, fully
  normal PR review would be forced into "coverage collapse → forced FAIL." Fixed by adding `rm -f
  "$WORK/coverage-severe.flag"` near the start of `run-panel.sh` (next to `ensure_slots`/`: >
  "$RESP"`). A MINOR item raised in the same round, sharing the same root cause, was fixed
  together: `ensure_slots()` only did `mkdir -p`, so orphaned cell files inside a slot directory
  (leftovers from a previous run or an old lens configuration) never got cleared — changed to
  `rm -rf "$1/slot"; mkdir -p "$1/slot"`. Also, `scrub_secrets`'s PEM awk state machine had a
  problem where, if the `END` line never appeared (a truncated or tampered cell output), `skip=1`
  would remain set and swallow all subsequent legitimate findings whole — while this is fail-safe
  in direction (not a leak), added `END { if (skip) print "[REDACTED-UNTERMINATED-PEM-BLOCK]" }`
  to at least preserve the fact that "something was swallowed." **Not adopted**: a suggestion to
  replace the L1-fail path's string-literal comparison of `panel_responded` with a dedicated
  output variable, and a suggestion to align `run-panel.sh`'s relative-path asymmetry for
  `$WORK` — both were judged cosmetic hardening rather than real defects, so neither was adopted
  in this round (all call sites already use absolute paths only, so it is safe as-is). New tests:
  `test-run-panel.sh` (j) (that both the flag and slot leftovers disappear on a re-run using the
  same `$WORK`, severe→normal), `test-lib.sh` (that an unterminated PEM leaves a warning marker) — full suite 589 passed (+3), the same 17 pre-existing unrelated failures remain.

- **Round 8 fix (after commit 15ab50d, PASSED — 0 CRITICAL/MAJOR, 5 MINOR)**: adopted 3 of the
  non-blocking hardening/UX items that were low-cost with real value. (1) the previous round's
  fix that changed `ensure_slots` to `rm -rf "$1/slot"` was inconsistent with the "guard arguments
  that could produce a destructive path" principle already followed in `precheck.sh`, but not
  applied to `run-panel.sh` — if `$WORK` is empty, this becomes `rm -rf /slot` (under the
  filesystem root), a latent destructive path. Added empty-string guards for `LENSES_DIR`/`WORK`
  (directly confirmed `DIFF` is already fail-fast because `realpath` already fails on an empty
  string, so no separate guard is needed there). (2) `precheck.sh` ran `test-plugins.py` →
  `test-codex-plugins.py` sequentially under `set -e`, so if the first validator failed, the
  second never ran, forcing the PR author into a round trip of fixing one category, pushing
  again, and only then discovering the other category (the fail-closed contract itself was
  preserved — this was a UX problem) — fixed to accumulate via `rc=0; ... || rc=1` so both run
  and the exit code reflects both. (3) `scrub_secrets`'s `sk-(proj-|ant-)?...` pattern had no
  left word boundary, so a substring like "risk-assessment-management-system" (the "sk-" inside
  "risk") could get wholly substituted if it ran 20+ characters — directly reproduced and
  confirmed — while this is fail-safe in direction (not a leak), it hurt review readability, so
  added a `(^|[^A-Za-z0-9_])` left boundary, reconfirmed that detection of actual keys
  (`sk-ant-...`/`sk-proj-...`) is preserved. **Not adopted**: the tests' `setup()` pattern of
  always prepending a new `$BIN` to PATH without ever removing the old one — since each test case
  always creates the mock it needs fresh, the newest mock always wins, so there's no real harm
  today (older test files already use this same pattern) — deferred an unnecessary refactor.
  Also deferred: leftover indentation in the workflow YAML heredocs, which is harmless cosmetic
  and doesn't affect model behavior. New tests: `test-run-panel.sh` (k) (empty
  lenses_dir/workdir argument guards), `test-precheck.sh` (l) (that both validators' errors are
  reported at once), `test-lib.sh` (guard against the risk-... false positive) — full suite 594 passed (+5), the same 17 pre-existing unrelated failures remain.

- **Round 9 fix (after commit f4a0f57, PASSED — 0 CRITICAL/MAJOR, 4 MINOR)**: this round
  explicitly noted, after re-checking the diff, that most candidate risks reviewed were already
  defended (the `if`-wrapped L1 fail-closed routing, `synthesize.sh`'s non-final `&&` list,
  `kiro_env` subshell inheritance, `realpath` fail-fast, the severe-flag/slot reset, and `while …
  done < <(sort)` not being a subshell). Of the remaining 4 MINOR items, 3 were adopted: (1) the
  "Build lens prompts" step in `.github/workflows/pr-review.yml` only did `mkdir -p` on
  `/tmp/pr-review/lenses` and never cleared it — sharing the same root cause caught in rounds
  7/8 with `coverage-severe.flag`/slot (on a non-ephemeral runner, changing the lens
  configuration could leave stale `*.txt` files that get picked up by the `LENS_FILES` glob,
  producing a phantom matrix row) — fixed to `rm -rf` and regenerate at the start of the run.
  (2) `ensure_slots()` itself didn't guard against an empty `$1`, relying purely on its only
  caller (`run-panel.sh`) to guard it — added a direct guard inside the function itself, in line
  with `precheck.sh`'s "a function that produces destructive paths must guard itself internally"
  principle. (3) a concern that overlapping jobs from different PRs on the same self-hosted
  runner (when parallelized across a runner pool) share the fixed `/tmp/pr-review` path and could
  step on each other's state — of the two alternatives the review suggested (switching to
  `$RUNNER_TEMP` / including the PR number in the path), the latter was chosen: the L1 step now
  computes `WORK="/tmp/pr-review-${PR_NUMBER}"` and exports it via `GITHUB_ENV`, and the entire
  workflow was aligned so every subsequent step reuses `$pr_work_dir` as-is (the single-PR
  re-run scenario is still defended by the existing script-level resets
  (coverage-severe.flag/slot/lenses); this change adds path isolation between different PRs). A
  full switch to `$RUNNER_TEMP` was deferred this round since it would have a much larger blast
  radius, touching other files like `/tmp/pr-diff*.txt`/`review.md` (the current review only
  flagged `/tmp/pr-review`). **Not adopted**: the test PATH accumulation and YAML heredoc
  indentation, already recorded as "deliberately deferred" in rounds 6/8, weren't re-judged.
  New tests: `test-lib.sh` (that `ensure_slots("")` fails, and that a normal workdir still gets
  its slot created) — full suite 596 passed (+2), the same 17 pre-existing unrelated failures remain.

- **Round 10 fix (after commit 75cfbab, PASSED — 0 CRITICAL/MAJOR, 4 MINOR)**: right after
  round 9 isolated `/tmp/pr-review` by PR number, this review caught one file **newly created by
  that same PR** that missed that same isolation — all 4 items were low-cost with real value and
  all were adopted. (1) `l1-output.txt` was still hardcoded to `/tmp/l1-output.txt`, inconsistent
  with the intent behind isolating `$WORK` by PR number (a runner-pool parallelization scenario
  could let another PR's L1-failure comment carry this PR's precheck output) — moved to
  `"$WORK/l1-output.txt"` and aligned the "Write L1 failure as review" step to reference
  `$pr_work_dir` too. (2) while `coverage-severe.flag`/slot/lenses are reset on every run,
  `$WORK/kiro-cwd` (Kiro's fake HOME) only did `mkdir -p`, so cache/session state left behind by
  kiro-cli could accumulate and carry over on a non-ephemeral runner (there are no credentials
  there, so it isn't a security impact, just a reproducibility problem) — added `rm -rf` at the
  `KIRO_CWD` definition line, closing the same root cause. (3) a hygiene problem where
  per-PR-isolated `/tmp/pr-review-<N>` directories were never cleaned up after a job finished,
  accumulating on disk in proportion to the number of PRs — added an `if: always()` cleanup step
  at the end of the workflow so `$pr_work_dir` is removed regardless of whether the job succeeds,
  fails, or is cancelled (the step ends with a non-fatal `exit 0` so a cleanup failure never
  flips the review's own result). (4) `test-lib.sh`'s new `ensure_slots` test didn't follow the
  `mktemp` convention established in round 4, instead using `/tmp/ensure_slots_test.$$` directly
  — replaced with `mktemp`. New tests: `test-run-panel.sh` (j)'s third sub-case (that
  `kiro-cwd` is also reset in a reused `$WORK`) — full suite 597 passed (+1), the same 17 pre-existing unrelated failures remain.

- **Round 11 fix (after commit 7e1c278, PASSED — 0 CRITICAL/MAJOR, 3 MINOR)**: rounds 9/10
  isolated `$pr_work_dir` by PR number, but `/tmp/pr-diff*.txt`, `/tmp/review*.md`, and
  `/tmp/comment.md` were still on fixed `/tmp` paths, so isolation only applied to the "work
  dir" (coverage-severe.flag/slot/lenses/kiro-cwd) while "the diff and the review body itself"
  could still cross-contaminate under runner-pool parallelization (MINOR-1) — round 9 had
  deferred a full switch to `$RUNNER_TEMP` due to blast radius, but layering these files onto the
  already-established `$pr_work_dir` pattern is mechanical and low-risk, so this was completed
  now: `pr-diff-raw.txt`/`pr-diff.txt`/`pr-diff-truncated.txt`/`review.md`/`review-clean.md`/
  `comment.md` were all moved under `$pr_work_dir`, so the existing cleanup step (`if: always()`)
  now automatically cleans up these artifacts too (a side benefit of improved disk hygiene).
  MINOR-2 (the L1-fail header branch's string-literal comparison of `panel_responded`) — agreed
  with the review's judgment that, since `steps.l1.outputs.result` already exists, the switch is
  effectively free, so the "Write L1 failure as review" step (already gated on
  `if: steps.l1.outputs.result == 'fail'`) now leaves a dedicated `l1_failed=1` flag in
  `GITHUB_ENV`, and the comment step checks only that flag — confirmed via local simulation that,
  on the L1-pass path, `l1_failed` is never set at all, so the `${l1_failed:-0}` fallback
  correctly resolves to "0." **Not adopted**: leftover YAML heredoc indentation (MINOR-3),
  already repeatedly confirmed as harmless cosmetic in rounds 6/8/10, wasn't re-judged. No script
  (run-panel.sh/synthesize.sh/lib.sh) changes were made, so there are no new unit tests — locally
  simulated the workflow YAML's path-substitution logic in bash and confirmed the L1-fail branch
  (header/file path) still works correctly; the full suite remains at 597 passed (scripts
  unchanged), the same 17 pre-existing unrelated failures remain.

- **Round 12 fix (after commit f77a9e1, PASSED — 0 CRITICAL/MAJOR, 4 MINOR)**: adopted 3, did not
  adopt 1. (1) since `$pr_work_dir` is isolated only by PR number, a `cancel-in-progress: true`
  cancelled prior run's `if: always()` cleanup step could `rm -rf` a path that a new run of the
  same PR just created (this only happens when the runner pool has 2+ hosts, and it resolves
  safely via fail-closed → re-run recovery, so it's a narrow-condition MINOR) — as the review
  suggested, added `${GITHUB_RUN_ID}` to the path (excluding `RUN_ATTEMPT`), separating the path
  per trigger (push). `RUN_ATTEMPT` was deliberately excluded — a manual "Re-run failed jobs" on
  the same run still reuses the same path, so the stale-state reset tests fixed in rounds 7–10
  (coverage-severe.flag/slot/lenses/kiro-cwd) still target a valid scenario. (2) directly
  reproduced and confirmed that `synthesize.sh`'s `RESP="$(tr ... < "$WORK/responded.txt"
  ...)"`, on a missing file, fails the redirect, making the command substitution itself
  non-zero, which under `set -e` kills the script before ever reaching the documented `(none —
  Claude solo)` fallback right below it (the current sole caller, `run-panel.sh`, always creates
  the file first via `: > "$RESP"`, so the real code path is safe — this is a latent asymmetry
  only exposed on a standalone call) — appended `|| true` so the fallback actually fires,
  confirmed by direct reproduction both before and after the fix. (3) `docs/ci-pr-review.md` was
  left with a `<runner-label>` placeholder for the runner label, inconsistent with the runbook,
  which uses the actual label — confirmed the label is already exposed as-is in `runs-on:` in
  `.github/workflows/pr-review.yml`, so there's no sanitization reason not to, and updated it to
  match the runbook. **Not adopted**: `lib.sh`'s reliance on GNU-sed-only syntax (the `I` flag,
  `-i`) has no CI impact since the self-hosted runner is fixed to Linux, and is only a macOS
  local-dev convenience issue — deferred this round (low payoff relative to rewrite cost). New
  tests: `test-synthesize.sh` (f) (that the documented fallback actually reaches the chair
  prompt when responded.txt is absent) — full suite 599 passed (+2), the same 17 pre-existing unrelated failures remain.

- **Round 13 fix (after commit 7c8159d, PASSED — 0 CRITICAL/MAJOR, 4 MINOR)**: adopted 2. (1) a
  finding that `run-panel.sh`'s `$SLOT` (="$WORK/slot") is still referenced as-is inside the
  Kiro cell's `cd "$KIRO_CWD"` subshell, so if `$WORK` is a relative path, that redirect resolves
  again relative to `$KIRO_CWD`, writing to the wrong place — actually reproduced via
  `cd "$BASE" && "$SCRIPT" diff.txt lenses relwork`: before the fix, the Kiro cell's output was
  written not to `relwork/slot/...` but to `relwork/kiro-cwd/relwork/slot/...` (a nested, wrong
  path). Added `WORK="$(realpath "$WORK")"` after the empty-string guard, the same way `DIFF` is
  handled (first running `mkdir -p "$WORK"` so realpath always succeeds even before the target
  exists) — directly verified the bug's reproduction and the fix's correctness by running both
  before and after. Confirmed `LENSES_DIR` needs no equivalent handling (the `cat "$lens_file"`
  that reads that value runs in the main process, before any `cd`, so it's always safe relative
  to the original cwd). (2) `tests/run-all.sh`'s `PATTERN="${1:-tests/**/*.sh}"` was defined but
  the actual for-loop hardcoded 3 directories, completely ignoring the argument — the scaffolding
  template in `plugins/project-init` (`references/tests-templates.md`) already documents `bash
  tests/run-all.sh [test-file-pattern]` (e.g. `... hooks`) as a contract, but this repo's own
  `run-all.sh` had lost that contract — actually wired `PATTERN`, when given, as a substring
  filter against file paths (with no argument, it still runs everything as before; all existing
  call sites pass no argument, so there's no regression). **Not adopted**: `test-lib.sh` sourcing
  `lib.sh` and thereby injecting `set -uo pipefail` into the harness shell (currently harmless
  since `run-all.sh` already uses the same options; this only matters in a hypothetical scenario
  where the harness options later diverge) was not adopted; ADR-011's own suggestion to split off
  its revision log is a documentation-structure decision, pending user confirmation. New tests:
  `test-run-panel.sh` (l) (that a relative workdir is absolutized even in the Kiro cell — directly
  reproduced the failure with the pre-fix version, then restored and confirmed) — full suite 600 passed (+1), the same 17 pre-existing unrelated failures remain (also separately confirmed the new filter with `bash tests/run-all.sh hooks`).

- **Round 14 fix (after commit 665809e, PASSED — 0 CRITICAL/MAJOR, 4 MINOR)**: adopted 2,
  reconfirmed 1 as an already-known pending documentation-structure decision, did not adopt 1.
  (1) a finding that `run-panel.sh`'s coverage-floor `row_count=$(grep -c ... "$RESP"
  2>/dev/null)` can produce a truly empty string when `$RESP` is missing/unreadable, and
  `[ "" -eq 0 ]` (without `set -e`) silently swallows this as false, dropping the degraded
  warning itself — the same class of asymmetry caught in round 12 around `responded.txt`'s
  absence. Directly tested: against a directory target, GNU grep still prints "0" to stdout
  (unrelated to the error), so this path doesn't reproduce that way, but confirmed that when the
  file is **entirely absent**, stdout is truly empty — fixed to `${row_count:-0}`, safe in both
  cases. However, confirmed that this latent path is unreachable via any end-to-end regression
  test through the actual script flow, since run-panel.sh itself unconditionally creates the file
  via `: > "$RESP"` at script start, and there's no external touchpoint to delete it in between
  (unlike synthesize.sh's RESP, this isn't a structure that can be re-invoked as a separate
  process) — verified the fix via manual bash reproduction, but there is no automated test
  (recorded as a known coverage limitation). (2) the workflow's `COMMON` lens-prompt text says
  "the diff is provided via stdin or an inline marker," but in fact **no lens-prompt recipient**
  receives it that way — confirmed via code review that the inline marker (`=== DIFF UNDER
  REVIEW ===`) is exclusive to `synthesize.sh`'s chair prompt and unrelated to the lens prompts.
  Codex receives it via stdin, and Kiro via an appended fs_read path instruction, so the
  inaccurate wording could lead a weaker model (kimi/glm) to mistakenly conclude "the diff never
  arrived" — instead of fully branching by cell type (which would require a workflow structure
  change), neutralized `COMMON` itself to accurately state "whichever of stdin or file-read
  instructions applies is the diff under review," confirmed via local simulation of heredoc
  rendering. **Not adopted**: splitting off ADR-011's revision log (repeatedly raised in rounds
  11–13) is still pending user confirmation — raised again this round, but a documentation
  structure decision is not handled arbitrarily within a round; the comment header's one-line
  exposure of the 16 tags (cosmetic readability) was deferred as not a functional defect. No new
  tests (reason stated above) — full suite remains at 600 passed, the same 17 pre-existing unrelated failures remain.

- **Round 15 fix (after commit ecdf6ba, PASSED — panel: codex responded 1/1, Kiro did not
  respond)**: codex raised 1 CRITICAL ("Kiro fs_read absolute-path read → leaks to the external
  service before scrub_secrets") and 1 MAJOR ("continues even if `mkdir -p`/`realpath` fails"),
  and the chair cross-checked both against the diff and the actual repo and **downgraded both to
  MINOR** — the CRITICAL item was simply reconfirmed, on the grounds that this exact residual
  risk is already documented and accepted in the ADR body itself (the above Decision, the
  "explicit accepted risk" paragraph) and in `docs/ci-pr-review.md`, and that the
  `head.repo.full_name == github.repository` gate already narrows the threat model to a
  write-permission collaborator (no changes made — reconfirmation of an already-adopted
  decision). For the MAJOR item, cross-checking against the diff showed the claim of "root-level
  destructive cleanup" doesn't actually hold (the only real code path is a non-destructive `rm
  -f`/`rm -rf` on a path that doesn't exist, and the end state is fail-closed via total cell
  failure → coverage collapse → forced FAIL), but a real latent hardening gap does exist —
  `mkdir -p "$WORK"`/`WORK="$(realpath "$WORK")"` have no explicit failure handling — consistent
  with the "operations that can produce a destructive path must handle failure explicitly"
  principle already established in rounds 8–9, so `|| exit 1` was added. Also adopted 2 MINOR
  items raised by codex and CONFIRMED by the chair in the same round: `synthesize.sh`'s
  truncation-marker text, "...see full output in CI logs...", is false — a successful cell's
  stdout (.md) is never printed anywhere in the CI logs (confirmed via code review that only a
  skipped cell's stderr tail ends up in the logs) — fixed to something like "full output not
  retained" so it no longer points to a recovery path that doesn't exist. The `⚠️` in
  `docs/ci-pr-review-runbook.md` conflicted with the "no emoji in formal docs" convention (real,
  e.g. in AGENTS.md/`docs/CLAUDE.md`) — accounting for the fact that it's a literal quotation of
  the banner string `synthesize.sh` actually outputs, wrapped only that line in a code span to
  reconcile it with the convention. **Not adopted**: a process/container FS sandbox (the
  structural fix for the CRITICAL item) is already recorded in the ADR as an operational
  follow-up outside this repository's development environment, and is out of this PR's scope.
  **Also handled this round**: the repeatedly-raised (rounds 11–14) split of ADR-011's revision
  log — `AskUserQuestion` received no response on either attempt (tool-stream error), so this
  proceeded without user confirmation, applying the recommended option by default ("Decision
  holds only the decision; the round-by-round log is split into an appendix"), creating this
  appendix. The Decision/Consequences body only had the round-log paragraphs removed — the
  wording itself is preserved as-is (not edited, only relocated) — applying this document's own
  convention of "never post-edit an already-accepted rationale" to this restructuring as well.

- **Round 16 fix (after commit 2b336a9, PASSED — 0 CRITICAL/MAJOR, 4 MINOR)**: this round, the
  first review after the appendix split, confirmed the appendix's existence itself via the diff,
  and stated no new defects were found in a full cross-check of the fail-closed contract, state
  resets, and scrub defenses. Adopted 2 of the 4 MINOR items, confirmed 2 as needing no action.
  (1) the workflow's `timeout-minutes: 50` estimate comment's "~15m for matrix retries" assumed
  the `PANEL_RETRIES=3` default, but that assumption wasn't stated in the comment, so raising this
  env var would silently invalidate the estimate — adopted by adding a line noting "based on
  PANEL_RETRIES=3" to the comment. (2) `docs/ci-pr-review-runbook.md`'s statement that "there is
  no separate detection for the case where a single lens is simultaneously empty across all
  models" matches the code, but this item was missing from the Decision's operational
  follow-up list above, hurting traceability — adopted by appending this item to the operational-
  follow-up sentence under "Coverage floor" (the existing sentence was left untouched, only a new
  sentence was appended — not an edit to the existing rationale). **Confirmed as needing no
  action**: (3) a finding that the test fixtures' canonical credential examples (`AKIA...`, the
  official AWS example `wJalrXUtnFEMI/...EXAMPLEKEY`, `ghp_...`) could trip this repo's
  `secret-scan.sh` PreToolUse commit hook — directly confirmed via `find` that
  `.claude/hooks/secret-scan.sh` itself **does not exist** in this checkout (the absence of 4
  hooks-related files is already known as one of this suite's 17 pre-existing unrelated
  failures) — no action needed since there is currently no hook that could actually block a
  commit (the hook's own absence is a separate, pre-existing gap outside this PR's scope). (4)
  `kiro_env()`'s unquoted conditional expansion (`${KIRO_API_KEY:+...}`) — the review itself
  judged this "fine as-is" and requested no action. No new tests (both were doc/comment changes)
  — full suite remains at 600 passed, the same 17 pre-existing unrelated failures remain (also
  observed, in the same round, an unrelated flaky test
  (`remarp-format-guide ... [summary] note layer`) intermittently appearing as an 18th failure —
  confirmed it's related to reactive-presentation and unrelated to files touched by this PR, not
  treated as a separate issue).

- **Round 17 fix (after commit 818b21d, PASSED — 0 CRITICAL/MAJOR, 3 MINOR)**: this round was
  mostly reconfirmation (`try_panel`'s stdin remains valid via realpath absolutization even
  after `cd`, the non-final `&&` list is safe, L1 pipefail is normal), but caught 1 new actual
  correctness defect. (1) `synthesize.sh`'s severe override, `sed -i '/^VERDICT:/d' "$OUT"`,
  deletes every line in the **entire** file matching that pattern — directly reproduced and
  confirmed this really does cause information loss if the chair's body prose explains/quotes a
  rule using a line starting with "VERDICT: ..." (the fail direction itself isn't compromised —
  the forced FAIL line is always appended after). Replaced with `tac "$OUT" | sed
  '0,/^VERDICT:/d' | tac`, which deletes **only the last matching line** — directly confirmed the
  regression test failed with the pre-fix version, then restored it and reconfirmed it passes.
  (2) case (l) in `test-run-panel.sh`'s bare `( cd "$BASE" && "$SCRIPT" ... )` call was
  inconsistent with the convention, stated at the top of the file itself, that "every non-zero
  exit path is wrapped in an if" — aligned it to `if ! ( ... ); then fail ...; fi`, matching the
  pattern used by (a)/(b)/(j) and other existing cases. (3) a finding that `tests/run-all.sh`'s
  `PATTERN` uses substring matching, so a short argument could match more broadly than intended
  — since this design matches project-init's documented template contract, behavior was left
  unchanged, and a one-line comment was added noting this characteristic and how to work around
  it (use a more specific directory/file-name fragment). New tests: `test-synthesize.sh` (g)
  (that the severe override preserves an explanatory prose line starting with "VERDICT:" while
  deleting only the chair's actual final verdict line — directly reproduced the failure with the
  pre-fix version, then restored and confirmed) — full suite 602 passed (+2), the same 17 pre-existing unrelated failures remain.

- **Round 18 fix (after commit 70c8618, PASSED — 0 CRITICAL/MAJOR, 1 MINOR)**: caught a new
  regression introduced by round 17's own fix. `tac "$OUT" | sed '0,/^VERDICT:/d' | tac` — GNU
  sed's `0,/re/d` range, if the pattern **never matches at all**, never satisfies its end
  condition, so it extends to EOF and deletes the **entire** input. Reachable path: a corner case
  where both the primary and fallback chair degrade to "non-empty, but with no `^VERDICT:` line
  at all" (the `[ ! -s "$OUT" ]` empty-file guard cannot catch this case), while
  `coverage-severe.flag` is simultaneously set — the result would leave only the banner and the
  forced `VERDICT: FAIL`, with the chair's entire body diagnosis erased (the fail direction itself
  is not compromised — the forced-FAIL line is always appended, so this is not a gate defect).
  Directly reproduced: running that exact pipeline against a 3-line input with no match produced
  a completely empty output string. Fixed by wrapping it in `grep -q '^VERDICT:' "$OUT"` so the
  deletion only runs when a match actually exists — reproduced both the match and no-match
  scenarios (for no-match, confirmed the failure with the pre-fix version → restored and
  reconfirmed it passes). New tests: `test-synthesize.sh` (h) (that the severe override preserves
  the body even for a degraded chair response with no VERDICT line at all) — full suite total
  619→621 (+2, matching the count of new tests). The passed/failed split numbers (605/16 vs
  606/15, etc.) fluctuated across repeated runs — but the actual list of failing tests (17 items
  related to the 4 missing hooks files, headline, design-tokens, and accent1) was identical every
  time — this is a known counting flake of the harness itself, already observed in prior rounds, and unrelated to this PR's diff.

- **Round 19 fix (after commit c6ca4f2, PASSED — 0 CRITICAL/MAJOR, 2 new MINOR + 1 existing
  reconfirmation)**: adopted 1 new MINOR. `precheck.sh` dies immediately under `set -euo
  pipefail` if an **infrastructure** step like `git fetch`/`archive` fails, before any validator
  ever runs, but the workflow's "Write L1 failure as review" step comments on that case exactly
  the same way as a "manifest/version-consistency failure" — confirmed via code review that this
  really could mislead a PR author into suspecting their own unrelated manifest (the fail-closed
  direction itself is correct — this wasn't a blocking issue, just misattribution). Fixed by
  distinguishing the two paths via whether `test-plugins.py`'s validator-run-only banner string
  ("Plugin Validation Suite") appears, so only the header branches differently (VERDICT: FAIL is
  identical on both paths — only the message becomes accurate). Since this is a workflow YAML
  conditional branch rather than a script change, it can't be exercised by pr-review unit tests
  — locally simulated both the banner-present and banner-absent inputs in bash to confirm the
  branch resolves correctly. The 1 new MINOR item was confirmed as needing no action: the severe
  override's `TAC_TMP="$(...)"` in `synthesize.sh` collapsing consecutive trailing blank lines in
  the body is pure lossless cosmetic — not adopted. The existing MINOR (reliance on GNU
  coreutils/sed-only tools) is a reconfirmation of an item already deferred in round 12 as
  "runner fixed to Linux," so it wasn't re-judged. The full suite remains at 621 total since
  scripts are unchanged, the same 17 pre-existing unrelated failures remain too.

- **Round 20 fix (after commit b006eec, PASSED — 0 CRITICAL/MAJOR, 5 MINOR, 4 of which are
  reconfirmations of already-known items)**: adopted the new MINOR-5. Round 19's "distinguish
  infra/manifest failure via the test-plugins.py banner string presence" heuristic has a finding
  that, if that validator dies before it even prints the banner (e.g. at the argparse/
  `Path(args.root).resolve()` stage), an actual validator failure could still be misclassified as
  infrastructure (no gate impact — both paths still give VERDICT: FAIL; this is a message-accuracy
  issue) — directly cross-checked `test-plugins.py`'s banner-printing code (inside `main()`, after
  argparse) and confirmed this corner theoretically exists. Instead of relying on the banner
  string, replaced it so that `precheck.sh` touches a dedicated sentinel,
  `touch "$WORK/l1-validators-started"`, right **before** calling python3 (i.e. only after the
  git fetch/archive/tar infrastructure steps have all succeeded), and the workflow now branches
  on that sentinel's presence — since this is completely independent of the validator's own print
  ordering, that corner case is structurally eliminated. New tests: `test-precheck.sh` (m) (that
  the sentinel is never created on a fetch-failure path, and is always created on a normal path
  that reaches the validators) — full suite total 621→624 (+3, matching the new test count), the
  same 17 pre-existing unrelated failures remain. The remaining 4 MINOR items (kiro_env's
  unquoted expansion, reliance on GNU-only tools, heredoc indentation, the lens-column blind
  spot) are all reconfirmations of items already judged in rounds 16–19, so they weren't
  re-judged — the review itself also suggested "keep the Decision body frozen post-appendix-
  split," a convention this follows as-is.

## Verification (2026-07-05, restructuring pass)

At the point this appendix was split off, the full suite was re-run to confirm that a purely
documentation-level restructuring had no effect on script behavior: `bash tests/run-all.sh` →
600 passed, the same 17 pre-existing unrelated failures remain (no script files changed — only
the `.md` was restructured).
