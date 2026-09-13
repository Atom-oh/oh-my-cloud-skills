---
sidebar_position: 3
title: "Use Kiro delegation"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="사용법-가이드" />
<span id="빠른-시작" />
<span id="kirodelegate--구현-위임-파이프라인" />
<span id="kiroreview--온디맨드-리뷰" />
<span id="pre-commit-훅-opt-in-기본-off" />
<span id="kiroconfigure--설정-조정" />
<span id="동작-원리" />
<span id="다음-단계" />


# Use Kiro delegation

## Start

```text
/kiro:setup
/kiro:delegate implement the approved pagination plan
/kiro:review --range --lenses correctness,security,scope
/kiro:configure
```

Setup validates actual CLI access and prepares `.kiro/agents/` configuration. Select implementation and review settings from the available local configuration. Automatic delegation, review hooks, and web search require their own opt-in settings.

The range review covers the committed work produced by delegation. A bare
`/kiro:review` uses the staged-diff path; see the
[review command](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/kiro/commands/review.md)
for scope options.

## Implementation

The current host prepares the plan/spec and declares editable paths. Kiro implements tasks in isolated worktrees; the host captures each diff, enforces scope, applies it, and runs relevant checks. A bounded fix loop can ask Kiro to repair failures. The host reports any direct implementation fallback and owns all commits.

## Reviews and false positives

On-demand review and optional commit/push hooks use the review engine. The host checks findings against the diff, runtime behavior, configuration, and tests. Review effort and model are configured separately from delegation.

`review.on_commit` and `review.on_push` default off. Their configured blocking thresholds apply only when enabled. A local advisory or disabled optional hook does not waive a required CI review.

## Trust and configuration

Kiro runs in a separate git worktree. Only the captured diff can be applied to the main tree, and `scope_guard.py` validates paths against the union of files declared by the plan. The host runs verification and owns commits.

This controls which captured changes reach the main tree. It is not a filesystem sandbox for Kiro. `--trust-tools` grants tool approval, not directory confinement. The implementer's `execute_bash` capability defaults off and is a separate opt-in trust decision; enabling it can allow host effects outside the worktree.

[Settings schema and defaults](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/kiro/skills/kiro-delegate/kiro.defaults.json)

## Related links

- [overview](/docs/kiro/overview)
- [kiro-delegate-agent](/docs/kiro/agents/kiro-delegate-agent)
- [kiro delegate](/docs/kiro/skills/kiro-delegate)
- [commands](/docs/kiro/commands/)
