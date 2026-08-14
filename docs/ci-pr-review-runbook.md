# Runbook: Verifying PR Review Panel behavior

Opening a PR automatically runs the two-stage gate on the self-hosted runner
(`oh-my-cloud-skills-claude-arm`): L1 (deterministic) → 3-model panel (each model reviews
the full diff with no scope restriction, ADR-016).

## Normal-operation checklist
1. **On L1 failure**: only an "L1 pre-check (manifest/version consistency) failed" block
   shows up in the PR comment and the AI panel is never invoked (zero cost) — the cause
   is right there in the comment body's `test-plugins.py`/`test-codex-plugins.py` output
   (dangling reference/version mismatch/JSON error/`.codex-plugin` manifest error).
2. **On L1 pass**: it's normal to see up to 3 model tags — `codex`, `kiro-opus`,
   `kiro-gpt` — on the PR comment's `_Cells (model):_` line (some cells may be
   intermittently skipped due to rate limiting/quota; `kiro-glm` is disabled by default
   due to its false-positive rate — see ADR-017). If one model doesn't respond (e.g. a
   kiro-cli flag got invalidated), a `⚠️ Coverage degraded` banner shows at the top of the
   review (this is the exact banner string `synthesize.sh` actually outputs). If one or
   fewer vendors survive, a `🛑 Coverage collapsed` banner shows (ADR-016), but it does
   not force the VERDICT — the chair's judgment stands as-is. **Antigravity (`agy`) is
   not in the panel** (ADR-010 — cannot authenticate headlessly).
3. **`chair_error`**: if the chair fails to produce a usable VERDICT on both attempts
   (primary + fallback), the comment's Status shows `ERROR` (not BLOCKED) — this is not
   a review finding but a CI infrastructure problem, so a re-run is all that's needed;
   there is no content to fix.
4. The gate decision is based on the last `VERDICT: PASS|FAIL` match (fail-closed; L1
   failure/chair_error also count as fail).

