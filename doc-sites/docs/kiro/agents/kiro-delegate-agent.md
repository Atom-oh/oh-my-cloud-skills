---
sidebar_position: 1
title: "Kiro delegate agent"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="트리거-키워드" />
<span id="신뢰-경계" />
<span id="파이프라인-kirodelegate" />
<span id="참고-파일" />
<span id="다른-에이전트와의-연계" />


# Kiro delegate agent

The orchestrator manages plan creation, Kiro task execution, diff capture, scope checks, host verification, commits, and a final delegation report. It activates for explicit Kiro implementation requests or the user's enabled default-delegation setting.

## Task pipeline {#task-pipeline}

Resolve the configured CLI and model, prepare a Kiro-native spec, isolate tasks in worktrees, and enforce the configured parallelism and fix limits. Verify the resulting changes with the project's real test commands. If a task falls back to host implementation, identify it in the report.

## Trust boundary {#trust-boundary}

Kiro runs in a separate git worktree. Only the captured diff can be applied to the main tree, and `scope_guard.py` validates paths against the union of files declared by the plan. The host runs verification and owns commits.

This controls which captured changes reach the main tree. It is not a filesystem sandbox for Kiro. `--trust-tools` grants tool approval, not directory confinement. The implementer's `execute_bash` capability defaults off and is a separate opt-in trust decision; enabling it can allow host effects outside the worktree.

## Related workflows {#related-workflows}

Use `/kiro:review` for review alone. Use co-agent for a second opinion from a diverse panel; its harness has different implementer eligibility requirements.

[Agent definition](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/kiro/agents/kiro-delegate-agent.md)
