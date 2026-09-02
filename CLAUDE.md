# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tool call parameters

- Write non-ASCII as literal UTF-8 in tool inputs, never `\uXXXX` escapes (incl. inside JSON strings). Exempt: escapes that are the file's own source syntax (char-class ranges, codepoint bounds).

## What This Is

A Claude Code plugin marketplace containing eight plugins for AWS cloud work:
- **aws-content-plugin** — Content creation (presentations, diagrams, docs, workshops)
- **aws-ops-plugin** — Infrastructure operations & troubleshooting (EKS, networking, IAM, observability)
- **kiro-power-converter** — Convert Claude Code plugins to Kiro IDE Power format
- **agentcore-creator** — Convert Claude Code plugins to Bedrock AgentCore (harness or Runtime)
- **co-agent** — Multi-AI collaboration (Kiro CLI, Codex, Antigravity): review, decision support, ADR co-authoring; Claude chairs
- **project-init** — Project scaffolding and documentation management
- **kiro** — Cost-savings delegation: Claude plans and verifies, Kiro CLI implements and reviews on its own subscription credits inside an isolated git worktree
- **atlas** — A self-syncing per-topic doc wiki for LLM consumption: docs declare the files they `cover`, drift is detected mechanically against a `code_rev` anchor, and stale docs can be auto-fixed just before a push

All plugins are installed via `/plugin marketplace add` or loaded locally with `--plugin-dir`.

## superpowers Integration Routing

When the `superpowers` workflow plugin is active, route into these plugins at the matching
lifecycle phase. (`superpowers` is read-only; this table is the authoritative, always-in-context
routing — per-plugin `CLAUDE.md` holds the detail. Design: `docs/superpowers/specs/2026-06-14-superpowers-integration-design.md`.)

| superpowers phase | + signal | → route to | status |
|-------------------|----------|-----------|--------|
| `systematic-debugging` | AWS/EKS symptom (NotReady, IP exhaustion, AccessDenied, PVC, throttling) | `aws-ops`: `ops-troubleshoot` or matched domain agent (eks/network/iam/storage/database) | ✅ active |
| `finishing-a-development-branch` | branch done, docs may be stale | `project-init`: `/sync-docs` + `/generate-changelog` (+ `/add-adr` if a decision was made) | ✅ active |
| `requesting-code-review` | non-code artifact (slides/PPTX deck/diagram/doc/gitbook/brochure/workshop) or IaC | `aws-content`: `content-review-agent`; IaC → `aws-ops`: `wellarchitected-agent` + `ops-security-audit`. **Read `docs/reference/review-routing.md` for gate precedence on mixed changesets.** | ✅ active |
| `writing-plans` | plan proposes AWS/IaC change | shift-left AWS security pre-check (`aws-ops`: `ops-security-audit` / mandate check: no 0.0.0.0/0, IAM `*`, secrets-in-env) before implement | ✅ active |

> co-agent is already wired separately: `co-agent:consensus` reuses `superpowers:subagent-driven-development` + writing-plans output, gated by the multi-AI panel.
> A diff that spans multiple artifact types fires ALL matching review gates — see `docs/reference/review-routing.md`.

## Development Commands

