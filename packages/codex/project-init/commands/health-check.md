---
description: Validate the project's Claude Code harness - files, hooks and the hook contract, skills/commands/agents, docs, security, tests - and score CLAUDE.md quality
allowed-tools: Read, Glob, Grep, Bash(bash ${CLAUDE_PLUGIN_ROOT}/scripts/harness-check.sh *), Bash(bash tests/run-all.sh *), Bash(grep *)
---

# Health Check

Report how healthy this project's Claude Code harness is and what to fix first. `harness-check.sh` has already run every deterministic check; its output is in Context. Your part is the judgment it cannot make: CLAUDE.md quality, whether an uncovered module needs a CLAUDE.md, whether a secret-pattern match is a real secret, the test run, and the Recommended Actions. Do not re-check by hand what the script reported, because a hand count can disagree with the score. This command only reports; it changes no files.

## Context

- Harness check: !`bash ${CLAUDE_PLUGIN_ROOT}/scripts/harness-check.sh`

Each line is `<STATUS> <id> <earned>/<max> <detail>` (PASS, FAIL, WARN, INFO, SKIP; INFO and SKIP carry 0/0), then one `CATEGORY <name> <earned>/<max>` line per category, then `TOTAL <earned>/<max> <percent>%`. If the script did not run in the project root (you have `cd`'d, or the output reports a missing CLAUDE.md the repo has), run `bash ${CLAUDE_PLUGIN_ROOT}/scripts/harness-check.sh <project root>` and use that output instead.

## Inputs

- `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffolder/SKILL.md`, sections `## CLAUDE.md Quality Criteria` and `## CLAUDE.md Anti-Patterns` (the CLAUDE.md rubric) and `## Module CLAUDE.md Coverage`. If the file cannot be read, stop and say so instead of scoring from memory.
- The root `CLAUDE.md`, the modules that `docs-modules` lists as uncovered, and the files and lines that a `sec-scan` or `sec-mcp` WARN names.

## Rules

- **Score**: the TOTAL percent is the score. Copy it and the CATEGORY points as printed, adding or removing none, so every run and model gives the same score. The harness Grade comes from the TOTAL percent: A >= 80%, B >= 60%, C >= 40%, D >= 20%, F < 20%.
- **CLAUDE.md quality**: score the root CLAUDE.md out of 100 with the SKILL.md criteria minus the anti-pattern deductions, and give it that section's letter grade. Report it on its own line, not inside the harness score.
- **Module coverage**: for each directory `docs-modules` lists, skim its code and apply SKILL.md `## Module CLAUDE.md Coverage`. Recommend `/project-init:add-module <dir>` only for a module that section says needs one, naming the rules or gotchas it would record.
- **Secrets**: for each `file:line` that `sec-scan` lists and each `.mcp.json` entry a `sec-mcp` WARN describes, read the value in place and judge whether it is a real credential or a sample, pattern definition, or test value. Never print a matched value, because reports get pasted into issues and chats. In CLAUDE.md, the rubric's secrets greps also catch forms the script misses, such as an unquoted value.
- **Tests**: if `tests/run-all.sh` exists, run `bash tests/run-all.sh` once and report the passed and failed counts from its summary plus the names of failing tests.
- **Status**, first match wins:
  - CRITICAL: any `contract-*` line is FAIL, you judged a committed secret real, or the harness Grade is D or F.
  - NEEDS ATTENTION: `secret-scan-scope` or `doc-sync-scope` is WARN; `hook-reg-secret-scan`, `hook-reg-verify-on-stop`, `hook-python3`, or `hook-disable-all` is WARN, because then a gate may not run; any other line is FAIL; the test run failed; the harness Grade is B or C; or the CLAUDE.md grade is D or F.
  - HEALTHY: otherwise.

## Recommended Actions

Give an action for every FAIL and WARN line and every CLAUDE.md deduction, one line each, naming the file and the command or edit (the fix the detail names, where it names one), and mark the minor ones `(minor)` instead of leaving them out. Order by impact: contract findings first, because a hook on the old contract silently does nothing; then a real secret; then FAIL lines; then WARN lines; then modules you judged to need a CLAUDE.md; then CLAUDE.md deductions. INFO lines are notes and SKIP lines are not findings, so neither is an action; `docs-modules` becomes one only through your judgment under **Module coverage**.

| Finding | Action |
|---------|--------|
| `contract-settings-json` FAIL | Fix the JSON syntax in `.claude/settings.json` before the other contract actions |
| any other `contract-*` FAIL, or `secret-scan-scope` or `doc-sync-scope` WARN | Run `/project-init:migrate-hooks` |
| a real secret | Rotate the credential first, since it is in git history; then move it to `.env` (`.env.example` is the template) |
| missing Core files, hooks, docs, or tests | Run `/project-init:init-project`, which keeps existing files, or name the one file to add |
| `hook-reg-*` FAIL or WARN | Register the hook, or rewrite its `command` in `.claude/settings.json`, in the form `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffolder/references/settings-json-template.md` shows |
| `hook-python3` WARN | Install python3, or replace the `python3` on PATH that does not run (such as the Windows Store alias) |
| `hook-disable-all` WARN | Remove `"disableAllHooks": true` from the file the detail names, unless the user set it on purpose |
| `hook-verify-cmd` WARN | Set `VERIFY_CMD=` in `.claude/hooks/verify-on-stop.sh` to the project's fast check, or remove the hook and its Stop registration |
| `core-commit-msg` WARN | Run `bash scripts/install-hooks.sh` |
| an uncovered module you judged to need a CLAUDE.md | `/project-init:add-module <dir>`, naming the rule or gotcha it will record |
| `components-dup`, `components-plugin-dup` | Delete the duplicate the detail names, keeping one path |
| `compat-*` WARN | Fix the frontmatter key or model pin the detail names |
| failing tests | Name the failing test; `/test-all` if the project has it |

## Report

The table, the CLAUDE.md line, the actions, and nothing else. The values below are illustrative.

```
## Project Health Report

Score: 94% (165/175), Grade A
Status: NEEDS ATTENTION

| Category | Points | Findings |
|----------|--------|----------|
| Core files | 37/37 | OK |
| Hooks | 33/38 | WARN hook-reg-secret-scan: path not anchored at $CLAUDE_PROJECT_DIR |
| Hook contract | 38/43 | WARN secret-scan-scope: predates the commit-scope fix (run /project-init:migrate-hooks) |
| Harness components | 20/20 | 3 load, no duplicates |
| Compatibility | 2/2 | notes: alias pin in .claude/agents/code-reviewer.md |
| Documentation | 9/9 | OK; modules: src/utils/ uncovered, needs none |
| Security | 16/16 | no secret-pattern matches |
| Tests | 10/10 | tests/run-all.sh: 58/58 passed |

CLAUDE.md Quality: 78/100 (Grade B) - largest deduction: hardcoded test count in Key Commands (-10)

### Recommended Actions
1. Run /project-init:migrate-hooks: secret-scan.sh predates the commit-scope fix and its registration uses a relative path
2. CLAUDE.md: replace "58 tests" in Key Commands with the command that prints the count
3. (minor) CLAUDE.md: drop the dependency list copied from package.json in Tech Stack
```

Category rows come from the CATEGORY lines in this order: `core` Core files, `hooks` Hooks, `contract` Hook contract, `components` Harness components, `compat` Compatibility, `docs` Documentation, `security` Security, `tests` Tests. In Findings, list the FAIL and WARN ids with their detail shortened, or `OK`. For Hook contract with no FAIL or WARN, write `OK (current hook contract)`. For Documentation, add your `docs-modules` judgment: the uncovered modules that need a CLAUDE.md, or that none do. For Security, add your verdict on each secret match (`real: <file:line>`, or `sample only`). For Tests, give the run result, or `not run (no tests/run-all.sh)`.
