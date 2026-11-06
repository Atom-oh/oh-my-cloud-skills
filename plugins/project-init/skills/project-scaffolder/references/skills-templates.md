# Skills and Command Templates

Templates for the project commands (`.claude/commands/<name>.md`) and skills (`.claude/skills/<name>/SKILL.md`) that `/init-project` generates for the tiers the user selected. Commands and skills both create slash commands and accept the same frontmatter, except that commands take no `name` or `paths`.

Rules for every template in this file:
- Copy the block as written and fill each `<...>` from detection. Where detection found nothing, leave a `<!-- TODO: ... -->` and list it in the init summary; do not invent a command to fill the gap.
- `description` states what the command or skill does and when to use it, key use case first, because Claude routes on it and the listing truncates `description` plus `when_to_use` at 1,536 characters.
- Anything that deploys, releases, or pushes sets `disable-model-invocation: true`, so only the user can start it.
- `allowed-tools` uses the space form (`Bash(git diff *)`).
- No `model`. `effort` appears only on `/test-all`, which is mechanical work.

There is no sync-docs skill: consumers already have the plugin command `/project-init:sync-docs`, and a local copy would duplicate it.

---

## Default Commands

### Test All Command

Tier: Default

Path: `.claude/commands/test-all.md`

Fill `<test command>` with the detected command (for example `npm test`, `pytest`, `go test ./...`, `cargo test`). If the project has no test command yet, drop that sentence and its `allowed-tools` rule and leave `<!-- TODO: add the project's test command -->`.

```markdown
---
description: Run the project's tests and the harness tests, then report failures. Use after a change, or when asked to run the tests.
allowed-tools: Read, Grep, Bash(<test command> *), Bash(bash tests/run-all.sh *)
argument-hint: "[test file or pattern]"
effort: low
---

Run `<test command>` (pass $ARGUMENTS to it if given), then `bash tests/run-all.sh` for the harness tests.

Report the totals for each suite first (passed, failed, skipped), then each failure with `file:line` and the assertion message. When a suite's command could not start, for example because a tool or the project's dependencies are missing, report it as not run, with the error, never as passed. If the cause is evident from the output, name it in one line. Do not change code unless asked, because the user decides whether a red test is a bug or a stale test.
```

### Review Command

Tier: Default (generated together with the code-reviewer agent in `agents-templates.md`)

Path: `.claude/commands/review.md`

```markdown
---
description: Review the current changes for bugs, security issues, and CLAUDE.md convention violations. Use before committing or opening a PR.
allowed-tools: Read, Glob, Grep, Bash(git diff *), Bash(git log *), Bash(git status *), Bash(git show *)
argument-hint: "[files or git ref]"
---

Scope: $ARGUMENTS if given, otherwise everything since HEAD: `git diff HEAD` (staged and unstaged) plus the untracked files `git status --short` lists, which `git diff` does not show. If there is nothing to review, say so and stop.

For a multi-file change, delegate to the code-reviewer agent with that scope and return its report as-is. Review a small diff directly, using the report format in `.claude/agents/code-reviewer.md`, because starting a subagent costs more than such a review.

Report every finding with its severity and confidence; do not filter by confidence, because the reader decides what to act on.
```

---

## Optional Command

### Deploy Command

Tier: Optional. Pre-checked when a `Dockerfile`, `template.yaml`, `cdk.json`, `serverless.yml`, or deploy script is detected.

Path: `.claude/commands/deploy.md`

Fill `<detected deploy method>` with what detection found (for example `Dockerfile`, `template.yaml (SAM)`, `cdk.json`). The template pre-approves no deploy commands, so each command the runbook lists asks for permission; that pause is intended for steps that cannot be undone.

```markdown
---
description: Deploy by following the project's deploy runbook in docs/runbooks/. Only the user starts a deploy.
disable-model-invocation: true
allowed-tools: Read, Glob, Bash(git status *), Bash(git log *), Bash(git branch --show-current)
argument-hint: "[environment]"
---

Deploy by following `docs/runbooks/deploy-*.md` (the one for $ARGUMENTS when several exist) and report the result of each step.

If no deploy runbook exists, do not deploy. Report the detected deployment method (<detected deploy method>) and offer to write the runbook first with `/add-runbook deploy-<environment>`: `/add-runbook deploy-$ARGUMENTS` when an environment was given, otherwise `/add-runbook deploy-production`. That name matches `docs/runbooks/deploy-*.md`; a runbook named plain `deploy.md` would not.

Run only the deploy, verification, and rollback commands the runbook lists. Pushes, tag deletions, and cloud deploys cannot be undone and differ per project, so an improvised step is riskier than stopping. Before the first step, show `git status --short` and the current branch; if the tree is dirty or the branch is not the one the runbook names, ask before continuing. If a step fails, stop, show its output, and quote the runbook's Rollback section; run a rollback step only after the user confirms it.
```

---

## Optional Skills

Generic workflow scaffolding; most useful when the team runs smaller models. Each body holds only facts about this project; the model already knows how to review, refactor, and release in general.

### Code Review Skill

Tier: Optional. The name shadows Claude Code's bundled `/code-review`, and the skill does the job of `/review` plus the code-reviewer agent, so `/init-project` generates it instead of that pair and the project keeps one review path. Offer it only when the team wants project review guidance loaded automatically whenever Claude reviews code.

Path: `.claude/skills/code-review/SKILL.md`

```markdown
---
name: code-review
description: The conventions and risk areas a code review in this project must check. Use when reviewing code in this repository.
---

Review against the conventions in `CLAUDE.md` and these project-specific risk areas:
<!-- TODO: list the areas where bugs have bitten this project, each with its reason, e.g. "money is integer cents; flag float arithmetic in billing/" -->

Report every finding that affects correctness, security, or a stated convention as `[CRITICAL|IMPORTANT|MINOR] <title> (confidence: <0-100>) — <path>:<line> — <issue> — <fix>`, most severe first. Do not drop a finding because confidence is low, because the reader filters.
```

### Refactor Skill

Tier: Optional

Path: `.claude/skills/refactor/SKILL.md`

```markdown
---
name: refactor
description: Refactor code in this project without changing its behavior. Use when asked to restructure, rename, extract, or clean up code.
---

Behavior must not change. Run `<test command>` before and after the change; if no test exercises the code you are changing, say so and offer to add one first, because a refactor without a check is a rewrite.

Project constraints:
<!-- TODO: public APIs, generated files, or module boundaries that a refactor must not change -->
```

### Release Skill

Tier: Optional

Path: `.claude/skills/release/SKILL.md`

Fill the version files from the detected manifests (for example `package.json` `version`, `pyproject.toml` `[project] version`).

```markdown
---
name: release
description: Cut a release of this project (bump the version, update the changelog, tag it). Only the user starts a release.
disable-model-invocation: true
allowed-tools: Read, Bash(git status *), Bash(git log *), Bash(git describe *)
---

Release facts for this project:
- Version lives in: <detected version files>
- Tag format: `v<X.Y.Z>`
- Changelog: update CHANGELOG.md with `/project-init:generate-changelog`
- Checks that must pass first: `<test command>`, and a clean working tree

Work in this order, because a pushed tag is hard to take back:
1. Confirm the tree is clean and the checks pass; stop and report if not.
2. Propose the next version from the commits since the last tag (`git log $(git describe --tags --abbrev=0)..HEAD --oneline`) and wait for the user to confirm it.
3. Update the version in every file listed above, then the changelog.
4. Commit, then create the annotated tag `v<X.Y.Z>`. Push only when the user asks.
```
