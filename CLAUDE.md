# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Claude Code plugin marketplace containing seven plugins for AWS cloud work:
- **aws-content-plugin** — Content creation (presentations, diagrams, docs, workshops)
- **aws-ops-plugin** — Infrastructure operations & troubleshooting (EKS, networking, IAM, observability)
- **kiro-power-converter** — Convert Claude Code plugins to Kiro IDE Power format
- **agentcore-creator** — Convert Claude Code plugins to Bedrock AgentCore (harness or Runtime)
- **co-agent** — Multi-AI collaboration (Kiro CLI, Codex, Antigravity): review, decision support, ADR co-authoring; Claude chairs
- **project-init** — Project scaffolding and documentation management
- **kiro** — Cost-savings delegation: Claude plans and verifies, Kiro CLI implements and reviews on its own subscription credits inside an isolated git worktree

All plugins are installed via `/plugin marketplace add` or loaded locally with `--plugin-dir`.

## superpowers Integration Routing

When the `superpowers` workflow plugin is active, route into these plugins at the matching
lifecycle phase. (`superpowers` is read-only; this table is the authoritative, always-in-context
routing — per-plugin `CLAUDE.md` holds the detail. Design: `docs/superpowers/specs/2026-06-14-superpowers-integration-design.md`.)

| superpowers phase | + signal | → route to | status |
|-------------------|----------|-----------|--------|
| `systematic-debugging` | AWS/EKS symptom (NotReady, IP 고갈, AccessDenied, PVC, throttling) | `aws-ops`: `ops-troubleshoot` or matched domain agent (eks/network/iam/storage/database) | ✅ active |
| `finishing-a-development-branch` | branch done, docs may be stale | `project-init`: `/sync-docs` + `/generate-changelog` (+ `/add-adr` if a decision was made) | ✅ active |
| `requesting-code-review` | non-code artifact (slides/diagram/doc/gitbook) or IaC | `aws-content`: `content-review-agent`; IaC → `aws-ops`: `wellarchitected-agent` + `ops-security-audit`. **Read `docs/reference/review-routing.md` for gate precedence on mixed changesets.** | ✅ active |
| `writing-plans` | plan proposes AWS/IaC change | shift-left AWS security pre-check (`aws-ops`: `ops-security-audit` / mandate check: no 0.0.0.0/0, IAM `*`, secrets-in-env) before implement | ✅ active |

> co-agent is already wired separately: `co-agent:consensus` reuses `superpowers:subagent-driven-development` + writing-plans output, gated by the multi-AI panel.
> A diff that spans multiple artifact types fires ALL matching review gates — see `docs/reference/review-routing.md`.

## Development Commands

```bash
# Load plugins locally for testing
claude --plugin-dir ./plugins/aws-content-plugin
claude --plugin-dir ./plugins/aws-ops-plugin

# Validate plugin manifests (all 7 plugins)
for f in plugins/*/.claude-plugin/plugin.json; do
  python3 -c "import json; d=json.load(open('$f')); name='$f'.split('/')[1]; print(f'{name}: {len(d[\"agents\"])} agents, {len(d[\"skills\"])} skills')"
done

# Verify all plugin.json references resolve to existing files
cd plugins/aws-ops-plugin && python3 -c "
import json, os
d = json.load(open('.claude-plugin/plugin.json'))
for a in d['agents']:
    assert os.path.isfile(a.lstrip('./')), f'Missing agent: {a}'
for s in d['skills']:
    assert os.path.isfile(s.lstrip('./') + '/SKILL.md'), f'Missing skill: {s}'
print('All references OK')
"

# Remarp VSCode Extension development
cd tools/remarp-vscode
npm install && npm run compile    # Build TypeScript
npx vsce package                  # Package .vsix
code --install-extension remarp-vscode-0.1.0.vsix  # Install locally

# Evaluate skills (quality, structure, token usage)
python3 scripts/eval-skills.py
python3 scripts/eval-skills.py --plugin aws-content-plugin --skill reactive-presentation

# Behavioral eval (E2E skill runtime testing via claude --print)
python3 scripts/eval-skill-behavior.py --skill reactive-presentation --dry-run
python3 scripts/eval-skill-behavior.py --case evals/reactive-presentation/flow-layout.yaml
python3 scripts/eval-skill-behavior.py --skill reactive-presentation --ci --threshold 70

# Validate Remarp source (rejection loop — run before build)
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py validate <project-dir>/
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py validate <project-dir>/ --json
```

