---
description: Poll for PR review feedback (AI + human) and auto-fix issues (loop bound from /co-agent:configure, default 5)
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
---

# PR Auto-Fix

Automatically read PR review feedback and fix issues in a loop.

## Context

- Current branch: !`git branch --show-current`
- PR status: !`gh pr list --head "$(git branch --show-current)" --json number,title,state,reviewDecision --jq '.[0]' 2>/dev/null || echo "No PR found"`

## Instructions

Execute the `pr-autofix` skill. The skill handles the full workflow:

1. Identify the PR from the current branch
2. Poll for AI review comments (marker resolved via `co_agent_config.py pr-autofix-marker` —
   configurable, regex auto-detect by default; tune: `/co-agent:configure set pr_autofix
   review_marker <s>`) and human review status (`CHANGES_REQUESTED`)
3. If all reviews pass → done
4. If any review is blocking → read issues, plan fixes on Fable/Opus, implement the plan with opus [medium effort] subagents in an isolated git worktree (parallel only when file sets are strictly disjoint), land only the plan-approved delta, verify build, commit, push
5. Repeat up to `$MAX_ITER` times — the skill resolves it via `co_agent_config.py pr-autofix-iterations` (tune: `/co-agent:configure set pr_autofix max_iterations <n>`, default 5)

Key constraints:
- Never modify `.github/workflows/*` files
- Only fix what the reviews mention — no extra refactoring
- Always verify the code compiles before committing
- Poll at 60-second intervals, timeout after 10 minutes
