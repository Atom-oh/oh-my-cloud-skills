# Changelog

<a id="english"></a>
<a id="korean"></a>

Release notes describe the behavior and settings at the recorded version. For the
current contracts, use [README.md](README.md) and the linked source/configuration.
The former language anchors both lead to this single English history.

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Add token-saver for concise response guidance in Claude Code and Codex, with a
  bounded session-start hook and manual skill. Preserve reasoning, verification,
  complete deliverables and required report formats.

### Changed

- Move the `kiro-opus` PR-review panel cell and co-agent's `kiro-cli` panel default
  from `claude-opus-4.8`/`claude-opus-5` to `claude-opus-5.5` (Claude Opus 5.5,
  2.00x kiro-cli credits vs. 2.20x for Opus 5), and the pr-autofix escalation
  ladder and its template CI workflow's chair-fallback model accordingly. Add an
  `*opus-5-5*` chair label ahead of the existing `*opus-5*` glob in
  `synthesize.sh` so Opus 5.5 is labeled correctly instead of matching the older
  pattern.
- Sync the mirrored project-init plugin from upstream `da91979` (v2.2.0) to
  `13ee3e1` (v2.4.0): a new `/migrate-hooks` command migrates hooks,
  `settings.json` and `.claude/agents/*.yml` files generated before v2.3 to
  Claude Code's actual hook contract (JSON on stdin, `exit 2` blocking,
  Markdown-with-frontmatter subagents — `.yml`/`.yaml` agent files are never
  loaded); `health-check` now detects that pre-v2.3 state and recommends the
  new command; generated agent templates moved from `.yml` to `.md`. No local
  divergence from upstream carried over (per the maintenance policy in
  `docs/reference/project-init-upstream-sync.md`); only the marketplace-uniform
  `version` field was restored after the sync. One file
  (`skills/project-scaffolder/references/hook-scripts.md`) is intentionally
  still on the old content pending an owner decision on a `secret-scan.sh`
  false positive; see PR #240.

### Removed

- Retire the `atlas` plugin (per-topic documentation drift detection and
  optional push-time sync), per owner request. See
  [ADR-025](docs/decisions/ADR-025-retire-atlas.md). Marketplace plugin count
  drops from nine to eight.

### Migration

- Uninstall the `atlas` plugin. Any `docs/atlas/` wiki content and
  `.claude/atlas.local.json` override in a consuming repository are untouched
  by this removal and can be deleted manually if no longer wanted; remove any
  pre-push hook that referenced it.

## [2.0.0] - 2026-09-13

This major release removes the previously supported Antigravity peer and requires
migration of configurations that selected it. All eight plugins share this version.

### Added

- Complete Codex packages for all eight plugins, with generated procedure entries,
  installed-runtime checks and native-hook fixtures. Project-init's maintained
  source remains mirrored while its Codex adaptation is generated locally.
- Co-agent implementation planning that validates configuration and fresh external
  reviewer readiness before choosing an eligible writer or explicit host mode.

### Changed

- Maintain project instructions, README, changelog, reference documents and public
  documentation in English. Preserve functional aliases, localized payloads and
  historical evidence; reconcile current contracts through ADR-021 and ADR-022.
- Share verified trusted-base context across the complete CI review panel and chair.
  Require latest-HEAD review, complete configured coverage and separate Codex
  package validation before merging.
- Align co-agent procedures, plugin listings and startup messages with Kiro plus
  the opposite host CLI: Codex when Claude hosts, or Claude when Codex hosts.
- Refresh presentation demos, public-site navigation and legacy locale redirects.

### Fixed

- PR review uses a validated zero-tool Kiro agent and a per-model canary preflight
  before sending PR input. Reject default-agent fallback, surface monthly/overage account-limit
  exhaustion without retries, and preserve required coverage failures (PR207).
- Block active Critical/Major findings even when a review contains a conflicting
  PASS marker, and reject stale review publication after the HEAD or target changes.
- Preserve the orchestration project's readiness record and model overrides when
  harness tasks execute in separate worktrees.
- Correct Codex component discovery and validation coverage, native-hook dispatch,
  and review runtime/model selection.

### Removed

- Antigravity (`agy`) peer, probe, hook and delegated implementation paths in
  co-agent. Retired configuration keys require migration. Kiro and the opposite
  host CLI remain available; an explicit native-host implementation plan still
  requires fresh external review readiness.

### Migration

- Remove retired peer settings and any retired `harness.implementer` selection
  using the [co-agent configuration guide](plugins/co-agent/commands/configure.md),
  then rerun `/co-agent:setup`.
- Recheck writer readiness before implementation. Codex-hosted harness work can
  use an explicitly authorized native-host plan; a READY external reviewer remains
  required. See the [implementation procedure](plugins/co-agent/skills/co-agent/references/delegated-implement.md).

## [1.17.0] - 2026-09-02

