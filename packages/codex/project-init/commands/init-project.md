---
description: Initialize a Claude Code project structure (CLAUDE.md, docs, settings and hooks, tests, plus optional commands, agents, and skills) in a new or existing project, adapted to the detected language and layout.
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(ls *), Bash(mkdir *), Bash(chmod +x .claude/hooks/*), Bash(git status *), Bash(git init *), Bash(git add *), Bash(git commit *), Bash(git remote get-url *), Bash(git log *), Bash(git tag --sort*), Bash(git tag --list *), Bash(git for-each-ref *), Bash(git describe *), Bash(bash scripts/install-hooks.sh *), Bash(bash tests/run-all.sh *), Bash(python3 -m json.tool *), Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-bilingual.py *), Bash(bash ${CLAUDE_PLUGIN_ROOT}/scripts/harness-check.sh *)
argument-hint: Optional project directory path (defaults to current directory)
---

# Initialize Claude Code Project Structure

## Goal

Set up the Claude Code harness the project will actually use: the Core files, plus the Default and Optional components the user keeps (see Artifacts). In an existing project, adapt everything to the detected language, commands, and layout. The run is done when the Finish checks pass or their remaining failures are reported, and the Summary is written.

Target: $ARGUMENTS, a project root path; empty means the current directory; create it if it does not exist. Run every command from the target directory, because the templates use project-relative paths.

## Templates

Templates are in `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffolder/references/`; the Artifacts table names the file and section for each output. Read a template before writing its files. If one cannot be read, stop and tell the user which one instead of writing from memory, because a reconstruction breaks the contracts it carries.

## Rules

- **Existing files win**, because users customize them and a second run must be safe: do not overwrite a file that exists; log it as `(existing, kept)`. These are updated in place instead, and logged as adapted:
  - `README.md` and `CHANGELOG.md`, per the Update Rules in their templates;
  - `.claude/settings.json`: add missing deny rules and hook registrations and keep every other key. A hook registered in an older form (a relative `bash .claude/hooks/...` path, or a gate with `|| true`) counts as registered: leave it for `/project-init:migrate-hooks`, which migrates it with a backup, instead of adding a second registration;
  - `.gitignore`: append `.env`, `.claude/settings.local.json`, and `.claude/worktrees/` when missing;
  - the AUTO-MANAGED regions in `CLAUDE.md` and `docs/reference/INDEX.md`.
- **Copy template code blocks as written**, changing only the adapt points in the Artifacts table and the `<...>` placeholders, because hooks, settings, and tests are contracts that a paraphrase breaks.
- **Use what detection finds** (the real source directories, commands, and layout), or the answers for a new project. Do not create `src/api/` or `src/persistence/` in a project with its own layout.
- **Ask once**, in the round below. A value still unknown after it becomes a `<!-- TODO: ... -->` listed in the summary; do not invent commands, options, or rollback steps.
- **Keep CLAUDE.md files lean**, per `## CLAUDE.md Anti-Patterns` and `## Module CLAUDE.md Coverage` in `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffolder/SKILL.md`.

## Detection

Read the manifests and list the directories (Glob, Read, `ls`); detection needs no build or install.

| File Found | Project Type | Source Dirs | Key Commands |
|-----------|-------------|-------------|--------------|
| `package.json` | Node.js | src/, app/, lib/, components/ | npm/yarn/pnpm |
| `pyproject.toml` / `requirements.txt` | Python | src/, app/, lib/ | pip, pytest, ruff |
| `go.mod` | Go | cmd/, pkg/, internal/ | go build, go test |
| `Cargo.toml` | Rust | src/ | cargo build, cargo test |
| `pom.xml` / `build.gradle` | Java/Kotlin | src/main/, src/test/ | mvn, gradle |
| None detected | New project | src/api/, src/persistence/ | (ask user) |

Also record:
- the test, lint, typecheck, and build commands (manifest scripts, Makefile targets, CI config). The quickest of lint, typecheck, and unit tests is the project's **fast check**.
- git state: whether `.git/` exists, `git remote get-url origin`, and `git status --short`.
- deploy signals: `Dockerfile`, `template.yaml`, `cdk.json`, `serverless.yml`, or a deploy script.
- which artifacts already exist. For existing shell tests outside `TEST_DIRS`, follow `## Test Runner` in tests-templates.md; if `tests/run-all.sh` is kept, say in the summary that it does not run the generated harness tests.
- when `.claude/` exists, the hook contract: `bash ${CLAUDE_PLUGIN_ROOT}/scripts/harness-check.sh --contract-only .`. Exit 1 triggers the Existing harness question.

### Implementation Reference Detection

Each selected layer gets a skeleton under `docs/reference/` (see Implementation reference docs). Match the signals at any depth (Glob `**/routes/`, `**/*.tf`), skipping `node_modules/`, `vendor/`, `.git/`, and build output.

| Layer | Detect when ANY present |
|---|---|
| infrastructure | `Dockerfile`, `docker-compose.yml`, `compose.yaml`, `k8s/`, `helm/` |
| data | `migrations/`, `prisma/`, `schema.sql`, `*.prisma`, `models/`, `entities/`, `db/` |
| api | `routes/`, `controllers/`, `api/`, `openapi.yaml`, `*.proto`, `swagger.json` |
| iac | `*.tf`, `cdk.json`, `template.yaml`, `serverless.yml`, `terragrunt.hcl` |
| frontend | `package.json` deps with react/vue/svelte/next/nuxt/angular, `index.html`, `vite.config.*` |
| ui | (frontend detected) AND any of `components/`, `styles/`, `tailwind.config.*`, `*.css`/`*.scss` |
| security | `.env.example`, `auth/`, `middleware/`, `permissions/`, `iam/`, `policies/` — **always pre-checked** |
| agent-llm | `prompts/`, package deps with anthropic/openai/langchain/bedrock |

The question round shows the result in this form:

```text
Detected implementation layers:
  ✓ Infrastructure (Dockerfile)
  ✓ API (routes/)
  ✓ Security (.env.example) — auto-recommended
  ─ Data — not detected
  ...

Proceed with detected set, or adjust? (a)ccept / (e)dit
```

On `(e)dit`, the user toggles each layer, pre-checked per detection. With zero detections, show every layer unchecked except Security, plus the note: *"More layers can be added later with /add-reference-doc <layer>."*

## Questions (one round)

Collect every answer before writing any file, with detected values as defaults.

Ask with the AskUserQuestion tool when it is available, because its answers arrive in this turn, where `allowed-tools` still cover the writes and commands that follow. Make as many calls as the items need (up to 4 questions of up to 4 options each), in this order:

- The Existing harness question alone, when it applies, because a migrate answer ends the run.
- One call with the confirmations: layers and components, each as `Accept` / `Edit` with the detected set named in the question text, plus git.
- Project facts and README fields: one question each, with the detected value or `Leave a TODO` as options and the value typed in "Other".
- After an `Edit`: that checklist as `multiSelect` questions of up to four items (the eight layers in two, the components in groups of four). Mark each detected or pre-checked item in its option description, because the selection replaces the defaults.

Without the tool, ask everything in one chat message using the blocks below, and wait for the reply. In it, say that the next turn will ask before each write and command, because the pre-approval ends with this turn, and that approving the plugin-script commands once beats "don't ask again", which saves a rule pinned to the versioned plugin path.

0. **Existing harness**, only when the contract check in Detection exited 1: "Existing hooks or registrations predate the current contract. Run /project-init:migrate-hooks first (recommended: it backs them up and regenerates them), or continue, and the generated tests will fail on the kept hooks until you migrate." On migrate, stop without writing anything and tell the user to run `/project-init:migrate-hooks`, then `/init-project` again.
1. **Project facts** detection could not answer. For a new project: name, a one-line description in English and in Korean, tech stack, and source layout (default `src/api/` and `src/persistence/`).
2. **Implementation reference layers**: the detection block above.
3. **Components**, with the same accept/edit pattern. Fill in the detected commands, and pre-check `/deploy` when a deploy signal was found, naming it:

   ```text
   Components (Core files are always generated):
     [x] /test-all: runs `<test command>` and the harness tests (Default)
     [x] /review + code-reviewer agent: reviews the diff before a commit; the one review path (Default)
     [ ] /deploy: follows docs/runbooks/deploy-*.md, user-invoked only, refuses to deploy without a runbook (Optional)
     [ ] security-auditor agent: on-demand audit of secrets, dependencies, and configuration (Optional)
     [ ] code-review skill: project review checklist loaded whenever Claude reviews code; replaces /review + code-reviewer as the review path, so selecting it unchecks them, and shadows the bundled /code-review (Optional)
     [ ] refactor skill: behavior-preserving refactors checked with the test command; generic scaffolding, most useful with smaller models (Optional)
     [ ] release skill: version, changelog, and tag facts, user-invoked only; generic scaffolding, most useful with smaller models (Optional)
     [ ] session-context.sh: reports a local-environment fact at session start, such as a pinned runtime that differs from the active one or a service the tests need that is not running; useful when those cause failures. Detected: <.nvmrc, .python-version, services> (Optional)
     [ ] notify.sh: webhook alert when Claude needs attention; needs CLAUDE_NOTIFY_WEBHOOK (Optional)
     [ ] verify-on-stop.sh: Stop gate that runs `<fast check>` when a turn ends on a changed tree and hands failures back to Claude; most useful with Sonnet or Haiku at low or medium effort, which sometimes report a change done without running a check (Optional)

   Proceed with this set, or adjust? (a)ccept / (e)dit
   ```

   With no pinned runtime or needed service detected, write `(nothing detected to report)` as the session-context `Detected:` list. With no git repository yet, append `needs a git repository to detect changes` to the verify-on-stop line.

4. **README fields** detection could not fill: maintainer name, GitHub username, and an optional demo image or GIF path.
5. **Git**. Without `.git/`: initialize a repository and commit the generated files (files that existed before this run stay untracked for the user to review and add)? With an existing repository: install the commit-msg hook that removes Co-Authored-By lines (it leaves a different existing hook or a hook manager alone and prints the line to add)?

## Artifacts

Create only the directories the selected artifacts need (`mkdir -p`).

| Artifact | Template (file + section) | Tier | Adapt |
|---|---|---|---|
| `CLAUDE.md` | claude-md-template.md, Root CLAUDE.md Template | Core | The real commands in Key Commands, and the fast check in its "Verify a change" line |
| `<module>/CLAUDE.md` | claude-md-template.md, Module CLAUDE.md Template | Core | Only for a module with rules, invariants, or gotchas the code does not show; for a new project, only where the answers gave such rules |
| Source directories | none | Core, new project only | The layout from the answers |
| `.claude/settings.json` | settings-json-template.md | Core | `permissions.allow` gets the detected test command and fast check as `Bash(<command> *)` (empty when none); register the Core hooks and each selected Optional hook |
| `.claude/hooks/secret-scan.sh` | hook-scripts.md, secret-scan.sh | Core | None |
| `.claude/hooks/check-doc-sync.sh` | hook-scripts.md, check-doc-sync.sh | Core | `SOURCE_ROOTS` set to the detected source roots |
| `scripts/setup.sh` | scripts-templates.md, setup.sh | Core | Detected prerequisites and install commands |
| `scripts/install-hooks.sh` | scripts-templates.md, install-hooks.sh | Core | None |
| `docs/architecture.md` | docs-templates.md, Architecture Document; writing-style-guide.md | Core | Components from the source, IaC, Dockerfiles, and dependency files, or for a new project from the answers and Plan-mode context; only the layers that apply |
| `docs/onboarding.md` | docs-templates.md, Onboarding Document | Core | Prerequisites and setup from the detected build system |
| `docs/decisions/.template.md` | docs-templates.md, ADR Template | Core | None |
| `docs/runbooks/.template.md` | docs-templates.md, Runbook Template | Core | None |
| `docs/api-reference.md` | docs-templates.md, API Reference Document | Core, only when routes, handlers, or controllers are detected | Endpoints from the code |
| `docs/reference/<layer>.md`, `docs/reference/INDEX.md` | reference-doc-template.md, `## Layer: <layer>` | Core, selected layers | See Implementation reference docs |
| `tests/run-all.sh`, `tests/hooks/test-hooks.sh`, `tests/hooks/test-secret-patterns.sh`, `tests/structure/test-plugin-structure.sh`, `tests/fixtures/secret-samples.txt`, `tests/fixtures/false-positives.txt` | tests-templates.md | Core | Uncomment the structure tests' version-consistency block only when the project has a version file, pointed at that file |
| `README.md` | readme-template.md; writing-style-guide.md | Core | Detected facts and the README answers |
| `CHANGELOG.md` | changelog-template.md; writing-style-guide.md | Core | Entries from tags and history (`git tag --sort=-v:refname`, `git log`), or an empty `[Unreleased]` in both languages for a new project |
| `.env.example` | docs-templates.md, Environment Template | Core | Variables the code reads, with no real values |
| `.gitignore` | none | Core | Patterns for the detected language, plus `.env`, `.claude/settings.local.json`, and `.claude/worktrees/` (Claude Code's linked worktrees, which `git add` must not pick up) |
| `.editorconfig` | none | Core | The indentation the code already uses; LF line endings and a final newline |
| `.mcp.json` | mcp-json-template.md, Base Template | Core | `{"mcpServers": {}}` unless the user asked for servers; detected integrations (GitHub remote, database config) go on the summary's MCP line |
| `.claude/commands/test-all.md` | skills-templates.md, Test All Command | Default | Detected test command |
| `.claude/commands/review.md` | skills-templates.md, Review Command | Default | None |
| `.claude/agents/code-reviewer.md` | agents-templates.md, Code Reviewer Agent | Default, with /review | None |
| `.claude/commands/deploy.md` | skills-templates.md, Deploy Command | Optional, pre-checked on a deploy signal | Detected deploy method |
| `.claude/agents/security-auditor.md` | agents-templates.md, Security Auditor Agent | Optional | None |
| `.claude/skills/code-review/SKILL.md` | skills-templates.md, Code Review Skill | Optional, instead of `/review` and code-reviewer | Risk areas from the answers, otherwise a TODO |
| `.claude/skills/refactor/SKILL.md` | skills-templates.md, Refactor Skill | Optional | Test command |
| `.claude/skills/release/SKILL.md` | skills-templates.md, Release Skill | Optional | Version files and test command |
| `.claude/hooks/session-context.sh` | hook-scripts.md, session-context.sh | Optional, only with a detected fact to report | Per the template's Customize note |
| `.claude/hooks/notify.sh` | hook-scripts.md, notify.sh | Optional | None |
| `.claude/hooks/verify-on-stop.sh` | hook-scripts.md, verify-on-stop.sh (Stop Hook, opt-in) | Optional, only in a git repository (existing, or created per question 5) | Replace only the default `npm run lint` inside `${VERIFY_CMD:-...}` with the fast check, never a slow suite; keep the `${VERIFY_CMD:-...}` form, which the generated tests override |

A selected component the Tier column rules out goes under Skipped with the reason.

### Implementation reference docs

For each selected layer, write `docs/reference/<layer>.md` from the fenced block under `## Layer: <layer>`, filling `{{COMPONENTS_TABLE}}` with rows for the detected paths and `{{CODE_POINTERS_AUTO}}` with the top 1-3 detected files.

Then write `docs/reference/INDEX.md` and upsert the `## Implementation References` block between the `<!-- AUTO-MANAGED:references -->` markers in the root `CLAUDE.md`, in the formats of the `## INDEX.md` and `## Root CLAUDE.md Block` sections of `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffolder/references/reference-doc-template.md`. In INDEX.md, a layer that detection found but the user deselected gets the status `declined` (`제외`), so `/sync-docs` stops recommending it.

## Finish

Run these in order.

1. Make the scripts executable:

   ```bash
   chmod +x .claude/hooks/*.sh scripts/*.sh tests/run-all.sh tests/*/*.sh
   ```

2. Run the checks:

   ```bash
   bash tests/run-all.sh
   python3 -m json.tool .mcp.json > /dev/null
   bash ${CLAUDE_PLUGIN_ROOT}/scripts/harness-check.sh --contract-only .
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-bilingual.py <each bilingual file this run created or updated>
   ```

   The bilingual files are `README.md`, `CHANGELOG.md`, `docs/architecture.md`, `docs/decisions/.template.md`, `docs/runbooks/.template.md`, `docs/reference/INDEX.md`, and each `docs/reference/<layer>.md`. Name each one this run created or updated, leaving out any `(existing, kept)`; do not pass a glob, because one that matches nothing reaches the checker as a literal path and it exits 2. Without python3, skip the JSON and bilingual checks and report them `unavailable`.

   If a check fails on a file this run created or updated, fix that file and run the check again. Report these failures instead of fixing them:
   - A bilingual-check issue in content that existed before this run (a released CHANGELOG section, the user's own README prose): report it as pre-existing, because the templates' Update Rules keep that content unchanged.
   - A test or contract failure caused by a kept pre-v2.3 hook or an older settings.json registration: leave the generated tests and those registrations as they are, because `/project-init:migrate-hooks` migrates them with a backup. Put it first in Next.
   - A failure in any other file of the user's: do not edit it to make a check pass.

   If verify-on-stop.sh was generated, run its `VERIFY_CMD` once; if it already fails on the current code, say so in the summary, because the gate hands that failure back after every turn that changes the tree.

3. Git, only as the user answered:
   - **New repository** (no `.git/` before this run): `git init`, then `bash scripts/install-hooks.sh`, then `git add` with the paths this run created, then `git commit -m "chore: initialize Claude Code project structure"`. Name the paths instead of `git add -A`, which would also stage anything else in the directory, such as a `.env`.
   - **Existing repository**: run `bash scripts/install-hooks.sh` if the user agreed. Do not commit, because the working tree may hold the user's uncommitted work; show `git status --short` for the generated paths instead.

   If `install-hooks.sh` exits 1 (a hook manager such as husky, or a different commit-msg hook), continue and report the line it printed on the summary's Git line.

4. Report the summary.

## Summary

End with this report and nothing longer; list each path once, under the first heading that applies:

```text
Created:  <path>, ...
Adapted:  <path> (<what was adapted>), ...          e.g. .claude/hooks/check-doc-sync.sh (SOURCE_ROOTS="app lib")
Kept:     <path> (existing, kept), ...
Skipped:  <component or path> (<reason>), ...       e.g. security-auditor (not selected), docs/api-reference.md (no API detected)
TODO:     <path>: <what to fill in>, ...
Checks:   tests <passed>/<total>; contract check <clean | findings>; JSON <valid | unavailable>; bilingual check <clean | findings | pre-existing: <file>:<line>, ... | unavailable>
Git:      <initialized and committed <short sha> (generated files only; left untracked: <pre-existing top-level paths>, review and `git add` them yourself) | existing repository: review `git status` and commit when ready | skipped>; commit-msg hook <installed | not installed: add `<line install-hooks.sh printed>` to <hook manager or existing hook>>
MCP:      <`claude mcp add --scope project ...` suggestions for detected integrations | none>

Next: <run /project-init:migrate-hooks, then> restart the Claude Code session so the new agents, skills, and MCP configuration load, then run /project-init:health-check.
```

Write the `<run /project-init:migrate-hooks, then>` part only when the contract check reported findings.
