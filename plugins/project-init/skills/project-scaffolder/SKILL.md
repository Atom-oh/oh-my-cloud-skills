---
name: project-scaffolder
description: Claude Code project structure for projects set up by project-init - the generated layout and its tiers, where a new module, doc, hook, or command belongs, the CLAUDE.md quality rubric and anti-patterns, and the module CLAUDE.md coverage rule. Use when the user asks how the project is organized, where something should go, or how a CLAUDE.md is scored.
user-invocable: false
---

# Project Scaffolder

`/init-project` generates the layout below from the templates in `references/`. `## CLAUDE.md Quality Criteria`, `## CLAUDE.md Anti-Patterns`, and `## Module CLAUDE.md Coverage` are the single source that `/sync-docs`, `/health-check`, and the doc-sync-checker agent cite by heading.

## Project Structure Pattern

`/init-project` generates by tier:
- **Core**: always generated.
- **Default**: generated unless the user unchecks it.
- **Optional**: generated only when the user checks it.

The Artifacts table in `${CLAUDE_PLUGIN_ROOT}/commands/init-project.md` maps every file to its template, tier, and adapt points.

```text
project-root/
├── CLAUDE.md                      # Core
├── README.md                      # Core: bilingual
├── CHANGELOG.md                   # Core: bilingual, Keep a Changelog
├── .gitignore                     # Core
├── .editorconfig                  # Core
├── .env.example                   # Core: variable names, no real values
├── .mcp.json                      # Core: {"mcpServers": {}}
├── docs/
│   ├── architecture.md            # Core: bilingual, Mermaid diagrams
│   ├── onboarding.md              # Core
│   ├── api-reference.md           # Core, only when an API is detected
│   ├── decisions/.template.md     # Core: ADR template
│   ├── runbooks/.template.md      # Core: runbook template
│   └── reference/                 # Core: one file per selected implementation layer, plus INDEX.md
├── .claude/
│   ├── settings.json              # Core: deny list and hook registrations
│   ├── hooks/
│   │   ├── secret-scan.sh         # Core: PreToolUse gate on git commit
│   │   ├── check-doc-sync.sh      # Core: PostToolUse module CLAUDE.md reminder
│   │   ├── session-context.sh     # Optional: SessionStart local-environment facts
│   │   ├── notify.sh              # Optional: Notification webhook
│   │   └── verify-on-stop.sh      # Optional: Stop gate that runs the fast check
│   ├── commands/
│   │   ├── test-all.md            # Default: runs the detected test command
│   │   ├── review.md              # Default: the review path, with code-reviewer
│   │   └── deploy.md              # Optional: runbook-driven, user-invoked only
│   ├── agents/
│   │   ├── code-reviewer.md       # Default: used by /review
│   │   └── security-auditor.md    # Optional
│   └── skills/                    # Optional: code-review, refactor, release
├── scripts/
│   ├── setup.sh                   # Core
│   └── install-hooks.sh           # Core: installs the git commit-msg hook
├── tests/                         # Core: run-all.sh, hooks/, structure/, fixtures/
└── <source root>/<module>/CLAUDE.md   # Core, only for modules with rules the code does not show
```

## How the Pieces Fit

Place a new piece by what it needs: a command or skill for a workflow Claude or the user starts (a skill when it carries supporting files, and `disable-model-invocation: true` when only the user may start it), an agent for isolated work in its own context, a hook for what must happen on every matching event whatever the model decides, and `.mcp.json` for external tools.

- The **Auto-Sync Rules** in the root CLAUDE.md are guidance Claude applies while working; nothing runs them automatically.
- `secret-scan.sh` blocks, with exit 2, a `git commit` whose files match a secret pattern; every other command passes silently.
- `check-doc-sync.sh` reminds Claude when an edited file's directory has no covering module CLAUDE.md.
- The commit-msg hook from `scripts/install-hooks.sh` removes Co-Authored-By lines.
- `/project-init:sync-docs` audits the docs once (inline for a small project, otherwise through the doc-sync-checker agent) and applies the findings.

## When to Create ADRs and Runbooks

- **ADR** (`/add-adr <title>`): a choice that would be expensive to reverse, or one a future reader would ask about (a new core dependency, an API or schema design, an infrastructure change). Routine implementation choices do not need one.
- **Runbook** (`/add-runbook <name>`): a procedure someone will repeat under pressure or get wrong from memory (deploy, rollback, database migration, incident response, non-trivial environment setup).

## Module CLAUDE.md Coverage

The source roots are the `SOURCE_ROOTS` in the project's `.claude/hooks/check-doc-sync.sh`, which `/init-project` sets to the detected layout. When that hook or its `SOURCE_ROOTS=` line is missing, they are those of `src app lib cmd pkg internal packages` that exist.

- A directory below a source root is covered when it, or an ancestor at or below the source root, has a `CLAUDE.md`; this is the rule `check-doc-sync.sh` enforces. A source root's own `CLAUDE.md` (such as `src/CLAUDE.md`) counts. Files directly in a source root need none.
- Report uncovered first-level module directories. Coverage is a report, not a quota: `/health-check` deducts no points for it.
- A first-level module gets its own CLAUDE.md only for rules, invariants, or gotchas the code does not show; a deeper directory only for conventions, invariants, or gotchas its ancestor's CLAUDE.md does not cover.
- For a rule about a file type across directories (every `*.test.ts`), use `.claude/rules/<topic>.md` with `paths:` frontmatter instead, because a module CLAUDE.md loads only when Claude reads files in its directory.

