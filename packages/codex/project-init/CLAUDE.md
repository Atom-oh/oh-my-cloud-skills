# project-init Plugin

## Role
Core plugin providing project structure initialization, documentation quality scoring, and auto-sync workflows. This is the primary plugin in the marketplace.

## Key Files
- `.claude-plugin/plugin.json` - Plugin manifest (name, version, description)
- `commands/init-project.md` - Main initialization command (17 steps, adapts to detected project type)
- `commands/sync-docs.md` - Documentation synchronization
- `commands/add-adr.md` - ADR creation
- `commands/add-module.md` - Module scaffolding
- `commands/add-runbook.md` - Runbook creation
- `commands/generate-readme.md` - Bilingual README.md generation/update
- `commands/generate-changelog.md` - Bilingual CHANGELOG.md generation/update
- `commands/health-check.md` - Project validation (includes pre-v2.3 hook contract detection)
- `commands/migrate-hooks.md` - Migrate pre-v2.3 hooks, settings.json, and `.yml` agents to the stdin/exit 2 contract (with backup, `--dry-run`)
- `commands/add-reference-doc.md` - Add layer-specific implementation reference doc
- `agents/doc-sync-checker.md` - Documentation sync analysis agent
- `skills/project-scaffolder/SKILL.md` - Scaffolding skill definition
- `skills/project-scaffolder/references/` - Template files for code generation (includes shared writing-style-guide)
- `skills/project-scaffolder/references/reference-doc-template.md` - 8-layer skeleton library used by /init-project and /add-reference-doc

## Rules
- All commands must have clear step-by-step instructions
- Reference templates contain code in fenced blocks for extraction
- The init-project command adapts based on detected project type
- Version in plugin.json must be updated for each release
- Bilingual support (Korean/English) in user-facing templates
- Architecture flows in generated docs use Mermaid flowchart, not ASCII box diagrams (see references/writing-style-guide.md Diagram Rules, ADR-007)
