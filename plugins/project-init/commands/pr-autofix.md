---
description: Poll for PR review feedback (AI + human) and auto-fix issues (max 3 iterations)
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
2. Poll for AI review comments (`<!-- bedrock-pr-review -->`) and human review status (`CHANGES_REQUESTED`)
3. If all reviews pass → done
4. If any review is blocking → read issues, plan fixes on Fable/Opus, implement the plan with sonnet subagents in an isolated git worktree (parallel only when file sets are strictly disjoint), land only the plan-approved delta, verify build, commit, push
5. Repeat up to 3 times

Key constraints:
- Never modify `.github/workflows/*` files
- Only fix what the reviews mention — no extra refactoring
- Always verify the code compiles before committing
- Poll at 60-second intervals, timeout after 10 minutes
