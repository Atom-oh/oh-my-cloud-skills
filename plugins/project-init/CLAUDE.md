# project-init Plugin

## Role
Core plugin providing project structure initialization, documentation quality scoring, and auto-sync workflows. This is the primary plugin in the marketplace.

## Key Files
- `.claude-plugin/plugin.json` - Plugin manifest (name, version, description)
- `commands/init-project.md` - Main initialization command (adapts to detected project type)
- `commands/sync-docs.md` - Documentation synchronization
- `commands/add-adr.md` - ADR creation
- `commands/add-module.md` - Module scaffolding
- `commands/add-runbook.md` - Runbook creation
- `commands/add-reference-doc.md` - Add layer-specific implementation reference doc
- `commands/generate-readme.md` - Bilingual README.md generation/update
- `commands/generate-changelog.md` - Bilingual CHANGELOG.md generation/update
- `commands/health-check.md` - Project validation: scores `harness-check.sh` output, then judges CLAUDE.md quality, secrets, and the recommended actions
- `commands/migrate-hooks.md` - Migrate pre-v2.3 hooks, settings.json, and `.yml` agents to the stdin/exit 2 contract, and regenerate a `secret-scan.sh` or `check-doc-sync.sh` that lacks the commit-scope or module-coverage marker (with backup, `--dry-run`)
- `agents/doc-sync-checker.md` - Documentation sync analysis agent
- `scripts/harness-check.sh` - Deterministic harness checks and score; its header holds the CLI, output, and exit-code contract, and its `points()` table is the only place points are defined. /health-check reads its output; /init-project and /migrate-hooks run `--contract-only`
- `scripts/check-bilingual.py` - Mechanical bilingual-structure checks (ADR-001/002); its docstring holds the rules and the CLI contract
- `skills/project-scaffolder/SKILL.md` - Scaffolding skill; single source for `## CLAUDE.md Quality Criteria`, `## CLAUDE.md Anti-Patterns` (with the secrets greps), and `## Module CLAUDE.md Coverage` (with the fallback source roots `harness-check.sh` also uses)
- `skills/project-scaffolder/references/` - Template files for code generation (includes shared writing-style-guide)
- `skills/project-scaffolder/references/reference-doc-template.md` - 8-layer skeleton library used by /init-project and /add-reference-doc

## Rules

### Writing commands, agents, skills, and templates
- Prompts run on the consumer's model: Opus 5.5 by default, or Sonnet 5.5 or Haiku 5.5, and on Amazon Bedrock, Google Cloud, and Microsoft Foundry the `sonnet` and `haiku` aliases still resolve to 4.5 models. Keep every output contract explicit (file paths, section headings, frontmatter keys, bilingual structure, exit codes, report format); smaller models do not infer them. Cut procedure, never contract.
- Write a command as a goal paragraph, its inputs, rules with a one-clause reason each, the output contract (including the expected length of generated documents), a check the model can run in place of "verify" prose (`bash -n`, `python3 -m json.tool`, a grep, a bundled script, the project's tests), and the final report; a named check bounds verification on Opus, and Sonnet 5.5 and Haiku 5.5 at `low` or `medium` effort sometimes report work done without running any check unless the prompt names one. Number steps only where order matters or a step is hard to undo (backups, migrations, registering a hook, git); for judgment work, state criteria instead of a procedure.
- Plain voice: no ALL-CAPS emphasis, which makes the model over-apply a rule; give the reason instead.
- Ask the user once, up front, only for what the repo and conversation cannot answer. Otherwise write `<!-- TODO: ... -->` and list it in the summary instead of inventing options, commands, or rollback steps.
- A command that asks before running tools uses AskUserQuestion when available, because its answers return in the same turn, where the command's `allowed-tools` still apply; a chat reply starts a new turn without them. One call holds up to 4 questions of up to 4 options (`multiSelect`, free-text "Other"), so split a longer checklist; without the tool, ask everything in one chat message.
- Reviewer and audit prompts report every finding with severity and confidence and leave filtering downstream; a "report only if confident" rule drops real findings.
- Model and effort: agents omit `model`, so `CLAUDE_CODE_SUBAGENT_MODEL` can still steer them, and set `effort` only for bounded or mechanical work. Opus 5.5, Sonnet 5.5, and Haiku 5.5 all default to `medium`, so an agent without `effort` runs at the level the user chose. Plugin commands set neither, because they run in the user's main conversation. Generated templates follow the same policy, except the generated `/test-all` (`effort: low`). Generated settings never set `model` or top-level `effortLevel`, which would apply to every model for everyone; document `maxEffortLevel` and `CLAUDE_CODE_SUBAGENT_MODEL` (`settings-json-template.md` `## Optional: Subagent Model`) as options.
- Commands and generated skills that release, deploy, push, or rewrite many files or a user's harness (such as `/init-project` and `/migrate-hooks`) set `disable-model-invocation: true`, so only the user can start them.
- One source of truth: point to a template or a SKILL.md section by path and heading instead of copying it, because copies drift (ADR-003).

### Paths and tools
- Reference plugin files as `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffolder/references/<file>.md` and `${CLAUDE_PLUGIN_ROOT}/scripts/<script>`, written literally: Claude Code substitutes the placeholder in command, agent, and skill content and in `allowed-tools`, not in the Bash environment. Relative forms (`skills/project-scaffolder/...`, `plugins/project-init/...`, `../skills/...`) do not resolve in a consumer project.
- A command that reads a template says: if the file cannot be read, stop and say so instead of writing from memory.
- Pre-approve a bundled script with exactly `Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-bilingual.py *)` or `Bash(bash ${CLAUDE_PLUGIN_ROOT}/scripts/harness-check.sh *)`. Write rewritten permission rules in the space form (`Bash(git log *)`); `Bash(x:*)` is equivalent, so do not churn untouched frontmatter for syntax alone.
- Skills use `allowed-tools`; `tools` is an agent field only, and lists plain tool names.
- Keep command, agent, skill, and reference file paths as they are; tests and consumers depend on them.

### Content
- The init-project command generates by tier: Core always, Default unless the user unchecks it, Optional only when checked (ADR-009). init-project, health-check, SKILL.md, and README use the same tier names.
- Bilingual support (Korean/English) in user-facing templates; generated bilingual docs must pass `check-bilingual.py`
- When a check flags content that existed before the command ran (a released CHANGELOG section, the user's own README prose), the command reports it as pre-existing instead of rewriting it
- `tests/structure/test-prompt-contracts.sh` asserts rules that several plugin files must state alike; change it together with the rule
- Architecture flows in generated docs use Mermaid flowchart, not ASCII box diagrams (see references/writing-style-guide.md Diagram Rules, ADR-007)
