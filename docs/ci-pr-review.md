# CI: Multi-AI PR Review — L1 Deterministic Gate + 4-Model Panel

PRs in this repo go through a two-stage gate on a self-hosted runner
(`oh-my-cloud-skills-claude-arm`): **L1** (manifest/version consistency — deterministic
script, no AI calls) → **4-model panel** (each model reviews the full diff with no scope
restriction → Claude chair synthesizes).
(design: `docs/superpowers/specs/2026-07-05-pr-review-hybrid-lens-design.md`, ADR-011;
the lens×model matrix was later reversed by ADR-016 — 4 models × 4 lenses = 16 cells
inflated the chair's input 4x and exhausted the 600s timeout (measured on #141/#146: both
models hit exactly 600s), and the lens checklist was unnecessary for frontier models.)

## L1 — deterministic pre-check (before any AI call, zero cost)
- `scripts/pr-review/precheck.sh` extracts the PR head's file tree via `git archive` as
  **data only** (no execution) → validates it from a base (trusted) checkout using
  `scripts/test-plugins.py --root <extracted tree>` **and
  `scripts/test-codex-plugins.py --root <extracted tree>`** (both must pass for L1 to pass).
- What it validates: `plugin.json`/`marketplace.json` JSON validity, dangling agent/skill/command
  references, plugin.json↔marketplace.json version consistency (`test-plugins.py`) + `.codex-plugin`/`.agents`
  manifest validity (`test-codex-plugins.py`).
- **On failure the AI panel is never invoked at all** — an immediate `VERDICT: FAIL` —
  so no AI cost is spent on a deterministically verifiable problem. The failure output is
  also run through `scrub_secrets()` before being posted as a PR comment
  (`.github/workflows/pr-review.yml` "Write L1 failure as review" step) — the validator's
  own error messages don't contain credentials, but this keeps the same defense line
  consistently applied as the matrix does.
- `precheck.sh` removes symlinks from the extracted PR tree before validation
  (`find "$TREE" -type l -delete`) — defense-in-depth that removes any chance for the
  validator to follow a path outside the tree.

