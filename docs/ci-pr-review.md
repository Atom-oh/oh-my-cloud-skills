# CI: Multi-AI PR Review — L1 Deterministic Gate + 3-Model Panel

PRs in this repo go through a two-stage gate on the self-hosted runner
(`oh-my-cloud-skills-claude-arm`): **L1** (manifest/version consistency — a deterministic
script, no AI calls) → **3-model panel** (each model reviews the full diff with no scope
restriction → Claude chairs and synthesizes; as of the default configuration — `kiro-glm`
is disabled by default due to its false-positive rate, see ADR-017).
(design: `docs/superpowers/specs/2026-07-05-pr-review-hybrid-lens-design.md`, ADR-011;
the lens×model matrix was reversed by ADR-016 — a 4-model×4-lens grid of 16 cells
quadrupled the chair's input and exhausted the 600s timeout (observed in #141/#146: both
models hit exactly 600s), and the lens checklists were unnecessary for frontier models.)

## L1 — Deterministic pre-check (before any AI call, zero cost)
- `scripts/pr-review/precheck.sh` extracts the PR head's file tree **as data only**
  (no execution) via `git archive` → validates it against `scripts/test-plugins.py --root
  <extracted tree>` **and `scripts/test-codex-plugins.py --root <extracted tree>`** run
  from the base (trusted) checkout (both must pass for L1 to pass).
- What's checked: `plugin.json`/`marketplace.json` JSON validity, dangling agent/skill/
  command references, plugin.json↔marketplace.json version consistency
  (`test-plugins.py`) + `.codex-plugin`/`.agents` manifest validity
  (`test-codex-plugins.py`).
- **On failure, the AI panel is not invoked at all** — an immediate `VERDICT: FAIL` —
  because AI cost shouldn't be spent on problems that are deterministically verifiable.
  Failure output also passes through `scrub_secrets()` before being posted as a PR comment
  (the "Write L1 failure as review" step in `.github/workflows/pr-review.yml`) — the
  validator's error messages themselves contain no credentials, but this applies the same
  defensive line consistently with the matrix.
- `precheck.sh` removes symlinks from the extracted PR tree before validation
  (`find "$TREE" -type l -delete`) — defense-in-depth that removes any chance for the
  validator to follow a path outside the tree.

## 3-Model panel (runs only if L1 passes)
- **Panel**: 3 models (Codex `openai.gpt-5.6-sol` + Kiro `claude-opus-5`/`gpt-5.6-terra`),
  each independently reviewing the full diff with no scope restriction (as of the default
  configuration — matrix membership is a config value, see the "Configuration" section
  below), all running in parallel (`&`+`wait`) — wall clock ≈ the single slowest cell (not
  a sequential sum).
  (Before ADR-016, each model was split across 4 lenses for up to 16 cells —
  `run-panel.sh` is structured to automatically scale the cell count to the number of
  `*.txt` files placed in the lens directory, so now that `.github/workflows/
  pr-review.yml` creates only one file (`FULL.txt`), the cell count equals the number of
  active models, and `run-panel.sh` itself is unchanged.) `kiro-glm` (`glm-5`) is disabled
  by default due to its false-positive rate — following the AWS-Demo-Platform ADR-015
  precedent, see this repo's ADR-017. (Rationale for the `kimi-k2.5` replacement: in
  production CI, `kiro-kimi` degraded (no response across all lenses) 2 out of 2 times,
  and 7 unsupported findings (including hallucinations) in PR reviews came uniquely from
  this model — `kiro-glm`/`kiro-opus`/`codex` had zero in the same investigation. An
  attempt to switch to `gpt-5.5` was directly reproduced as being rejected with
  `INVALID_MODEL_ID` (HTTP 400) via `kiro-cli --v3 chat` (initially substituted with
  `minimax-m2.5`) → it was then discovered that **the `--v3` flag itself was the cause**
  (directly reproduced and confirmed that `kiro-cli chat` without `--v3` responds
  normally for gpt-5.5/kimi-k2.5/minimax-m2.5/glm-5/claude-opus-4.8 — and that `--mode
  default`/`--trust-tools=fs_read` (the flag used at the time — changed to
  `--trust-tools=` by ADR-013, below)/`--no-interactive`/`--wrap never` behave identically
  regardless of `--v3`) → settled on `gpt-5.5` with `--v3` dropped (same model as codex,
  but a separate harness/tool-access path, so review content diverges). Decision record:
  ADR-012.
