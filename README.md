# oh-my-cloud-skills

Eight plugins for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and
[Codex](https://developers.openai.com/codex/plugins): cloud content, AWS operations,
agent and plugin conversion, peer review, implementation delegation, and project documentation.

[Documentation](https://www.atomai.click/oh-my-cloud-skills/) ·
[Changelog](CHANGELOG.md) ·
[Releases](https://github.com/Atom-oh/oh-my-cloud-skills/releases) ·
[License](LICENSE)

## Plugins

| Plugin | Workflows |
|---|---|
| [aws-content-plugin](plugins/aws-content-plugin/) | Interactive web decks, editable PowerPoint, architecture and animated diagrams, technical documents, GitBook sites, workshops, brochures, and personal profiles |
| [aws-ops-plugin](plugins/aws-ops-plugin/) | AWS/EKS troubleshooting, health checks, networking, identity, observability, storage, databases, analytics, cost, and Well-Architected reviews |
| [kiro-power-converter](plugins/kiro-power-converter/) | Convert plugin sources or individual skills into Kiro Powers, including steering, hooks, assets, and MCP configuration |
| [agentcore-creator](plugins/agentcore-creator/) | Discover requirements, design and test locally, then prepare AgentCore harness configuration or a Runtime application |
| [co-agent](plugins/co-agent/) | Peer review, decisions, ADRs, context synchronization, consensus/harness implementation, PR feedback fixes, and ADR reconciliation |
| [project-init](plugins/project-init/) | Initialize and maintain the current host's project instructions, skills, architecture docs, ADRs, runbooks, and reference guides |
| [kiro](plugins/kiro/) | Delegate implementation to Kiro CLI, with host verification and optional commit/push review and web search |
| [atlas](plugins/atlas/) | A per-topic repository wiki with coverage metadata, git-based drift checks, and optional push-time synchronization |

Both [Claude](.claude-plugin/marketplace.json) and
[Codex](.agents/plugins/marketplace.json) marketplaces contain these plugins.
Manifests and generated inventories define their current entry points; source
skills, commands, agents, and generated Codex entries are different populations.

## Installation

### Claude Code

Run these commands inside Claude Code, installing only the plugins you need:

```text
/plugin marketplace add Atom-oh/oh-my-cloud-skills
/plugin install aws-content-plugin@oh-my-cloud-skills
/plugin install co-agent@oh-my-cloud-skills
```

Use another name from the plugin table to install that package. From a local checkout:

```bash
claude --plugin-dir ./plugins/aws-content-plugin
```

Remove a package with `/plugin uninstall aws-content-plugin@oh-my-cloud-skills`;
remove the marketplace with `/plugin marketplace remove oh-my-cloud-skills`.

### Codex CLI

Use a Codex CLI with plugin support:

```bash
codex plugin marketplace add Atom-oh/oh-my-cloud-skills
codex
```

Open `/plugins`, select **Oh My Cloud Skills**, and install the desired packages.
For local development, run `codex plugin marketplace add ./` from this repository.
Manage the registered source with:

```bash
codex plugin marketplace list
codex plugin marketplace upgrade oh-my-cloud-skills
codex plugin marketplace remove oh-my-cloud-skills
```

Uninstall individual packages through `/plugins`. Start a new thread when needed
to load the installed entries.

### Skills, commands, and specialists in Codex

Request a workflow naturally or select it with `/skills` or the `$` picker.
Each plugin's `.codex-plugin/inventory.json` maps generated entries to shared
procedures. Same-name aliases can share an entry. Atlas graph and project-init
health-check use `source-command-graph` and `source-command-health-check`.

Claude commands become skill workflows in Codex. Agent Markdown supplies specialist
instructions; it does not register native Codex agent types, models, memory, or
permission grants. Internal specialist entries require explicit host selection.
External CLI workflows still need the relevant executable and authentication.

Declared plugin hooks require host trust. Project-init instead provides project
hook templates: install them in the consumer project, establish project trust,
inspect their definitions, and grant hook trust. Installing project-init alone
does not activate those project hooks. See
[runtime verification and evidence scope](docs/reference/codex-runtime-verification.md).

## Quick Start

| Request | Workflow |
|---|---|
| “Create a 30-minute English EKS operations deck with speaker notes and a quiz.” | reactive-presentation |
| “Create an editable AWS light PowerPoint deck from this outline.” | aws-light-fcd |
| “Draw this multi-AZ AWS architecture and export PNG.” | architecture-diagram |
| “Show request traffic and a failover scenario.” | animated-diagram |
| “Build a Workshop Studio lab with verification and cleanup.” | workshop-creator |
| “Diagnose why these pods cannot reach the service.” | ops-network-diagnosis |
| “Assess this cluster's health.” | ops-health-check |
| “Get a second opinion on this diff.” | co-agent review |
| “Delegate this approved implementation plan to Kiro.” | kiro-delegate |
| “Initialize this existing project for Codex.” | project-init |
| “Find Atlas pages that drifted from the code.” | atlas |

Commands shown below name the Claude workflows; select their corresponding
installed skill entries in Codex. Review a concrete deployment or publication
candidate before executing actions that require authorization.

## Reactive Presentation

The [reactive-presentation skill](plugins/aws-content-plugin/skills/reactive-presentation/SKILL.md)
authors Remarp source and builds interactive HTML. It supports fragments, presenter
notes, comparison/tabs, quizzes, timelines, checklists, code, and custom calculators
or simulations. A multi-file deck uses `_presentation.md`, block files, assets,
and generated HTML with a shared framework.

A local source workflow, run from this marketplace checkout:

```bash
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py validate ./my-presentation/
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py build ./my-presentation/ --lang en
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py sync ./my-presentation/
```

Use [Remarp quick start](doc-sites/docs/remarp-guide/quick-start.md),
[CLI reference](doc-sites/docs/remarp-guide/build-cli.md), and
[keyboard controls](doc-sites/docs/remarp-guide/keyboard-shortcuts.md) for the
current syntax and runtime behavior. The
[VS Code extension](doc-sites/docs/remarp-guide/vscode-extension.md) supplies preview,
source navigation, build, and issue annotations; `slide-fix` applies those annotations.

PPTX theme extraction applies a supplied brand to web slides. Screenshot-based
PPTX export captures a built deck; native editable PowerPoint uses
[aws-light-fcd](plugins/aws-content-plugin/skills/aws-light-fcd/SKILL.md).
Keep these output formats distinct. Shared AWS icons are reused across the workflows.

## Architecture Diagrams

The [architecture-diagram skill](plugins/aws-content-plugin/skills/architecture-diagram/SKILL.md)
provides YAML-driven Draw.io layout, hand-authored XML for unsupported structures,
and Excalidraw sketch output. Validate XML and require layout score at least 80
before Draw.io export. Sizes, colors, labels, and spacing come from the
[canonical design tokens](plugins/aws-content-plugin/skills/architecture-diagram/references/design-tokens.md).

Use simple Canvas DSL for a small linear flow; use HTML/CSS for larger or grouped
slide diagrams. Remarp's `:::archify` path renders through its configured, pinned
Archify dependency and embeds an explorable diagram. Check the source skill for
that dependency and output contract rather than treating it as another marketplace plugin.

## Animated Diagrams

[animated-diagram](plugins/aws-content-plugin/skills/animated-diagram/SKILL.md)
uses SVG/SMIL for repeated traffic motion and JavaScript/CSS state machines for
controlled scaling, deployment, and failover scenarios. Keep a readable static
architecture, labels, legend, and working reset/replay controls.

## Documents

The [document agent](plugins/aws-content-plugin/agents/document-agent.md) writes
technical reports and solution comparisons with evidence, diagrams, and useful
references. [brochure](plugins/aws-content-plugin/skills/brochure/SKILL.md) creates a
product or solution landing page; [gh-home](plugins/aws-content-plugin/skills/gh-home/SKILL.md)
creates a personal profile or portfolio. Both produce responsive HTML.

## GitBook Sites

[gitbook](plugins/aws-content-plugin/skills/gitbook/SKILL.md) supplies site structure,
SUMMARY navigation, rich components, diagrams, and cross-link checks. Create language
variants only when the deliverable requires them.

## Workshops

[workshop-creator](plugins/aws-content-plugin/skills/workshop-creator/SKILL.md)
produces Workshop Studio modules, labs, directives, and optional infrastructure.
Each lab explains prerequisites, commands, expected results, verification, and cleanup.

## AWS Ops

Use [ops-troubleshoot](plugins/aws-ops-plugin/skills/ops-troubleshoot/SKILL.md) for a
concrete failure, [ops-health-check](plugins/aws-ops-plugin/skills/ops-health-check/SKILL.md)
for an overall assessment, and the network, observability, security-audit, or
Well-Architected skill for its specific scope. Specialist procedures cover EKS,
network, IAM, observability, storage, database, analytics, cost, and architecture;
the coordinator correlates multi-domain incidents.

The workflow is scope → read-only evidence → diagnosis → authorized remediation →
verification. A scored assessment must identify its rubric and evidence gaps.
Bundled MCP servers are defined in the host manifests; additional integrations
require their own setup. See the [operations guide](doc-sites/docs/aws-ops-plugin/overview.md).

## Kiro Power Converter

[kiro-convert](plugins/kiro-power-converter/skills/kiro-convert/SKILL.md) accepts a
local plugin, GitHub source, marketplace candidate, or individual skill. It maps
metadata, steering, hooks, MCP settings, and assets into Kiro Power format.

```bash
python3 plugins/kiro-power-converter/skills/kiro-convert/scripts/convert_plugin_to_power.py \
  --source ./plugins/aws-ops-plugin --output /var/tmp/aws-ops-power --target export
```

Targets include export, project, and global installation. `--preserve-skills`
retains supported skill structure. Resolve ambiguous marketplace candidates to an
explicit source; inspect generated metadata and required environment variables
before loading the Power in [Kiro](https://kiro.dev).

## AgentCore Creator

[agentcore-create](plugins/agentcore-creator/skills/agentcore-create/SKILL.md) follows
Discovery → Design → Skill-First Build → Convert → Deploy and Verify. Existing
plugin input can enter at conversion. Choose harness configuration for a supported
managed loop or generated Strands/Runtime code for custom orchestration. Model
mapping, compatibility, tool/Gateway integration, and Memory options live in the
converter and its references. Generated files are not proof of cloud deployment.

## Co-agent

The current host chairs, excludes itself from external peer selection, verifies
findings against source, and owns the final synthesis. Peer responses are advisory;
agreement alone does not validate a finding.

The [co-agent skill](plugins/co-agent/skills/co-agent/SKILL.md) has **six modes**:

| Mode | Result |
|---|---|
| `review` | Evidence-checked findings and disagreements |
| `decide` | Options, tradeoffs, and a host recommendation |
| `adr` | A decision record informed by peer perspectives |
| `sync-context` | Marked AGENTS.md distilled from CLAUDE.md, plus the Kiro steering bridge |
| `consensus` | Host implementation with required peer gates |
| `harness` | Eligible peer implementation in isolated worktrees; host design, verification, and commits |

**`/co-agent:setup` is a separate readiness command.** It probes actual peer
usability; an installed binary alone is insufficient. Casual review/decide/ADR can
continue solo with an explicit notice. Consensus and harness require the usable
peer evidence and coverage their gates specify, and cannot silently become solo.
A plain code-review request does not automatically authorize multi-AI fan-out.

```text
/co-agent:setup
/co-agent review the current diff
/co-agent:configure
/co-agent:sync-context
```

`/co-agent:configure` shows effective models, supported effort, profiles, timeouts,
and budgets. The [canonical defaults](plugins/co-agent/skills/co-agent/co-agent.defaults.json)
and local overrides are authoritative; provider catalog IDs need not match across vendors.

[pr-autofix](plugins/co-agent/skills/pr-autofix/SKILL.md) polls AI/human feedback,
plans confirmed fixes, applies them in an isolated worktree, validates, and pushes
within configured bounds. [decision-reconcile](plugins/co-agent/skills/decision-reconcile/SKILL.md)
checks ADR contradictions and drift, then drafts a superseding decision.

## Kiro Delegation

`/kiro:setup` probes the CLI and prepares its agents. `/kiro:delegate` follows a
host-authored plan through task worktrees, Kiro implementation, diff capture, scope
validation, and host tests/commits. `/kiro:review` requests a review;
`/kiro:configure` shows effective settings.

The scope guard controls which captured changes reach the main tree. It does not
sandbox the Kiro process. Enabling the implementer's shell tool is a separate trust
decision. Default delegation, automatic review, and delegated search have separate
opt-in settings. Review settings are independent of implementation settings; see
[kiro.defaults.json](plugins/kiro/skills/kiro-delegate/kiro.defaults.json).

## Project Init and Atlas

Project-init adapts the existing repository to the selected host. Its workflows
include `init-project`, `sync-docs`, `add-adr`, `add-module`, `add-runbook`,
`add-reference-doc`, `generate-readme`, `generate-changelog`, and `health-check`.
Use actual source directories and build commands, preserve handwritten instructions,
and assess only applicable host checks. Project-init keeps upstream-owned source
separate from its repository-owned Codex overlay; see
[upstream synchronization](docs/reference/project-init-upstream-sync.md).

Atlas pages declare `covers`, `related`, and `code_rev` metadata. Git compares each
page's own revision anchor with changed covered files; the index helps select
relevant topics. `/atlas:init`, `/atlas:add-doc`, `/atlas:graph`, `/atlas:sync`, and
`/atlas:configure` manage the wiki. Start sync with `--dry-run` to inspect drift
without a model call or writes. On-demand repair can use the active Codex host;
opt-in unattended repair remains Claude-backed. See the
[Atlas contract](plugins/atlas/skills/atlas/SKILL.md) and
[defaults](plugins/atlas/skills/atlas/atlas.defaults.json).

<a id="workflows"></a>
<a id="content-review"></a>

## Quality Gate

Content output follows the
[content-review rubric](plugins/aws-content-plugin/agents/content-review-agent.md)
before publishing: score at least 85 on the standard scale, with the rubric's
Critical/Warning limits and format-specific scoring. Source validation and a build
are necessary evidence, not a substitute for the content review.

Local co-agent PR/push hooks, Kiro commit/push reviews, and Atlas push synchronization
are optional controls with their own consent and failure policies. Their disabled
or fail-open state does not waive this repository's required GitHub checks.

Repository PRs require **latest-HEAD AI Code Review and Codex package validation**.
The configured review roster covers the full reviewed diff, and a chair verifies
findings. Active Critical/Major findings block merge. Missing, failed, or truncated
required coverage is an error, not an implicit pass. Review the HEAD, target branch,
and prerequisite PRs immediately before merge; retain the enforced diff caps.

Use [CI review policy](docs/ci-pr-review.md),
[CI roster defaults](scripts/pr-review/pr-review.defaults.json),
[AI review workflow](.github/workflows/pr-review.yml), and
[Codex validation workflow](.github/workflows/codex-validation.yml) as the authority.
The privileged review executes trusted-base code and treats PR content as data;
the separate GitHub-hosted validation job checks the PR's generated packages without
provider secrets.

<a id="skills"></a>

## Project Structure

| Path | Maintained purpose |
|---|---|
| `plugins/` | Shared plugin procedures, references, scripts, and both host manifests |
| `.claude-plugin/marketplace.json` | Claude marketplace |
| `.agents/plugins/marketplace.json` | Codex marketplace |
| `scripts/sync-codex-plugins.py`, `scripts/codex/` | Codex projection generator and templates |
| `scripts/pr-review/` | Repository CI review tooling and configuration |
| `doc-sites/` | Public documentation and frozen demo artifacts |
| `docs/` | Architecture, ADRs, runbooks, and internal references |
| `tests/` | Repository validation and regression checks |
| `tools/remarp-vscode/` | Remarp editor extension |

Maintained documentation is English only. Requested deliverables can use another
language; literal aliases, syntax tokens, fixtures, and frozen demo payloads remain
data. [README.ko.md](README.ko.md) is a compatibility pointer to this README.
Release notes describe historical behavior, not current runtime guarantees.

## Development

Edit maintained sources or generator/templates, then regenerate affected Codex
outputs. Do not repair generated copies alone. Run the repository checks from its root:

```bash
bash tests/run-all.sh
python3 scripts/test-plugins.py
python3 scripts/test-codex-plugins.py
python3 scripts/sync-codex-plugins.py --check
python3 scripts/eval-skills.py
```

Runtime/adapter changes also use the local probes described in
[CLAUDE.md](CLAUDE.md) and the runtime verification guide. Those fixtures do not
certify external provider readiness. Public-site work uses the checks in
[doc-sites/CLAUDE.md](doc-sites/CLAUDE.md). See the
[version tags](https://github.com/Atom-oh/oh-my-cloud-skills/tags) for released artifacts.