## 4-Model Panel (runs only if L1 passes)
- **Panel**: 4 models (Codex `openai.gpt-5.6-sol` + Kiro `claude-opus-4.8`/`gpt-5.6-terra`/`glm-5`),
  each independently reviewing the entire diff with no scope restriction (as of the default
  configuration — matrix membership is a config value, see the "Configuration" section
  below), all run in parallel (`&`+`wait`) — wall-clock time ≈ the single slowest cell
  (not a sequential sum).
  (Before ADR-016, each model was split across 4 lenses, giving 16 cells — `run-panel.sh`
  is structured to automatically scale the number of cells to however many `*.txt` files
  sit in the lens directory, so now that `.github/workflows/pr-review.yml` creates only
  one file (`FULL.txt`) it produces 4 cells, and `run-panel.sh` itself is unchanged.)
  (Rationale for the `kimi-k2.5` replacement: in production CI, `kiro-kimi` degraded (no
  response across all lenses) 2/2 times, and in PR reviews it was the only model that
  produced 7 unsupported findings — including hallucinations — while `kiro-glm`/`kiro-opus`/
  `codex` had zero in the same investigation. An attempt to switch to `gpt-5.5` →
  directly reproduced a rejection with `INVALID_MODEL_ID` (HTTP 400) when routed through
  `kiro-cli --v3 chat` (the first substitute tried was `minimax-m2.5`) → subsequent
  investigation found **the `--v3` flag itself was the cause** (directly reproduced and
  confirmed that `kiro-cli chat` without `--v3` responds normally for all of
  gpt-5.5/kimi-k2.5/minimax-m2.5/glm-5/claude-opus-4.8 — and that `--mode default`/
  `--trust-tools=fs_read` (the flag in use at the time — later changed to
  `--trust-tools=` by ADR-013, see below)/`--no-interactive`/`--wrap never` behave
  identically regardless of `--v3`) → settled on `gpt-5.5` with `--v3` dropped (same
  underlying model as codex, but a separate harness/tool-access path so the review content
  differs). Decision recorded in ADR-012.
- **Kiro diff delivery: from `fs_read` path reference → to a capped, directly embedded argv
  (ADR-013)** — Kiro cells now receive `--trust-tools=` (no tools granted) instead of
  `--trust-tools=fs_read`, and the diff is capped by `KIRO_DIFF_CAP` (default 100000B) and
  embedded directly in argv. Reason: trusting `fs_read` with an untrusted PR diff means a
  diff-injection could induce an absolute-path read, and that value could then be
  **exposed in a public PR comment** through the chair's synthesis — this was judged to
  exceed the "accepted residual risk" level explicitly stated in ADR-011, given the
  combination of a public repo + `pull_request_target` (discovered during review of
  claude-code-usage-dashboard PR #4). A diff exceeding the cap is delivered to the Kiro
  cell only as a prefix, and this is signaled via `::warning::` +
  `$WORK/kiro-diff-truncated.flag`, and shown as a banner in the review body (it does not
  force the VERDICT — codex continues to see the full diff).
- **Antigravity (`agy`) is not in the matrix** — it only supports OAuth interactive login,
  so it cannot authenticate in headless CI (ADR-010).
- **Chair**: Claude Fable 5 (`us.anthropic.claude-fable-5`) synthesizes the findings from
  the 4 cells into a single review + `VERDICT: PASS|FAIL` (fail-closed, the last match in
  the file is what's adopted — ADR-016). The first attempt is given `Read Grep Glob` and
  wrapped in a wall-clock timeout (`CHAIR_TIMEOUT`, default **300 seconds**). If it fails
  to produce a usable VERDICT (connection refused/hang/empty response, etc.), it
  **falls back once to Claude Opus 5 (`CHAIR_FALLBACK_MODEL`), but this time with no file
  tools granted at all** (`CHAIR_FALLBACK_TIMEOUT`, default **120 seconds**) — the fallback
  is self-contained because the diff and panel reviews are already on stdin, and with no
  tools it cannot crawl the repo tree. If both attempts fail, this is a CI infrastructure
  problem rather than a review finding, so it signals `chair_error=1`, and the workflow
  gate correctly shows "ERROR" in the comment rather than "BLOCKED — CRITICAL/MAJOR". The
  chair label in the comment header reflects whichever model was actually used.
  (Why it was lowered from 600s to 300s/120s: the old 600s combined an instruction telling
  the chair to "read CLAUDE.md/AGENTS.md directly" with `Read Grep Glob` access, which led
  to crawling the repo tree on large diffs, and #141/#146 both timed out at exactly 600s —
  the root cause was closed by removing that Read instruction from the prompt and removing
  tool access entirely from the fallback, ADR-016.)
- **Data residency**: paths differ per matrix member —
  - **Codex / Claude (chair)**: Amazon Bedrock **us-east-1** (openai.gpt-5.6-sol is
    bedrock-mantle, In-Region only; fable-5 is a US inference profile), AWS auth via EKS
    Pod Identity (SigV4).
  - **Kiro**: **an external API-key-based service** — the PR diff is sent externally (in
    the default configuration, 3 of the 4 cells are Kiro; matrix membership is a config
    value so the actual cell count can vary). Not In-Region.
  - **Sensitive-diff policy**: for changes where external transmission is inappropriate,
    disable the external panel (Kiro) and review with only the Bedrock In-Region member
    (Codex). **For the actual procedure to turn this off, see "How this actually takes
    effect in CI" in the "Configuration" section below** — simply writing
    `.claude/pr-review.local.json` into the workspace does not take effect (checkout wipes
    it on every run + `pull_request_target` checks out the base ref).
    (Since this is a public marketplace, the diff becomes public on merge anyway →
    currently accepted-risk; a private fork would need a forced skip gate — ADR-009.)

## Configuration — matrix membership (`scripts/pr-review/panel_config.py`)
- Which cells (codex/kiro-opus/kiro-gpt/kiro-glm) participate in the matrix comes from
  configuration, not hardcoding in `scripts/pr-review/run-panel.sh` — it reuses the same
  layering as the co-agent plugin's `co_agent_config.py` (defaults.json + gitignored local
  override): `scripts/pr-review/pr-review.defaults.json` (committed) +
  `.claude/pr-review.local.json` (gitignored, repo-local override). pr-review is a
  repo-only configuration that runs only in CI, so there is no co-agent user-scope layer
  (`~/.claude/co-agent.user.json`) here — only two layers.
- `python3 scripts/pr-review/panel_config.py show --root .` — shows the effective config
  table. `python3 scripts/pr-review/panel_config.py set <cell> enabled <true|false> --root .`
  — adds or removes a cell from the matrix without a code change (e.g. turning off all
  three Kiro cells under the "sensitive-diff policy" above, or removing a single model that
  keeps being flaky). `python3 scripts/pr-review/panel_config.py set <cell> model <name>
  --root .` — Kiro-only (codex is pinned via `~/.codex/config.toml` and has no model key).
  (Uses the same full-path + `--root .` notation as the runbook — copy-pasteable.)
- Matrix membership (models) is configuration. Lenses no longer exist after ADR-016 — each
  model reviews the entire diff with no scope restriction.
- **How this actually takes effect in CI (important — simply writing
  `.claude/pr-review.local.json` into the workspace never takes effect):**
  - **Path A — a permanent change (verified, always works)**: edit
    `scripts/pr-review/pr-review.defaults.json` directly and commit. This takes effect
    starting with the **next** PR merged into `main` (because `pull_request_target` checks
    out the base ref, this same limitation applied when switching the Kiro roster from
    `kimi-k2.5` to `gpt-5.5` — it doesn't apply to the PR that carries this change itself).
    Suitable for a persistent config change like "remove one model that keeps being flaky."
  - **Path B — a temporary override for just this one PR (untested — needs runner
    infrastructure confirmation)**: `.claude/pr-review.local.json` is gitignored, so
    committing it does nothing, and if it's placed in the workspace,
    `actions/checkout@v4`'s default behavior (`clean: true` → `git clean -ffdx`) wipes it
    on every run. If the self-hosted runner this workflow executes on has **a path outside
    the git workspace that persists across jobs** (e.g. a separately mounted volume —
    **whether such a path actually exists/persists on this repo's current runner is not
    confirmed**), point `PR_REVIEW_CONFIG_ROOT` at that path (e.g. `/persist`) in this
    workflow's job `env:`, and place the override file not at that path directly but at
    **`<that path>/.claude/pr-review.local.json`** (`panel_config.py`'s `local_path()`
    reads `<root>/.claude/pr-review.local.json` — the root itself is not the file path).
    Code support already exists (`scripts/pr-review/run-panel.sh` already honors this env
    var first). Using this path requires infrastructure staff to first confirm that the
    runner actually has a real persistent path.
- Disabling a cell also removes it from the coverage-floor logic's "expected models" —
  so an intentional disablement isn't mistaken for a degraded/severe warning
  (`run-panel.sh`'s `ALL_TAGS`/`CODEX_ENABLED`).

## Configuration — review memory (`docs/pr-review/review-memory.md`, ADR-015)

**A single committed file** holding accumulated review knowledge. CI and the interactive
review agents read the same file.

- **Location**: `docs/pr-review/review-memory.md` (committed). Three fixed sections —
  `Recurring real issues` / `Known false-positive patterns` / `Panel-cell judgment quality`
  (a cumulative table).
- **Only one local host updates it** — only the host (Claude) of `/co-agent:pr-autofix`
  writes to it. CI **never commits automatically** (a self-modification with no review,
  wired directly to PR text, would be an injection risk). Planners/implementers are
  forbidden from writing this file (giving file-write access to something that processes
  untrusted review text, when that write ends up in a future review prompt, is an
  injection path).
- **3 read paths**:
  - Panel prompt — `memory_excerpt` (`scripts/pr-review/lib.sh`) caps the excerpt at
    `MEMORY_CAP` (default **4000B**) and appends it after the shared prompt
    (`lenses/FULL.txt`) in the "Build review prompt" step (before ADR-016 it was appended
    per lens file; now there's only one file). If the file doesn't exist, nothing is
    appended (**fail-open** — the absence of memory doesn't block the review). The
    `Panel-cell judgment quality` table is **excluded** from the excerpt (telling a cell
    "you're not trusted" is just noise). Why the cap is a small 4000B: Kiro cells carry
    the prompt+diff in argv and share the kernel argv budget with `KIRO_DIFF_CAP` (100KB).
  - Chair — `synthesize.sh` inlines an excerpt capped at `CHAIR_MEMORY_CAP` (default
    8000B) directly into **stdin** (ADR-016: when the chair falls back, `Read` itself
    isn't available, so a path-based instruction wouldn't work at that point — always
    using stdin makes both the primary and fallback attempts self-contained). The chair
    dismisses any finding matching a known false positive that the diff doesn't support,
    and publishes two sections — `### 🧠 MEMORY CANDIDATES` and `### PANEL QUALITY` (fixed
    format `PANEL-QUALITY: <cell>=<unsupported>/<total>`) — **before** the VERDICT line
    (either is omitted if it has nothing to report).
  - Interactive — `gate-chair` and `content-review-agent` read the same file at startup,
    and **propose** promoting anything applicable repo-wide into that file (they don't
    write directly).
- **The same delay characteristic as roster changes** — because `pull_request_target`
  checks out the base ref, a memory update only takes effect starting with the **next**
  PR merged into `main`. It does not apply to the review of the PR that carries this
  change (same constraint as "Path A" above). Put another way: a PR's head cannot
  manipulate the memory used for its own review — it isn't an injection surface.
- **Roster exclusion is advisory only** — for the procedure when a threshold is exceeded,
  see "When panel-cell judgment quality crosses the threshold" in
  `docs/ci-pr-review-runbook.md`. Automatic disabling was not adopted because it risks
  coverage collapse → fail-closed (ADR-015).

## Files
- `.github/workflows/pr-review.yml` — `pull_request_target` (base-ref checkout, diff is
  data), L1 gate → (on pass) build review prompt (shared across the 4 models) → panel
  fan-out → synthesize → gate → comment upsert
- `scripts/pr-review/precheck.sh` — L1: extracts the PR head as data via `git archive`
  then deterministically validates it with `test-plugins.py --root` +
  `test-codex-plugins.py --root`.
- `scripts/pr-review/{lib,run-panel,synthesize}.sh` — parallel matrix execution
  (model × lens double loop) + chair synthesis. Failed cells are skipped gracefully.
  Diagnostic logs default to **redaction (stripping auth/provider/prompt/diff fragments)
  + length limiting** (raw stderr is never exposed in comments/logs). `lib.sh`'s
  `scrub_secrets()` regex-substitutes AWS/GitHub/Slack/OpenAI·Anthropic/Google key formats
  + JWTs (the shape of an EKS Pod Identity token) out of each cell's output before it
  reaches the chair — a general last line of defense (e.g. against a credential-like value
  accidentally leaking into a cell's output through some other path), while the Kiro
  `fs_read` residual leak path was closed structurally by removing `fs_read` itself
  (ADR-013, amends ADR-011).
- `scripts/pr-review/panel_config.py`, `scripts/pr-review/pr-review.defaults.json`
  (committed defaults), `.claude/pr-review.local.json` (gitignored, repo-local override) —
  the two-layer configuration for matrix membership. See the "Configuration" section above
  for detailed usage.
- `scripts/test-plugins.py --root <path>`, `scripts/test-codex-plugins.py --root <path>` —
  the option that lets the manifest validators run against an arbitrary tree (L1-only;
  by default they validate this repo itself).

## Authentication
- Kiro: `ai-panel-keys` ExternalSecret (`<secret-path>`) → runner env (external API key)
- Codex/Claude: EKS Pod Identity (`<ci-runner-role>`, Bedrock) SigV4 — requires a Pod
  Identity Association
