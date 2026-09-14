---
sidebar_position: 2
title: "PR autofix"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="pr-autofix-skill" />
<span id="리뷰-소스" />
<span id="워크플로우" />
<span id="판정-기준" />
<span id="제약-사항" />
<span id="레퍼런스" />
<span id="pr-review-workflowyml" />


# PR autofix

PR autofix gathers AI and human review feedback, validates findings against the code, and applies bounded fixes with separate planning and implementation workers.

## Feedback loop {#feedback-loop}

1. Read the PR's current HEAD, review summaries, inline comments, unresolved threads, and check results.
2. Reject stale or unsupported findings; prepare a concrete fix plan for confirmed issues.
3. Apply the plan in an isolated worktree, run relevant tests and required checks, then commit and push.
4. Wait for review of the new HEAD and repeat within `pr_autofix.max_iterations`.
5. Report remaining findings, review coverage, checks, and the final PR state.

A failed review, absent response, or review of an older commit is not evidence that the current change is clean. Validate severity against the affected runtime path; do not automatically implement every suggestion.

## Limits and integration {#limits-and-integration}

[Canonical iteration setting](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/skills/co-agent/co-agent.defaults.json)

AI review requires the consumer repository to install the example workflow and its
paired gate helper; follow the [CI workflow setup](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/skills/pr-autofix/SKILL.md#ci-workflow-setup).
The autofix loop never edits `.github/workflows/*`; configure that automation separately.

The skill itself does not grant merge authorization or bypass protection rules. Follow the repository's explicit review and merge policy. Local optional review hooks and CI review workflows are separate controls.

[Skill contract](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/skills/pr-autofix/SKILL.md) · [Example review workflow](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/skills/pr-autofix/references/pr-review-workflow.yml)