## CLAUDE.md Quality Criteria

Score each CLAUDE.md out of 100 on these six criteria, then subtract the `## CLAUDE.md Anti-Patterns` deductions (floor 0):

| Criterion | Max | What to check |
|-----------|-----|---------------|
| Commands/workflows | 20 | Build, test, and deploy commands, including a way to verify a change, are present and copy-paste ready |
| Architecture clarity | 20 | States what the code does not make obvious: boundaries, entry points, locations the names do not reveal |
| Non-obvious patterns | 15 | Gotchas, quirks, and non-default conventions, each with its reason |
| Conciseness | 15 | Every line passes the prune test; nothing Claude can read from the code or config |
| Currency | 15 | Matches the current code, commands, and dependencies |
| Actionability | 15 | Instructions are concrete and executable, not vague |

Grades: A (90-100), B (70-89), C (50-69), D (30-49), F (0-29)

Line count is information only, not a deduction.

## CLAUDE.md Anti-Patterns

| Anti-Pattern | Deduction | How to detect |
|-------------|-----------|---------------|
| Restates what code or config shows: file-by-file listings, standard conventions, dependency lists copied from manifests | -10 | Compare with the manifest and the directory listing |
| Volatile specifics: hardcoded counts, versions, dates | -10 | Numbers next to "tests", "files", "steps", or "commands"; version strings; dates |
| Emphasis inflation (MUST, NEVER, CRITICAL on many lines) or rules without a reason | -5 | Grep below, then read whether the rules carry reasons |
| Thinking or verification scaffolding ("think step by step", "double-check everything") | -5 | Grep below |
| Vague instructions ("write good code", "follow best practices") | -10 | Grep below |
| Contains secrets | -20 | Grep below |
| Stale dependencies or commands | -10 | Check commands and dependencies against the manifest |
| A section fails the prune test ("Would removing this cause Claude to make mistakes?") | -5 each, max -15 | Judgment, per section |

Grep starting points (a hit is a lead to read, not a deduction by itself):

```bash
grep -cE '\b(MUST|NEVER|ALWAYS|CRITICAL|IMPORTANT)\b' CLAUDE.md    # emphasis inflation
grep -inE 'step by step|double-check|think (carefully|hard)' CLAUDE.md   # scaffolding
grep -inE 'best practice|clean code|good code' CLAUDE.md             # vague instructions
grep -nE 'AKIA[0-9A-Z]{16}|sk-(ant|proj|svcacct|admin)-[A-Za-z0-9_-]{40,}|sk-[A-Za-z0-9]{32,}|gh[pousr]_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{40,}|xox[bp]-[0-9]+-|[sr]k_live_[A-Za-z0-9]{24,}|AIza[A-Za-z0-9_-]{35}|-----BEGIN ([A-Z]+ )?PRIVATE KEY( BLOCK)?-----' CLAUDE.md   # secret-shaped tokens
grep -inE '(password|passwd|secret|api[_-]?key)[a-z_]*.?[[:space:]]*[:=]' CLAUDE.md   # credential assignments, including JSON keys
```

For the secrets deduction, a credential assignment counts only when its value is a literal: a placeholder (`${VAR}`, `{{...}}`, `<...>`, `%(name)s`) or an environment reference (`process.env.X`, `os.environ[...]`, `$VAR`) is not a secret. Report the file, line, and pattern, never the matched value.

## Reference Files

Templates in `references/` (plugin path `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffolder/references/`):
- [claude-md-template.md](references/claude-md-template.md) - Root and module CLAUDE.md templates
- [settings-json-template.md](references/settings-json-template.md) - settings.json deny list, hook registrations, and the optional team effort cap and subagent model
- [hook-scripts.md](references/hook-scripts.md) - Hook scripts and the hook input contract
- [skills-templates.md](references/skills-templates.md) - Project command and skill templates (/test-all, /review, /deploy, code-review, refactor, release)
- [agents-templates.md](references/agents-templates.md) - Agent definitions (code-reviewer, security-auditor) and the model/effort policy
- [docs-templates.md](references/docs-templates.md) - Architecture, ADR, runbook, onboarding, API reference, and .env templates
- [reference-doc-template.md](references/reference-doc-template.md) - Skeletons for the 8 implementation reference layers (docs/reference/)
- [writing-style-guide.md](references/writing-style-guide.md) - Shared bilingual and style rules for every generated document (ADR-003)
- [readme-template.md](references/readme-template.md) - Bilingual README.md section structure and generation rules
- [changelog-template.md](references/changelog-template.md) - Bilingual CHANGELOG.md rules following Keep a Changelog
- [mcp-json-template.md](references/mcp-json-template.md) - .mcp.json base template and server entry shape
- [scripts-templates.md](references/scripts-templates.md) - setup.sh and install-hooks.sh (Core)
- [tests-templates.md](references/tests-templates.md) - Test runner and harness validation tests
