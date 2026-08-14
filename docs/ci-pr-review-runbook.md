# Runbook: Verifying PR Review Panel Behavior

Opening a PR automatically triggers a two-stage gate on a self-hosted runner
(`oh-my-cloud-skills-claude-arm`): L1 (deterministic) → 4-model panel (each model reviews
the entire diff with no scope restriction, ADR-016).

## Normal-behavior checks
1. **On L1 failure**: only an "L1 pre-check (manifest/version consistency) failed" block
   appears in the PR comment, and the AI panel is not invoked (zero cost) — the cause
   appears directly in the comment body, in the `test-plugins.py`/`test-codex-plugins.py`
   output (dangling reference/version mismatch/JSON error/`.codex-plugin` manifest error).
2. **On L1 pass**: it's normal to see up to 4 model tags — `codex`, `kiro-opus`,
   `kiro-gpt`, `kiro-glm` — on the `_Cells (model):_` line in the PR comment (some cells
   may be intermittently skipped due to rate limits/quota). If one model doesn't respond
   (e.g. a kiro-cli flag got invalidated), a `⚠️ Coverage degraded` banner appears at the
   top of the review (this is the exact banner string `synthesize.sh` actually emits). If
   one or fewer vendors survive, a `🛑 Coverage collapsed` banner appears (ADR-016), but
   it does not force the VERDICT — the chair's judgment stands as-is. **Antigravity
   (`agy`) is not in the panel** (ADR-010 — cannot authenticate headlessly).
3. **`chair_error`**: if the chair fails to produce a usable VERDICT on both attempts
   (primary + fallback), the comment Status shows `ERROR` (not BLOCKED) — this is a CI
   infrastructure problem, not a review finding, so simply re-running is enough; there's
   nothing in the content to fix.
4. The gate decision is based on the last `VERDICT: PASS|FAIL` match (fail-closed; an L1
   failure or chair_error also fails).

