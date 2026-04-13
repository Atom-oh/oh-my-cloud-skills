---
description: Add a new module directory with CLAUDE.md and update architecture docs
allowed-tools: Read, Write, Edit, Bash(mkdir:*), Bash(ls:*), Bash(find:*), Glob, Grep
argument-hint: Module path (e.g. src/auth, src/notifications)
---

# Add Module

Create a new module directory with documentation and update project-level docs.

## Step 1: Validate Module Path

Target: $ARGUMENTS

- If no path provided, ask the user for the module path
- Verify the path is under a source directory (src/, app/, lib/, etc.)
- If the directory already exists, check if CLAUDE.md is missing and offer to create it

```bash
ls -la <module_path> 2>/dev/null
```

## Step 2: Understand the Module

Ask the user:
- What is this module's responsibility? (one sentence)
- What are its key dependencies or relationships with other modules?

If the user skips, infer from the directory name.

## Step 3: Create Module Directory and CLAUDE.md

```bash
mkdir -p <module_path>
```

Create `<module_path>/CLAUDE.md` with:

```markdown
# <Module Name> Module

## Role
<module responsibility from user input>

## Key Files
<!-- Key files will be added as the module grows -->

## Dependencies
<relationships with other modules>

## Rules
<!-- Module-specific conventions -->
```

## Step 4: Update docs/architecture.md

Read `docs/architecture.md` and add the new module to the Components section.

If a Data Flow section exists, suggest where the new module fits.

## Step 5: Update Root CLAUDE.md

Read the root `CLAUDE.md` and update the Project Structure section to include the new module.

## Step 6: Verify Hook Coverage

Read `.claude/hooks/check-doc-sync.sh` and verify the hook monitors the correct source directory path. If the new module is under a directory not covered by the hook, suggest updating it.

## Step 7: Summary

Display:
- Created directory and CLAUDE.md
- Updated architecture.md
- Updated root CLAUDE.md
- Any suggested follow-up actions (e.g. create an ADR if this is a significant architectural addition)
