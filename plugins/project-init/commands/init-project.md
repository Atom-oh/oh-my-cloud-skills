---
description: Initialize a Claude Code project structure with CLAUDE.md, docs, hooks, skills, agents, and MCP config. Adapts to existing projects by detecting language/framework.
allowed-tools: Read, Write, Edit, Bash(mkdir:*), Bash(chmod:*), Bash(git init:*), Bash(git add:*), Bash(git commit:*), Bash(git remote:*), Bash(git log:*), Bash(git tag:*), Bash(git describe:*), Bash(git diff:*), Bash(ls:*), Bash(find:*), Bash(bash scripts/*), Glob, Grep
argument-hint: Optional project directory path (defaults to current directory)
---

# Initialize Claude Code Project Structure

Set up a complete Claude Code project structure in the target directory. Adapts to existing projects by detecting language, framework, and directory layout.

## Step 1: Determine Target Directory

Target: $ARGUMENTS

- If a path is provided, use it as the project root
- If empty, use the current working directory
- If the directory doesn't exist, create it

```bash
ls -la <target_dir> 2>/dev/null
```

## Step 2: Detect Existing Project

Scan for existing project files to determine if this is a new or existing project:

```bash
# Detect language/framework
ls package.json pyproject.toml go.mod Cargo.toml pom.xml build.gradle Gemfile composer.json 2>/dev/null

# Detect existing source directories
ls -d src/ app/ lib/ cmd/ pkg/ internal/ components/ pages/ routes/ 2>/dev/null

# Check dependency files for framework detection
cat package.json 2>/dev/null | head -30
cat pyproject.toml 2>/dev/null | head -30
```

**If existing project detected:**
- Do NOT create `src/api/` or `src/persistence/` if they don't match the project
- Instead, identify the actual source directories and create module `CLAUDE.md` files for each
- Adapt Tech Stack, Commands, and Conventions based on detected framework
- Warn the user before overwriting any existing files

**Project type detection rules:**

| File Found | Project Type | Source Dirs | Key Commands |
|-----------|-------------|-------------|--------------|
| `package.json` | Node.js | src/, app/, lib/, components/ | npm/yarn/pnpm |
| `pyproject.toml` / `requirements.txt` | Python | src/, app/, lib/ | pip, pytest, ruff |
| `go.mod` | Go | cmd/, pkg/, internal/ | go build, go test |
| `Cargo.toml` | Rust | src/ | cargo build, cargo test |
| `pom.xml` / `build.gradle` | Java/Kotlin | src/main/, src/test/ | mvn, gradle |
| None detected | New project | src/api/, src/persistence/ | (ask user) |

**If new project (no existing files):**
- Ask the user for project name, description, tech stack
- Create the default `src/api/` and `src/persistence/` structure

## Step 3: Create Directory Structure

Create directories based on detection results:

**Always create:**
```bash
mkdir -p docs/decisions
mkdir -p docs/runbooks
mkdir -p .claude/hooks
mkdir -p .claude/skills/code-review
mkdir -p .claude/skills/refactor
mkdir -p .claude/skills/release
mkdir -p .claude/skills/sync-docs
mkdir -p .claude/commands
mkdir -p .claude/agents
mkdir -p scripts
mkdir -p tools/prompts
```

**For new projects only** (no existing source detected):
```bash
mkdir -p src/api
mkdir -p src/persistence
mkdir -p tests/unit
mkdir -p tests/integration
```

## Step 4: Generate CLAUDE.md

Read the template from [references/claude-md-template.md](../skills/project-scaffolder/references/claude-md-template.md).

**For existing projects:**
- Auto-fill Tech Stack from detected dependency files
- Auto-fill Project Structure from actual directory layout
- Auto-fill Key Commands from detected build system (package.json scripts, Makefile targets, etc.)
- Auto-fill Conventions from observed code patterns (linter configs, .editorconfig, etc.)

**For new projects:**
- Ask the user for project name, description, tech stack
- Fill in the template with user responses

Always include Auto-Sync Rules section.

## Step 5: Generate .claude/settings.json and All Hooks

Read [references/settings-json-template.md](../skills/project-scaffolder/references/settings-json-template.md) and create `.claude/settings.json` with all hook registrations (SessionStart, PreToolUse, PostToolUse, Notification).

Read [references/hook-scripts.md](../skills/project-scaffolder/references/hook-scripts.md) and create:
- `.claude/hooks/check-doc-sync.sh` - PostToolUse documentation sync
- `.claude/hooks/secret-scan.sh` - PreToolUse secret scanning
- `.claude/hooks/session-context.sh` - SessionStart context loading
- `.claude/hooks/notify.sh` - Notification webhook

Make all hooks executable:

```bash
chmod +x .claude/hooks/*.sh
```

**For existing projects**: Adapt `check-doc-sync.sh` to use the actual source directory path instead of hardcoded `src/`.

## Step 6: Generate Skills

Read [references/skills-templates.md](../skills/project-scaffolder/references/skills-templates.md) and create:
- `.claude/skills/code-review/SKILL.md`
- `.claude/skills/refactor/SKILL.md`
- `.claude/skills/release/SKILL.md`
- `.claude/skills/sync-docs/SKILL.md`

## Step 7: Generate Slash Commands

Read [references/skills-templates.md](../skills/project-scaffolder/references/skills-templates.md) (Common Slash Command Templates section) and create:
- `.claude/commands/review.md` - Code review on diff
- `.claude/commands/test-all.md` - Execute full test suite
- `.claude/commands/deploy.md` - Build and deploy

**For existing projects**: Adapt test and deploy commands to match the detected framework.

## Step 8: Generate Agents

Read [references/agents-templates.md](../skills/project-scaffolder/references/agents-templates.md) and create:
- `.claude/agents/code-reviewer.yml` - Parallel code review agent
- `.claude/agents/security-auditor.yml` - Security audit agent

## Step 9: Generate Docs

Read [references/docs-templates.md](../skills/project-scaffolder/references/docs-templates.md) and create:

### architecture.md (Production-Grade)

Generate `docs/architecture.md` following the Architecture Document template with:

1. **Language Switcher**: shields.io badge line with `[![English](...)]` and `[![Korean](...)]` linking to `#english` and `#한국어`. English section first, Korean section second.
2. **System Overview**: 2-3 sentence summary of the project architecture
3. **Components by Layer**: Group into Ingestion/Storage/Processing/Query/Presentation/Observability/Security layers. Only include layers that apply.
   - **For existing projects**: Read source directories, IaC files (terraform/, cdk/), Dockerfiles, and dependency files to auto-detect components
   - **For new projects**: Use user input from Plan mode or interactive questions
4. **Full Architecture Diagram**: ASCII box diagram using `┌─┐│└─┘▶▼` characters showing all components and data flow
5. **Data Flow Summary**: One-line arrow chain showing the critical path
6. **Infrastructure Tables**: If IaC files (terraform/, cdk/, cloudformation/) are detected, list modules/constructs in a table
7. **Key Design Decisions**: List architectural choices with WHY explanations (from Plan mode context if available)
8. **Operations**: Cross-reference to runbooks in `docs/runbooks/`

Both Korean and English sections must have identical structure and content.

### Other Docs

- `docs/decisions/.template.md` - ADR template
- `docs/runbooks/.template.md` - Runbook template
- `docs/onboarding.md` - For existing projects, pre-fill prerequisites and setup steps from detected build system
- `docs/api-reference.md` - Only if project has API endpoints (detected from routes, handlers, controllers)

## Step 10: Generate Module CLAUDE.md Files

**For new projects:**
- `src/api/CLAUDE.md`
- `src/persistence/CLAUDE.md`
- `tests/unit/CLAUDE.md`
- `tests/integration/CLAUDE.md`

**For existing projects:**
- Scan all top-level source directories
- Create `CLAUDE.md` for each directory that doesn't have one
- Auto-fill module role based on directory name and contained files
- If `tests/` directory exists, create `tests/CLAUDE.md`

## Step 11: Generate MCP Configuration

Read [references/mcp-json-template.md](../skills/project-scaffolder/references/mcp-json-template.md).

Create `.mcp.json` with an empty configuration:

```json
{
  "mcpServers": {}
}
```

If project context suggests MCP integrations (e.g., GitHub remote exists, database config found), add commented example configurations.

## Step 12: Generate README.md (Bilingual)

Read [references/writing-style-guide.md](../skills/project-scaffolder/references/writing-style-guide.md) for shared bilingual and style rules.
Read [references/readme-template.md](../skills/project-scaffolder/references/readme-template.md) for structure and generation rules.

If `README.md` already exists, read it to preserve user-specific content.

**Auto-detect** from information gathered in Step 2:
- Project name, description, version, license from manifest files
- GitHub URL from `git remote get-url origin`
- Tech stack from detected language/framework
- Test commands from detected build system
- Prerequisites from runtime version requirements

**Ask the user** only for fields that cannot be auto-detected:
- One-line description in Korean (if not available)
- Maintainer name and GitHub username
- Demo image/GIF path (optional)

Generate `README.md` with bilingual (English/Korean) structure:
1. Top layout: project name (h1), shields.io badges (license, version, language toggle), bilingual one-line description
2. `# English` section with all applicable sections (Overview, Features, Prerequisites, Installation, Usage, Project Structure, Testing, Contributing, License, Contact)
3. `# 한국어` section with identical structure in Korean
4. No emojis, code blocks with language tags, 경어체 for Korean, imperative for English

## Step 13: Generate CHANGELOG.md (Bilingual)

Read [references/writing-style-guide.md](../skills/project-scaffolder/references/writing-style-guide.md) for shared bilingual and style rules.
Read [references/changelog-template.md](../skills/project-scaffolder/references/changelog-template.md) for structure and generation rules.

If `CHANGELOG.md` already exists, preserve all existing entries.

**Analyze git history:**
```bash
git tag --sort=-v:refname 2>/dev/null
git log --oneline -30 2>/dev/null
```

Generate `CHANGELOG.md` with bilingual (English/Korean) structure:
1. Title: `# Changelog` with language toggle badges
2. `# English` section: introductory statement, `[Unreleased]`, version sections (newest first), reference links
3. `# 한국어` section: identical structure with Korean descriptions
4. Categorize changes under standard headings (Added, Changed, Deprecated, Removed, Fixed, Security)
5. Category headings stay in English in both sections (Keep a Changelog convention)
6. English entries use imperative verbs, Korean entries use 명사형 종결

If this is a new project with no tags or history, create the template with an empty `[Unreleased]` section.

## Step 14: Generate Other Supporting Files

Create (only if they don't already exist):
- `.gitignore` with patterns appropriate for the detected language (include `.env`, `settings.local.json`)
- `.env.example` from [references/docs-templates.md](../skills/project-scaffolder/references/docs-templates.md) - adapted to project type
- `.editorconfig` with sensible defaults

Read [references/scripts-templates.md](../skills/project-scaffolder/references/scripts-templates.md) and create:
- `scripts/setup.sh` - Project setup for new developers
- `scripts/install-hooks.sh` - Git hooks installer

Make scripts executable:

```bash
chmod +x scripts/*.sh
```

## Step 15: Initialize Git (Optional)

If `.git/` doesn't already exist, ask the user if they want to initialize:

```bash
git init
```

Install Git hooks via the installer script:

```bash
bash scripts/install-hooks.sh
```

This installs the `commit-msg` hook that removes all Co-Authored-By lines from commit messages, preventing Claude and other AI assistants from appearing as contributors.

Then stage and create initial commit:

```bash
git add -A
git commit -m "Initial project structure for Claude Code"
```

## Step 16: Generate Test Framework

Read [references/tests-templates.md](../skills/project-scaffolder/references/tests-templates.md) and create:

```bash
mkdir -p tests/hooks tests/structure tests/fixtures
```

- `tests/run-all.sh` - Test runner with TAP-style output and assertion functions
- `tests/hooks/test-hooks.sh` - Hook existence, permissions, registration, behavior
- `tests/hooks/test-secret-patterns.sh` - Secret pattern true positive / false positive tests
- `tests/structure/test-plugin-structure.sh` - Manifest validation, version sync, file existence
- `tests/fixtures/secret-samples.txt` - True positive samples
- `tests/fixtures/false-positives.txt` - False positive samples

**For existing projects**: Adapt structure tests to validate the actual project's files, manifests, and CLAUDE.md sections.

Make test runner executable:

```bash
chmod +x tests/run-all.sh tests/hooks/*.sh tests/structure/*.sh
```

## Step 17: Summary

Display the created structure and explain the auto-sync mechanisms:

1. **CLAUDE.md Auto-Sync Rules** - Plan mode exit triggers doc updates
2. **Hook (check-doc-sync.sh)** - Write/Edit triggers missing doc detection (with parent-dir walking)
3. **Hook (secret-scan.sh)** - PreToolUse blocks commits containing secrets
4. **Hook (session-context.sh)** - Session start loads project context
5. **Hook (commit-msg)** - Auto-removes Co-Authored-By lines (AI contributor exclusion)
6. **Skill (/sync-docs)** - Manual full documentation sync with quality scoring
7. **Commands (/review, /test-all, /deploy)** - Common development workflows with error recovery
8. **Agents (code-reviewer, security-auditor)** - Parallel analysis agents with structured output schemas
9. **README.md** - Bilingual (EN/KR) project documentation with shields.io badges
10. **CHANGELOG.md** - Bilingual (EN/KR) change log following Keep a Changelog convention
11. **Test Suite (tests/run-all.sh)** - Automated harness validation
12. **Deny List (settings.json)** - Dangerous commands explicitly blocked

If existing project was detected, highlight what was adapted vs created fresh.
