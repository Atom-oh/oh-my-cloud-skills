---
description: Validate entire project setup - files, hooks, permissions, CLAUDE.md quality, and configuration
allowed-tools: Read, Glob, Grep, Bash(find:*), Bash(ls:*), Bash(git log:*), Bash(wc:*), Bash(bash -n:*), Bash(python3 -m json.tool:*)
---

# Health Check

Validate the entire Claude Code project setup and report issues.

## Step 1: Check Core Files

Verify required files exist:

```bash
ls CLAUDE.md README.md .gitignore LICENSE 2>/dev/null
ls .claude/settings.json 2>/dev/null
ls docs/architecture.md 2>/dev/null
```

Score:
- CLAUDE.md exists: +20
- .claude/settings.json exists: +10
- docs/architecture.md exists: +10
- README.md exists: +5
- .gitignore exists: +5
- LICENSE exists: +5

## Step 2: Check Hook Configuration

Verify hooks are properly configured:

```bash
ls .claude/hooks/*.sh 2>/dev/null
ls .git/hooks/commit-msg 2>/dev/null
```

Check `.claude/settings.json` has hook registrations:
- PostToolUse hook for doc-sync: +10
- PreToolUse hook for secret scanning: +10
- SessionStart hook: +5
- commit-msg Git hook (Claude exclusion): +10

Verify hooks are executable:
```bash
find .claude/hooks -name '*.sh' ! -perm -u+x 2>/dev/null
```

## Step 3: Check Skills

```bash
find .claude/skills -name 'SKILL.md' 2>/dev/null
```

- code-review skill: +5
- refactor skill: +5
- release skill: +5
- sync-docs skill: +5

## Step 4: Check Documentation Coverage

Count module CLAUDE.md files:

```bash
find src/ app/ lib/ cmd/ -name 'CLAUDE.md' 2>/dev/null
```

Count source directories without CLAUDE.md:

```bash
find src/ app/ lib/ cmd/ -type d -mindepth 1 2>/dev/null
```

- All modules have CLAUDE.md: +10
- docs/decisions/ has at least one ADR: +5
- docs/runbooks/ has at least one runbook: +5

## Step 5: Check Security

- `.env` is in `.gitignore`: +5
- `.env.example` exists (if project uses env vars): +5
- No secrets detected in CLAUDE.md or committed files: +10
- `.mcp.json` does not contain real tokens: +5

## Step 6: Check CLAUDE.md Quality

Run a quick quality assessment on root CLAUDE.md:
- Under 500 lines: +5
- Has Tech Stack section: +5
- Has Key Commands section: +5
- Has Project Structure section: +5
- Commands are copy-paste ready: +5
- No vague instructions detected: +5

## Step 7: Check Tests Structure

```bash
ls -d tests/ test/ spec/ __tests__/ 2>/dev/null
```

- Test directory exists: +5
- Test CLAUDE.md exists: +5

## Step 8: Report

Present a comprehensive health report:

```
## Project Health Report

### Score: XX/200

### Status: HEALTHY | NEEDS ATTENTION | CRITICAL

### Core Files
| File | Status |
|------|--------|
| CLAUDE.md | OK / MISSING |
| .claude/settings.json | OK / MISSING |
| docs/architecture.md | OK / MISSING |
| .gitignore | OK / MISSING |

### Hooks
| Hook | Type | Status |
|------|------|--------|
| check-doc-sync.sh | PostToolUse | OK / MISSING / NOT EXECUTABLE |
| secret-scan.sh | PreToolUse | OK / MISSING |
| session-context.sh | SessionStart | OK / MISSING |
| commit-msg | Git Hook | OK / MISSING |

### Skills: X/4 installed
### Documentation: X/Y modules covered
### Security: PASS / X issues found
### CLAUDE.md Quality: XX/100 (Grade: X)

### Recommended Actions
1. [action 1]
2. [action 2]
```

### Health Grades

| Score | Grade | Status |
|-------|-------|--------|
| 160-200 | A | HEALTHY - Project is well configured |
| 120-159 | B | GOOD - Minor improvements recommended |
| 80-119 | C | NEEDS ATTENTION - Several gaps to address |
| 40-79 | D | POOR - Significant setup issues |
| 0-39 | F | CRITICAL - Project needs initialization |