- **Kiro diff delivery: from an `fs_read` path reference → directly embedding a capped
  argv (ADR-013)** — Kiro cells receive `--trust-tools=` (no tools granted) instead of
  `--trust-tools=fs_read`, and the diff is capped by `KIRO_DIFF_CAP` (default 100000B) and
  embedded directly in argv. Reason: trusting `fs_read` with an untrusted PR diff could let
  diff-injection induce an absolute-path read, and that value could then be **exposed in a
  public PR comment** via the chair's synthesis — this was judged to exceed the "accepted
  residual risk" level stated by ADR-011, in the combination of a public repo +
  `pull_request_target` (discovered during review of claude-code-usage-dashboard PR #4). A
  diff exceeding the cap is delivered to the Kiro cell only as a truncated prefix, and is
  signaled via `::warning::` + `$WORK/kiro-diff-truncated.flag`, shown as a banner in the
  review body (it does not force the VERDICT — codex continues to see the full diff).
- **Antigravity (`agy`) is not in the matrix** — it's OAuth interactive-login-only, so it
  cannot authenticate in headless CI (ADR-010).
- **Chair**: Claude Fable 5 (`us.anthropic.claude-fable-5`) synthesizes the findings from
  the 3 cells into a single review + `VERDICT: PASS|FAIL` (fail-closed, the last match in
  the file wins — ADR-016). The primary attempt has `Read Grep Glob` and is wrapped in a
  wall-clock timeout (`CHAIR_TIMEOUT`, default **450 seconds**). If it fails to produce a
  usable VERDICT (connection refused/hang/empty response, etc.), it **falls back once to
  Claude Opus 5 (`CHAIR_FALLBACK_MODEL`), this time granting no file tools at all**
  (`CHAIR_FALLBACK_TIMEOUT`, default **300 seconds**) — since the diff + panel reviews are
  already fully present on stdin, the fallback is self-contained, and with no tools it
  cannot crawl the repo tree. If both attempts fail, this is a CI infrastructure problem
  rather than a review finding, so it signals `chair_error=1`, letting the workflow gate
  display "ERROR" precisely (rather than "BLOCKED — CRITICAL/MAJOR") in the comment. The
  chair label in the comment header reflects the model actually used.
  (Reason for lowering from 600s→300s/120s: the old single 600s attempt combined the
  instruction "have the chair read CLAUDE.md/AGENTS.md directly" with granting `Read Grep
  Glob`, which led to a repo-tree crawl on large diffs, and #141/#146 both timed out at
  exactly 600s — removing that Read instruction from the prompt and stripping tools
  entirely from the fallback closed the root cause, ADR-016.)
- **Data residency**: paths differ by matrix member —
  - **Codex / Claude (chair)**: Amazon Bedrock **us-east-1** (`openai.gpt-5.6-sol` is
    bedrock-mantle In-Region only, `fable-5` is a US inference profile), AWS auth via EKS
    Pod Identity (SigV4).
  - **Kiro**: an **external API-key-based service** — the PR diff is sent externally (as
    of the default configuration, 2 of the 3 cells are Kiro; matrix membership is a
    config value, so the actual cell count may differ). Not In-Region.
  - **Sensitive-diff policy**: for changes where external transmission is inappropriate,
    disable the external panel (Kiro) and review with only the Bedrock In-Region member
    (Codex). **See the "How this is actually applied in CI" subsection of the
    "Configuration" section below for the actual procedure to turn this off** — simply
    writing `.claude/pr-review.local.json` into the workspace does NOT apply it (the
    checkout wipes it every run + `pull_request_target` checks out the base ref).
    (Since this is a public marketplace, the diff becomes public on merge anyway →
    currently an accepted risk; a private fork would need a mandatory skip gate — ADR-009.)

## Configuration — Matrix membership (`scripts/pr-review/panel_config.py`)
- Which cells (codex/kiro-opus/kiro-gpt; `kiro-glm` disabled by default due to its
  false-positive rate — see ADR-017) participate in the matrix comes from configuration,
  not hardcoding in `scripts/pr-review/run-panel.sh` — reusing the same layering as the
  co-agent plugin's `co_agent_config.py` (defaults.json + gitignored local override):
  `scripts/pr-review/pr-review.defaults.json` (committed) +
  `.claude/pr-review.local.json` (gitignored, repo-local override). Since pr-review is
  repo-specific configuration that only runs in CI, there is no co-agent-style
  user-scope layer (`~/.claude/co-agent.user.json`) — only these two layers.
- `python3 scripts/pr-review/panel_config.py show --root .` — shows the effective
  configuration table.
  `python3 scripts/pr-review/panel_config.py set <cell> enabled <true|false> --root .` —
  add or remove a cell from the matrix without code changes (e.g. turning off both Kiro
  cells per the "sensitive-diff policy" above, or removing just one persistently flaky
  model). `python3 scripts/pr-review/panel_config.py set <cell> model <name> --root .` —
  Kiro-\* only (codex is pinned via `~/.codex/config.toml`, so it has no `model` key).
  (Uses the same full-path + `--root .` notation as the runbook, for uniform copy-paste.)
- Matrix membership (models) is a config value. Lenses no longer exist as of ADR-016 —
  each model reviews the full diff with no scope restriction.
- **How this is actually applied in CI (important — simply writing
  `.claude/pr-review.local.json` into the workspace NEVER applies it):**
  - **Path A — permanent change (verified, always works)**: edit
    `scripts/pr-review/pr-review.defaults.json` directly and commit it. This applies
    starting with the **next** PR merged into `main` (since `pull_request_target` checks
    out the base ref, this doesn't apply to the review of the PR carrying the change
    itself — the same constraint applied when switching the Kiro roster from
    `kimi-k2.5`→`gpt-5.5`). Suited to lasting configuration changes like "remove one
    persistently flaky model."
  - **Path B — a temporary, one-PR-only change (untested — requires runner
    infrastructure verification)**: `.claude/pr-review.local.json` is gitignored, so
    committing it is meaningless, and if placed inside the workspace,
    `actions/checkout@v4`'s default behavior (`clean: true` → `git clean -ffdx`) wipes it
    every run. If the self-hosted runner this workflow runs on has a **path outside the
    git workspace that persists across jobs** (e.g. a separately mounted volume — **it is
    not currently confirmed whether such a path exists/persists on this repo's current
    runner**), point that path (e.g. `/persist`) via `PR_REVIEW_CONFIG_ROOT` in this
    workflow's job `env:`, and place the override file not at that path directly but at
    **`<that path>/.claude/pr-review.local.json`** (`panel_config.py`'s `local_path()`
    reads `<root>/.claude/pr-review.local.json` — the root itself is not the file path).
    Code support already exists (`scripts/pr-review/run-panel.sh` already respects this
    env var with top priority). Before using this path, infrastructure ownership must
    first confirm that a real persistent path exists on that runner.
- Disabling a cell also excludes it from the "expected models" set used by the coverage
  floor logic — so an intentional disablement isn't mistaken for a degraded/severe
  warning (`run-panel.sh`'s `ALL_TAGS`/`CODEX_ENABLED`).

## Configuration — Review memory (`docs/pr-review/review-memory.md`, ADR-015)

A **single committed file** holding accumulated review knowledge. CI and the interactive
review agents read the same file.

- **Location**: `docs/pr-review/review-memory.md` (committed). Three fixed sections —
  `Recurring real issues` / `Known false-positive patterns` / `Panel cell judgment quality`
  (cumulative table).
- **Only one local host updates it** — only the host (Claude) of
  `/co-agent:pr-autofix` writes to it. CI **never auto-commits** to it (unreviewed
  self-modification + direct exposure to PR text = an injection risk). The planner/
  implementer are forbidden from writing this file (giving write access to a file that
  gets fed into future review prompts, to a component that processes untrusted review
  text, is an injection vector).
- **Three read paths**:
  - Panel prompt — `memory_excerpt` (`scripts/pr-review/lib.sh`) appends an excerpt
    capped by `MEMORY_CAP` (default **4000B**) after the shared prompt
    (`lenses/FULL.txt`) in the "Build review prompt" step (before ADR-016 this was
    appended per lens file; now there's only one file). If the file doesn't exist,
    nothing gets appended (**fail-open** — an absent memory file doesn't block review).
    The `Panel cell judgment quality` table is **excluded** from the excerpt (telling a
    cell "you're not trusted" is noise, not signal).  The cap is small at 4000B because
    Kiro cells carry the prompt+diff in argv and share the kernel argv budget with
    `KIRO_DIFF_CAP` (100KB).
  - Chair — `synthesize.sh` inlines an excerpt capped by `CHAIR_MEMORY_CAP` (default
    8000B) directly on **stdin** (ADR-016: since `Read` itself isn't available on the
    chair's fallback attempt, a path-based instruction wouldn't work there — always using
    stdin makes both the primary and fallback attempts self-contained). The chair
    dismisses any finding that matches a known false positive if the diff doesn't support
    it, and publishes two sections — `### 🧠 MEMORY CANDIDATES` +
    `### PANEL QUALITY` (fixed format `PANEL-QUALITY: <cell>=<unsupported>/<total>`) —
    **before** the VERDICT line (both are omitted if there's nothing to report).
  - Interactive — `gate-chair` and `content-review-agent` read the same file at startup,
    and **propose** (never directly write) promoting any repo-wide-applicable item into
    that file.
- **Same latency characteristics as roster changes** — since `pull_request_target` checks
  out the base ref, a memory update takes effect only starting with the **next** PR merged
  into `main`. It does not apply to the review of the PR carrying the change itself (the
  same constraint as "Path A" above). Conversely, this means the PR head cannot manipulate
  the memory that will be used for its own review — it is not an injection surface.
- **Roster exclusion is advisory only** — when a threshold is exceeded, the procedure is
  in the "When a panel cell's judgment quality crosses the threshold" section of
  `docs/ci-pr-review-runbook.md`. Automatic disablement was not adopted, since it risks a
  coverage collapse → fail-closed situation (ADR-015).

## Files
- `.github/workflows/pr-review.yml` — `pull_request_target` (base-ref checkout, diff is
  data), L1 gate → (on pass) build the review prompt (shared across models) → panel
  fan-out → synthesize → gate → comment upsert.
- `scripts/pr-review/precheck.sh` — L1: extracts the PR head as data via `git archive`,
  then deterministically validates it with `test-plugins.py --root` +
  `test-codex-plugins.py --root`.
- `scripts/pr-review/{lib,run-panel,synthesize}.sh` — runs the matrix in parallel
  (model×lens double loop) + chair synthesis. A failed cell is skipped gracefully.
  Diagnostic logs default to **redaction (stripping auth/provider/prompt/diff fragments) +
  length limiting** (raw stderr is never exposed in comments/logs). `lib.sh`'s
  `scrub_secrets()` regex-replaces AWS/GitHub/Slack/OpenAI·Anthropic/Google key formats +
  JWTs (shaped like EKS Pod Identity tokens) in each cell's output before handing it to
  the chair — a general last line of defense (e.g. for the case where a credential-like
  value happens to leak into cell output through some other path); the Kiro `fs_read`
  residual leak path was structurally closed by removing `fs_read` itself (ADR-013,
  amends ADR-011).
- `scripts/pr-review/panel_config.py`, `scripts/pr-review/pr-review.defaults.json`
  (committed defaults), `.claude/pr-review.local.json` (gitignored, repo-local override)
  — the two-layer configuration for matrix membership. See the "Configuration" section
  above for detailed usage.
- `scripts/test-plugins.py --root <path>`, `scripts/test-codex-plugins.py --root <path>`
  — an option that lets the manifest validators run against an arbitrary tree (L1-only;
  by default they validate this repo itself).

## Authentication
- Kiro: `ai-panel-keys` ExternalSecret (`<secret-path>`) → runner env (external API key)
- Codex/Claude: EKS Pod Identity (`<ci-runner-role>`, Bedrock) SigV4 — requires a Pod
  Identity Association
