---
name: project-scaffolder
description: Understand and apply Claude Code project structure patterns. Use when user asks about project organization, wants to add new modules, or needs guidance on where to place files in a Claude Code project.
tools: Read, Glob
user-invocable: false
---

# Project Scaffolder

Knowledge skill for Claude Code project structure patterns and conventions.

## Project Structure Pattern

A well-organized Claude Code project follows this structure:

```
project-root/
├── CLAUDE.md                      # Project memory and instructions for Claude
├── README.md                      # Project documentation
├── .gitignore
├── .env.example                   # Environment variable template (no real secrets)
├── .editorconfig                  # Editor formatting rules
├── .mcp.json                      # MCP server configuration
├── docs/
│   ├── architecture.md            # System architecture document
│   ├── onboarding.md              # New developer onboarding guide
│   ├── api-reference.md           # API documentation (if applicable)
│   ├── decisions/                 # Architecture Decision Records (ADRs)
│   │   └── .template.md
│   └── runbooks/                  # Operational runbooks
│       └── .template.md
├── .claude/
│   ├── settings.json              # Permissions and hooks configuration
│   ├── hooks/
│   │   ├── check-doc-sync.sh     # PostToolUse: Documentation sync detection
│   │   ├── secret-scan.sh        # PreToolUse: Secret detection gate
│   │   ├── session-context.sh    # SessionStart: Load project context
│   │   └── notify.sh             # Notification: Webhook alerts
│   ├── commands/
│   │   ├── review.md             # /review: Code review on diff
│   │   ├── test-all.md           # /test-all: Execute full test suite
│   │   └── deploy.md             # /deploy: Build and deploy
│   ├── skills/
│   │   ├── code-review/SKILL.md  # Confidence-based code review
│   │   ├── refactor/SKILL.md     # Safe refactoring with verification
│   │   ├── release/SKILL.md      # Semver release automation
│   │   └── sync-docs/SKILL.md    # Documentation sync with quality scoring
│   └── agents/
│       ├── code-reviewer.yml     # Parallel code review agent
│       └── security-auditor.yml  # Security audit agent
├── scripts/
│   ├── setup.sh                  # Project setup for new developers
│   └── install-hooks.sh          # Git hooks installer
└── src/
    ├── api/
    │   └── CLAUDE.md              # API module context
    └── persistence/
        └── CLAUDE.md              # Persistence module context
```

## Key Principles

### CLAUDE.md Hierarchy
- **Root CLAUDE.md**: Project-wide context (overview, tech stack, conventions, commands)
- **Module CLAUDE.md**: Module-specific context (role, key files, rules)
- Keep each CLAUDE.md concise and under 500 lines - it's part of the prompt context

### Auto-Sync Mechanisms
1. **CLAUDE.md Auto-Sync Rules**: Embedded in root CLAUDE.md, triggered after Plan mode
2. **PostToolUse Hook** (check-doc-sync.sh): Detects missing module docs after Write/Edit
3. **PreToolUse Hook** (secret-scan.sh): Scans for secrets before shell commands
4. **SessionStart Hook** (session-context.sh): Loads project context at session start
5. **Notification Hook** (notify.sh): Sends webhook alerts on events
6. **Sync-docs Skill**: Manual full documentation synchronization
7. **Git commit-msg Hook**: Auto-removes Co-Authored-By lines (AI contributor exclusion)

### Extension Types
| Type | Location | Purpose |
|------|----------|---------|
| Skills | `.claude/skills/` | Auto-activate on task match (AI-driven) |
| Commands | `.claude/commands/` | User-invocable slash commands |
| Hooks | `.claude/hooks/` | Deterministic lifecycle event scripts |
| Agents | `.claude/agents/` | Isolated parallel work (subagents) |
| MCP | `.mcp.json` | External tool connections |

### When to Create New Module CLAUDE.md
- Any new directory under the source root (src/, app/, lib/, etc.) should have a `CLAUDE.md`
- Use `/add-module <path>` to create directory + CLAUDE.md + update architecture docs in one step
- Document: module role, key files, dependencies, and module-specific rules

### When to Create ADRs
- New technology/dependency added
- API design decisions
- Database schema changes
- Infrastructure changes
- Any decision with trade-offs worth recording
- Use `/add-adr <title>` for auto-numbered creation

### When to Create Runbooks
- Deployment procedures exist
- Database migration steps are needed
- Incident response plans are required
- Environment setup is non-trivial
- Use `/add-runbook <name>` for template-based creation

### CLAUDE.md Quality Criteria

When evaluating or creating CLAUDE.md files, target these scores (total 100):

| Criterion | Max | What to check |
|-----------|-----|---------------|
| Commands/workflows | 20 | Build/test/deploy commands present and copy-paste ready? |
| Architecture clarity | 20 | Codebase structure understandable from this file alone? |
| Non-obvious patterns | 15 | Gotchas, quirks, and conventions documented? |
| Conciseness | 15 | No verbose explanations or obvious info? |
| Currency | 15 | Reflects current codebase state? |
| Actionability | 15 | Instructions are executable, not vague? |

Grades: A (90-100), B (70-89), C (50-69), D (30-49), F (0-29)

### CLAUDE.md Anti-Patterns

| Anti-Pattern | Impact | Detection |
|-------------|--------|-----------|
| Over 500 lines | Context bloat | `wc -l` |
| Vague instructions ("write good code") | Useless guidance | Grep for vague phrases |
| Duplicated docs (copy of README) | Wasted context | Compare with README |
| No test guidance | Skipped tests | Missing test commands/patterns |
| No error patterns | Inconsistent handling | Missing error handling section |
| Contains secrets | Security risk | Grep for key patterns |

### Security Best Practices
- Secrets: Never store in CLAUDE.md or committed files
- `.env.example`: Use for environment variable templates (no real values)
- `settings.local.json`: Add to `.gitignore` for local overrides
- PreToolUse hook: Enable secret scanning by default
- MCP scope: Configure with minimum permissions only

### Existing Project Adaptation

When applying this structure to existing projects:
- Detect language/framework from dependency files (package.json, pyproject.toml, go.mod, etc.)
- Use existing source directories instead of creating src/api/ and src/persistence/
- Auto-fill Tech Stack, Commands, and Conventions from detected build system
- Create module CLAUDE.md for each existing source directory

## Reference Files

For detailed templates, see:
- [references/claude-md-template.md](references/claude-md-template.md) - CLAUDE.md template
- [references/settings-json-template.md](references/settings-json-template.md) - settings.json with all hooks
- [references/hook-scripts.md](references/hook-scripts.md) - Hook script implementations (5 hooks)
- [references/skills-templates.md](references/skills-templates.md) - Skills and slash command templates
- [references/agents-templates.md](references/agents-templates.md) - Agent definitions (code-reviewer, security-auditor)
- [references/docs-templates.md](references/docs-templates.md) - Architecture, ADR, Runbook, Onboarding, API Reference, .env templates
- [references/mcp-json-template.md](references/mcp-json-template.md) - MCP server configuration template
- [references/scripts-templates.md](references/scripts-templates.md) - Setup, deploy, seed-db, install-hooks scripts
- [references/tests-templates.md](references/tests-templates.md) - Test framework and harness validation templates
- [references/readme-template.md](references/readme-template.md) - Bilingual README.md generation rules and section structure
- [references/changelog-template.md](references/changelog-template.md) - Bilingual CHANGELOG.md generation rules following Keep a Changelog
