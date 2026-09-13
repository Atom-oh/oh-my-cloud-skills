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

## Six skill modes

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

## Components

The Claude package declares `co-agent`, `gate-chair`, `harness-analyst`, `pr-autofix-planner`, and `pr-autofix-implementer`; its skills are `co-agent`, `pr-autofix`, and `decision-reconcile`. The planner and implementer are internal PR workers that require prepared inputs. Codex exposes these workflows through generated overlays, including command wrappers.

## Configuration and gates

Use `/co-agent:configure` to inspect merged configuration, its source, and host-specific peer availability. The defaults file defines profiles, model lists, effort, timeouts, context limits, call budgets, and retry bounds. A deep profile can use multiple models per peer; a default profile uses the single model setting. Do not infer a provider's supported model catalog from a configured string.

[Canonical defaults](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/skills/co-agent/co-agent.defaults.json)

`pr_gate.enabled` and `push_gate.enabled` default off. These optional local hooks are separate from mandatory CI and branch protection. Missing, failed, or stale required review coverage is not a successful review.

## Context synchronization

`/co-agent:sync-context` distills `CLAUDE.md` into a marked `AGENTS.md` and creates `.kiro/steering/project-context.md` as a bridge. The source hash detects drift; unmarked handwritten files are protected. Use `/co-agent:configure set autosync on` to opt into automatic synchronization prompts.

## Related workflows

[PR autofix](/docs/co-agent/skills/pr-autofix) applies review feedback. [Decision reconcile](/docs/co-agent/skills/decision-reconcile) finds contradictions across ADRs and current code. Ordinary code review or an unqualified “decide” request does not by itself request a multi-AI panel; explicitly invoke co-agent when peer input is wanted.
