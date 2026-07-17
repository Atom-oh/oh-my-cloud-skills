# Changelog

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **agentcore-creator: AgentCore harness as a first-class conversion target** — new `references/agentcore-harness.md` (harness APIs, four skill sources with exact payloads, models via LiteLLM/Bedrock Mantle, memory/filesystem, versioning/endpoints, Step Functions, harness-vs-Runtime decision grid); Phase 2 gains a deploy-target decision gate and Phase 4 becomes dual-path — Path A attaches plugin skills unchanged as git/s3 SKILL.md sources into a `CreateHarness` config (no code-gen), Path B keeps the existing Strands/Runtime script

### Changed
- **project-init: pr-autofix model tiering + worktree isolation** — fix planning runs on Fable/Opus (inline when the host already runs a strong tier, otherwise a strong-model subagent); implementation is delegated to sonnet subagents working in a disposable git worktree, and the host lands only the plan-approved delta — the user's uncommitted changes are physically out of reach
- **agentcore-creator: refresh 2026 AgentCore feature coverage** — mapping-rules now records GA statuses (harness GA 2026-06-17, Evaluations GA 2026-03 + Recommendations/Batch Eval/A-B GA 2026-06, Policy GA 2026-03 + Bedrock Guardrails 2026-06, Managed Knowledge Base GA, Web Search GA, CDK L2 stable, CLI v0.19) and a new Harness Conversion mapping table; agent/skill/doc-site pages and marketplace descriptions updated to match

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

[Unreleased]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.14.1...HEAD
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

---

<a id="korean"></a>

# 한국어