## Region/model (unified on us-east-1)
- Claude chair: `us.anthropic.claude-fable-5` (US geo, on-demand) · endpoint/region
  `us-east-1`
  - The first attempt has `Read Grep Glob` and must produce a VERDICT within
    `CHAIR_TIMEOUT` (default **300 seconds**). If it can't (connection refused/hang/empty
    response/an unusable VERDICT), it retries once against `CHAIR_FALLBACK_MODEL`
    (default `us.anthropic.claude-opus-5`), but **this time with no file tools granted at
    all** (`CHAIR_FALLBACK_TIMEOUT`, default **120 seconds**) — this is self-contained
    since the diff+panel reviews are already on stdin, and with no tools it can't crawl
    the repo tree (ADR-016 — the old single 600-second attempt combined an instruction to
    "Read CLAUDE.md/AGENTS.md" with file-tool access, which exhausted that timeout exactly
    on large diffs, #141/#146). To tune this, set `CHAIR_TIMEOUT`/
    `CHAIR_FALLBACK_TIMEOUT`/`CHAIR_FALLBACK_MODEL` in the workflow `env`.
- codex: `openai.gpt-5.6-sol` (bedrock-mantle, In-Region us-east-1; the image's
  `~/.codex/config.toml` region decides this) — reviews the full diff once. (`gpt-5.5` →
  `openai.gpt-5.6-sol` deprecation replacement — ADR-014.)
- kiro-cli: `claude-opus-4.8`/`gpt-5.6-terra`/`glm-5` each review the full diff once, 3
  calls total under the default active roster (matrix membership is a config value —
  `panel_config.py`, see the "Configuration" section in `docs/ci-pr-review.md`).
  (`kimi-k2.5` was replaced after 2/2 production coverage degradations + 7 unsupported
  findings. **`--v3` is not used** — `kiro-cli --v3 chat ... --model gpt-5.5` (the old
  model name — the name in use at the time of the reproduction below; replaced by
  ADR-014 with `gpt-5.6-terra`) is listed under `--list-models` but the actual call is
  rejected with `INVALID_MODEL_ID` (HTTP 400) — this isn't a problem with the model
  itself, but because **the separate backend that the `--v3` flag routes to** has a
  narrower model catalog. Confirmed that `kiro-cli chat` without `--v3` (with the rest of
  the flags at the time being `--mode default --trust-tools=fs_read --no-interactive
  --wrap never` — `--trust-tools=fs_read` was later changed to `--trust-tools=` (no tools
  granted) by ADR-013, below) responds normally across all 5 models including gpt-5.5.
  `--v3` was originally introduced to fix a stdin-ignored/`fs_read` tool-name bug unrelated
  to model support (commit `c5b19c7`) — since both bugs are already worked around via the
  argv delivery method, they don't recur without `--v3`. See ADR-012 for the full
  background/evidence behind the replacement.)
- **Kiro diff delivery (ADR-013)**: Kiro cells use `--trust-tools=` (no tools granted, with
  the diff embedded directly in argv as text capped by `KIRO_DIFF_CAP`, default 100000B)
  instead of `--trust-tools=fs_read` (referencing the diff by file path) — this
  structurally closes a CRITICAL residual risk where trusting `fs_read` with an untrusted
  diff could let diff-injection induce an absolute-path read, exposing credentials via a
  public PR comment (discovered during review of claude-code-usage-dashboard PR #4). When
  debugging: if a Kiro cell comes back empty, first check whether the diff was truncated
  by exceeding `KIRO_DIFF_CAP` — via `$WORK/kiro-diff-truncated.flag` (and the
  "✂️ Kiro diff truncated" banner in the review body) — rather than assuming a
  `--trust-tools=` typo/invalidation.
- AWS auth: EKS Pod Identity (ci-runner role) SigV4

## When L1 fails
- Read the `test-plugins.py`/`test-codex-plugins.py` output attached to the comment
  directly — the error message points to the exact file path/field (e.g. dangling agent
  reference, plugin.json↔marketplace.json version mismatch, `.codex-plugin/plugin.json`
  schema error).
- Local reproduction: `python3 scripts/test-plugins.py` and
  `python3 scripts/test-codex-plugins.py` (both against the current checkout by default),
  or target a specific tree with `--root <arbitrary tree>`.
- If L1 itself (fetch/archive) fails due to an infrastructure problem (e.g. a `git fetch`
  error), the cause is printed directly in the "L1 pre-check" step output in the runner
  log — since this is fail-closed, the gate also FAILs in this case.

## Diagnosing an empty (skipped) panel cell
- Check the cause in the `[<model>] skipped; stderr` block in the runner log (404 Engine
  not found = model/region mismatch, credentials error = missing Pod Identity, etc.).
- Even if one model drops out entirely (e.g. the kiro-cli binary is missing), the other 3
  models still independently review the full diff — there's no single point of failure
  (**under the default active roster** — in a codex-only configuration where all 3 Kiro
  cells have been disabled via the "sensitive-diff policy," codex is the sole vendor, so
  this invariant doesn't hold. See below and the "Configuration" section of
  `docs/ci-pr-review.md` for coverage-floor handling in that configuration).
- If a specific model isn't missing a binary but is **persistently flaky** (sustained
  degradation, not intermittent non-response), remove it in the following two steps —
  don't read them out of order: (1) **local preview** — running
  `python3 scripts/pr-review/panel_config.py set <cell> enabled false --root .` in a local
  clone writes to `.claude/pr-review.local.json` (the gitignored local override file), and
  you can immediately check the result with `show` — **this file by itself has no effect
  on CI**. (2) **actually applying it in CI** — you must **manually copy** the value
  confirmed in (1) into `scripts/pr-review/pr-review.defaults.json`, **commit, and merge**
  it before it actually takes effect starting with PRs after that merge into `main`.
  **Leaving only the override file from (1) in the CI workspace and re-running does not
  work** (checkout's default clean wipes gitignored files on every run, and this doesn't
  apply to the review of the PR carrying this change either, due to `pull_request_target`'s
  base-ref checkout — for the detailed constraints and the exception workaround, see "How
  this actually takes effect in CI" in the "Configuration" section of
  `docs/ci-pr-review.md`).
  Use `python3 scripts/pr-review/panel_config.py show --root .` to check the current
  (local) effective configuration.

## When panel-cell judgment quality crosses the threshold (ADR-015)

The `Panel-cell judgment quality` table in `docs/pr-review/review-memory.md` is
accumulated by the `/co-agent:pr-autofix` host parsing the chair's
`PANEL-QUALITY: <cell>=<unsupported>/<total>` line. If a cell has both
**`unsupported >= 5`** and **`unsupported/total >= 0.5`**, pr-autofix prints an exclusion
**recommendation**. **There is no automatic application** — a human follows the procedure
below (the same path used for excluding `kimi-k2.5` in ADR-012).

1. **Verify the evidence** — don't just trust the table's numbers; look at the underlying
   basis. Sample recent PR review comments to check whether that cell's dismissed findings
   were genuinely unsupported (not backed by the diff), or were actually real issues that
   the chair mis-classified as false positives. The table is a **signal**, not a
   judgment. (Also distinguish whether it was actually just non-response due to coverage
   degradation — that's not a judgment-quality problem, it's the "Diagnosing an empty
   panel cell" item above.)
2. **Write an ADR** — an exclusion is a roster change, so record the decision (ADR-012 is
   the precedent — cite figures like "7 dismissed findings vs 0" as evidence). The reason
   the memory table exists is precisely so this evidence doesn't only live in chat history.
3. **Apply it for real** — preview locally with
   `python3 scripts/pr-review/panel_config.py set <cell> enabled false --root .` (that file
   is gitignored and has no effect on CI), then **manually copy** the confirmed value into
   `scripts/pr-review/pr-review.defaults.json` and **commit + merge** — exactly the same
   path as step 2 in "if a specific model keeps being flaky" above. It takes effect
   starting with PRs after that merge into `main`.
4. **Clean up the table** — delete the excluded cell's row from the memory file (the rule
   is to delete wrong/invalid entries immediately).

> Why automatic disabling was not adopted: once one or fewer vendors survive,
> cross-verification itself stops functioning, and the system could quietly stabilize in
> that state without any human intervention (ADR-015's rejected alternative 3). (As of
> 2026-07 this state forced a severe banner + fail-closed — ADR-016 changed the
> enforcement to banner-only, but this doesn't affect this section's conclusion: exclusion
> is still judged and committed by a human.)
