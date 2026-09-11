---
description: Poll for PR review feedback (AI + human) and auto-fix issues (loop bound from /co-agent:configure, default 5)
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
---

# PR Auto-Fix

Drive the current branch's PR to a passing review state: poll AI and human review
feedback, fix what the reviews raise, push, and repeat until required reviews are
complete or a defined blocker is reached. When the user authorized merging, verify
the final HEAD, CI and integration path, then merge. The landed changes are exactly the
plan-approved delta, consumed by the PR's reviewers and whoever merges. Excellent means
every blocking finding is resolved with the smallest change that addresses it — and
nothing else moves.

## Context

- Current branch: !`git branch --show-current`
- PR status: !`gh pr list --head "$(git branch --show-current)" --json number,title,state,reviewDecision --jq '.[0]' 2>/dev/null || echo "No PR found"`

## Instructions

Execute the `pr-autofix` skill — it is the canonical workflow (polling cadence,
state machine, worktree isolation, and safety rails all live there, not here). In outline:

1. Identify the PR from the current branch.
2. Poll AI review comments (marker resolved via `co_agent_config.py pr-autofix-marker` —
   configurable, regex auto-detect by default; tune: `/co-agent:configure set pr_autofix
   review_marker <s>`) and human review status (`CHANGES_REQUESTED`).
3. Judge required coverage for the latest HEAD. Keep observing live review handles;
   missing or failed required review is not a pass. Report `review_unavailable`
   when external action is required, following the skill's state model.
4. If any review is blocking → read the issues, plan fixes on Fable/Opus, implement the
   plan with opus [medium effort] subagents in an isolated git worktree, land only the
   plan-approved delta, verify, commit, push.
5. Repeat up to the loop bound the skill resolves via `co_agent_config.py
   pr-autofix-iterations` (tune: `/co-agent:configure set pr_autofix max_iterations <n>`,
   default 5).
6. Once required reviews and CI pass, complete the user's authorized review/merge
   workflow. Re-read HEAD, target branch and prerequisite PR state before merging.
