---
sidebar_position: 1
title: "Kiro delegate skill"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="트리거" />
<span id="안전의-의미와-한계" />
<span id="명령" />
<span id="pre-commit-리뷰-opt-in" />
<span id="구현-모델과-리뷰-모델을-다르게-유지하는-이유" />
<span id="default-delegate-모드" />
<span id="절대-하지-않는-것" />
<span id="참고-파일" />


# Kiro delegate skill

Use this skill to assign implementation work to Kiro CLI. An explicit delegation request authorizes the workflow; automatic routing is controlled by `default_delegate` and defaults off.

## Pipeline and output {#pipeline-and-output}

Prepare the approved plan and Kiro-native task spec; execute in isolated worktrees; capture and validate declared paths; apply changes; run host verification; use a bounded fix loop; report tests, fallbacks, and delegation coverage. The host owns commits and the final result.

## Scope and shell trust {#scope-and-shell-trust}

Kiro runs in a separate git worktree. Only the captured diff can be applied to the main tree, and `scope_guard.py` validates paths against the union of files declared by the plan. The host runs verification and owns commits.

This controls which captured changes reach the main tree. It is not a filesystem sandbox for Kiro. `--trust-tools` grants tool approval, not directory confinement. The implementer's `execute_bash` capability defaults off and is a separate opt-in trust decision; enabling it can allow host effects outside the worktree.

## Review configuration {#review-configuration}

On-demand reviews are separate from implementation. Commit/push review hooks default off and use independent review settings. Tracked local configuration cannot silently opt a user into protected consent settings. Inspect effective configuration with `/kiro:configure`.

[Skill contract](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/kiro/skills/kiro-delegate/SKILL.md) · [Defaults](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/kiro/skills/kiro-delegate/kiro.defaults.json)
