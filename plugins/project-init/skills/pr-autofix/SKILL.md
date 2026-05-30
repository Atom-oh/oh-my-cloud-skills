---
name: pr-autofix
description: After creating a PR, poll for AI and human review feedback, auto-fix issues, and push (max 3 iterations)
triggers:
  - "pr autofix"
  - "pr review fix"
  - "PR 자동 수정"
  - "리뷰 피드백 수정"
---

# PR Auto-Fix Skill

After you create a PR (via `gh pr create`), automatically wait for review feedback — from AI Code Review CI and/or human reviewers — then read the feedback, fix issues, and push. Repeat up to 3 times until all reviews pass.

## When to use

Invoke this skill immediately after creating a PR. It replaces the manual cycle of:
1. Push → wait for review → read comments → fix → push again

## Review Sources

This skill monitors two review sources simultaneously:

| Source | Detection | Pass Condition |
|--------|-----------|----------------|
| **AI Code Review** | `<!-- bedrock-pr-review -->` marker in issue comments | `**Status: PASSED**` in comment body |
| **Human Reviewer** | `gh pr reviews` with `CHANGES_REQUESTED` state | All reviews `APPROVED` or no reviews yet |

Both sources must pass for the PR to be considered approved. If either is blocking, proceed to fix.

## Flow

```
PR created → poll for reviews → ALL PASS? → done
                               → ANY BLOCKED? → read issues → fix code → commit & push → repeat
                               → 3 iterations? → stop, notify user
```

## Steps

### 1. Identify the PR

Get the PR number from the current branch:

```bash
REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner')
PR_NUMBER=$(gh pr list --head "$(git branch --show-current)" --json number --jq '.[0].number')
```

If no PR is found, stop and inform the user.

### 2. Poll for review feedback

Poll every 60 seconds until reviews appear or timeout (10 minutes). Check both sources on each poll:

**AI Review:**

```bash
gh api "repos/${REPO}/issues/${PR_NUMBER}/comments" \
  --jq '.[] | select(.body | contains("<!-- bedrock-pr-review -->")) | {updated_at, body}'
```

Verify the comment's `updated_at` timestamp is after the last push to ensure it reflects the latest code.

**Human Review:**

```bash
# NOTE: `gh pr reviews` does not exist — reviews are read via `gh pr view --json reviews`.
gh pr view "$PR_NUMBER" --json reviews \
  --jq '.reviews[] | select(.state == "CHANGES_REQUESTED" or .state == "APPROVED")
        | {author: .author.login, state, body, submittedAt}'
```

Also read inline review comments (line-level feedback):

```bash
gh api "repos/${REPO}/pulls/${PR_NUMBER}/comments" \
  --jq '.[] | select(.pull_request_review_id != null) | {path, line, body, created_at}'
```

### 3. Check verdict

Evaluate each review source:

**AI Review verdict:**
- Body contains `**Status: PASSED**` → PASS
- Body contains `**Status: BLOCKED**` → BLOCKED
- No AI review comment found → SKIP (no CI configured)

**Human Review verdict:**
- All reviews are `APPROVED` → PASS
- Any review is `CHANGES_REQUESTED` → BLOCKED
- No human reviews yet → SKIP (not yet reviewed)

**Combined verdict:**
- Both PASS (or SKIP) → done, inform user
- Either BLOCKED → proceed to fix

### 4. Fix issues (if BLOCKED)

Read all blocking feedback and the current diff. Fix issues from both sources:

**From AI Review:**
- Parse the review comment body for issue descriptions
- Focus on **CRITICAL** and **MAJOR** issues first
- Fix **MINOR** issues if trivial

**From Human Review:**
- Read the review body text (high-level feedback)
- Read inline comments (`path`, `line`, `body`) for specific code feedback
- Address each comment in the referenced file and line

**Constraints:**
- Do NOT refactor beyond what the reviews ask
- Do NOT modify CI/CD workflow files (`.github/workflows/*`)
- Verify the fix compiles/builds before committing:

```bash
# Detect project type and verify build. Each check is self-contained so a
# missing manifest never falls through and triggers a different toolchain
# (e.g. `A && B || C` would run C when A is false — grouped to prevent that).
[ -f go.mod ] && go build ./...
[ -f package.json ] && { npm run build 2>/dev/null || npx tsc --noEmit 2>/dev/null; }
if [ -f pyproject.toml ]; then
  PY=$(git diff --name-only --diff-filter=M -- '*.py')
  [ -n "$PY" ] && python3 -m py_compile $PY
fi
[ -f Cargo.toml ] && cargo check
```

### 5. Commit and push

```bash
git add <changed-files>
git commit -m "fix: address review feedback (iteration N/3)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
git push
```

### 6. Repeat or stop

- If iteration < 3: go back to step 2 (poll for new review after push)
- If iteration == 3 and still BLOCKED: stop and tell the user that manual review is needed
- Track iteration count by counting commits with message prefix `fix: address review feedback`

```bash
ITERATION=$(git log --oneline --grep="fix: address review feedback" origin/main..HEAD | wc -l)
```

## Important constraints

- **Max 3 iterations** — after 3 failed attempts, stop unconditionally
- **Never modify workflow files** — the review CI itself must not be changed during autofix
- **Scope discipline** — only fix what the reviews mention, nothing else
- **Build verification** — always verify the code compiles before committing
- **Polling patience** — CI takes 2-5 minutes; poll at 60s intervals, not faster
- **Human review courtesy** — when fixing human comments, add a brief reply acknowledging the fix if possible

## CI Workflow Setup

To use the AI review mode, the project needs the AI Code Review GitHub Actions workflow. A reference workflow is available at:

```
references/pr-review-workflow.yml
```

Copy it to your project's `.github/workflows/pr-review.yml` and configure:
1. Set `ANTHROPIC_MODEL` in repository variables (e.g., `us.anthropic.claude-opus-4-8`)
2. Ensure the runner has AWS Bedrock access (or set `ANTHROPIC_API_KEY` for direct API)
3. Grant `pull-requests: write` and `contents: read` permissions
