# Skills Templates

Templates for `.claude/skills/` SKILL.md files.

---

## Code Review Skill

Path: `.claude/skills/code-review/SKILL.md`

```markdown
# Code Review Skill

Review changed code with confidence-based scoring to filter false positives.

## Review Scope

By default, review unstaged changes from `git diff`. The user may specify different files or scope.

## Review Criteria

### Project Guidelines Compliance
- Import patterns and module boundaries
- Framework conventions and language style
- Function declarations and error handling
- Naming conventions from CLAUDE.md

### Bug Detection
- Logic errors and null/undefined handling
- Race conditions and memory leaks
- Security vulnerabilities (OWASP Top 10)
- Performance problems

### Code Quality
- Code duplication and unnecessary complexity
- Missing critical error handling
- Test coverage gaps
- Accessibility issues (for frontend code)

## Confidence Scoring

Rate each issue 0-100:
- **0-24**: Likely false positive or pre-existing issue. Do not report.
- **25-49**: Might be real but possibly a nitpick. Do not report.
- **50-74**: Real issue but minor. Report only if critical.
- **75-89**: Verified real issue, important. Report with fix suggestion.
- **90-100**: Confirmed critical issue. Must report.

**Only report issues with confidence >= 75.**

## Output Format

For each issue:
### [CRITICAL|IMPORTANT] <issue title> (confidence: XX)
**File:** `path/to/file.ext:line`
**Issue:** Clear description of the problem
**Guideline:** Reference to CLAUDE.md rule or security standard
**Fix:** Concrete code suggestion

If no high-confidence issues found, confirm code meets standards with brief summary.
```

---

## Refactor Skill

Path: `.claude/skills/refactor/SKILL.md`

```markdown
# Refactor Skill

Refactor existing code to improve quality without changing behavior.

## Principles
- Improve structure without changing behavior
- Single Responsibility Principle (SRP)
- Remove duplicate code (DRY)
- Small, incremental steps with verification

## Process

### 1. Analysis
- Identify the target code and its tests
- Map all callers and dependencies
- Confirm test coverage exists (suggest adding tests first if not)

### 2. Plan
Present the refactoring plan to the user:
- What will change
- What will NOT change (behavior preservation)
- Risk assessment (low/medium/high)

### 3. Execute
- Make changes in small, verifiable steps
- Run tests after each step if possible
- Keep commits atomic

### 4. Verify
- Confirm all existing tests pass
- Verify no behavior changes
- Check that the refactoring achieved its goal
```

---

## Release Skill

Path: `.claude/skills/release/SKILL.md`

```markdown
# Release Skill

Automate the release process with validation checks.

## Procedure

### 1. Pre-release Checks
- Verify working tree is clean: `git status`
- Verify all tests pass
- Check for uncommitted changes

### 2. Determine Version
- Review changes since last tag: `git log $(git describe --tags --abbrev=0)..HEAD --oneline`
- Apply semver rules:
  - MAJOR: Breaking API changes
  - MINOR: New features, backward compatible
  - PATCH: Bug fixes only

### 3. Update Changelog
- Group changes by type (Added, Changed, Fixed, Removed)
- Include commit references
- Add date and version header

### 4. Create Release
- Update version in relevant files (package.json, pyproject.toml, etc.)
- Create git tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
- Generate release notes

### 5. Summary
- Display version bump
- List key changes
- Show next steps (push tag, deploy, etc.)
```

---

## Sync Docs Skill

Path: `.claude/skills/sync-docs/SKILL.md`

```markdown
# Sync Docs Skill

Synchronize project documentation with current code state.

## Actions

### 1. Quality Assessment
Score each CLAUDE.md file (0-100) across:
- Commands/workflows (20 pts)
- Architecture clarity (20 pts)
- Non-obvious patterns (15 pts)
- Conciseness (15 pts)
- Currency (15 pts)
- Actionability (15 pts)

Apply anti-pattern deductions:
- Over 500 lines (-15)
- Vague instructions (-10)
- Duplicated docs (-10)
- No test guidance (-10)
- Contains secrets (-20)

Output quality report with grades (A-F) before making changes.

### 2. Root CLAUDE.md Sync
- Update Overview, Tech Stack, Conventions, Key Commands
- Verify commands are copy-paste ready against actual scripts

### 3. Architecture Doc Sync
- Update docs/architecture.md to reflect current system structure
- Add new components, update data flows, reflect infrastructure changes

### 4. Module CLAUDE.md Audit
- Scan all directories under source root
- Create CLAUDE.md for modules missing one
- Update existing module CLAUDE.md files if out of date
- Score each module CLAUDE.md

### 5. ADR and Runbook Audit
- Check recent commits for undocumented architectural decisions
- Verify runbook coverage against project characteristics
- Flag stale ADRs and outdated runbooks

### 6. README.md Sync
- Update project structure section to match actual directory layout

### 7. Report
Output before/after quality scores, anti-patterns detected, and list of all changes.
```

---

## Common Slash Command Templates

These are slash commands generated in `.claude/commands/` by `/init-project`.

---

### Review Command

Path: `.claude/commands/review.md`