이 프로젝트의 모든 주요 변경 사항은 이 파일에 기록됩니다.
이 문서는 [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)를 기반으로 하며,
[Semantic Versioning](https://semver.org/spec/v2.0.0.html)을 따릅니다.

## [Unreleased]

### Added
- **agentcore-creator: AgentCore harness를 1급 변환 타깃으로 추가** — 신규 `references/agentcore-harness.md`(harness API, 4가지 스킬 소스 정확한 페이로드, LiteLLM/Bedrock Mantle 모델, 메모리/파일시스템, 버저닝/엔드포인트, Step Functions, harness-vs-Runtime 결정 그리드); Phase 2에 배포 타깃 결정 게이트, Phase 4는 이중 경로 — Path A는 플러그인 스킬을 git/s3 SKILL.md 소스로 무변환 attach하는 `CreateHarness` 설정(코드 생성 없음), Path B는 기존 Strands/Runtime 스크립트 유지

### Changed
- **project-init: pr-autofix 모델 티어링 + worktree 격리** — 수정 계획은 Fable/Opus에서 수립(호스트가 이미 상위 티어면 인라인, 아니면 강한 모델 서브에이전트)하고 구현은 일회용 git worktree에서 sonnet 서브에이전트가 수행; 호스트가 worktree diff를 계획과 대조해 승인분만 브랜치에 반영 — 사용자의 미커밋 변경은 물리적으로 격리
- **agentcore-creator: 2026 AgentCore 기능 커버리지 갱신** — mapping-rules에 GA 상태 기록(harness GA 2026-06-17, Evaluations GA 2026-03 + Recommendations/배치 평가/A-B GA 2026-06, Policy GA 2026-03 + Bedrock Guardrails 2026-06, Managed Knowledge Base GA, Web Search GA, CDK L2 stable, CLI v0.19) 및 Harness Conversion 매핑 표 신설; 에이전트/스킬/doc-site 페이지와 마켓플레이스 설명 동기화

## [1.14.1] - 2026-07-15

### Changed
- **aws-content-plugin: `profile-page` 스킬을 `gh-home`으로 이름 변경** — GitHub Pages 유저 사이트 메인(홈)을 만드는 스킬이므로 이름에 대상을 반영; 사용법 가이드에 준비물(public Pages repo, 로그인된 `gh` CLI, 선택: LinkedIn URL·repo별 Demo URL)을 명시한 섹션도 추가

## [1.14.0] - 2026-07-15

### Added
- **aws-content-plugin: 신규 `profile-page` 스킬 추가** — 개인 프로필/개발자 포트폴리오 페이지를 자기완결형 반응형 HTML 한 장으로 생성(사이드바 아이덴티티 + 경력 타임라인 + GitHub/Live/repo별 선택 Demo 링크의 프로젝트 카드); `gh`로 사용자의 GitHub에서 프로젝트를 큐레이션(Pages 활성 repo 우선)하고, 선택적 LinkedIn URL 입력(WebFetch, 사용자 확인 후보 사실만, 지어내지 않음)을 받으며, brochure의 `check_brochure.py` self-check를 재사용 — `--mobile-breakpoint` 파라미터화 ([#119](https://github.com/Atom-oh/oh-my-cloud-skills/pull/119))

### Changed
- **pr-review + co-agent: `gpt-5.5` deprecation 대응 `gpt-5.6` 계열로 교체** — pr-review CI 패널의 `kiro-gpt` 셀은 `gpt-5.6-terra`로, co-agent의 기본 `codex` 패널 모델은 `openai.gpt-5.6-sol`로 변경 (ADR-014)
- **co-agent: 패널 기본 모델 갱신** — kiro-cli의 단일 `model`(`profile: default`, 예: 하이브리드 게이트 verify 단계에서 사용)이 `claude-opus-4.8`로, codex가 `openai.gpt-5.5`(위 ADR-014로 `openai.gpt-5.6-sol`로 대체됨)(`effort: high`)로, agy가 `Gemini 3.1 Pro (High)`로 변경 ([#112](https://github.com/Atom-oh/oh-my-cloud-skills/pull/112))

### Fixed
- **co-agent: `/co-agent:setup`이 이미 설치된 공식 `codex` 플러그인에도 계속 설치를 권하던 문제 수정** — `detect_plugin()`이 marketplace 디렉터리 basename을 peer의 git repo 이름과만 비교했으나, 실제 Claude Code 설치기는 marketplace 디렉터리를 `marketplace.json`의 `"name"` 필드로 명명함; marketplace 신원과 매칭된 entry의 `source`가 실제 in-tree 디렉터리로 해석되는지를 함께 확인하는 두 번째 신호를 추가 ([#110](https://github.com/Atom-oh/oh-my-cloud-skills/pull/110))

## [1.13.0] - 2026-07-07

### Added
- **project-init: `/generate-readme`에 실시간 GitHub 지표 + langgraph 스타일 README 헤더 추가** — 신규 stdlib-only 헬퍼가 git remote에서 `owner/repo`를 감지하고, `gh`로 지표를 가져오되 실패 시 인증 없는 `urllib`로 폴백하며, 가운데 정렬된 자동 갱신 shields.io 배지 헤더를 렌더링. 셸로 예외를 던지지 않음(`gh` → HTTP → git-only 순 우아한 저하) ([#97](https://github.com/Atom-oh/oh-my-cloud-skills/pull/97))
- **co-agent 하이브리드 리뷰 게이트 + 병렬 구현 웨이브 추가** — `/co-agent:harness`의 기본 리뷰 모드가 `hybrid`(병렬 find → 체어 triage → 병렬 verify)로 변경, 구현자도 순차 1태스크 대신 겹치지 않는 파일 단위 태스크 웨이브를 병렬 실행 ([#101](https://github.com/Atom-oh/oh-my-cloud-skills/pull/101))
- **co-agent 역할별 모델 티어링 추가** — 전체에 한 모델을 쓰는 대신 역할별로 배치: 체어(triage/종합)엔 강한 모델, find 패널엔 저비용 breadth, verify엔 각 AI의 최강 모델, harness 쓰기 경로엔 별도 설정 가능한 `implementer_model`/`implementer_effort` ([#104](https://github.com/Atom-oh/oh-my-cloud-skills/pull/104))
- **co-agent: Kiro·Codex·Agy가 이제 하나의 증류된 `AGENTS.md`를 공유** — 패널 멤버별 개별 컨텍스트 파일 대신 단일 파일로 통일해 컨텍스트 드리프트 제거

### Removed
- **co-agent: deprecated된 `gemini` CLI fallback 제거** — Agy가 이제 Gemini 계열 패널의 유일한 멤버, 1.11.0에서 시작한 ADR-010 마이그레이션 완결 ([#101](https://github.com/Atom-oh/oh-my-cloud-skills/pull/101))

### Fixed
- **co-agent: `/co-agent:setup`의 `agy` 프리플라이트 프로브가 항상 타임아웃되던 문제 수정** — `agy`를 직접 호출하면 11-18초에 응답하는데도, 프로브의 stdin 채널 프롬프트가 "read ... from stdin"처럼 읽기-동사 형태로 지시해 `agy`가 두 번째 stdin 읽기를 실제로 시도하게 만들었고, 이미 닫힌 파이프에 걸려 풀 타임아웃까지 행(hang). 전치사형("the text you received via stdin")으로 재구성 ([#107](https://github.com/Atom-oh/oh-my-cloud-skills/pull/107))
- **co-agent: `codex`의 setup 프로브가 신뢰된 git 디렉터리 밖에서 실패하고 콜드스타트엔 타임아웃이 너무 짧던 문제 수정** — `--skip-git-repo-check`(프로브 전용) 추가, 프로브 타임아웃 20초 → 45초로 상향
- **co-agent: 근거 없는/할루시네이션 리뷰 지적의 유일한 원인 모델 교체** — `kimi-k2.5`가 이 저장소 자체 PR 이력에서 기각된 패널 지적 7건 중 전부를 차지(다른 모델은 0건)했고 CI에서 무응답 저하도 반복됨; 기본 Kiro find 패널을 `minimax-m2.5`로 교체 ([#109](https://github.com/Atom-oh/oh-my-cloud-skills/pull/109))
- **co-agent: consensus verdict 파싱이 실제 veto를 놓치던 문제 수정** — peer 응답이 정확한 `BLOCK:`/`PASS`가 아닌 `BLOCKED:`/`PASSED`로 흔들리면 누락됐던 것을 두 표기 모두 인식하도록 수정
- **co-agent: harness `capture-diff`가 조용히 빈 diff를 반환하던 문제 수정** — peer가 worktree 내부에서 커밋하면 암묵적이고 이미 stale해진 `HEAD` 기준으로 diff하던 것을, `worktree add` 시점에 고정한 절대 base SHA 기준으로 diff하도록 수정
- **co-agent: `cumulative-diff`가 `scope_guard.py`에서 이미 고친 경로 정규화 버그를 중복 보유하던 문제 수정** — 별도 구현 대신 동일한 `allowed_set()`을 재사용하도록 수정

### Security
- **co-agent harness: 조작된 worktree diff가 태스크 스코프 락을 탈출할 수 있던 취약점 수정** — `scope_guard.py`의 `lstrip("./")`가 `../../src/foo.py`를 `src/foo.py`로 붕괴시켜 계획 밖 파일이 allow-list를 통과할 수 있었음; 이제 `posixpath.normpath` 사용 + 남은 `..` 이탈 시 fail-closed
- **co-agent harness: worktree의 base-SHA 마커를 샌드박스 내 peer가 읽을 수 있던 취약점 수정** — `git -C <worktree> rev-parse --git-dir`로 샌드박스 안에서 스코프 경계를 알아낼 수 있었음; 마커를 host 측, 메인 저장소 git 디렉터리 하위로 이동

### Changed
- 모든 플러그인과 `marketplace.json`을 1.13.0으로 범프

## [1.12.1] - 2026-06-26

### Fixed
- **co-agent: `/co-agent:setup`(및 `/co-agent:harness`, 스킬 Step 0)이 마켓플레이스 저장소 루트가 아닌 디렉터리에서 실행되면 스크립트를 찾지 못하던 문제.** `${CLAUDE_PLUGIN_ROOT:-plugins/co-agent}`를 썼으나 Claude Code는 plain `${CLAUDE_PLUGIN_ROOT}` 토큰만 치환하고(bash `:-default` 형식 미지원) `CLAUDE_PLUGIN_ROOT`를 Bash 툴에 export하지 않으므로, 리터럴이 셸에 도달해 변수 미설정 상태로 `plugins/co-agent`를 사용자 cwd 기준으로 해석(`No such file or directory`). 셋 다 plain `${CLAUDE_PLUGIN_ROOT}` 형식으로 변경(`configure`/`consensus`/`sync-context`와 일치)

### Documentation
- **README: Codex CLI 설치법** — 이 저장소는 Codex 플러그인 마켓플레이스이기도 함(`.agents/plugins/marketplace.json`); `codex plugin marketplace add` + `codex /plugins` 선택기, 저장소 범위 자동 검색, `CO_AGENT_HOST=codex`에서 Codex가 의장이 되는 점을 문서화(EN + KO)

### Changed
- 모든 플러그인과 `marketplace.json`을 1.12.1로 범프

## [1.12.0] - 2026-06-25

### Added
- **co-agent PR 합의 게이트** (`PreToolUse(Bash)` 훅) — `gh pr create` 시점에 PR diff를 멀티-AI 패널에 병렬 팬아웃해 CRITICAL/MAJOR **정족수**(기본: 투표 peer의 과반 AND ≥2) 충족 시 **PR 차단(exit 2)**. **opt-in·기본 off·fail-open** — 내부 오류/전 peer 타임아웃/사용 가능한 peer 없음이면 PR 허용. 팬아웃 전 데이터 경계: hunk 인지 full-diff secret-scan(AWS/GitHub/Slack/OpenAI/Anthropic/Google + quoted/unquoted env)으로 시크릿을 **추가**하는 diff는 전송 거부, peer별 크리덴셜성 env 정화, untrusted diff는 `argv`에 미노출(stdin/temp-file 채널; reviewer는 read-only/sandbox 실행). `CO_AGENT_PR_GATE=off` 또는 `pr_gate.enabled=false`로 우회 ([#96](https://github.com/Atom-oh/oh-my-cloud-skills/pull/96))
- **co-agent `/co-agent:harness`** — host 설계 / peer 구현 / 패널 리뷰 오케스트레이터: host가 설계·failing 테스트·모든 커밋을 소유하고, cross-provider peer 구현자는 격리된 git worktree(workspace-write 샌드박스) 안에서만 코드를 작성하며, consensus 게이트가 리뷰하고 캡처된 scope-guard된 worktree diff만 반영. opt-in·로컬 커밋만 ([#94](https://github.com/Atom-oh/oh-my-cloud-skills/pull/94))
- **co-agent `/co-agent:setup`** — 패널 준비도 프리플라이트: peer별 최적 접근 경로(공식 plugin → raw CLI + 설치 안내 → none) 감지, 실사용 프로브, review/consensus/harness 흐름이 팬아웃 전 참조하는 readiness 요약(`.claude/co-agent-panel.local.json`) 기록 ([#94](https://github.com/Atom-oh/oh-my-cloud-skills/pull/94))

### Changed
- 모든 플러그인과 `marketplace.json`을 1.12.0으로 범프

## [1.11.0] - 2026-06-14

### Added
- **co-agent Antigravity(`agy`) 패널 멤버** — Google Antigravity가 Gemini 패밀리 멤버로 패널에 합류(기본 모델 `Gemini 3.1 Pro (High)`; 어댑터 `agy -p "<P>" --model "<token>" --sandbox`, `--sandbox`로 읽기전용). **deprecated된 `gemini` CLI를 대체** — 둘 다 설치 시 팬아웃은 `agy`만 쓰고 `gemini`는 스킵, `agy` 없으면 `gemini` 사용. 전 모드(Review/Decide/ADR + consensus)에 연결. `MODEL_RE`를 완화해 공백·괄호 포함 모델 토큰을 허용하되 셸 메타문자는 계속 차단 ([#69](https://github.com/Atom-oh/oh-my-cloud-skills/pull/69))

### Changed
- **co-agent doc-sync 인지형 `CLAUDE.md` 훅** — `PostToolUse(CLAUDE.md)` 훅이 `/sync-docs`를 트리거로 명시(영향 파일 `AGENTS.md`/`GEMINI.md`)하고, `/co-agent:configure`가 `autosync on`을 권장해 AI 컨텍스트가 doc sync의 일부로 재생성되도록 함 — upstream 동기화 대상 `/sync-docs`를 fork하지 않고 co-agent 쪽에서 루프를 닫음 ([#68](https://github.com/Atom-oh/oh-my-cloud-skills/pull/68))
- 모든 플러그인과 `marketplace.json`을 1.11.0으로 범프

### Fixed
- **co-agent: consensus에서 bare-`kiro` 호출 차단** — `pairs`는 패널 **키**(`kiro`, `antigravity`)를 내보내지만 실행 바이너리는 `kiro-cli`/`agy`. `BINARIES` 맵 + `co_agent_config.py binary <ai>` 단일 진실원천, `pairs`→팬아웃 경계 가드, 회귀 테스트 추가. Review 모드의 stale `/kiro-cli:review` 슬래시 위임도 headless `kiro-cli chat` 어댑터로 교체 ([#71](https://github.com/Atom-oh/oh-my-cloud-skills/pull/71))

## [1.10.0] - 2026-06-14

### Added
- **brochure 스킬 + 에이전트** (`aws-content-plugin`) — AWS 솔루션용 단일 페이지 반응형 온라인 브로셔(랜딩 페이지)를 자기완결 HTML 한 파일로: 히어로 + 가치 + 기능 + 임베드 아키텍처 다이어그램 + CTA, 접근성/반응형(모바일·태블릿·PC) 검증, GitHub Pages 공개 배포 ([#63](https://github.com/Atom-oh/oh-my-cloud-skills/pull/63))
- **architecture-diagram 스펙 기반 레이아웃 엔진** — `layout_aws.py`(YAML 스펙 → `.drawio`) + 골든 예제; 서버리스 `stages` + 멀티리전 + 하이브리드 블록 합성 엔진; `lint_layout` 디자인 스코어링 + 레이아웃 게이트; `.drawio`에 공유 AWS 아이콘 임베드(AgentCore + 모든 공식 아이콘) + 스케치 스타일 `.excalidraw` 생성기 ([#55](https://github.com/Atom-oh/oh-my-cloud-skills/pull/55), [#61](https://github.com/Atom-oh/oh-my-cloud-skills/pull/61))
- **project-init `decision-reconcile` 스킬** — 누적 ADR(`ADR-NNN`) 모순 및 ADR-현실 드리프트를 다양한 멀티-에이전트 패널로 탐지 후 superseding ADR 초안 작성; 로컬 전용 ([#56](https://github.com/Atom-oh/oh-my-cloud-skills/pull/56), [#57](https://github.com/Atom-oh/oh-my-cloud-skills/pull/57))
- **reactive-presentation** — `theme.mode:dark` 빌드 옵션, 슬라이드별 테마 + 적응형 로고(light:dark 혼합), 테마별 네이티브 로고(일괄 invert 제거)

### Changed
- **에이전트별 모델 티어 (품질 우선)** — 산출물 기준 전체 에이전트 재편: 판단/종합 게이트(`content-review-agent`, `wellarchitected-agent`, `co-agent` 의장)와 고위험 오케스트레이션/변환/IAM(`ops-coordinator-agent`, `agentcore-creator-agent`, `iam-agent`)은 Opus, 생성·진단 워커는 Sonnet; 멀티-AI 패널 리뷰 반영 ([#62](https://github.com/Atom-oh/oh-my-cloud-skills/pull/62))
- **reactive-presentation 토큰 이코노미** — lean SKILL.md/CLAUDE.md(progressive disclosure) + 25K 레퍼런스 문서의 정확한 단일 SECTION INDEX·스패닝 컨텍스트 가이드 ([#64](https://github.com/Atom-oh/oh-my-cloud-skills/pull/64))
- 모든 플러그인과 `marketplace.json`을 1.10.0으로 범프

### Fixed
- `agentcore-creator`: 실제 AgentCore MCP 도구 이름 사용 (ADR-009) ([#60](https://github.com/Atom-oh/oh-my-cloud-skills/pull/60))

## [1.9.0] - 2026-06-10

### Added
- **reactive-presentation v1.9.0 토큰 디자인 시스템** — 디자인 토큰 기반(type/spacing/radius/shadow/color-role/motion/z), 라이트 기본 듀얼 테마 스코프 + 토큰 기반 컴포넌트 프리미티브, `theme.css` 토큰화, `design-tokens.css` 동봉. PPTX/브랜드 추출이 코어 토큰을 구동, `validate`에 디자인-린트 규칙(raw-hex / inline-style / off-scale / raw-rgba / overflow) 추가 ([#53](https://github.com/Atom-oh/oh-my-cloud-skills/pull/53))
- **reactive-presentation 콘텐츠 품질 레이어** — 구조화된 발표자 노트 스키마(`NOTE_STRUCTURE` 린트), 슬라이드 제목 보이스 가이드(`TITLE_LENGTH` 린트, 콘텐츠 슬라이드 한정), "Forbidden AI-slide-tells" 섹션 통합, content-review 소스 누락 교차 검증 ([#54](https://github.com/Atom-oh/oh-my-cloud-skills/pull/54))

### Changed
- 모든 플러그인과 `marketplace.json`을 1.9.0으로 범프

## [1.8.0] - 2026-06-10

### Added
- **co-agent consensus 파이프라인** — 교차 패밀리 멀티모델 합의 게이트가 적용된 자율 doc→plan→implementation. Stage A(P0–P2 계획 게이트), Stage B(P3 `scope_guard.py` 파일셋 락 + Stop/PostToolUse 훅을 갖춘 세션 게이트 자율 TDD 루프), Stage C(P4 누적 스코프 diff 최종 게이트 + P5 리포트 + 전체 파이프라인 기본 + 재개). 신규 스크립트: `consensus_state.py`, `parse_plan.py`, `scope_guard.py`, `consensus_hooks.py`; `/co-agent:consensus`에 `plan`/`review`/`implement` 서브모드 ([#49](https://github.com/Atom-oh/oh-my-cloud-skills/pull/49), [#50](https://github.com/Atom-oh/oh-my-cloud-skills/pull/50), [#51](https://github.com/Atom-oh/oh-my-cloud-skills/pull/51))
- **co-agent Kiro 멀티모델 패널** — 주력 패널 opus / kimi-k2.5 / glm-5(Kiro 라우터 교차 벤더), `deep` 기본 ([#52](https://github.com/Atom-oh/oh-my-cloud-skills/pull/52))

### Changed
- 모든 플러그인과 `marketplace.json`을 1.8.0으로 범프

## [1.7.2] - 2026-06-09

### Added
- **co-agent consensus 모드 (Phase 1)** — 고신뢰 멀티-AI 리뷰. `check_citations.py`가 각 발견을 diff와 대조해 `supported`/`needs-review`/`unsupported` 분류; AI별 모델 리스트 + `deep` 프로파일 + `MAX_CALLS=12` 캡 + 라운드로빈 트림 + 비용 매트릭스; `/co-agent:consensus` 리뷰 전용 명령 + SKILL Mode 5. co-agent 패널 리뷰로 재설계(confidence 투표·영속 로그·자동수정 기본값 컷; `--apply` 수정 루프는 Phase 2로 연기) ([#47](https://github.com/Atom-oh/oh-my-cloud-skills/pull/47))
- **Codex 플러그인 지원** — 6개 플러그인의 `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json`(codex 마켓플레이스), `scripts/test-codex-plugins.py` 검증기(구조 테스트 연동)
- **AI 컨텍스트 파일** — `CLAUDE.md`를 증류한 `AGENTS.md`(Codex)·`GEMINI.md`(Gemini), `/co-agent:sync-context` 산출
- `docs/static/demos/`에 Bedrock reactive-presentation 데모

### Changed
- 모든 플러그인과 `marketplace.json`을 1.7.2로 범프

## [1.7.1] - 2026-06-02

### Added
- **co-agent `sync-context`** — `CLAUDE.md`를 증류해 패널이 자동 로드하는 AI별 컨텍스트 파일 생성: `AGENTS.md`(Codex, ~32 KiB 캡), `GEMINI.md`(Gemini, 가볍게 유지). Kiro는 `CLAUDE.md` 직접 사용. 스킬 Mode 4이자 독립 명령 `/co-agent:sync-context`로 제공. `check_ai_context.py`가 마커·크기 캡·staleness(`claude-md-sha`)·시크릿 스캔 검증; 마커 없는 수기 파일과 `AGENTS.override.md`는 보호 ([#39](https://github.com/Atom-oh/oh-my-cloud-skills/pull/39), [#41](https://github.com/Atom-oh/oh-my-cloud-skills/pull/41))
- **`/co-agent:configure`** — 패널 튜닝 (AI별 `model`, Codex `effort`, `enabled`, `timeout`). 헤드리스로 실제 설정 가능한 것만 노출(effort는 Codex 전용 — Gemini/Kiro는 헤드리스 effort 플래그 없음); 팬아웃이 `co_agent_config.py`를 읽어 설정이 실시간 반영(비활성 AI 제외, model/effort 플래그 주입). 레이어드 설정: `co-agent.defaults.json`(커밋) <- `.claude/co-agent.local.json`(gitignore) ([#40](https://github.com/Atom-oh/oh-my-cloud-skills/pull/40))
- **옵트인 autosync** — `/co-agent:configure set autosync on`이면 `CLAUDE.md` PostToolUse 훅이 컨텍스트 파일 stale 시 Claude에게 `/co-agent:sync-context` 재실행을 지시(기본 off = 알림만) ([#41](https://github.com/Atom-oh/oh-my-cloud-skills/pull/41))
- co-agent 사용법 가이드 + Docusaurus 문서 갱신 (개요/설치/스킬, 사이드바/내비 `kiro-review` -> `co-agent`)

### Changed
- 모든 플러그인과 `marketplace.json`을 1.7.1로 범프

## [1.7.0] - 2026-05-31

### Changed
- **`kiro-review` -> `co-agent` 리네임** — 멀티-AI 협업 플러그인으로 재정의. 설치된 CLI(Kiro `kiro-cli chat --no-interactive`, Codex `codex exec -s read-only`, Gemini `gemini -p -o text`) 패널을 의장으로 운영, 같은 프롬프트를 병렬 팬아웃하고 Claude가 합의/이견 종합. 3가지 모드: 멀티-AI 리뷰(코드/아키텍처 + Well-Architected -> PASS/REVIEW/FAIL), Decide(의사결정 보조), ADR 협업(Nygard 형식, `/add-adr` 연동). CLI가 하나도 없으면 Claude 단독 — graceful degradation
- 패널을 바이너리 존재(`command -v`)만으로 감지; `kiro-cli`는 인터랙티브 로그인 **또는** `KIRO_API_KEY`로 인증되므로 env-key 사전 게이트 제거
- 컨텍스트는 STDIN으로만 전달(신뢰 불가 리포 내용을 명령줄에 인터폴레이션 금지); 패널 출력은 자문으로 취급(프롬프트 인젝션 경계); CLI별 `timeout`으로 멈춘 CLI가 종합을 막지 않음
- 스킬 트리거를 멀티-AI 의도로만 좁힘(다른 스킬과 충돌하던 일반 "코드 리뷰"/"decide"/"adr" 제거)
- 모든 플러그인과 `marketplace.json`을 1.7.0으로 범프

## [1.6.0] - 2026-05-30

### Added
- `aws-ops-plugin` ops-observability에 **AWS DevOps Agent** 연동 — Agent Spaces, CloudWatch→EventBridge→Lambda→webhook 연결, `aws devopsagent create-backlog-task`, Kiro 호환 완화 계획을 통한 인시던트 에스컬레이션 ([#25](https://github.com/Atom-oh/oh-my-cloud-skills/pull/25))
- `aws-ops-plugin` ops-security-audit에 **AWS Security Agent** 연동 — 설계/코드 보안 리뷰, 온디맨드 침투 테스트, 조직 보안 요구사항, CI/CD API
- ops-observability에 오픈소스 observability 레퍼런스 추가 — OpenTelemetry, Grafana, Loki, Tempo, ClickHouse, VictoriaMetrics/Thanos/Mimir — 및 버전 호환성 섹션 (ClickHouse 서버 ↔ OTel exporter ↔ operator ↔ 디스트로 고정)
- `project-init`에 `/add-reference-doc` 커맨드 및 implementation-reference-docs 워크플로우 추가 (upstream 동기화): init-project Step 4.5, sync-docs Phase 1.5, doc-sync-checker 검증
- `agentcore-creator` 매핑 규칙/코드 템플릿에 Opus 4.8 호환성 섹션 추가 (4.6/4.7은 이력 보존)

### Changed
- `agentcore-creator` `opus` 별칭을 `us.anthropic.claude-opus-4-8`로 마이그레이션 (MODEL_MAP + 미러 문서); `agentcore-creator-agent`를 opus로 상향; "most capable" 4.6/4.7 표기 정리
- `kiro-review`의 Kiro CLI 연동을 Kiro CLI 2.5.0 기준으로 재작성 — 존재하지 않는 `Skill(skill: "kiro-cli:review")` 대신 `kiro-cli chat --no-interactive`(headless) 위임; `command -v kiro-cli` 탐지로 수정; 과도한 `model: opus` 핀 제거
- `project-init` rsync exclude 목록 강화 — upstream 동기화가 로컬 CLAUDE.md/SKILL.md 커스터마이징을 덮어쓰지 않도록
- 모든 플러그인 및 `marketplace.json`을 1.6.0으로 상향

### Fixed
- `kiro-review`: 누락된 위임 메커니즘 추가 (`kiro-cli:review`는 스킬이 아닌 슬래시 커맨드); 적대적 리뷰 수정 (`/kiro-cli:adversarial-review`); `git diff | kiro-cli` 파이프의 빈 diff 거짓 PASS 및 kiro-cli 실패 가드
- `pr-autofix`: 잘못된 `gh pr reviews` → `gh pr view --json reviews` 수정; `package.json` 없이 `npx tsc`가 실행되던 `&&/||` 우선순위 수정; 컴파일 에러를 숨기던 fail-open 빌드 검증 수정 (stderr 노출 + 실패 시 커밋 차단); 모델 ID/Co-Authored-By를 Opus 4.8로 갱신
- 잘못된 Altinity ClickHouse operator Helm repo URL 수정 (`docs.altinity.com` → `helm.altinity.com`)

## [1.5.1] - 2026-05-14

### Changed
- 모든 플러그인의 Bedrock 모델 ID를 Claude 4.0 (`-4-20250514`)에서 최신 모델(Opus 4.7, Sonnet 4.6, Haiku 4.5)로 마이그레이션 (`agentcore-creator` MODEL_MAP 및 템플릿)
- 생성되는 에이전트 코드(`convert_plugin_to_agentcore.py`)에 4.7 호환 기본값 적용 (`max_tokens=16000`, adaptive thinking 가이드, `temperature`/`top_p`/`top_k` 제거)
- `kiro-power-converter` 모델 예시를 `claude-sonnet-4`에서 `claude-sonnet-4-6`로 업데이트

### Added
- `agentcore-mapping-rules.md`에 Model-Specific Compatibility Notes 섹션 추가 (Opus 4.7 breaking changes, 4.6 deprecations, Haiku 4.5 제약)
- `agentcore-create/SKILL.md` Phase 2.1에 작업 프로필별 Bedrock 모델 추천 테이블 추가
- `agent-code-templates.md`에 Recommended Inference Defaults 섹션과 4.7 specific defaults 추가
- `aws-content-plugin/CLAUDE.md`에 Subagent Spawn Policy 섹션 추가 (4.7 호환 — 명시적 spawn/skip 조건)

### Fixed
- AIOps 데모 페이지의 잘못된 모델 ID `anthropic.claude-sonnet-4-6-20250514` 수정 (date suffix는 Claude 4.6이 아닌 Claude 4.0 출시일)

## [1.5.0] - 2026-04-29

### Added
- reactive-presentation 품질 검증을 위한 반복 개선(rejection loop) 추가 ([#19](https://github.com/Atom-oh/oh-my-cloud-skills/pull/19))
- project-init 플러그인에 pr-autofix 스킬 추가 ([#23](https://github.com/Atom-oh/oh-my-cloud-skills/pull/23))

### Fixed
- PPTX 테마 추출 색상 팔레트를 dk/lt 슬롯명 대신 휘도 기반 선택으로 수정 (반전된 다크 테마 처리)
- PPTX 테마 추출 푸터 오인식을 하단 20% 위치 필터로 수정
- PPTX 테마 추출 레이아웃 배경을 키워드 기반 매칭 및 `<p:bgRef>` XML 파싱으로 수정
- PDF 내보내기 CSS 경로를 하드코딩된 `../common/` 대신 동적 `_resolveCommonPath()`로 수정
- PPTX 내보내기에서 블록 HTML의 `window.__remarpTheme`에서 색상을 추출하여 누락된 테마 배경 수정
- TOC 내보내기 블록 카드 셀렉터를 `<div class="block-card">`와 `<a class="block-card">` 구조 모두 지원하도록 수정

## [1.4.0] - 2026-04-14

### Added
- Bedrock AgentCore 배포를 위한 agentcore-creator 플러그인 추가 (5-Phase 대화형 워크플로우)
- 프로젝트 스캐폴딩 및 문서 동기화를 위한 project-init 플러그인 추가 (8개 명령)
- Kiro CLI 기반 종합 아키텍처 심층 리뷰를 위한 kiro-review 플러그인 추가
- aws-ops-plugin에 Well-Architected Framework 6-pillar 리뷰 추가 (wellarchitected-agent, 100점 스코어링) ([#16](https://github.com/Atom-oh/oh-my-cloud-skills/pull/16))
- Remarp 슬라이드 이슈 어노테이션 처리를 위한 slide-fix 스킬 추가
- Remarp VSCode 확장에 이슈 어노테이션 시스템 추가 (프롬프트 바, `<!-- issue: -->` 어노테이션, 사이드바 이슈 배지)
- html2canvas iframe 캡처를 통한 PPTX 이미지 내보내기 추가
- 스택 기반 블록 파서와 Pandoc 스타일 콜론 카운트 ::: 블록 중첩 추가
- Slide Master 메타데이터, --figma, --stitch 디자인 소스 옵션을 포함한 PPTX 템플릿 추출 추가
- session-context, secret-scan, doc-sync 훅 및 안전 권한 추가

### Changed
- 이슈 어노테이션 구문 간소화: `<!-- !issue: -->` → `<!-- issue: -->`
- 제출 버튼을 /slide-fix 안내 토스트로 교체 (`claude --print` CLI 의존성 제거)

### Fixed
- preview.ts의 XSS 방어 및 frontmatter 정규식 수정
- 스택 기반 블록 파서 버그 3건 수정
- 캔버스 에디터 슬라이드 컨텍스트 타겟팅 수정
- 캔버스 DSL 좌표 쉼표 주변 공백 처리 수정
- _group_p_with_list의 정규식 그룹 인덱스 및 compile_preset_to_js NameError 수정
- kiro-review SessionStart 훅 복원 및 컨버터 따옴표 이스케이프 수정

## [1.2.5] - 2026-04-06

### Added
- README.md → README.ko.md 자동 번역 훅 추가
- 문서 사이트에 라이브 다이어그램 데모 추가 ([#11](https://github.com/Atom-oh/oh-my-cloud-skills/pull/11))
- 상세 스킬 가이드 및 8개 데모 페이지 추가 ([#9](https://github.com/Atom-oh/oh-my-cloud-skills/pull/9))

### Fixed
- 테이블 th/td 폰트 크기가 부모 테이블 요소에서 상속되도록 수정
- fragment 래퍼가 열 경계를 넘는 문제 및 heading-group 간격 수정
- :::left/:::right 열 내부에서 :::click 블록이 작동하지 않는 문제 수정

## [1.2.3] - 2026-03-20

### Added
- content-review-agent에 Canvas 복잡도 게이트 추가
- reactive-presentation SKILL.md에 HTML 아키텍처 패턴 및 STOP 게이트 추가
- 인터랙티브 슬라이드 패턴 가이드 추가 (interactive-patterns-guide.md)

### Changed
- 에이전트 및 SKILL.md 결정 가이드에서 canvas vs HTML 선택 지침 강화
- monitoring/dashboard 매핑을 canvas에서 html+script로 수정

### Fixed
- canvas 과다 사용 수정 -- 에이전트가 더 이상 모든 다이어그램을 :::canvas로 기본 설정하지 않음

## [1.2.2] - 2026-03-15

### Added
- Canvas DSL에 직교 화살표 라우팅 추가
- reactive-presentation 데이터 시각화 디자인 가이드 추가
- Remarp VSCode 확장에 비주얼 에디터, 캔버스 에디터, CSS 에디터 추가
- :::prompt 블록 지원 및 블록별 내보내기 버튼 추가
- AIOps 90분 프레젠테이션 데모 추가

### Changed
- 플러그인 스킬에 훅, 참조 문서, 개선된 패턴 적용
- 플러그인을 최신 Claude Code 형식으로 마이그레이션 (훅, 검증, 토큰 최적화)

### Fixed
- 멀티 블록 프레젠테이션의 blocks config 버그 수정

## [1.2.1] - 2026-03-05

### Added
- Remarp VSCode 확장 자동완성 및 미리보기 개선
- Remarp 우선 워크플로우 문서 추가

### Changed
- 캔버스 애니메이션 프롬프트, PPTX 테마 추출기, kiro 변환 규칙 개선
- 플러그인 CLAUDE.md 키워드 라우팅 및 팀 워크플로우 문서 업데이트
- 에이전트 frontmatter에서 하드코딩된 model 필드 제거

### Fixed
- 컨버터에서 'Block N:' 접두사 슬라이드 제목 제거
- remarp_to_slides.py의 `../common/` → `./common/` 에셋 경로 수정
- remarp_to_slides.py 컨버터 렌더링 버그 3건 수정

## [1.1.0] - 2026-03-03

### Added
- Claude Code → Kiro Power 변환을 위한 kiro-power-converter 플러그인 추가
- GitHub Pages 배포를 포함한 Docusaurus 문서 사이트 추가
- i18n 지원 추가 (ko 기본, en 플레이스홀더)
- 구문 하이라이팅 및 미리보기를 위한 Remarp VSCode 확장 추가
- audience frontmatter 필드 추가 및 에이전트 계획 질문 강화

### Changed
- cloudwatch-agent를 observability-agent로 교체, analytics-agent 추가
- Remarp를 프레젠테이션 기본 콘텐츠 저작 포맷으로 지정

### Fixed
- Slide Master 레이아웃 세부사항이 포함된 PPTX 테마 추출 수정

## [1.0.0] - 2026-02-26

### Added
- 최초 릴리스
- aws-content-plugin 추가: presentation, architecture diagram, animated diagram, document, gitbook, workshop 에이전트
- aws-ops-plugin 추가: EKS, network, IAM, observability, storage, database, cost, analytics, ops-coordinator 에이전트
- Canvas 애니메이션, 퀴즈, 키보드 내비게이션을 포함한 reactive-presentation 스킬 추가
- 콘텐츠 리뷰 품질 게이트 추가 (100점 척도)
- PPTX/PDF 테마 추출 추가
- AWS Architecture Icons 통합 추가 (4,224개 파일)
- 발표자 뷰 및 발표자 노트 추가

[Unreleased]: https://github.com/Atom-oh/oh-my-cloud-skills/compare/v1.14.1...HEAD
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
