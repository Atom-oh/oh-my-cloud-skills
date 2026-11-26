---
sidebar_position: 1
title: "co-agent"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="co-agent-개요" />
<span id="구성-요소" />
<span id="에이전트-5개" />
<span id="스킬-3개" />
<span id="명령-6개" />
<span id="사전-요구사항-선택적--있는-것만-사용" />
<span id="일곱-가지-모드" />
<span id="의장-원칙-chair-principle" />
<span id="판정-기준-review-모드" />
<span id="패널-설정-co-agentconfigure" />
<span id="현재-기본값-co-agentdefaultsjson" />
<span id="ai-컨텍스트-동기화-co-agentsync-context" />
<span id="auto-invocation-키워드" />


# co-agent

Second opinions, decisions, ADRs, and implementation pipelines with peer review. The current host chairs the work.

## Six skill modes {#six-skill-modes}

| Mode | Result | Execution requirement |
| --- | --- | --- |
| `review` | Evidence-checked findings and disagreements | Available peers; solo allowed with notice |
| `decide` | Option comparison and the host's recommendation | Available peers; solo allowed with notice |
| `adr` | Alternatives, tradeoffs, and an ADR draft | Available peers; solo allowed with notice |
| `sync-context` | Shared AGENTS.md and Kiro steering bridge | Local context validation |
| `consensus` | Host implementation with plan and final review gates | READY peer required |
| `harness` | Worktree implementation by an eligible peer or explicitly selected host mode | Fresh READY raw-CLI reviewer required; host owns verification and commits |

When no eligible implementer is READY, harness requires an explicit, authorized
host-mode choice through `--allow-host-implementation`. Configuration and readiness
errors must be repaired first. Both modes require a fresh, gate-eligible reviewer;
see the
[harness contract](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/commands/harness.md).

`/co-agent:setup` is a separate command that probes installed/authenticated peer CLIs and records readiness before the gated workflows run.

Claude chairs Claude Code sessions; Codex chairs Codex sessions. The host does not call itself as an external peer. External responses are advisory: the host checks evidence, attributes findings, and reports meaningful disagreement.

The active CLI candidates are Kiro plus the opposite host CLI: Codex when Claude
hosts, or Claude when Codex hosts. Antigravity (`agy`) and the legacy Gemini CLI
are retired. Refresh setup after migrating old provider settings.
The [v2.0.0 migration guide](/docs/releases/v2.0.0#co-agent-migration) describes
the supported peers and implementation choices.

## Kiro task scope {#kiro-task-scope}

Kiro joins a panel only for eligible AWS work: AWS architecture review, AWS resource review, and AWS CDK or Terraform authoring. It ships disabled, so enable it in the panel configuration and select the matching task scope with `CO_AGENT_TASK_SCOPE` (`aws-architecture-review`, `aws-resource-review`, `aws-cdk-authoring` or `aws-terraform-authoring`). The restriction applies before readiness probes and peer calls, even when a saved profile enables Kiro. General reviews, ADRs, documentation and unrelated implementation use the opposite host CLI only. In a mixed task, Kiro receives just the eligible AWS part. Shipped model lists are empty, so each peer CLI runs its own configured model until you set a `models` list.

## Components {#components}

The canonical `co-agent` skill runs in the current host instead of a duplicate
orchestrator agent. The Claude package has three agents: `gate-chair`,
`pr-autofix-planner`, and `pr-autofix-implementer`. Their judgment, read-only planning,
and edit-only implementation boundaries remain separate. Its three source skills
are `co-agent`, `pr-autofix`, and `decision-reconcile`; five source commands complete
the workflows. Codex exposes 11 generated entry skills, including command wrappers
and agent procedures, not native agent registrations.

The old `co-agent:co-agent` persona and `harness-analyst` are retired. Use `/co-agent`
for orchestration and `/co-agent:configure analyze [session-dir]` for advisory run
analysis. See [roles and migration](/docs/co-agent/agents/co-agent) for the retained
workers and model/memory behavior. Decision reconcile's four dynamic review lenses
are unchanged; they are not additional registered agents.

## Configuration and gates {#configuration-and-gates}

Use `/co-agent:configure` to inspect merged configuration, its source, and host-specific peer availability. The defaults file defines profiles, model lists, effort, timeouts, context limits, call budgets, and retry bounds. A deep profile can use multiple models per peer; a default profile uses the single model setting. Do not infer a provider's supported model catalog from a configured string.

`/co-agent:configure analyze [session-dir]` reads harness/consensus records and
proposes evidence-backed configuration changes without applying them. It reports
observations only when fewer than three runs are recorded. Applying a proposal is
a separate, authorized configuration change.

[Canonical defaults](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/skills/co-agent/co-agent.defaults.json)

`pr_gate.enabled` and `push_gate.enabled` default off. These optional local hooks are separate from mandatory CI and branch protection. Missing, failed, or stale required review coverage is not a successful review.

## Context synchronization {#context-synchronization}

`/co-agent:sync-context` maintains one concise, reviewed `AGENTS.md`. The host and an available opposite-host reviewer draft independently from the same secret-free evidence, cross-review each other, and the host reconciles one candidate of at most 200 lines and 10 KiB. The candidate is checked with `check_ai_context.py --check-candidate` before it replaces the file, and a residual-file secret audit runs after publishing. Handwritten files without the co-agent marker are protected, and `.kiro/steering/project-context.md` keeps a bridge to the shared file. Kiro is not used for context drafting. An older `AGENTS.md` distilled from `CLAUDE.md` is still validated, including its source-hash drift check. Use `/co-agent:configure set autosync on` to opt into automatic synchronization prompts.

## Related workflows {#related-workflows}

[PR autofix](/docs/co-agent/skills/pr-autofix) applies review feedback. [Decision reconcile](/docs/co-agent/skills/decision-reconcile) finds contradictions across ADRs and current code. Ordinary code review or an unqualified “decide” request does not by itself request a multi-AI panel; explicitly invoke co-agent when peer input is wanted.