## Plugin Architecture

Each plugin follows the same structure:

```
plugins/<plugin-name>/
├── .claude-plugin/plugin.json    # Manifest: agents[], skills[], mcpServers{}
├── CLAUDE.md                     # Auto-invocation keyword → agent routing rules
├── agents/<name>.md              # Agent definitions (YAML frontmatter + markdown body)
└── skills/<name>/                # Skill directories
    ├── SKILL.md                  # Entry point (YAML frontmatter with triggers)
    ├── references/               # Distilled knowledge docs
    └── templates/                # Templates (content-plugin only)
```

### Agent File Format

Every agent `.md` file has YAML frontmatter with four core fields (some agents add
optional `skills`/`color`/`mcpServers`). `model` tiers are quality-first (per PR #62):
`opus` for judgment/synthesis gates and high-stakes orchestration/IAM, `sonnet` for
generation/diagnosis workers.

```yaml
---
name: eks-agent
description: "Description with trigger keywords."
tools: Read, Write, Glob, Grep, Bash, AskUserQuestion
model: sonnet
---
```

The body contains: Core Capabilities, Diagnostic Commands, Decision Tree (Mermaid), Error→Solution mapping, MCP Integration, Reference Files, Output Format.

### Skill File Format

Each `SKILL.md` has frontmatter with `name`, `description`, and `triggers` (keyword list). The `references/` subdirectory holds distilled operational knowledge extracted from source docs.

### MCP Configuration

`aws-ops-plugin` bundles 2 MCP servers in `plugin.json` → `mcpServers`:
- `awsdocs` (stdio/uvx) — Official AWS documentation search
- `awsapi` (stdio/uvx) — Direct AWS API calls

`aws-content-plugin` bundles 1 MCP server:
- `playwright` (stdio/npx `@playwright/mcp@0.0.78`, version-pinned) — browser automation for content-review-agent's
  Visual Testing, brochure-agent's product-screenshot capture, and reactive-presentation-agent;
  those three agents opt in via frontmatter `mcpServers: [playwright]` (an explicit `tools:`
  allowlist alone doesn't inherit session MCP tools)

The remaining 3 servers are provided by the `deploy-on-aws` plugin (available when both plugins are loaded):
- `awsknowledge` (HTTP) — Architecture recommendations
- `awspricing` (stdio/uvx) — Pricing data
- `awsiac` (stdio/uvx) — CloudFormation/CDK validation

### Hooks

Plugins use `hooks` in `plugin.json` for automated checks:
- **PostToolUse (Bash)** — Detects build warnings in `remarp_to_slides.py` output (content), AWS error patterns (ops)
- **PostToolUse (Edit/Write)** — Detects reactive-presentation skill file changes, validates Remarp frontmatter and slide notes
- **SessionStart** — Plugin load announcements with domain context

### Auto-Invocation

Each plugin's `CLAUDE.md` defines keyword→agent routing tables. Keywords include both English and Korean terms. When a user prompt matches keywords, the corresponding agent activates automatically.

## Versioning

All plugins share a single version tracked in their `plugin.json` → `"version"` field, mirrored in `marketplace.json`. Git tags **must** match this version.

- **Single source of truth**: `plugin.json` `"version"` in all plugins + `marketplace.json` (keep them in sync)
- **Git tag format**: `v{version}` (e.g., `v1.1.0`) — created on the release commit
- **Release process**: bump `"version"` in all `plugin.json` files + `marketplace.json` → commit → `git tag v{version}` → push with `--tags`
- **Validation**: `git describe --tags` should match all `plugin.json` and `marketplace.json` versions
- Each plugin also carries a `.codex-plugin/plugin.json` alongside its `.claude-plugin/plugin.json`
  (Codex-format manifest, kept version-synced with its Claude counterpart) — not covered by the
  snippet below, which validates the Claude manifests + marketplace + tag.

```bash
# Verify version consistency across all 7 plugins' .claude-plugin/plugin.json
VS=$(for f in plugins/*/.claude-plugin/plugin.json; do python3 -c "import json; print(json.load(open('$f'))['version'])"; done | sort -u)
MV=$(python3 -c "import json; vs=set(p['version'] for p in json.load(open('.claude-plugin/marketplace.json'))['plugins']); print(vs.pop() if len(vs)==1 else 'MISMATCH')")
TAG=$(git describe --tags --abbrev=0 2>/dev/null | sed 's/^v//')
echo "plugins=$VS marketplace=$MV tag=$TAG"
[ "$(echo "$VS" | wc -l)" = "1" ] && [ "$VS" = "$MV" ] && [ "$VS" = "$TAG" ] && echo "OK: all match" || echo "MISMATCH"
```

## Key Conventions

- Content plugin agents produce artifacts (HTML, .drawio, .md); ops plugin agents produce diagnoses with commands
- Content goes through `content-review-agent` quality gate (100-point scale: PASS ≥85, REVIEW 70-84, FAIL <70)
- Ops plugin reference files are commands-first, with Mermaid decision trees and error→solution tables
- Korean/English bilingual keywords in all auto-invocation rules
- AWS icons are packaged in `aws-content-plugin/skills/reactive-presentation/assets/aws-icons.zip` (4 icon sets: Service, Group, Category, Resource)
- Remarp-generated HTML contains `<meta name="generator" content="remarp">` for extension recognition
- Remarp VSCode Extension source lives in `tools/remarp-vscode/` (TypeScript, packaged as .vsix)
- Extension entry point: `src/extension.ts`, preview logic: `src/preview.ts`
- HTML preview converts relative resource paths to webview URIs and injects CSP for proper rendering

## Remarp VSCode Extension

Source: `tools/remarp-vscode/` | Entry: `src/extension.ts` | Preview: `src/preview.ts`

### File Detection
- `.remarp.md` extension → auto `remarp` language ID
- `.md` + frontmatter `remarp: true` → auto `remarp` language ID switch
- `.html` + `<meta name="generator" content="remarp">` → recognized as Remarp HTML

### Preview (2 modes)
| Mode | File | Rendering |
|------|------|-----------|
| Markdown | `.md` / `.remarp.md` | Slide parsing → HTML + sidebar (notes, issues, prompt bar) |
| HTML | Remarp HTML | Direct HTML load + resource path → webview URI conversion |

- **Sidebar layout**: Right panel with Speaker Notes + Issue badges + Prompt bar + Submit button
- **Arrow key slide navigation**: ←→ / Space / PageUp/PageDown (inside preview)
- **Scroll Sync**: `remarp.scrollSync` setting controls editor cursor ↔ preview slide sync
- **Source file tracking**: HTML `<meta name="remarp-source">` → auto-discovers `.md` file (up to 3 parent dirs)
- **Slide type rendering**: cover, compare, tabs, agenda, timeline, quiz, checklist, cards, code, steps, title, section, thankyou
- **Directive rendering**: `@background` → background image, `@badge` → overlay image

### Issue Annotation System
- **Prompt bar**: Sidebar input → inserts `<!-- issue: text -->` into source `.md`
- **Issue badges**: Yellow badges in sidebar, removable via × button
- **Slide fix**: `remarp.submitIssues` command → shows toast guiding user to run `/slide-fix` in Claude Code
- **`/slide-fix` skill**: Reads `<!-- issue: -->` annotations via `remarp_to_slides.py issues --json`, fixes each slide, removes annotations, rebuilds HTML
- **Auto-cleanup**: `/slide-fix` removes `<!-- issue: -->` comments after fixing

### Visual Edit Mode (PPT edit mode)
- **Activate**: `Cmd+Shift+E` / editor titlebar Edit button / per-slide floating Edit button
- **Features**: element drag (position), resize, Property Panel (font/color/margin)
- **CSS writeback**: changes → auto-written to `:::css` block in source `.md`
- **Canvas writeback**: canvas element move/resize → `:::canvas` DSL coordinates updated in source `.md`
- **Canvas editing**: drawio-style SVG overlay hitboxes for element select/move, waypoint editing, step animation control

### Key Files
| File | Role |
|------|------|
| `src/extension.ts` | Entry point: command registration, file detection, build script discovery |
| `src/preview.ts` | Preview panel: MD/HTML rendering, slide parsing, navigation |
| `src/htmlPreview.ts` | Dedicated HTML preview handler for Remarp HTML files |
| `src/outline.ts` | Slide outline provider for editor sidebar |
| `src/completions.ts` | Autocomplete: @directives, :::blocks, :::css, :::canvas DSL |
| `src/cssEditor.ts` | CSS editing: `:::css` block parse/create/update |
| `src/canvasEditor.ts` | Canvas editing: `:::canvas` DSL coordinates/size/step/animate-path update |
| `src/visualEditor.ts` | Visual editor controller: message routing (to CSS/Canvas editors) |
| `media/edit-mode.js` | Webview: drag/resize/property panel UI |
| `media/canvas-editor.js` | Webview: Canvas SVG overlay, hitbox, waypoint editing |
| `media/prompt-bar.js` | Webview: AI prompt bar UI for slide improvement |

## Plugin Inventory

### aws-content-plugin (9 agents, 9 skills)

| Agent | Creates |
|-------|---------|
| `presentation-agent` | Presentation format dispatcher (PPTX vs Web) |
| `reactive-presentation-agent` | Interactive HTML slideshows via reactive-presentation framework (Remarp) |
| `architecture-diagram-agent` | Draw.io XML → PNG/SVG |
| `animated-diagram-agent` | SVG + SMIL animation HTML |
| `document-agent` | Markdown technical documents |
| `gitbook-agent` | GitBook documentation sites |
| `workshop-agent` | AWS Workshop Studio content |
| `brochure-agent` | Single-page responsive online brochure (landing page) HTML |
| `content-review-agent` | Quality gate for all content types |

Content skills: `reactive-presentation`, `architecture-diagram`, `animated-diagram`,
`gitbook`, `workshop-creator`, `slide-fix`, `brochure`, `gh-home`, and
**`aws-light-fcd`** — the native **PPTX** skill (PptxGenJS, AWS Light theme, Pretendard).
The presentation-agent dispatcher routes PPTX requests to `aws-light-fcd`; it shares the
official 811-icon library with `reactive-presentation` via `kit.icon()` (referenced in
place, not duplicated). `gh-home` is a personal profile/portfolio page (GitHub Pages user-site home) analog of
`brochure` (person, not product) and reuses its self-check script.

### aws-ops-plugin (10 agents, 6 skills)

| Agent | Domain |
|-------|--------|
| `eks-agent` | EKS cluster management, node groups, upgrades, add-ons |
| `network-agent` | VPC CNI, ALB/NLB, DNS, Security Groups |
| `iam-agent` | IRSA, Pod Identity, RBAC, aws-auth |
| `observability-agent` | CloudWatch, AMP, AMG, ADOT, Prometheus/Grafana |
| `storage-agent` | EBS/EFS/FSx CSI drivers, PVC binding |
| `database-agent` | RDS/Aurora, DynamoDB, ElastiCache |
| `cost-agent` | Cost analysis via awspricing MCP |
| `analytics-agent` | OpenSearch, ClickHouse, Athena, QuickSight, Kinesis |
| `ops-coordinator-agent` | Multi-domain incident coordination |
| `wellarchitected-agent` | AWS Well-Architected 6-pillar review, 100-point scoring |

Ops skills: `ops-troubleshoot`, `ops-health-check`, `ops-network-diagnosis`, `ops-observability`, `ops-security-audit`, `ops-wellarchitected-review` — each with `references/` subdirectory containing distilled runbooks. `ops-observability` also covers the open-source stack (OpenTelemetry, Grafana, Loki, Tempo, ClickHouse, VictoriaMetrics) and **AWS DevOps Agent** incident escalation; `ops-security-audit` covers **AWS Security Agent** (design/code review, on-demand penetration testing).

### kiro-power-converter (1 agent, 1 skill)

| Agent | Purpose |
|-------|---------|
| `kiro-converter-agent` | Converts Claude Code plugins to Kiro Power format |

Skill: `kiro-convert` — interactive workflow for plugin-to-power conversion with `references/` subdirectory containing format specs and conversion rules.

### agentcore-creator (1 agent, 1 skill)

| Agent | Purpose |
|-------|---------|
| `agentcore-creator-agent` | Converts Claude Code plugins to Bedrock AgentCore — config-only to **harness** (GA 2026-06: skills attach unchanged as git/s3 SKILL.md sources, `CreateHarness`/`InvokeHarness`) or Strands code-gen to Runtime (Gateway, Memory, Lambda) |

Skill: `agentcore-create` — 5-Phase conversion workflow (Discovery, Design, Skill-First Build, AgentCore Convert, Deploy) with `references/` and `scripts/` subdirectories. Phase 2 decides the deploy target (harness-vs-Runtime grid in `references/agentcore-harness.md`); Phase 4 is dual-path (A: harness config, B: Runtime code-gen). The `opus` alias resolves to `us.anthropic.claude-opus-4-8`; modern-Opus (4.7/4.8) param contract (no `temperature`/`top_p`/`top_k`, no `thinking.type:"enabled"`+`budget_tokens`) is documented in `references/agentcore-mapping-rules.md`.

### co-agent (3 agents, 1 skill, 5 commands)

| Agent | Purpose |
|-------|---------|
| `co-agent` | Multi-AI panel chair — fans review/decision/ADR prompts to Kiro/Codex/Antigravity CLIs and synthesizes |
| `gate-chair` | Hybrid-gate chair judgment isolated on `model: opus` — Phase T triage + verify round-close verdicts; makes zero external calls (fan-out/consent/cost stay with the host), for hosts running a cheaper tier |
| `harness-analyst` | Hill-climbing analyst (advisory-only, `model: sonnet`) — mines accumulated `.claude/co-agent-consensus/` run records (`stage_wall.tsv`, task/gate `result.json`) into proposed `/co-agent:configure set` commands; never writes config, observations-only below 3 recorded runs |

Skill: `co-agent` — 6 modes: **Review** (multi-AI code/arch review + Well-Architected), **Decide** (decision support when unsure), **ADR** (co-author ADRs), **sync-context** (distill `CLAUDE.md` → `AGENTS.md` once; Kiro, Codex, and Agy all share that one distilled file — Kiro via `.kiro/steering/project-context.md` → `#[[file:AGENTS.md]]`, Codex and Agy both read `AGENTS.md` natively from their cwd — the fan-out additionally folds it into Agy's context as defense-in-depth for non-root-cwd runs), **Consensus** (autonomous doc→plan→implementation pipeline gated by the multi-model panel, `/co-agent:consensus`), and **harness** (host-designs / peer-implements / panel-reviews orchestrator, `/co-agent:harness`). Fans the same prompt to whichever AI CLIs are installed — Kiro (`kiro-cli chat --no-interactive`; auth via login or `KIRO_API_KEY`), Codex (`codex exec -s read-only`), Agy (`agy -p --sandbox`; Gemini support removed — ADR-010) — in parallel, then **Claude synthesizes** (consensus vs. dissent). Degrades gracefully; if no CLI is present, Claude answers solo. Adapters: `references/ai-cli-adapters.md`.

Commands: `/co-agent:configure` — tune the panel (per-AI `model`, Codex `effort`, `enabled`, `timeout`, `autosync` opt-in, and **role-based model tiering**: chair on the host's strong tier; hybrid-gate find phase wide-and-cheap on the configured `profile deep` breadth vs. verify phase on each AI's single strongest `model` via `pairs --profile default`; write-path-only `set harness implementer_model`/`implementer_effort` stored per implementer (keyed by the explicitly-set `harness.implementer`, so no cross-CLI model leak on switch) that `impl-flags` prefers over the panel settings — see `commands/configure.md` "모델 티어링"). `/co-agent:sync-context` — distill `CLAUDE.md` → `AGENTS.md` and wire the Kiro steering bridge to that same `AGENTS.md` (Mode 4 surfaced as a standalone command). Layered config: `co-agent.defaults.json` (committed) ← `.claude/co-agent.local.json` (gitignored). Only headless-settable options are exposed (effort is Codex-only); the fan-out reads `co_agent_config.py` so settings are live. The `CLAUDE.md` PostToolUse hook reminds when `AGENTS.md` drifts stale, and — if `autosync on` — tells Claude to re-run sync-context. Scripts: `check_ai_context.py` (context-file validator), `co_agent_config.py` (panel settings). `/co-agent:consensus` — autonomous doc→plan→implementation pipeline gated by the multi-model panel (Stage A plan gate · Stage B implement · Stage C final gate + report; resumable). `/co-agent:harness` — host-designs / peer-implements (isolated git worktree + workspace-write sandbox) / panel-reviews orchestrator; the host owns the failing test and every commit, and lands only the peer's captured, scope-guarded worktree diff so out-of-worktree writes never reach the main tree; reviews via the **hybrid gate** by default (parallel find → chair triage → parallel verify of the curated digest — `references/hybrid-gate.md`; `set harness review_mode hybrid|relay|parallel`), and implements with **one configured implementer fanned out as parallel per-task subagents** in disjoint-file waves (`set harness implementer codex|agy`, `set harness parallel_tasks`, default 3) (`references/delegated-implement.md`; `co_agent_config.py implementer|impl-flags`, `worktree.py`). `/co-agent:setup` — panel-readiness preflight: detects each peer (`plugin`→`raw`→`none`) and probes real usability, then writes a readiness summary (`.claude/co-agent-panel.local.json`) the other flows consult before fanning out (`check_panel.py`).

### project-init (1 agent, 3 skills, 10 commands)

| Agent | Purpose |
|-------|---------|
| `doc-sync-checker` | Documentation sync analysis, quality scoring, missing doc detection |

Skills: `project-scaffolder` — Claude Code project structure patterns and conventions. `pr-autofix` — PR review feedback auto-fix (AI + human review polling, max 3 iterations). `decision-reconcile` — ADR contradiction detection across accumulated ADRs (and ADR-vs-reality drift) via a diverse multi-agent panel (varied Claude model tiers + optional co-agent CLIs, one review lens each), then drafts a superseding ADR to reverse/reconcile the decision. **Local to this fork** — not present in the whchoi98/project-init upstream source (see `plugins/project-init/references/upstream-sync.md`). Triggers: 의사결정 번복, ADR 모순, reconcile ADRs.

Commands: `/init-project`, `/sync-docs`, `/add-adr`, `/add-module`, `/add-runbook`, `/generate-readme`, `/generate-changelog`, `/health-check`, `/pr-autofix`, `/add-reference-doc`

### kiro (1 agent, 1 skill, 4 commands)

| Agent | Purpose |
|-------|---------|
| `kiro-delegate-agent` | Plans + verifies; hands implementation tasks to Kiro CLI inside an isolated git worktree; falls back to writing the code itself when Kiro's fix loop is exhausted |

Skill: `kiro-delegate` — cost-savings delegation to Kiro CLI (subscription credits), not a
second opinion (that's `co-agent`). Reuses co-agent's `worktree.py`/`scope_guard.py`/
`parse_plan.py` verbatim — the isolation/scoping mechanics are identical, only the
implementer CLI differs; co-agent's own harness refuses Kiro as an implementer
(`SANDBOX_IMPLEMENTERS = codex, agy` — no cwd-confined write sandbox), and this plugin's
worktree+capture+scope_guard path is what makes delegating to it safe **for changes
reaching the main tree** (host-side side effects of a granted `execute_bash` are a
separate trust decision — `plugins/kiro/CLAUDE.md` → "Trust decision").

Commands: `/kiro:setup` (probe + model list + `.kiro/agents/*.json` generation),
`/kiro:delegate`, `/kiro:review`, `/kiro:configure`. A `PreToolUse(Bash)` hook can run a
Kiro-powered review before `git commit` (fail-open; blocks only on `critical` findings
by default) — **off by default** (the reviewer's `fs_read` isn't scoped to just the diff
file, so only enable for diffs you trust the authorship of); `/kiro:configure set review
on_commit on` to enable.

## Workflows

```
Content:   presentation-agent (dispatcher) → reactive-presentation-agent → content-review-agent → GitHub Pages
                                          → aws-light-fcd skill (native .pptx) → QA render → embed_fonts.py
           Remarp HTML ↔ .remarp.md (bidirectional visual editing via VSCode extension)
           PPTX theme:  .pptx → extract_pptx_theme.py → theme-manifest.json + theme-override.css
           PPTX export: export_pptx.py (headless Playwright capture + python-pptx, speaker notes 포함) → .pptx
                        (브라우저 폴백: toc.html Export PPTX 버튼 → html2canvas + PptxGenJS)
           PPTX native: aws-light-fcd → deck_kit.js/arch_kit.js (PptxGenJS) → kit.icon() shares reactive-presentation 811-icon lib
           architecture-diagram-agent → layout_aws.py (YAML spec → .drawio, standard patterns) → validate+lint → PNG
                                       → hand-authored .drawio (non-standard shapes) → PNG
           animated-diagram-agent → .html (SVG+SMIL)
           document-agent → content-review-agent → .md
           gitbook-agent → content-review-agent → git push
           workshop-agent → content-review-agent → Workshop Studio

Ops:       User issue → auto-routed agent → Diagnose → Resolve → Verify
           Incident → ops-coordinator → specialist agents (7) → aggregate → root cause → fix

AgentCore: Plugin source → analyze → harness-vs-Runtime decision → A: harness config (skills attach as-is) | B: generate Strands artifacts → user refinement → deploy via CLI → verify

Co-agent:  /co-agent → detect panel (Kiro/Codex/Antigravity) → fan-out prompt → Claude synthesizes → Review report / Decision / ADR

kiro:      /kiro:setup → probe kiro-cli, list models, write .kiro/agents/*.json
           /kiro:delegate → Claude plans (Kiro spec) → per task: worktree → Kiro implements → capture-diff → scope_guard → Claude applies+tests → bounded retry → Claude fallback → commit → delegation-rate report
           git commit → PreToolUse hook (opt-in, off by default) → Kiro review (fail-open, blocks only on `critical`)
```

## Auto-Sync Rules

Documentation stays in sync via hooks and skills:

| Trigger | Mechanism | Action |
|---------|-----------|--------|
| File edit (Write/Edit) | `check-doc-sync.sh` (PostToolUse) | Walks parent dirs for missing CLAUDE.md, warns if absent |
| File edit on README.md | PostToolUse hook | Auto-prompts Korean translation to README.ko.md |
| `git commit` (Bash) | `secret-scan.sh` (PreToolUse) | Blocks commits containing API keys, tokens, passwords |
| Session start | `session-context.sh` (SessionStart) | Loads project type, version, branch, uncommitted file count |
| `remarp_to_slides.py` run | PreToolUse inline hook | Verifies common/ assets (theme.css, JS) exist before build |
| Commit creation | `.git/hooks/commit-msg` | Strips Co-Authored-By lines from commit messages |
| Manual | `/sync-docs` skill | Full documentation sync with quality scoring |
| Plan mode exit | CLAUDE.md convention | Update docs when architectural decisions change |
