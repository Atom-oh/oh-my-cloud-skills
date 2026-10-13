---
description: Create a new operational runbook from template in docs/runbooks/
allowed-tools: Read, Write, Edit, Bash(mkdir:*), Bash(ls:*), Bash(find:*), Glob, Grep
argument-hint: Runbook name (e.g. deploy-production, database-migration, incident-response)
---

# Add Runbook

Create a new operational runbook with structured steps and update project-level docs.

## Step 1: Determine Runbook Name

Target: $ARGUMENTS

- If no name provided, ask the user for the runbook name
- Convert to kebab-case for the filename (e.g. "Deploy Production" -> `deploy-production.md`)
- Check if `docs/runbooks/` directory exists; create it if missing
- Check if the runbook already exists; if so, offer to update it instead

```bash
ls docs/runbooks/ 2>/dev/null
```

## Step 2: Gather Runbook Details

Ask the user:

1. **Purpose**: What operational task does this runbook cover? (one sentence)
2. **When to use**: Under what circumstances should someone follow this runbook?
3. **Prerequisites**: What tools, permissions, or access are needed?
4. **Procedure**: What are the high-level steps? (Claude will expand these)
5. **Rollback**: Is there a recovery procedure if something goes wrong?

If the user provides minimal input, infer from the runbook name and project context:
- Read `CLAUDE.md` for tech stack and deployment info
- Read `docs/architecture.md` for system components
- Infer appropriate steps based on the runbook topic

## Step 3: Read Templates and Style Guide

Read the shared writing style guide and runbook template:

```
Read file: skills/project-scaffolder/references/writing-style-guide.md
Read file: skills/project-scaffolder/references/docs-templates.md
```

Follow all bilingual structure, formatting, and style rules from the writing style guide.
Use the Runbook Template section as the base structure.

## Step 4: Create Bilingual Runbook

Create `docs/runbooks/<runbook-name>.md` with bilingual (English/Korean) structure:

```markdown
# Runbook: <Title>

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

## Overview
<purpose from user input or inferred from context>

## When to Use
<circumstances that trigger this runbook>

## Prerequisites
- <required permissions>
- <required tools>
- <required access>

## Procedure

### 1. <First Phase>
<detailed steps with copy-paste ready commands>

### 2. <Second Phase>
<detailed steps with copy-paste ready commands>

### 3. <Third Phase>
<detailed steps with copy-paste ready commands>

## Verification
- [ ] <check 1>
- [ ] <check 2>

## Rollback
1. <rollback step 1>
2. <rollback step 2>

## Notes
- Last verified: <today's date>
- Author: <user or inferred>

---

<a id="korean"></a>

# 한국어

## 개요
<사용자 입력 또는 컨텍스트에서 유추한 목적>

## 사용 시점
<이 런북을 따라야 하는 상황>

## 사전 요구 사항
- <필요한 권한>
- <필요한 도구>
- <필요한 접근 권한>

## 절차

### 1. <첫 번째 단계>
<복사-붙여넣기 가능한 명령어와 상세 단계>

### 2. <두 번째 단계>
<복사-붙여넣기 가능한 명령어와 상세 단계>

### 3. <세 번째 단계>
<복사-붙여넣기 가능한 명령어와 상세 단계>

## 검증
- [ ] <확인 1>
- [ ] <확인 2>

## 롤백
1. <롤백 단계 1>
2. <롤백 단계 2>

## 참고
- 최종 검증일: <오늘 날짜>
- 작성자: <사용자 또는 유추>
```

Key principles:
- Every command must be **copy-paste ready** (no placeholder paths without explanation)
- Include **verification steps** after each major phase
- Rollback section must be actionable, not vague
- Use code blocks with language tags for all commands
- Both language sections must contain identical information
- English uses imperative mood; Korean uses 경어체 (~합니다)
- No emojis; code blocks must specify the language
- Code blocks and commands are identical in both sections; only descriptive text is translated

## Step 5: Update Root CLAUDE.md

Read the root `CLAUDE.md`. If a Runbooks section exists, add the new runbook. If not, suggest adding one.

## Step 6: Update docs/architecture.md

If the runbook relates to a specific component (e.g. deployment, database), check if `docs/architecture.md` references operational procedures. If an Infrastructure or Operations section exists, add a cross-reference.

## Step 7: Validate Bilingual Output

After writing the runbook, verify:

- [ ] Language toggle uses HTML `<a><img></a>` with `#english` and `#korean` anchors
- [ ] Explicit `<a id="english">` and `<a id="korean">` tags before each language heading
- [ ] Both language sections have identical structure and information
- [ ] All commands and code blocks are identical in both sections
- [ ] No emojis in the document
- [ ] Code blocks specify the language

## Step 8: Summary

Display:
- Created runbook file path and name
- Overview of sections included
- Suggested follow-up actions:
  - Create related runbooks (e.g. if deploy-production was created, suggest rollback-production)
  - Link the runbook from relevant module CLAUDE.md files
  - Schedule periodic review of the runbook
