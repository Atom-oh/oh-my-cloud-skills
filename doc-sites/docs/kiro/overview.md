---
sidebar_position: 1
title: "Kiro delegation"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="kiro-개요" />
<span id="구성-요소" />
<span id="에이전트-1개" />
<span id="스킬-1개" />
<span id="명령-4개" />
<span id="동작-방식" />
<span id="왜-싸지나" />
<span id="웹-검색-위임-bedrock-사용자용-opt-in" />
<span id="신뢰-경계-co-agent가-kiro를-구현자로-거부하는-이유" />
<span id="다음-단계" />


# Kiro delegation

Delegate implementation and optional reviews to Kiro CLI while the current host owns the plan, verification, and commits.

## Workflow {#workflow}

Plan → Kiro-native spec → task worktrees → Kiro implementation → capture diff → scope validation → host tests → host commit → delegation report. If Kiro exhausts the configured fix loop, the host can finish that task and report the fallback.

The purpose is to move implementation and optional review work to the configured Kiro account. Actual savings depend on subscription, model, usage, and the amount of host verification; the plugin does not guarantee a price reduction.

## Commands {#commands}

| Command | Purpose |
| --- | --- |
| `/kiro:setup` | Probe CLI/authentication, prepare agents, and inspect opt-in settings |
| `/kiro:delegate` | Plan, delegate, verify, and report implementation |
| `/kiro:review` | Request an on-demand review |
| `/kiro:configure` | Show or change effective settings |

## Trust boundary {#trust-boundary}

Kiro runs in a separate git worktree. Only the captured diff can be applied to the main tree, and `scope_guard.py` validates paths against the union of files declared by the plan. The host runs verification and owns commits.

This controls which captured changes reach the main tree. It is not a filesystem sandbox for Kiro. `--trust-tools` grants tool approval, not directory confinement. The implementer's `execute_bash` capability defaults off and is a separate opt-in trust decision; enabling it can allow host effects outside the worktree.

## Optional automation {#optional-automation}

Default delegation, commit review, push review, and delegated web search default off. Review model and effort are independent from implementation settings. A null model means the code resolves the setting; do not replace it in documentation with a guessed “latest” catalog ID.

Delegated web search is available for a host without its own search tool. Its restricted agent has only `web_search`; the query is passed via a file, and invalid agent configuration is rejected. Native host search takes priority.

[Canonical defaults](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/kiro/skills/kiro-delegate/kiro.defaults.json)

## Related links {#related-links}

- [installation](/docs/kiro/installation)
- [usage guide](/docs/kiro/usage-guide)
- [kiro-delegate-agent](/docs/kiro/agents/kiro-delegate-agent)
- [kiro delegate](/docs/kiro/skills/kiro-delegate)
- [commands](/docs/kiro/commands/)