## Region/model (unified on us-east-1)
- Claude chair: `us.anthropic.claude-fable-5` (US geo, on-demand) · endpoint/region
  `us-east-1`
  - The primary attempt is granted `Read Grep Glob` and must produce a VERDICT within
    `CHAIR_TIMEOUT` (default **450 seconds**). If it fails to (connection
    refused/hang/empty response/unusable VERDICT), it retries once with
    `CHAIR_FALLBACK_MODEL` (default `us.anthropic.claude-opus-5`), but **this time with
    no file tools granted at all** (`CHAIR_FALLBACK_TIMEOUT`, default **300 seconds**) —
    the diff+panel reviews are already on stdin, so this attempt is self-contained, and
    with no tools it cannot crawl the repo tree (ADR-016 — the old single 600-second
    attempt combined the instruction "Read CLAUDE.md/AGENTS.md" with granting file tools,
    which exhausted exactly that timeout on large diffs, #141/#146). To tune this, set
    `CHAIR_TIMEOUT`/`CHAIR_FALLBACK_TIMEOUT`/`CHAIR_FALLBACK_MODEL` in the workflow's
    `env`.
- codex: `openai.gpt-5.6-sol` (bedrock-mantle, In-Region us-east-1; the region is
  determined by the image's `~/.codex/config.toml`) — reviews the full diff once.
  (`gpt-5.5`→`openai.gpt-5.6-sol` deprecation replacement — ADR-014.)
- kiro-cli: `claude-opus-5`/`gpt-5.6-terra`, each reviewing the full diff once — 2 calls
  total under the default active roster (matrix membership is a config value —
  `panel_config.py`, see the "Configuration" section of `docs/ci-pr-review.md`).
  `glm-5` (`kiro-glm`) is disabled by default due to its false-positive rate — following
  the AWS-Demo-Platform ADR-015 precedent, see this repo's ADR-017. (`kimi-k2.5` was
  replaced after 2/2 production coverage-degradation incidents + 7 unsupported findings.
  **`--v3` is not used** — `kiro-cli --v3 chat ... --model gpt-5.5` (the model name used
  at the time of this reproduction; replaced by `gpt-5.6-terra` under ADR-014) is listed
  by `--list-models` but the actual call is rejected with `INVALID_MODEL_ID` (HTTP 400) —
  this isn't a problem with the model itself, but because **the separate backend that
  `--v3` routes to** has a narrower model catalog. `kiro-cli chat` without `--v3` (with
  the remaining flags at the time being `--mode default --trust-tools=fs_read
  --no-interactive --wrap never` — `--trust-tools=fs_read` was changed to
  `--trust-tools=` (no tools granted) under ADR-013, below) was confirmed to respond
  normally for all 5 models including gpt-5.5. `--v3` was originally introduced to fix a
  stdin-ignoring/`fs_read` tool-name bug unrelated to model support (commit `c5b19c7`) —
  since both bugs are already bypassed by the argv-based delivery, they don't recur even
  without `--v3`. See ADR-012 for the full replacement background/rationale.)
- **Kiro diff delivery (ADR-013)**: Kiro cells use `--trust-tools=` (no tools granted,
  diff embedded as capped text directly in argv, `KIRO_DIFF_CAP` default 100000B) instead
  of `--trust-tools=fs_read` (diff referenced by file path) — this structurally closes a
  CRITICAL residual risk where trusting `fs_read` on an untrusted diff could let
  diff-injection induce an absolute-path read, exposing credentials via a public PR
  comment (discovered during the claude-code-usage-dashboard PR #4 review). When
  debugging: if a Kiro cell comes back empty, first check whether the diff was truncated
  by exceeding `KIRO_DIFF_CAP` (see `$WORK/kiro-diff-truncated.flag` and the "✂️ Kiro diff
  truncated" banner in the review body) rather than assuming `--trust-tools=` was
  mistyped/invalidated.
- AWS auth: EKS Pod Identity (ci-runner role) SigV4

## When L1 fails and blocks the PR
- Read the `test-plugins.py`/`test-codex-plugins.py` output attached to the comment
  directly — the error message points to the exact file path/field (e.g. dangling agent
  reference, plugin.json↔marketplace.json version mismatch, `.codex-plugin/plugin.json`
  schema error).
- Local reproduction: `python3 scripts/test-plugins.py` and `python3
  scripts/test-codex-plugins.py` (both against the current checkout by default), or
  `--root <arbitrary tree>` to target a specific tree.
- If L1 itself (fetch/archive) fails due to an infrastructure problem (e.g. a `git fetch`
  error), the cause shows up directly in the "L1 pre-check" step output in the runner log
  — since this is fail-closed, the gate is FAIL in this case too.

## Diagnosing a skipped panel cell
- Check the cause in the `[<model>] skipped; stderr` block in the runner log (404 Engine
  not found = model/region mismatch, credentials error = missing Pod Identity, etc.).
- Even if one model drops out entirely (e.g. the kiro-cli binary is missing), the other 2
  models still independently review the full diff — there's no single point of failure
  (**under the default active roster** — in a codex-only configuration where the
  "sensitive-diff policy" has turned off both Kiro cells, codex is the only vendor left,
  so this invariant no longer holds. See below and the "Configuration" section of
  `docs/ci-pr-review.md` for how the coverage floor is handled in that configuration).
- If a specific model is not simply missing its binary but is **persistently flaky**
  (continuously degraded, not just intermittent non-response), remove it in the following
  two steps — do not read them in reverse order: (1) **Local preview** — running
  `python3 scripts/pr-review/panel_config.py set <cell> enabled false --root .` in a local
  clone writes to `.claude/pr-review.local.json` (a gitignored local override file), and
  you can immediately confirm the result with `show` — **this file itself has no effect
  on CI**. (2) **Actual CI application** — you must **manually copy** the value confirmed
  in (1) into `scripts/pr-review/pr-review.defaults.json`, **commit it, and merge** for it
  to actually take effect starting with PRs after `main`. **Simply placing the (1)
  override file in the CI workspace and re-running does NOT work** (checkout's default
  clean behavior wipes gitignored files every run, and this doesn't apply to the review
  of the PR carrying the change itself either, due to `pull_request_target`'s base-ref
  checkout — for the detailed constraints and an exceptional workaround, see "How this is
  actually applied in CI" in the "Configuration" section of `docs/ci-pr-review.md`).
  Use `python3 scripts/pr-review/panel_config.py show --root .` to check the current
  (local) effective configuration.

## When a panel cell's judgment quality crosses the threshold (ADR-015)

The `Panel cell judgment quality` table in `docs/pr-review/review-memory.md` is
accumulated by the `/co-agent:pr-autofix` host parsing the chair's
`PANEL-QUALITY: <cell>=<unsupported>/<total>` line. If a cell has
**`unsupported >= 5` and `unsupported/total >= 0.5`**, pr-autofix outputs an exclusion
**recommendation**. **There is no automatic enforcement** — a human follows the procedure
below (the same path as the `kimi-k2.5` exclusion in ADR-012).

1. **Verify the evidence** — don't take the table's numbers at face value; look at the
   underlying evidence. Sample recent PR review comments to confirm whether that cell's
   dismissed findings were actually unsupported (not backed by the diff), or whether the
   chair misclassified genuine issues as false positives. The table is a **signal**, not
   the judgment itself. (Also distinguish this from cases where there simply was no
   response due to coverage degradation — that's not a judgment-quality problem, it's the
   "Diagnosing a skipped panel cell" item above.)
2. **Write an ADR** — since exclusion is a roster change, record the decision (following
   the ADR-012 precedent of citing numbers like "7 dismissed findings vs. 0"). The memory
   table exists precisely so this evidence doesn't remain only in chat history.
3. **Apply it for real** — after locally previewing with `python3
   scripts/pr-review/panel_config.py set <cell> enabled false --root .` (that file is
   gitignored, so it has no effect on CI), **manually copy** the confirmed value into
   `scripts/pr-review/pr-review.defaults.json`, **commit and merge it** — exactly the
   same path as step 2 of "If a specific model is ... persistently flaky" above. It takes
   effect starting with PRs after `main`.
4. **Clean up the table** — delete the excluded cell's row from the memory file (incorrect
   or invalid entries should be removed immediately on principle).

> Why automatic disablement was not adopted: if the surviving vendor count drops to one or
> fewer, cross-checking itself stops functioning, and the system could quietly stabilize
> in that state without human intervention (ADR-015 rejected alternative 3). (As of
> 2026-07, this state used to force a severe banner + fail-closed — ADR-016 changed the
> enforcement to banner-only, but this doesn't affect this section's conclusion: exclusion
> is still a human judgment call that gets committed.)
</content>
</invoke>