### Added
- **aws-content-plugin: Archify becomes the fifth diagram path — explorable/interactive diagrams inside Remarp decks (ADR-020, [#161](https://github.com/Atom-oh/oh-my-cloud-skills/pull/161))** — [Archify](https://github.com/tt-a1i/archify) (MIT) is adopted as a **version-pinned dependency** (2.16.0 @ `199360cc`, never forked; a dirty or unpinned clone fails the build). The new `:::archify` block carries an Archify architecture JSON spec (inline or by path); the build renders it through the pinned clone, injects official AWS icons post-render (`archify_icons.py` — the PoC's two load-bearing contracts, paint order and `<g transform>` placement, kept as code; the service-name vocabulary is `layout_aws.py`'s new `ARCH_STEMS` table so both diagram paths name services identically, resolved against the shared 811-icon library), and embeds the result as a focus-isolated iframe — arrow keys stay with the deck until the presenter clicks in, Esc returns on a served deck. `export_pptx.py --base-url` flattens deliberately: the slide image is the diagram's MAP state and the interactive URL rides in the speaker notes. Guard rails: `--map`/`icons=` values are confined to the bundled icon library (the injector inlines file content into a publishable artifact, so an arbitrary path was an exfiltration vector), and `tests/structure/test-archify-structure-probe.sh` fails loudly when an Archify upgrade changes the output markup. PoC evidence + repro: `docs/decisions/poc/adr-020/`; the docs site gains a pipeline demo drawn with the feature itself; routing registered in the plugin/root tables and `docs/reference/review-routing.md`

### Changed
- **deconstraining rewrite completes across every plugin ([#156](https://github.com/Atom-oh/oh-my-cloud-skills/pull/156) aws-ops, [#160](https://github.com/Atom-oh/oh-my-cloud-skills/pull/160) the remaining six)** — the R1 survival test established on aws-content-plugin now covers aws-ops (inverse problem: zero MUST/NEVER tokens but heavy template scaffolding and verbatim duplication — net additive goal prose + dedup, −49 lines) and co-agent / kiro / atlas / agentcore-creator / kiro-power-converter (41 files, net −373 lines; project-init excluded as an upstream mirror). A negative instruction survives only as a tool/format contract, a silent-failure trap, security/PII, or a script gate — everything else becomes a goal statement
- **co-agent: pr-autofix control flow is an explicit state graph ([#158](https://github.com/Atom-oh/oh-my-cloud-skills/pull/158))** — one state file (`.claude/co-agent-consensus/pr-autofix/pr-<N>/state.json`: iteration, max_iter, replanned_this_pass, phase, stop_reason) replaces the git-grep-derived counter and the gate-replanned sentinel; git log is demoted from source of truth to a poll-entry repair signal (cross-checked, adopted with a warning on mismatch), so the loop self-heals under rebases and dropped commits

### Fixed
- **atlas: read-side exfiltration gap and a `git push --dry-run` misfire ([#159](https://github.com/Atom-oh/oh-my-cloud-skills/pull/159))** — the confined fixer's PreToolUse guard now restricts Read/Grep/Glob to the wiki root (not just Edit), closing the read-then-launder path with no functional cost since the covered diff already arrives on stdin; each synced doc's own diff also gets a narrow secret-scan pass before staging; and `--dry-run` pushes no longer trigger the sync
- **hooks leak/dead-code audit ([#160](https://github.com/Atom-oh/oh-my-cloud-skills/pull/160))** — hooks still reading the long-dead `$TOOL_*` env contract migrated to the stdin-JSON contract; kiro's leaked `acp-server` orphan processes (ppid=1, left by headless `timeout` kills) are reaped by SessionStart/Stop hooks; eval-skills' heading check became fence-aware and `colors-reference.md` lost its raw hex literals (the suite's one standing failure)
- **co-agent: push-gate false positive on long camelCase identifiers** — the unquoted-credential branch matched ordinary source assignments like `var token = relationshipTokenGeometry(...)` (measured on PR #161's vendored Archify viewer JS); the value now also requires a digit or `/`,`+` — present in virtually all real key material, absent from identifiers — with every true-positive class (AKIA, PATs, base64, quoted literals) still covered
- **scripts: sync-plugin-cache.sh died under `set -e` on its first file and only covered 3 of 8 plugins** — `((COUNT++))` returns status 1 on the first increment; and the hardcoded plugin list silently let cached copies of the other five plugins (notably co-agent's live hooks) drift from source

## [1.16.0] - 2026-08-18

### Added
- **pre-push review gates (both plugins, opt-in and off by default) + a SessionStart routing hook for kiro's toggles** — `git push` is the last checkpoint before content leaves the machine, so both plugins can now review the range about to be pushed: co-agent's `push_gate` fans 3 lenses (correctness/security/scope) round-robin across the panel and judges by BLOCKing-lens count (2+ = BLOCKED, exactly 1 = CHAIR JUDGMENT REQUIRED, since a hook cannot call Claude directly), and kiro's `review.on_push` runs the same 3 lenses as parallel `kiro-cli` calls with `push_block` defaulting one tier stricter (`warning`) than the commit gate's `critical`. Both are **off by default** — enabling either is consent to send diff content to a third-party backend — and `co_agent_config.py` gains kiro's tracked-file consent stripping so a repo committing `.claude/co-agent.local.json` with `pr_gate`/`push_gate` enabled cannot opt an installing user in. Both gates SKIP (fail-open, advisory) any push they cannot describe: a `cd`/`pushd` or preceding `git commit` in the same invocation, a redirect at another repo/work tree, a ref deletion, and `--all`/`--tags`/`--mirror` or an explicit refspec — the range they diff is `@{upstream}...HEAD` (three-dot, from the merge base), which says nothing about what those forms actually send. Enabling both warns that every push then runs two independent review rounds. Separately, `plugins/kiro/hooks/session-routing.sh` fixes a dead toggle: a plugin's own `CLAUDE.md` is NOT loaded into session context (only the project's is), so `default_delegate`/`websearch.enabled` changed nothing in any consumer repo — the routing rules are now emitted from a SessionStart hook, which is the one plugin-side channel whose output does land in context
- **kiro: use the headless levers that were always there — `--effort`, `--resume-id`, `--require-mcp-startup`, credit telemetry** — the public headless blog post lists only four flags, and this plugin's own `references/kiro-headless.md` repeated that list as if it were exhaustive; `kiro-cli chat --help` on 2.11.1 shows `--effort`, `--resume`/`--resume-id`/`--resume-picker` and `--list-sessions --format json` all exist, so the doc bug (not the CLI) is why delegation ran without them. Now: (1) fix rounds **resume** instead of restarting — the new `scripts/kiro_run.py session-id <wt>` reads the session store (grouped by `cwd`, so a per-task worktree identifies its session unambiguously) and round 2 re-runs with `--resume-id <id>` carrying only the trimmed failing-test output, falling back to a fresh full-context call when there's no id (a missing session id never fails a task); (2) new `delegate.effort` (default **`low`** — the implementer is applying a spec Claude already wrote, same reasoning as `pr-autofix-implementer`) and `review.effort` (default **`high`** — the blocking verdict IS that call's product), both `/kiro:configure set <delegate|review> effort <low|medium|high|xhigh|max>` with `default` omitting the flag, and a hand-edited garbage value coercing to "omit" rather than breaking the call; (3) `kiro_run.py credits <log>...` sums the `Credits: <n>` turn footers out of the logs the pipeline already redirects (ANSI-stripped) into the delegation-rate report — best-effort, the line is omitted rather than guessed if the footer format changes; (4) `--require-mcp-startup` on the delegate call turns a silently-dead MCP server into exit 3 up front (treated as infrastructure failure → Claude fallback, not a fix-round-worthy task failure). `references/kiro-headless.md`'s flag section is rewritten against the measured surface, narrowing the upstream gap (kiro#5423, kiro#9066) to the one thing genuinely absent: turn-level event streaming

### Changed
- **project-init is now a byte-identical upstream mirror; `pr-autofix` and `decision-reconcile` move to co-agent** — keeping 12 files locally diverged from `whchoi98/project-init` meant maintaining an rsync exclude list on every sync and losing a hint the moment someone forgot one. `plugins/project-init/` now tracks upstream `da91979` (v2.2.0) verbatim, with `version` in `.claude-plugin/plugin.json` as the single local delta. The two local-only skills went to the plugin they always belonged to (both are multi-model panels): `pr-autofix` (+ its `pr-autofix-planner`/`pr-autofix-implementer` agents and `/co-agent:pr-autofix`) and `decision-reconcile`. Consequences: the superpowers lifecycle routing hints live only in the root `CLAUDE.md` table (in-plugin hints would be wiped by the next sync — `tests/structure/test-superpowers-integration.sh` now asserts project-init stays hint-free); the local GitHub-metrics badge helper (`fetch_github_metrics.py` + `/generate-readme` Step 2.5) and project-init's `.codex-plugin/plugin.json` are deleted, so it no longer appears in the Codex marketplace; `doc-sync-checker` keeps upstream's bare `model: opus` (an explicit exception to the `model`+`effort` rule, since the file is a mirror). `scripts/test-plugins.py` discovers agents/skills on disk when a manifest omits the arrays, so mirrored plugins are still frontmatter-validated instead of silently skipped, and `scripts/test-codex-plugins.py` skips a plugin listed in its `CLAUDE_ONLY` allowlist (project-init) instead of erroring, while any OTHER plugin missing a `.codex-plugin` manifest — or a stale Codex marketplace entry left behind for an allowlisted one — is still an error. Sync procedure: `docs/reference/project-init-upstream-sync.md`
- **pr-autofix loop bound is now a co-agent setting instead of a hardcoded 5** — `/co-agent:configure set pr_autofix max_iterations <n>` (default 5, positive int), read by the skill at start via `co_agent_config.py pr-autofix-iterations`. The right number depends on how incrementally the repo's review CI surfaces findings, which is a per-repo property, not a skill constant

## [1.15.0] - 2026-07-24

### Added
- **kiro: web search delegation for WebSearch-less sessions (Claude Code on Bedrock)** — kiro-cli has a native `web_search` tool; sessions without a `WebSearch` tool can now opt in (`/kiro:setup` asks, or `/kiro:configure set websearch enabled on`) to route web searches through it via the new `kiro_websearch.py`. The generated `kiro-websearch` agent is search-only (`web_search` is its ONLY tool — no fs_read/fs_write/execute_bash, so no preToolUse path guard is even needed), the script fail-closed refuses a tampered agent file (same defense as `/kiro:review`), only the query text ever leaves the machine, and the always-loaded routing rule in `plugins/kiro/CLAUDE.md` never fires when the session has its own WebSearch tool. Off by default; `websearch.enabled` is a consent-gated key in tracked-config stripping alongside `default_delegate`/`review.on_commit` — a repo committing `.claude/kiro.local.json` with `enabled: true` cannot silently opt an installing user's session into query egress. The routing rule instructs Claude to write the query to a per-invocation temp file with its file-write tool (no shell involved) and run a fixed `--query-file` command, so query text derived from untrusted context never touches the host shell at all — not even as heredoc input, whose delimiter line a hostile query could terminate early
- **kiro: new cost-savings delegation plugin (7th plugin)** — Claude plans and verifies; Kiro CLI implements and reviews on its own flat-rate subscription credits inside an isolated git worktree, so token-expensive work moves off this session's budget. Not a second opinion (that's `co-agent`) — purely cost. Commands: `/kiro:setup`, `/kiro:delegate`, `/kiro:review`, `/kiro:configure`; reuses co-agent's `worktree.py`/`scope_guard.py`/`parse_plan.py` verbatim, with an opt-in (off by default) `PreToolUse(Bash)` pre-commit review gate
- **agentcore-creator: AgentCore harness as a first-class conversion target** — new `references/agentcore-harness.md` (harness APIs, four skill sources with exact payloads, models via LiteLLM/Bedrock Mantle, memory/filesystem, versioning/endpoints, Step Functions, harness-vs-Runtime decision grid); Phase 2 gains a deploy-target decision gate and Phase 4 becomes dual-path — Path A attaches plugin skills unchanged as git/s3 SKILL.md sources into a `CreateHarness` config (no code-gen), Path B keeps the existing Strands/Runtime script

### Changed
- **project-init: pr-autofix — 5 iterations (was 3), implementer promoted to opus/medium (was sonnet/high)** — 3 rounds was too tight for review loops that surface findings incrementally (a fix that clears round-1 feedback often uncovers round-2 feedback the same panel hadn't reached yet); raised the ceiling to 5. Separately, the implementer subagent moves from `sonnet`+`high` to `opus`+`medium`: the implementer's job is edit-only mechanical application of an already-approved plan, so reasoning depth (`high`) buys nothing, but opus's stronger multi-file edit reliability directly cuts fix-loop iterations — a plan-approved edit that needs a second pass costs a full extra poll-fix-push cycle here, not just one subagent call, so the reliability trade dominates the token-cost trade
- **all plugins: per-agent `effort` frontmatter + DeepSWE-based model tiering** — every agent now declares a reasoning-effort tier alongside `model`, following the DeepSWE v1.1 leaderboard (all Claude curves knee at HIGH; opus HIGH beats sonnet HIGH on both score and cost since sonnet burns 2x+ agent steps): `opus`+`xhigh` for 9 judgment/synthesis gates, `opus`+`high` for 11 multi-step diagnosis/build workers promoted from sonnet (eks, network, storage, database, observability, analytics, reactive-presentation, workshop, brochure, architecture/animated-diagram), `sonnet`+`medium` for single-artifact writers, `sonnet`+`low` for pure dispatch/scan; supersedes PR #62's sonnet-worker rule (root `CLAUDE.md` Agent File Format updated)
- **project-init: pr-autofix model tiering + worktree isolation** — fix planning runs on Fable/Opus (inline when the host already runs a strong tier, otherwise a strong-model subagent); implementation is delegated to a bundled edit-only `pr-autofix-implementer` agent (enforced `tools:` — no Bash/network) working in a disposable git worktree, with a read-only `pr-autofix-planner` agent for the plan; all landing mechanics extracted to a stage-gated, unit-tested pipeline script (`scripts/land_delta.sh` — execution-surface denylist, cleanliness/containment/equality gates, user-edit-preserving rollback), and the host lands only the plan-approved delta — the user's uncommitted changes stay out of the implementer's working path (checkout-level isolation, not a security sandbox)
- **agentcore-creator: refresh 2026 AgentCore feature coverage** — mapping-rules now records GA statuses (harness GA 2026-06-17, Evaluations GA 2026-03 + Recommendations/Batch Eval/A-B GA 2026-06, Policy GA 2026-03 + Bedrock Guardrails 2026-06, Managed Knowledge Base GA, Web Search GA, CDK L2 stable, CLI v0.19) and a new Harness Conversion mapping table; agent/skill/doc-site pages and marketplace descriptions updated to match

### Fixed
- **aws-content-plugin: workshop-agent completion gate contradicted the 90-point exempt scale** — the agent hardcoded "PASS (≥85)" in its workflow and Quality Review sections while Workshop content is Visual-Testing-exempt and judged on the 90-point scale (PASS ≥77), so valid 77-84 PASS verdicts were rejected by the agent's own rules; both gates now reference the exempt scale (doc-sites mirrors and the workshop-creator CQP reference synced)
- **kiro: `/kiro:delegate` silently wrote code nowhere** — `kiro_setup.py` generated `.kiro/agents/{kiro-implementer,kiro-reviewer}.json` with Claude Code's nested `preToolUse` hook shape (`{"matcher","hooks":[{"type","command"}]}`); kiro-cli 2.11.1 requires a FLAT shape (`{"matcher","command"}`) and rejects the nested form with `missing field \`command\`` — `kiro-cli agent validate` exits 0 even on that error, so the bad config went undetected, kiro-cli silently fell back to its default agent, and every fs_write/fs_read/execute_bash call was rejected with "no user to approve" (headless mode has no auto-approval on the default agent). Both agent templates now emit the flat shape, `write-agents` validates the written files via `kiro-cli agent validate` (checking stderr for "error", not the exit code) and fails loudly instead of writing a config that silently doesn't work, and `references/spec-format.md`/`SKILL.md` now spell out task-sizing rules (one task = one layer, ≤5 files, ordered by dependency) so a multi-layer request gets decomposed by the orchestrator instead of handed to Kiro as one oversized task that dies against `delegate.timeout`. Follow-up: the new validation itself fail-opened on a timeout/OSError launching `kiro-cli` (only PATH-absence should fail open) and skipped re-validating a FILE ALREADY ON DISK on a non-`--force` re-run — the exact "re-run write-agents after seeing the ❌" recovery move a user would take reproduced the silent-bad-config problem this check exists to catch. Both are now fail-closed once kiro-cli is on PATH, and the skip-exists path re-validates instead of trusting the old file. Second follow-up: the exit-0 success check only read `stderr`, asymmetric with the exit-nonzero branch which reads both streams — a kiro-cli build that prints its validation error to stdout while still exiting 0 (the exact untrustworthy-exit-code behavior this function exists to work around) would sail past it; now checks both streams, and treats ANY non-empty output as failure (a confirmed-clean file produces empty stdout+stderr) rather than matching a specific substring, so a future kiro-cli release rewording or relocalizing its error text can't silently defeat the check. Third follow-up: `verify_agents()` — the check the delegate pipeline actually trusts before every run — only compared the on-disk JSON against the generator's own dict output, so a file that `write_agents` itself had already flagged INVALID (byte-identical to the generator's output, but rejected by kiro-cli — exactly this bug's shape) would still pass `verify_agents`'s dict-equality check and be trusted; `verify_agents` now re-runs the same `kiro-cli agent validate` check, closing the one path that could still reintroduce the silent-fallback failure this whole fix exists to prevent

## [1.14.1] - 2026-07-15

### Changed
- **aws-content-plugin: rename the `profile-page` skill to `gh-home`** — the skill targets the GitHub Pages user-site home, so the name now says so; also adds a usage-guide section with explicit prerequisites (public Pages repo, authenticated `gh` CLI; optional LinkedIn URL and per-repo Demo URLs)

## [1.14.0] - 2026-07-15

### Added
- **aws-content-plugin: new `profile-page` skill** — builds a personal profile / developer-portfolio page as one self-contained responsive HTML (sidebar identity + experience timeline + project cards with GitHub / Live / optional per-repo Demo links); curates projects from the user's GitHub via `gh` with Pages-enabled repos first, takes an optional LinkedIn URL (WebFetch, user-confirmed candidate facts, never fabricated), and reuses brochure's `check_brochure.py` self-check — now parameterized with `--mobile-breakpoint` ([#119](https://github.com/Atom-oh/oh-my-cloud-skills/pull/119))

### Changed
- **pr-review + co-agent: `gpt-5.5` deprecated, bump to `gpt-5.6` variants** — the pr-review CI panel's `kiro-gpt` cell moves to `gpt-5.6-terra`; co-agent's default `codex` panel model moves to `openai.gpt-5.6-sol` (ADR-014)
- **co-agent: update default panel models** — kiro-cli's single `model` (used under `profile: default`, e.g. the hybrid gate's verify phase) is now `claude-opus-4.8`; codex is now `openai.gpt-5.5` (superseded by ADR-014 above, `openai.gpt-5.6-sol`) at `effort: high`; agy is now `Gemini 3.1 Pro (High)` ([#112](https://github.com/Atom-oh/oh-my-cloud-skills/pull/112))

### Fixed
- **co-agent: `/co-agent:setup` kept suggesting to install an already-installed official `codex` plugin** — `detect_plugin()` only matched a marketplace directory's basename against the peer's own git repo name, but Claude Code's installer names the on-disk marketplace directory after `marketplace.json`'s own `"name"` field instead; added a second signal that verifies both the marketplace's identity and that the matched entry's `source` resolves to a real, in-tree directory ([#110](https://github.com/Atom-oh/oh-my-cloud-skills/pull/110))

## [1.13.0] - 2026-07-07

### Added
- **project-init: live GitHub metrics + langgraph-style README header** for `/generate-readme` — a new stdlib-only helper detects `owner/repo` from the git remote, fetches metrics via `gh` with an unauthenticated `urllib` fallback, and renders a centered, self-updating shields.io badge header; never raises to the shell (graceful `gh` → HTTP → git-only degradation) ([#97](https://github.com/Atom-oh/oh-my-cloud-skills/pull/97))
- **co-agent hybrid review gate + parallel implement waves** — `/co-agent:harness`'s default review mode is now `hybrid` (parallel find → chair triage → parallel verify), and the implementer runs disjoint-file task waves in parallel instead of one task at a time ([#101](https://github.com/Atom-oh/oh-my-cloud-skills/pull/101))
- **co-agent role-based model tiering** — place cost-efficient models per role instead of one model everywhere: a strong model for the chair (triage/synthesis), cheap breadth for the find panel, each AI's strongest model for verify, and a separately configurable `implementer_model`/`implementer_effort` for the harness write path ([#104](https://github.com/Atom-oh/oh-my-cloud-skills/pull/104))
- **co-agent: Kiro, Codex, and Agy now share one distilled `AGENTS.md`** context file instead of per-AI copies, closing drift between panel members' project context

### Removed
- **co-agent: drop the deprecated `gemini` CLI fallback** — Agy is now the sole Gemini-family panel member, completing the ADR-010 migration started in 1.11.0 ([#101](https://github.com/Atom-oh/oh-my-cloud-skills/pull/101))

### Fixed
- **co-agent: `/co-agent:setup`'s `agy` preflight probe always timed out** even though a direct `agy` call answers in 11-18s — the probe's stdin-channel prompt phrased the instruction as a read-verb ("read ... from stdin"), which made `agy` try to invoke a second, literal stdin read that hit an already-closed pipe and hung to the full timeout; rephrased as a preposition ("the text you received via stdin") ([#107](https://github.com/Atom-oh/oh-my-cloud-skills/pull/107))
- **co-agent: `codex`'s setup probe failed outside a trusted git directory** and used too tight a timeout for cold starts — pass `--skip-git-repo-check` (probe-only) and raise the probe timeout 20s → 45s
- **co-agent: replace the sole model attributed to hallucinated/unfounded review findings** — `kimi-k2.5` accounted for 7 dismissed panel claims across this repo's own PR history and 0 for any other model, plus repeated zero-response coverage degradation in CI; the default Kiro find panel now uses `minimax-m2.5` ([#109](https://github.com/Atom-oh/oh-my-cloud-skills/pull/109))
- **co-agent: consensus verdict parsing dropped a real veto** when a peer drifted to `BLOCKED:`/`PASSED` instead of the exact `BLOCK:`/`PASS` — now accepts both variants
- **co-agent: harness `capture-diff` could silently return an empty diff** once a peer committed inside its worktree (it diffed against an implicit, now-stale `HEAD`) — pins an absolute base SHA at `worktree add` time and diffs against that instead
- **co-agent: `cumulative-diff` duplicated a path-normalization bug already fixed in `scope_guard.py`** — now reuses the same `allowed_set()` implementation instead of a second copy

### Security
- **co-agent harness: a crafted worktree diff could escape the task's scope lock** — `scope_guard.py`'s `lstrip("./")` collapsed `../../src/foo.py` to `src/foo.py`, letting an out-of-plan file slip past the allow-list; now uses `posixpath.normpath` and fails closed on any residual `..` escape
- **co-agent harness: the worktree's base-SHA marker was readable by the sandboxed peer** via `git -C <worktree> rev-parse --git-dir`, letting it discover the scope boundary from inside the sandbox; the marker now lives host-side, under the main repo's git directory

### Changed
- Bump all plugins and `marketplace.json` to 1.13.0

## [1.12.1] - 2026-06-26

### Fixed
- **co-agent: `/co-agent:setup` (and `/co-agent:harness`, skill Step 0) couldn't find their scripts when run from any directory other than the marketplace repo root.** They used `${CLAUDE_PLUGIN_ROOT:-plugins/co-agent}`, but Claude Code only substitutes the plain `${CLAUDE_PLUGIN_ROOT}` token (not the bash `:-default` form) and does not export `CLAUDE_PLUGIN_ROOT` into the Bash tool — so the literal reached the shell with the var unset and resolved `plugins/co-agent` against the user's cwd (`No such file or directory`). Switched all three to the plain `${CLAUDE_PLUGIN_ROOT}` form, matching `configure`/`consensus`/`sync-context`

### Documentation
- **README: Codex CLI installation** — the repo is also a Codex plugin marketplace (`.agents/plugins/marketplace.json`); document `codex plugin marketplace add` + the `codex /plugins` picker, repo-scoped auto-discovery, and that co-agent makes Codex the chair under `CO_AGENT_HOST=codex` (EN + KO)

### Changed
- Bump all plugins and `marketplace.json` to 1.12.1

## [1.12.0] - 2026-06-25

### Added
- **co-agent PR consensus gate** (`PreToolUse(Bash)` hook) — at `gh pr create`, fan the PR diff out to the multi-AI panel in parallel and **block the PR (exit 2) on a quorum** (default: majority of voting peers AND ≥2) flagging CRITICAL/MAJOR. **Opt-in, default off, fail-open** — any internal error / all-peer timeout / no usable peer allows the PR. Data boundary before fan-out: a hunk-aware full-diff secret-scan (AWS/GitHub/Slack/OpenAI/Anthropic/Google + quoted/unquoted env) refuses to send a diff that **adds** a secret, the peer subprocess env is sanitized of credential-looking vars per peer, and the untrusted diff never enters `argv` (stdin / temp-file channels; reviewers run read-only/sandboxed). Bypass via `CO_AGENT_PR_GATE=off` or `pr_gate.enabled=false` ([#96](https://github.com/Atom-oh/oh-my-cloud-skills/pull/96))
- **co-agent `/co-agent:harness`** — host-designs / peer-implements / panel-reviews orchestrator: the host owns the design, the failing test, and every commit; a cross-provider peer implementer writes code only inside an isolated git worktree under a workspace-write sandbox; the consensus gate reviews and only the captured, scope-guarded worktree diff lands. Opt-in, local commits only ([#94](https://github.com/Atom-oh/oh-my-cloud-skills/pull/94))
- **co-agent `/co-agent:setup`** — panel-readiness preflight: detect each peer's best access path (official plugin → raw CLI + install nudge → none), probe real CLI usability, and write a readiness summary (`.claude/co-agent-panel.local.json`) the review / consensus / harness flows consult before fanning out ([#94](https://github.com/Atom-oh/oh-my-cloud-skills/pull/94))

### Changed
- Bump all plugins and `marketplace.json` to 1.12.0

## [1.11.0] - 2026-06-14

### Added
- **co-agent Antigravity (`agy`) panel member** — Google Antigravity joins the panel as the Gemini-family member (default model `Gemini 3.1 Pro (High)`; adapter `agy -p "<P>" --model "<token>" --sandbox`, read-only via `--sandbox`). **Supersedes the deprecated `gemini` CLI** — when both are installed the fan-out runs `agy` and skips `gemini`; `gemini` still runs if `agy` is absent. Wired across all modes (Review/Decide/ADR + consensus). `MODEL_RE` relaxed to allow the spaced/parenthesized model token (e.g. `Gemini 3.1 Pro (High)`) while still blocking shell metacharacters ([#69](https://github.com/Atom-oh/oh-my-cloud-skills/pull/69))

### Changed
- **co-agent doc-sync-aware `CLAUDE.md` hook** — the `PostToolUse(CLAUDE.md)` hook message names `/sync-docs` as a trigger (and the affected `AGENTS.md`/`GEMINI.md`), and `/co-agent:configure` recommends `autosync on` so the AI context regenerates as part of a doc sync — closing the loop on the co-agent side without forking the upstream-synced `/sync-docs` ([#68](https://github.com/Atom-oh/oh-my-cloud-skills/pull/68))
- Bump all plugins and `marketplace.json` to 1.11.0

### Fixed
- **co-agent: stop bare-`kiro` invocation in consensus** — `pairs` emits the panel **key** (`kiro`, `antigravity`), not the runnable binary (`kiro-cli`, `agy`); add a `BINARIES` map + `co_agent_config.py binary <ai>` source-of-truth, loud guards at the `pairs`→fan-out boundary, and a regression test. Also replace the stale `/kiro-cli:review` slash-delegation (Review mode) with the headless `kiro-cli chat` adapter ([#71](https://github.com/Atom-oh/oh-my-cloud-skills/pull/71))

## [1.10.0] - 2026-06-14

### Added
- **brochure skill + agent** (`aws-content-plugin`) — single-page responsive online brochure (landing page) for an AWS solution as one self-contained HTML file: hero + value + features + embedded architecture diagram + CTA, accessibility/responsive (mobile/tablet/PC) checks, deployed publicly via GitHub Pages ([#63](https://github.com/Atom-oh/oh-my-cloud-skills/pull/63))
- **architecture-diagram spec-driven layout engine** — `layout_aws.py` (YAML spec → `.drawio`) with golden exemplars; serverless `stages` + multi-region + hybrid block-composition engines; design scoring + layout gate in `lint_layout`; embedded shared AWS icons in `.drawio` (AgentCore + any official icon) and a sketch-style `.excalidraw` generator ([#55](https://github.com/Atom-oh/oh-my-cloud-skills/pull/55), [#61](https://github.com/Atom-oh/oh-my-cloud-skills/pull/61))
- **project-init `decision-reconcile` skill** — detect contradictions across accumulated ADRs (`ADR-NNN`) and ADR-vs-reality drift via a diverse multi-agent panel, then draft a superseding ADR; local-only ([#56](https://github.com/Atom-oh/oh-my-cloud-skills/pull/56), [#57](https://github.com/Atom-oh/oh-my-cloud-skills/pull/57))
- **reactive-presentation** — `theme.mode:dark` build option, per-slide theme + adaptive logo (light:dark mix), per-theme native logos (no blanket invert)

### Changed
- **Per-agent model tiers (quality-first)** — retier all plugin agents by deliverable: Opus for the judgment/synthesis gates (`content-review-agent`, `wellarchitected-agent`, `co-agent` chair) and high-stakes orchestration/conversion/IAM (`ops-coordinator-agent`, `agentcore-creator-agent`, `iam-agent`), Sonnet for generation + diagnosis workers; reviewed by a multi-AI panel ([#62](https://github.com/Atom-oh/oh-my-cloud-skills/pull/62))
- **reactive-presentation token economy** — lean SKILL.md/CLAUDE.md (progressive disclosure) + a single accurate SECTION INDEX with spanning-context guidance for the 25K reference docs ([#64](https://github.com/Atom-oh/oh-my-cloud-skills/pull/64))
- Bump all plugins and `marketplace.json` to 1.10.0

### Fixed
- `agentcore-creator`: use the real AgentCore MCP tool names (ADR-009) ([#60](https://github.com/Atom-oh/oh-my-cloud-skills/pull/60))

## [1.9.0] - 2026-06-10

### Added
- **reactive-presentation v1.9.0 token design system** — a design-token foundation (type/spacing/radius/shadow/color-role/motion/z), light-default dual-theme scopes with token-backed component primitives, a tokenized `theme.css`, and `design-tokens.css` shipped. PPTX/brand extraction drives the core tokens, and `validate` gains design-lint rules (raw-hex / inline-style / off-scale / raw-rgba / overflow) ([#53](https://github.com/Atom-oh/oh-my-cloud-skills/pull/53))
- **reactive-presentation content-quality layer** — structured speaker-note schema (`NOTE_STRUCTURE` lint), slide-title voice guidance (`TITLE_LENGTH` lint, scoped to content slides), a consolidated "Forbidden AI-slide-tells" section, and a content-review source-omission cross-check ([#54](https://github.com/Atom-oh/oh-my-cloud-skills/pull/54))

### Changed
- Bump all plugins and `marketplace.json` to 1.9.0

## [1.8.0] - 2026-06-10

### Added
- **co-agent consensus pipeline** — autonomous doc→plan→implementation with cross-family multi-model consensus gates. Stage A (P0–P2 plan gate), Stage B (P3 session-gated autonomous TDD implement loop with `scope_guard.py` file-set lock + Stop/PostToolUse hooks), Stage C (P4 final gate on the cumulative scoped diff + P5 report + full-pipeline default + resume). New scripts: `consensus_state.py`, `parse_plan.py`, `scope_guard.py`, `consensus_hooks.py`; `/co-agent:consensus` gains `plan`/`review`/`implement` sub-modes ([#49](https://github.com/Atom-oh/oh-my-cloud-skills/pull/49), [#50](https://github.com/Atom-oh/oh-my-cloud-skills/pull/50), [#51](https://github.com/Atom-oh/oh-my-cloud-skills/pull/51))
- **co-agent Kiro multi-model panel** — mainstay panel opus / kimi-k2.5 / glm-5 (cross-vendor via the Kiro router), `deep` by default ([#52](https://github.com/Atom-oh/oh-my-cloud-skills/pull/52))

### Changed
- Bump all plugins and `marketplace.json` to 1.8.0

## [1.7.2] - 2026-06-09

### Added
- **co-agent consensus mode (Phase 1)** — higher-confidence multi-AI review. `check_citations.py` classifies each finding against the diff (`supported`/`needs-review`/`unsupported`); per-AI model lists with a `deep` profile + `MAX_CALLS=12` cap + round-robin trim + cost matrix; `/co-agent:consensus` review-only command + SKILL Mode 5. Reshaped by a co-agent panel review (cut confidence-voting, persistent logs, autonomous-fix-by-default; `--apply` fix loop deferred to Phase 2) ([#47](https://github.com/Atom-oh/oh-my-cloud-skills/pull/47))
- **Codex plugin support** — `.codex-plugin/plugin.json` for all 6 plugins, `.agents/plugins/marketplace.json` (codex marketplace), and `scripts/test-codex-plugins.py` validator wired into the structure tests
- **AI context files** — `AGENTS.md` (Codex) + `GEMINI.md` (Gemini) distilled from `CLAUDE.md` via `/co-agent:sync-context`
- Bedrock reactive-presentation demo under `docs/static/demos/`

### Changed
- Bump all plugins and `marketplace.json` to 1.7.2

## [1.7.1] - 2026-06-02

### Added
- **co-agent `sync-context`** — distill `CLAUDE.md` into the per-AI context files the panel auto-loads: `AGENTS.md` (Codex, ~32 KiB cap) and `GEMINI.md` (Gemini, kept lean); Kiro reads `CLAUDE.md` directly. Available as Mode 4 and the standalone `/co-agent:sync-context` command. `check_ai_context.py` validates marker, size caps, staleness (`claude-md-sha`), and runs a secret scan; hand-written files (no marker) and `AGENTS.override.md` are protected ([#39](https://github.com/Atom-oh/oh-my-cloud-skills/pull/39), [#41](https://github.com/Atom-oh/oh-my-cloud-skills/pull/41))
- **`/co-agent:configure`** — tune the panel (per-AI `model`, Codex `effort`, `enabled`, `timeout`). Only headless-settable options are exposed (effort is Codex-only — Gemini/Kiro have no headless effort flag); the fan-out reads `co_agent_config.py` so settings are live (a disabled AI is dropped; model/effort flags are injected). Layered config: `co-agent.defaults.json` (committed) <- `.claude/co-agent.local.json` (gitignored) ([#40](https://github.com/Atom-oh/oh-my-cloud-skills/pull/40))
- **Opt-in autosync** — `/co-agent:configure set autosync on` makes the `CLAUDE.md` PostToolUse hook tell Claude to re-run `/co-agent:sync-context` when the generated context files drift stale (default off = reminder only) ([#41](https://github.com/Atom-oh/oh-my-cloud-skills/pull/41))
- co-agent usage guide + Docusaurus docs refresh (overview/installation/skill, sidebar/navbar `kiro-review` -> `co-agent`)

### Changed
- Bump all plugins and `marketplace.json` to 1.7.1

## [1.7.0] - 2026-05-31

### Changed
- **Rename `kiro-review` -> `co-agent`** — reframe as a multi-AI collaboration plugin. Chairs a panel of installed CLIs (Kiro `kiro-cli chat --no-interactive`, Codex `codex exec -s read-only`, Gemini `gemini -p -o text`), fanning the same prompt out in parallel and letting Claude synthesize consensus vs. dissent. Three modes: multi-AI Review (code/arch + Well-Architected -> PASS/REVIEW/FAIL), Decide (decision support when unsure), ADR co-authoring (Nygard format, `/add-adr` integration). Degrades gracefully — no CLI present means Claude answers solo
- Detect the panel by binary presence only (`command -v`); `kiro-cli` authenticates via interactive login **or** `KIRO_API_KEY`, so no env-key pre-gating
- Pass context via STDIN only (never interpolate untrusted repo content into the command line); treat panel output as advisory (prompt-injection boundary); per-CLI `timeout` so one hung CLI can't block synthesis
- Tighten skill triggers to multi-AI intent only (drop generic "code review"/"decide"/"adr" that collided with other skills)
- Bump all plugins and `marketplace.json` to 1.7.0

## [1.6.0] - 2026-05-30

### Added
- **AWS DevOps Agent** integration in `aws-ops-plugin` ops-observability — incident escalation via Agent Spaces, CloudWatch→EventBridge→Lambda→webhook wiring, `aws devopsagent create-backlog-task`, and Kiro-compatible mitigation plans ([#25](https://github.com/Atom-oh/oh-my-cloud-skills/pull/25))
- **AWS Security Agent** integration in `aws-ops-plugin` ops-security-audit — design/code security review, on-demand penetration testing, org requirements, CI/CD API
- Open-source observability reference in ops-observability — OpenTelemetry, Grafana, Loki, Tempo, ClickHouse, VictoriaMetrics/Thanos/Mimir — plus a Version Compatibility section (ClickHouse server ↔ OTel exporter ↔ operator ↔ distro pinning)
- `/add-reference-doc` command and implementation-reference-docs workflow in `project-init` (synced from upstream): init-project Step 4.5, sync-docs Phase 1.5, doc-sync-checker validation
- Opus 4.8 compatibility section in `agentcore-creator` mapping rules and code templates (4.6/4.7 retained as history)

### Changed
- Migrate `agentcore-creator` `opus` alias to `us.anthropic.claude-opus-4-8` (MODEL_MAP + mirrored docs); bump `agentcore-creator-agent` to opus; de-stale "most capable" 4.6/4.7 claims
- Rewrite `kiro-review` Kiro CLI integration for Kiro CLI 2.5.0 — delegate via `kiro-cli chat --no-interactive` (headless) instead of the non-existent `Skill(skill: "kiro-cli:review")`; fix detection with `command -v kiro-cli`; drop over-provisioned `model: opus` pin (inherit parent session)
- Harden `project-init` rsync exclude list so upstream sync no longer clobbers local CLAUDE.md/SKILL.md customizations
- Bump all plugins and `marketplace.json` to 1.6.0

### Fixed
- `kiro-review`: add the missing delegation mechanism (`kiro-cli:review` is a slash command, not a skill); fix adversarial review (`/kiro-cli:adversarial-review`, not `review --adversarial`); guard `git diff | kiro-cli` pipes against empty-diff false PASS and kiro-cli runtime failure
- `pr-autofix`: fix invalid `gh pr reviews` → `gh pr view --json reviews`; fix `&&/||` precedence that ran `npx tsc` with no `package.json`; fix fail-open build verification that hid compiler errors (now keeps stderr visible and blocks commit on failure); update model IDs/Co-Authored-By to Opus 4.8
- Fix wrong Altinity ClickHouse operator Helm repo URL (`docs.altinity.com` → `helm.altinity.com`)

## [1.5.1] - 2026-05-14

### Changed
- Migrate all plugin Bedrock model IDs from Claude 4.0 (`-4-20250514`) to current models (Opus 4.7, Sonnet 4.6, Haiku 4.5) in `agentcore-creator` MODEL_MAP and templates
- Update generated agent code (`convert_plugin_to_agentcore.py`) to include 4.7-compatible defaults (`max_tokens=16000`, adaptive thinking guidance, no `temperature`/`top_p`/`top_k`)
- Update `kiro-power-converter` model examples from `claude-sonnet-4` to `claude-sonnet-4-6`

### Added
- Add Model-Specific Compatibility Notes section to `agentcore-mapping-rules.md` (Opus 4.7 breaking changes, 4.6 deprecations, Haiku 4.5 limitations)
- Add Model Selection Guide table to `agentcore-create/SKILL.md` Phase 2.1 with Bedrock model recommendations per task profile
- Add Recommended Inference Defaults section to `agent-code-templates.md` with 4.7-specific defaults
- Add Subagent Spawn Policy section to `aws-content-plugin/CLAUDE.md` (4.7 compatibility — explicit spawn/skip conditions)

### Fixed
- Fix invalid model ID `anthropic.claude-sonnet-4-6-20250514` in AIOps demo pages (date suffix was Claude 4.0 release date, not 4.6)

## [1.5.0] - 2026-04-29

### Added
- Add iterative refinement (rejection loop) for reactive-presentation quality validation ([#19](https://github.com/Atom-oh/oh-my-cloud-skills/pull/19))
- Add pr-autofix skill to project-init plugin ([#23](https://github.com/Atom-oh/oh-my-cloud-skills/pull/23))

### Fixed
- Fix PPTX theme extraction color palette using luminance-based selection instead of dk/lt slot names (handles inverted dark themes)
- Fix PPTX theme extraction footer misidentification with bottom-20% position filter
- Fix PPTX theme extraction layout background with keyword-based matching and `<p:bgRef>` XML parsing
- Fix PDF export CSS path resolution with dynamic `_resolveCommonPath()` instead of hardcoded `../common/`
- Fix PPTX export missing theme background by extracting colors from `window.__remarpTheme` in block HTML
- Fix TOC export block card selector to support both `<div class="block-card">` and `<a class="block-card">` structures

## [1.4.0] - 2026-04-14

### Added
- Add agentcore-creator plugin with interactive 5-phase workflow for Bedrock AgentCore deployment
- Add project-init plugin with 8 commands for project scaffolding and documentation sync
- Add kiro-review plugin for comprehensive architecture deep review via Kiro CLI
- Add Well-Architected Framework 6-pillar review to aws-ops-plugin (wellarchitected-agent, 100-point scoring) ([#16](https://github.com/Atom-oh/oh-my-cloud-skills/pull/16))
- Add slide-fix skill for Remarp slide issue annotation processing
- Add issue annotation system for Remarp VSCode extension (prompt bar, `<!-- issue: -->` annotations, issue badges in sidebar)
- Add PPTX image export via html2canvas iframe capture
- Add Pandoc-style colon-count nesting for ::: blocks with stack-based block parser
- Add PPTX template extraction with Slide Master metadata, --figma and --stitch design source options
- Add session-context, secret-scan, doc-sync hooks and safety permissions

### Changed
- Simplify issue annotation syntax from `<!-- !issue: -->` to `<!-- issue: -->`
- Replace submit button with /slide-fix guidance toast (remove `claude --print` CLI dependency)

### Fixed
- Fix XSS defense and frontmatter regex in preview.ts
- Fix 3 bugs in stack-based block parser
- Fix canvas editor slide context targeting
- Fix canvas DSL whitespace handling around commas
- Fix regex group indices in _group_p_with_list and NameError in compile_preset_to_js
- Restore kiro-review SessionStart hook and fix converter quote escaping

## [1.2.5] - 2026-04-06

### Added
- Add README.md to README.ko.md auto-translate hook
- Add live diagram demos to documentation site ([#11](https://github.com/Atom-oh/oh-my-cloud-skills/pull/11))
- Add detailed skill guides with 8 demo pages ([#9](https://github.com/Atom-oh/oh-my-cloud-skills/pull/9))

### Fixed
- Fix table th/td font-size to inherit from parent table element
- Fix fragment wrappers crossing column boundaries and heading-group spacing
- Fix :::click blocks not working when nested inside :::left/:::right columns

## [1.2.3] - 2026-03-20

### Added
- Add Canvas complexity gate in content-review-agent
- Add HTML Architecture pattern and STOP gate in reactive-presentation SKILL.md
- Add interactive slide patterns guide (interactive-patterns-guide.md)

### Changed
- Strengthen canvas vs HTML selection guidance in agent and SKILL.md decision guides
- Fix monitoring/dashboard mapping from canvas to html+script

### Fixed
- Fix canvas overuse -- agent no longer defaults all diagrams to :::canvas

## [1.2.2] - 2026-03-15

### Added
- Add orthogonal arrow routing to Canvas DSL
- Add data visualization design guide for reactive-presentation
- Add visual editor, canvas editor, and CSS editor to Remarp VSCode extension
- Add :::prompt block support and per-block export buttons
- Add AIOps 90-minute presentation demo

### Changed
- Enhance plugin skills with hooks, references, and improved patterns
- Migrate plugins to latest Claude Code format with hooks, validation, and token optimization

### Fixed
- Fix blocks config bug in multi-block presentations

## [1.2.1] - 2026-03-05

### Added
- Add Remarp VSCode extension completions and preview improvements
- Add Remarp-first workflow documentation

### Changed
- Enhance canvas animation prompts, PPTX theme extractor, and kiro conversion rules
- Update plugin CLAUDE.md keyword routing and team workflow docs
- Remove hardcoded model field from agent frontmatter

### Fixed
- Strip 'Block N:' prefix from slide titles in converter
- Correct `../common/` to `./common/` asset paths in remarp_to_slides.py
- Fix 3 rendering bugs in remarp_to_slides.py converter

## [1.1.0] - 2026-03-03

### Added
- Add kiro-power-converter plugin for Claude Code to Kiro Power conversion
- Add Docusaurus documentation site with GitHub Pages deployment
- Add i18n support (ko default, en placeholder)
- Add Remarp VSCode extension for syntax highlighting and preview
- Add audience frontmatter field and strengthen agent planning questions

### Changed
- Replace cloudwatch-agent with observability-agent, add analytics-agent
- Make Remarp the default content authoring format for presentations

### Fixed
- Fix PPTX theme extraction with Slide Master layout details

## [1.0.0] - 2026-02-26

### Added
- Initial release
- Add aws-content-plugin: presentation, architecture diagram, animated diagram, document, gitbook, workshop agents
- Add aws-ops-plugin: EKS, network, IAM, observability, storage, database, cost, analytics, ops-coordinator agents
- Add reactive-presentation skill with Canvas animations, quizzes, and keyboard navigation
- Add content review quality gate (100-point scale)
- Add PPTX/PDF theme extraction
- Add AWS Architecture Icons integration (4,224 files)
- Add presenter view with speaker notes

[Unreleased]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.17.0...v2.0.0
[1.17.0]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.16.0...v1.17.0
[1.16.0]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.15.0...v1.16.0
[1.15.0]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.14.1...v1.15.0
[1.14.1]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.14.0...v1.14.1
[1.14.0]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.13.0...v1.14.0
[1.13.0]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.12.1...v1.13.0
[1.12.1]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.12.0...v1.12.1
[1.12.0]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.11.0...v1.12.0
[1.11.0]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.10.0...v1.11.0
[1.10.0]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.9.0...v1.10.0
[1.9.0]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.8.0...v1.9.0
[1.8.0]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.7.2...v1.8.0
[1.7.2]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.7.1...v1.7.2
[1.7.1]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.7.0...v1.7.1
[1.7.0]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.6.0...v1.7.0
[1.6.0]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.5.1...v1.6.0
[1.5.1]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.5.0...v1.5.1
[1.5.0]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.2.5...v1.4.0
[1.2.5]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.2.3...v1.2.5
[1.2.3]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.2.2...v1.2.3
[1.2.2]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.1.0...v1.2.1
[1.1.0]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/Atom-oh/oh-my-cloud-skills/releases/tag/v1.0.0