```bash
# One-command setup for new developers (prereq check, .env, doc-sites deps)
./scripts/setup.sh
./scripts/install-hooks.sh   # commit-msg hook: strips Co-Authored-By lines

# Load plugins locally for testing
claude --plugin-dir ./plugins/aws-content-plugin
claude --plugin-dir ./plugins/aws-ops-plugin

# Structural test suite — the canonical validation (manifests, frontmatter, references)
python3 scripts/test-plugins.py                 # all plugins; -p <plugin> for one, -v verbose
python3 scripts/test-codex-plugins.py           # Codex-format manifests (project-init: deliberate silent skip, CLAUDE_ONLY)

# Stale plugin cache check — local ~/.claude/plugins/cache vs source (--fix to copy)
./scripts/sync-plugin-cache.sh

# Quick manual manifest inspection (all 8 plugins).
# project-init is an upstream mirror whose manifest declares no agents/skills arrays
# (Claude Code discovers them by convention), hence the .get() defaults.
for f in plugins/*/.claude-plugin/plugin.json; do
  python3 -c "import json; d=json.load(open('$f')); name='$f'.split('/')[1]; print(f'{name}: {len(d.get(\"agents\", []))} agents, {len(d.get(\"skills\", []))} skills')"
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

# Remarp VSCode Extension build/package: see tools/remarp-vscode/CLAUDE.md (canonical);
# extension detail: docs/reference/remarp-vscode-extension.md

# Evaluate skills (quality, structure, token usage)
python3 scripts/eval-skills.py
# NOTE: there is no `--plugin` flag; eval-skills.py selects by SKILL name only.
python3 scripts/eval-skills.py --skill reactive-presentation --verbose --threshold 85

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

Every agent `.md` file has YAML frontmatter with five core fields (some agents add
optional `skills`/`color`/`mcpServers`/`memory` — `memory: project|user` gives the agent
a persistent `agent-memory/<name>/MEMORY.md` it maintains across sessions; applied to
agents that accumulate cross-session knowledge: ops domain agents + coordinator +
wellarchitected (project — environment facts, incident patterns), content-review &
gate-chair & harness-analyst (project — recurring findings, past verdicts/proposals),
co-agent & kiro-delegate (user — peer-CLI behavior is machine-wide, not per-project)). `model`/`effort` tiers follow the DeepSWE v1.1
cost-efficiency data (2026-07, supersedes PR #62's sonnet-worker rule). **Above the
dispatch/scan floor there is one model — `opus` — and the tier is expressed through
`effort` alone** — the DeepSWE data showed opus at a *lower* effort beating sonnet at a
higher one on both score and cost, because sonnet burns 2x+ agent steps to reach the same
place and each extra step is a full context re-read. The floor is the only `sonnet`
survivor, and it is a row in the same table, not a footnote to it:

| Tier | Role | Examples |
|------|------|----------|
| `opus`+`xhigh` | judgment/synthesis gates where the verdict is the product | `content-review-agent`, `ops-coordinator-agent`, `gate-chair`, `wellarchitected-agent`, `iam-agent` |
| `opus`+`high` | multi-step diagnosis / build workers | ops domain agents (`iam-agent` excepted — its permission verdicts are security judgments, tiered `xhigh` since PR #130), `architecture-diagram-agent`, `workshop-agent` |
| `opus`+`medium` | mechanical application of an already-approved plan | `pr-autofix-implementer` (only) |
| `opus`+`low` | single-artifact writers, analysis with a narrow output | `document-agent`, `gitbook-agent`, `cost-agent`, `kiro-converter-agent`, `harness-analyst` |
| `sonnet`+`low` | pure dispatch/scan — routes to another agent | `presentation-agent` (only) |

`pr-autofix-implementer` is the sole `opus`+`medium`: it applies an already-approved plan,
so deeper reasoning buys nothing, but its multi-file edit reliability has to hold — a
plan-approved edit needing a second pass costs a whole extra review-poll cycle in that
skill, not just one subagent call.

The `sonnet`+`low` floor exists because that agent has no judgment to deepen, so opus buys
nothing at any effort: `presentation-agent` is a format dispatcher whose only tool is
`AskUserQuestion`. `doc-sync-checker` (project-init) is outside this table entirely — that
plugin is an upstream mirror, so its bare `model: opus` with no `effort` is the fork
source's value and stays untouched. Everywhere else the former `sonnet` tiers moved to `opus`+`low` — same
rung of the cost ladder, since the DeepSWE win came from fewer agent steps rather than a
cheaper per-token rate. Write tiers as `` `model` ``+`` `effort` `` (e.g. `opus`+`low`)
wherever they're referenced, here and in per-plugin docs.

```yaml
---
name: eks-agent
description: "Description with trigger keywords."
tools: Read, Write, Glob, Grep, Bash, AskUserQuestion
model: opus
effort: high
---
```

The body contains: Core Capabilities, Diagnostic Commands, Decision Tree (Mermaid), Error→Solution mapping, MCP Integration, Reference Files, Output Format.

### Skill File Format

Each `SKILL.md` has frontmatter limited to the six fields the Agent Skills spec
(`https://agentskills.io/specification`) defines — `name`, `description`, `license`,
`compatibility`, `metadata`, `allowed-tools` — plus the Claude Code extensions
`user-invocable` / `disable-model-invocation`. Any other key (`triggers:`, `model:`,
`invocation:`, `argument-hint:`, `tools:`) is **inert**: the runtime ignores it silently.
**Trigger keywords therefore belong in `description`**, which is the sole selection
surface — a `triggers:` list strands its keywords where nothing reads them. `scripts/eval-skills.py` enforces
the allowed-key set in its Structure dimension. The `references/` subdirectory holds
distilled operational knowledge extracted from source docs.

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
  (Codex-format manifest, kept version-synced with its Claude counterpart), and there is a second,
  separate Codex marketplace at `.agents/plugins/marketplace.json` — project-init excepted (it
  carries no `.codex-plugin/plugin.json` and so is absent from that file). All four surfaces
  (Claude manifests, Claude marketplace, Codex manifests, Codex marketplace) are covered by the
  snippet below — `.agents/plugins/marketplace.json` drifted to a stale version once already
  (fixed alongside the atlas plugin's addition) precisely because nothing checked it.

```bash
# Verify version consistency across all 8 plugins' .claude-plugin/plugin.json, both
# marketplaces, the Codex manifests (project-init excepted), and the git tag
VS=$(for f in plugins/*/.claude-plugin/plugin.json; do python3 -c "import json; print(json.load(open('$f'))['version'])"; done | sort -u)
MV=$(python3 -c "import json; vs=set(p['version'] for p in json.load(open('.claude-plugin/marketplace.json'))['plugins']); print(vs.pop() if len(vs)==1 else 'MISMATCH')")
CV=$(for f in plugins/*/.codex-plugin/plugin.json; do python3 -c "import json; print(json.load(open('$f'))['version'])"; done | sort -u)
CMV=$(python3 -c "import json; vs=set(p['version'] for p in json.load(open('.agents/plugins/marketplace.json'))['plugins']); print(vs.pop() if len(vs)==1 else 'MISMATCH')")
TAG=$(git describe --tags --abbrev=0 2>/dev/null | sed 's/^v//')
echo "plugins=$VS marketplace=$MV codex-plugins=$CV codex-marketplace=$CMV tag=$TAG"
[ "$(echo "$VS" | wc -l)" = "1" ] && [ "$VS" = "$MV" ] && [ "$VS" = "$CV" ] && [ "$VS" = "$CMV" ] && [ "$VS" = "$TAG" ] && echo "OK: all match" || echo "MISMATCH"
```

## Key Conventions

- Architecture decisions are ADRs in `docs/decisions/` (ADR-001…); add new ones via `/add-adr`, reconcile contradictions via `co-agent:decision-reconcile`
- Content plugin agents produce artifacts (HTML, .drawio, .md); ops plugin agents produce diagnoses with commands
- Content goes through `content-review-agent` quality gate (100-point scale: PASS ≥85, REVIEW 70-84, FAIL <70; Visual-Testing-exempt content is judged on a 90-point scale: PASS ≥77)
- Ops plugin reference files are commands-first, with Mermaid decision trees and error→solution tables
- Korean/English bilingual keywords in all auto-invocation rules — except `atlas`,
  which is deliberately English-only (it's a general-purpose, exportable-to-any-repo
  plugin, not scoped to this marketplace's Korean-speaking AWS-practitioner audience)
- AWS icons are packaged in `aws-content-plugin/skills/reactive-presentation/assets/aws-icons.zip` (4 icon sets: Service, Group, Category, Resource)
- Remarp-generated HTML contains `<meta name="generator" content="remarp">` for extension recognition
- Remarp VSCode Extension source lives in `tools/remarp-vscode/` (TypeScript, packaged as .vsix)
- Extension entry point: `src/extension.ts`, preview logic: `src/preview.ts`
- HTML preview converts relative resource paths to webview URIs and injects CSP for proper rendering

## Remarp VSCode Extension

Source: `tools/remarp-vscode/` (TypeScript, packaged as .vsix) | Entry: `src/extension.ts` |
Preview: `src/preview.ts`. Two preview modes (Markdown slide parsing / Remarp HTML direct
load), issue-annotation system (`<!-- issue: -->` → `/slide-fix`), and a visual edit mode
with `:::css` / `:::canvas` writeback. **Working on the extension? Read
`docs/reference/remarp-vscode-extension.md` first** — file detection rules, preview/sidebar
behavior, and key-file map live there, not here; build/package commands are canonical in
`tools/remarp-vscode/CLAUDE.md`.

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

Skill: `agentcore-create` — 5-Phase conversion workflow (Discovery, Design, Skill-First Build, AgentCore Convert, Verify — deployment itself is §4.5 of Convert) with `references/` and `scripts/` subdirectories. Phase 2 decides the deploy target (harness-vs-Runtime grid in `references/agentcore-harness.md`); Phase 4 is dual-path (A: harness config, B: Runtime code-gen). Model aliases resolve through `MODEL_MAP` in `scripts/convert_plugin_to_agentcore.py` (the single source — currently the Claude 5 generation: `opus` -> Opus 5, `sonnet` -> Sonnet 5); the no-sampling / no-`budget_tokens` param contract (Opus 4.7+, Sonnet 5, Fable 5) is documented in `references/agentcore-mapping-rules.md`.

### co-agent (5 agents, 3 skills, 6 commands)

| Agent | Purpose |
|-------|---------|
| `co-agent` | Multi-AI panel chair — fans review/decision/ADR prompts to Kiro/Codex/Antigravity CLIs and synthesizes |
| `gate-chair` | Hybrid-gate chair judgment isolated on its own `opus`+`xhigh` subagent — Phase T triage + verify round-close verdicts; makes zero external calls (fan-out/consent/cost stay with the host), for hosts running a cheaper tier |
| `harness-analyst` | Hill-climbing analyst (advisory-only, `opus`+`low`) — mines accumulated `.claude/co-agent-consensus/` run records (`stage_wall.tsv`, task/gate `result.json`) into proposed `/co-agent:configure set` commands; never writes config, observations-only below 3 recorded runs |
| `pr-autofix-planner` | Read-only fix planner for pr-autofix (enforced Read/Grep/Glob; fable/opus) |
| `pr-autofix-implementer` | Edit-only plan implementer for pr-autofix (enforced Read/Write/Edit/Grep/Glob — no Bash/network; opus [medium effort]) |

Skill: `co-agent` — 6 modes: **Review** (multi-AI diff/arch review), **Decide** (decision support with comparison table), **ADR** (co-authored decision records), **sync-context** (distill `CLAUDE.md` → `AGENTS.md` once; Kiro/Codex/Antigravity (`agy`) all share that one distilled file), **Consensus** (doc→plan→implement pipeline, `/co-agent:consensus`), **harness** (delegated implementation orchestrator, `/co-agent:harness`). Fans the same prompt to whichever AI CLIs are installed — Kiro/Codex/Antigravity (`agy`; Gemini removed — ADR-010) — in parallel, then **Claude synthesizes**. Degrades gracefully to solo when no CLI is present. Adapters: `references/ai-cli-adapters.md`.

Also in co-agent (moved out of project-init, now an upstream mirror — `docs/reference/project-init-upstream-sync.md`): `pr-autofix` — PR review feedback auto-fix loop (plan on Fable/Opus → opus [medium effort] implementer in a disposable worktree → only the plan-approved delta lands; loop bound `set pr_autofix max_iterations`, default 5; CI review-comment marker resolved from `pr_autofix.review_marker`, regex auto-detect when unset; closes the **PR review memory loop** — the host, never the planner/implementer, reads and updates the one committed `docs/pr-review/review-memory.md` that CI's review prompts also read, ADR-015; escalation ladder — only when `push_gate.enabled` is on, off by default, fails open when it can't review — pass >3 runs the pre-push lens gate before pushing, re-planning once on a blocking verdict; pass >5 escalates the panel/chair models for that gate call only, never persisted to config), and `decision-reconcile` — ADR contradiction/drift detection via a diverse multi-agent panel, drafting a superseding ADR. Triggers: reversed decisions, ADR contradictions, reconcile ADRs.

Commands: `/co-agent:configure` (per-AI model/effort/enabled/timeout, role-based model tiering, layered config `co-agent.defaults.json` ← `.claude/co-agent.local.json`), `/co-agent:sync-context`, `/co-agent:consensus` (Stage A plan gate · Stage B implement · Stage C final gate; resumable), `/co-agent:harness` (host-designs / peer-implements in isolated worktree / hybrid-gate reviews — parallel find → chair triage → parallel verify; `references/hybrid-gate.md`, `references/delegated-implement.md`), `/co-agent:pr-autofix`, `/co-agent:setup` (panel-readiness preflight → `.claude/co-agent-panel.local.json`).

> Full detail — fan-out adapters/auth, gate quorum/consent/data-boundary contracts, configure keys, tiering rules — lives in `plugins/co-agent/CLAUDE.md` (auto-loads when working in that plugin).

### project-init (1 agent, 1 skill, 9 commands) — upstream mirror

| Agent | Purpose |
|-------|---------|
| `doc-sync-checker` | Documentation sync analysis, quality scoring, missing doc detection |

Skill: `project-scaffolder` — Claude Code project structure patterns and conventions.

Commands: `/init-project`, `/sync-docs`, `/add-adr`, `/add-module`, `/add-runbook`, `/generate-readme`, `/generate-changelog`, `/health-check`, `/add-reference-doc`

**This plugin is a byte-identical mirror of `whchoi98/project-init`** — the only local delta
is `version` in `.claude-plugin/plugin.json` (marketplace-uniform). Never edit it in place:
the next sync wipes the change. Local features that used to live here moved to co-agent
(`pr-autofix`, `decision-reconcile`) or to the root routing table (superpowers hints). It
also carries no `.codex-plugin/plugin.json`, so it is absent from the Codex marketplace
(`scripts/test-codex-plugins.py` deliberately skips it silently — `CLAUDE_ONLY`; a standing warning on a known-correct state would be noise), and its manifest
declares no `agents`/`skills` arrays — `scripts/test-plugins.py` discovers them on disk so
the frontmatter is still validated. Sync procedure and rationale:
`docs/reference/project-init-upstream-sync.md`.

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
`/kiro:delegate`, `/kiro:review`, `/kiro:configure`. Two opt-in, off-by-default
`PreToolUse(Bash)` review hooks: pre-commit (Kiro reviews the staged diff — the diff
content is sent to Kiro's backend, enabling is consent; fail-open,
blocks only on `critical`) and pre-push (3-lens correctness/security/scope over the
push range; `critical` BLOCKED, `warning`-only CHAIR JUDGMENT REQUIRED; warns if
co-agent's `push_gate` is also on). **Web search delegation** (off by default): sessions
without a `WebSearch` tool (Bedrock) route searches through kiro-cli's native
`web_search` via `kiro_websearch.py` — query text is the only egress.

> Full detail — hook consent/data-boundary contracts, `fs_read` guard, websearch
> fail-closed rules, trust decision — lives in `plugins/kiro/CLAUDE.md` (auto-loads when
> working in that plugin).

### atlas (1 agent, 1 skill, 5 commands)

| Agent | Purpose |
|-------|---------|
| `atlas-sync-agent` | Decides which atlas docs have drifted and repairs their prose; refuses anything outside the wiki root |

Skill: `atlas` — a per-topic documentation wiki written **for LLM consumption**, kept in
sync with the code mechanically. Each doc's frontmatter declares `covers` globs and a
`code_rev` anchor, so staleness is a glob match over `git diff --name-only` with **no LLM
pass** — detection is O(changed files × docs) and free. Docs default to `docs/atlas/`
(`root` config key) with an AUTO-MANAGED `INDEX.md` an agent reads first to pick which
bodies to load, instead of cramming everything into `CLAUDE.md`. The glob matcher is
hand-rolled rather than `fnmatch`: `fnmatch`'s `*` crosses `/`, which would let a doc
claim territory it does not cover.

Commands: `/atlas:init`, `/atlas:sync`, `/atlas:add-doc`, `/atlas:graph`,
`/atlas:configure`. One opt-in, **off-by-default** `PreToolUse(Bash)` hook: push-time
auto-sync (`sync.on_push`) runs one confined `claude -p` per stale doc just before
`git push`, so the doc fix rides along in that same push — enabling it sends covered-file
diff content to Anthropic on every push, so turning it on **is** the consent, and a
git-tracked `.claude/atlas.local.json` cannot enable it. Always fail-open: every failure
path prints to stderr and exits 0, because a broken doc-syncer must never wedge a push.
A `SessionStart` hook emits the operative "read INDEX.md first" rule, since a plugin's own
`CLAUDE.md` is never injected into a consuming repo's context.

> Full detail — write confinement, prompt-injection posture, the consent boundary, and the
> context-injection failure mode — lives in `plugins/atlas/CLAUDE.md` (auto-loads when
> working in that plugin) and `docs/decisions/ADR-019-atlas-push-sync.md`.

## Workflows

```
Content:   presentation-agent (dispatcher) → reactive-presentation-agent → content-review-agent → GitHub Pages
                                          → aws-light-fcd skill (native .pptx) → QA render → embed_fonts.py
           Remarp HTML ↔ .remarp.md (bidirectional visual editing via VSCode extension)
           PPTX theme:  .pptx → extract_pptx_theme.py → theme-manifest.json + theme-override.css
           PPTX export: export_pptx.py (headless Playwright capture + python-pptx, speaker notes included) → .pptx
                        (browser fallback: toc.html Export PPTX button → html2canvas + PptxGenJS)
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
           gh pr create → PreToolUse hook (opt-in) → same-prompt panel fan-out → quorum BLOCK/PASS
           git push → PreToolUse hook (opt-in) → 3-lens (correctness/security/scope) round-robin fan-out → 2+ BLOCK / 1 BLOCK (chair judgment) / 0 (pass)

kiro:      /kiro:setup → probe kiro-cli, list models, write .kiro/agents/*.json
           /kiro:delegate → Claude plans (Kiro spec) → per task: worktree → Kiro implements → capture-diff → scope_guard → Claude applies+tests → bounded retry → Claude fallback → commit → delegation-rate report
           git commit → PreToolUse hook (opt-in, off by default) → Kiro review (fail-open, blocks only on `critical`)
           git push → PreToolUse hook (opt-in, off by default) → 3-lens Kiro review (fail-open; `critical` BLOCKED, `warning`-only chair judgment)
           web search needed + no WebSearch tool (Bedrock) → kiro_websearch.py --query-file (opt-in) → summary + source URLs

atlas:     /atlas:init → scan repo → propose doc set (AskUserQuestion) → write skeletons w/ covers+code_rev → atlas_index.py --write → offer sync.on_push (states the egress first)
           /atlas:sync → atlas_drift.py (each doc's own code_rev..HEAD → covers glob match → work packets) → atlas_sync.py --dry-run → confined `claude -p` per doc (PreToolUse realpath guard + write-confinement revert) → validate → INDEX regen → docs(atlas): sync commit (staged narrowly: only the synced docs + INDEX.md, never the whole wiki root)
           git push → PreToolUse hook (opt-in, off by default) → drift detect → auto-fix → commit rides along in THAT push (fail-open: always exit 0)
           session start → SessionStart hook → "read INDEX.md first, pick by description+covers" rule, gated on INDEX.md existing (not on any toggle) — a plugin's own CLAUDE.md never reaches a consuming repo
```

## Docs Site & CI

- `doc-sites/` — Docusaurus site (en/ko i18n) deployed to https://www.atomai.click/oh-my-cloud-skills/ by `.github/workflows/deploy-docs.yml` on push to main; build detail in `doc-sites/CLAUDE.md`
- `.github/workflows/pr-review.yml` — CI multi-AI PR review (ADR-009); runbook in `docs/ci-pr-review-runbook.md`, review memory in `docs/pr-review/review-memory.md` (host-maintained, see pr-autofix)

## Auto-Sync Rules

Documentation stays in sync via hooks and skills:

| Trigger | Mechanism | Action |
|---------|-----------|--------|
| File edit (Write/Edit) | `check-doc-sync.sh` (PostToolUse) | Walks parent dirs for missing CLAUDE.md, warns if absent |
| File edit on README.md | PostToolUse hook | Auto-prompts Korean translation to README.ko.md |
| `git commit` (Bash) | `secret-scan.sh` (PreToolUse) | Blocks commits containing API keys, tokens, passwords |
| `git commit` (Bash) | `pre-commit-review.sh` (kiro, PreToolUse, opt-in) | Kiro-run review of the staged diff; fail-open, blocks only on `critical` |
| `git push` (Bash) | `pre-push-review.sh` (kiro, PreToolUse, opt-in) / `consensus_hooks.py pre-push-gate` (co-agent, PreToolUse, opt-in) | 3-lens (correctness/security/scope) review of the range about to be pushed; fail-open; `critical`/2+-lens BLOCKED, `warning`/1-lens CHAIR JUDGMENT REQUIRED |
| `git push` (Bash) | `pre-push-sync.sh` (atlas, PreToolUse, opt-in) | Detects atlas docs whose `covers` files changed since their `code_rev` and auto-fixes them, so the `docs(atlas): sync` commit rides along in that same push; always fail-open (exit 0) |
| Session start | `.claude/hooks/session-context.sh` (repo's own, SessionStart) | Loads project type, version, branch, uncommitted file count |
| Session start | `plugins/atlas/hooks/session-context.sh` (atlas, SessionStart) | Emits the operative "read `INDEX.md` first, pick docs by `description`/`covers`" rule whenever the wiki is initialized — a plugin's own `CLAUDE.md` never reaches a consuming repo's context, so this hook is the only channel that does, and it is gated only on `INDEX.md` existing (not on any toggle) |
| Session start / turn end (Stop) | `reap_kiro_orphans.sh` (co-agent) | Kills orphaned (ppid=1) kiro `acp-server` processes leaked by headless `timeout` kills |
| `remarp_to_slides.py` run | PreToolUse inline hook | Verifies common/ assets (theme.css, JS) exist before build |
| Commit creation | `.git/hooks/commit-msg` | Strips Co-Authored-By lines from commit messages |
| Manual | `/sync-docs` skill | Full documentation sync with quality scoring |
| Plan mode exit | CLAUDE.md convention | Update docs when architectural decisions change |