```markdown
---
description: Run code review on current changes with confidence-based filtering
allowed-tools: Read, Glob, Grep, Bash(git diff:*), Bash(git log:*)
---

# Code Review

Review the current code changes using confidence-based scoring.

## Step 1: Get Changes

Determine the scope of review:

- If $ARGUMENTS specifies files, review those files
- Otherwise, review unstaged changes: `git diff`
- If no unstaged changes, review staged changes: `git diff --cached`

## Step 2: Review

For each changed file, apply the code-review skill criteria:
- Project guidelines compliance (from CLAUDE.md)
- Bug detection (logic errors, security, performance)
- Code quality (duplication, complexity, test coverage)

## Step 3: Score and Filter

Rate each issue 0-100. Only report issues with confidence >= 75.

## Step 4: Output

Present findings in structured format with file paths, line numbers, and fix suggestions.
If no high-confidence issues, confirm code meets standards.

## Error Recovery

### If no changes found (Step 1)
No diff output means nothing to review. Inform the user:
- Check if changes are committed: `git log -1 --oneline`
- Check if on the right branch: `git branch --show-current`
- Suggest specifying files directly: `/review path/to/file`

### If CLAUDE.md is missing or empty (Step 2)
Cannot evaluate project guidelines without CLAUDE.md. Suggest:
- Run `/init-project` to generate CLAUDE.md
- Or create a minimal CLAUDE.md with conventions section

### If diff is too large (>500 lines)
Focus on high-risk files first:
1. Files with security-sensitive changes (hooks, scripts)
2. Files with logic changes
3. Documentation changes (lower priority)
```

---

### Test All Command

Path: `.claude/commands/test-all.md`

```markdown
---
description: Execute the full test suite and report results
allowed-tools: Read, Bash(npm test:*), Bash(npm run test:*), Bash(pytest:*), Bash(go test:*), Bash(cargo test:*), Bash(mvn test:*), Bash(gradle test:*), Glob
---

# Test All

Execute the full test suite for this project.

## Step 1: Detect Test Framework

Read project files to determine the test framework:
- `package.json` -> look for test script (jest, vitest, mocha)
- `pyproject.toml` / `setup.cfg` -> pytest
- `go.mod` -> go test
- `Cargo.toml` -> cargo test
- `pom.xml` -> mvn test
- `build.gradle` -> gradle test

## Step 2: Run Tests

Execute the appropriate test command:

```bash
# Node.js
npm test

# Python
pytest -v

# Go
go test ./...

# Rust
cargo test

# Java (Maven)
mvn test

# Java (Gradle)
gradle test
```

## Step 3: Report

Present:
- Total tests run, passed, failed, skipped
- Failed test details with file paths and error messages
- Suggest fixes for failing tests if the cause is apparent

## Error Recovery

### If test runner itself fails
\```bash
bash -n tests/run-all.sh          # Check syntax
ls -la tests/**/*.sh              # Check permissions
chmod +x tests/**/*.sh            # Fix permissions
\```

### Common failure categories and fixes

| Failure Pattern | Likely Cause | Fix |
|---|---|---|
| "file not found" | Missing file after restructure | Create file or update test |
| "invalid JSON" | Malformed manifest | `python3 -m json.tool <file>` |
| "Version mismatch" | Manifest versions diverged | Update both to same version |
| "not executable" | Permission reset by git | `chmod +x` on affected files |
| "bash syntax error" | Bad edit in script | `bash -n <file>` to locate error |

### If many tests fail at once
Likely a structural change broke multiple assumptions:
1. `git log -1` — what was the last change?
2. `git diff HEAD~1` — what specifically changed?
3. Fix the root cause, not individual tests
```

---

### Deploy Command

Path: `.claude/commands/deploy.md`

```markdown
---
description: Build and deploy the application following project runbooks
allowed-tools: Read, Bash(npm run build:*), Bash(npm run deploy:*), Bash(docker build:*), Bash(sam build:*), Bash(sam deploy:*), Bash(cdk deploy:*), Glob
---

# Deploy

Build and deploy the application.

## Step 1: Pre-Deploy Checks

1. Verify working tree is clean: `git status`
2. Verify current branch (warn if not main/production)
3. Run tests to ensure nothing is broken
4. Check if a deployment runbook exists: `ls docs/runbooks/deploy-*.md`

## Step 2: Follow Runbook

If a deployment runbook exists in `docs/runbooks/`, follow its steps.

If no runbook exists, detect the deployment method:
- `Dockerfile` -> docker build and push
- `template.yaml` / `samconfig.toml` -> SAM build and deploy
- `cdk.json` -> CDK deploy
- `package.json` scripts -> npm run deploy / npm run build

## Step 3: Verify

After deployment:
- Check deployment status
- Verify health endpoint if available
- Report deployment result

## Step 4: Summary

Display:
- What was deployed and where
- Deployment method used
- Verification results
- Suggest creating a deployment runbook if none exists

## Error Recovery

### If pre-deploy checks fail (Step 1)
\```bash
git stash                         # Stash uncommitted changes
git checkout main                 # Switch to main branch
\```

### If deployment fails (Step 2/3)
Check deployment logs and retry:
- Docker: `docker logs <container>`
- SAM: `sam logs --stack-name <name>`
- CDK: check CloudFormation console for rollback details

### If a bad deployment was published — rollback
\```bash
# If using git tags for releases
git push origin ":refs/tags/v$VERSION"
git tag -d "v$VERSION"
git revert HEAD
git push origin main
\```

### If health check fails after deployment (Step 3)
- Check service logs for startup errors
- Verify environment variables are set
- Confirm database migrations ran successfully
- If unrecoverable, trigger rollback procedure above
```
