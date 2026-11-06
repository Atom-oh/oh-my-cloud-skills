---
description: Migrate project-init hooks, settings.json registrations, and agents to the current hook contract (stdin JSON, exit 2 gates, $CLAUDE_PROJECT_DIR paths, commit-scoped secret scan, first-level module coverage, Markdown subagents)
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(bash ${CLAUDE_PLUGIN_ROOT}/scripts/harness-check.sh *), Bash(date *), Bash(mkdir *), Bash(cp *), Bash(chmod *), Bash(diff *), Bash(rm .claude/agents/*), Bash(bash -n *), Bash(python3 -m json.tool *), Bash(bash .claude/hooks/*), Bash(bash tests/run-all.sh *)
argument-hint: Optional --dry-run to report what would change without writing
---

# Migrate Hooks to the Current Contract

Hooks and agents that older project-init versions generated live in the consuming project, so plugin updates cannot fix them, and they fail silently: hooks that read environment variables Claude Code never sets, gates that cannot block, `.yml` agents that never load, a secret scan that misses `git add . && git commit`, a doc-sync hook that asks for a CLAUDE.md in every subdirectory, and relative registration paths that exit 127 after Claude `cd`s into a subdirectory. This command replaces those files with the current templates, keeps a backup, and carries project-specific edits over. The steps are numbered because they overwrite files and must run in order.

Mode: $ARGUMENTS (`--dry-run` reports only; the default applies changes)

## Inputs

Read these before writing anything. If a file cannot be read, stop and say so instead of writing from memory.

- `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffolder/references/hook-scripts.md`: the current hook scripts, one section per script, headed by its name.
- `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffolder/references/settings-json-template.md`: the registration shapes that Step 4 applies.
- `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffolder/references/agents-templates.md`: the agent templates, for Step 5.

## Step 1: Detect What Needs Migration

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/harness-check.sh --contract-only
```

- Exit 0 with at least one PASS line: the scripts are current, but `--contract-only` does not check registration paths. Grep `.claude/settings.json` for a `command` that runs `.claude/hooks/` without `$CLAUDE_PROJECT_DIR`. If there is one, migrate those registrations only: run Steps 2, 4, 6, and 7 (with `--dry-run`, list them and stop). Otherwise report "Already on the current hook contract" and stop.
- Exit 0 with only SKIP lines: the project has no project-init hooks or agents to migrate. Say so, suggest `/project-init:init-project`, and stop.
- Exit 1: build the migration list from the FAIL and WARN lines.

| Line | Migration |
|------|-----------|
| `contract-settings-json` | Back up (Step 2), fix the syntax until `python3 -m json.tool .claude/settings.json` passes, and run Step 1 again before acting on any other row, since those rows read registrations from the file |
| `contract-env-vars` | Regenerate each script the detail names (Step 3); Step 4 drops the arguments from its registration |
| `contract-gate-true` | Step 4 removes the suffix from the gate registration |
| `contract-gate-missing` | Write each named gate from its `hook-scripts.md` section (Step 3; there is no old script). For `verify-on-stop.sh`, set `VERIFY_CMD=` to the fast check that CLAUDE.md `## Key Commands` names; when it names none, remove the Stop registration instead and say so. A gate with no section in `hook-scripts.md` is not a project-init hook: report it and leave it to the user |
| `contract-exit1`, `secret-scan-scope` | Regenerate `secret-scan.sh` (Step 3) |
| `doc-sync-scope` | Regenerate `check-doc-sync.sh` (Step 3) |
| `contract-yml-agents` | Convert each named agent to Markdown (Step 5) |

Step 4 runs whenever the list is not empty; rewriting a registration to its current string is idempotent and also fixes relative paths.

With `--dry-run`, print the list in the report format below, titled "Hook Migration Plan (dry run)", with the action each row would take, and stop.

## Step 2: Back Up

```bash
date +%Y%m%d-%H%M%S
```

Use its output as `<stamp>`:

```bash
mkdir -p .claude/backup-<stamp>
cp -R .claude/hooks .claude/settings.json .claude/backup-<stamp>/
```

Leave `.claude/hooks` out of the `cp` when it does not exist. When `.claude/agents` exists, also run `cp -R .claude/agents .claude/backup-<stamp>/`.

Then write `.claude/backup-<stamp>/.gitignore` with the single line `*`, so git never stages the backup and the commit-scope secret scan does not flag the pattern literals in the old `secret-scan.sh`. Do not delete the backup; the user decides when it goes.

## Step 3: Regenerate Hook Scripts

For each script on the migration list, write the fenced `bash` block from its `hook-scripts.md` section to `.claude/hooks/<name>.sh`. Before overwriting, carry the project's own values into the new script, since the old script is their only record:

- the `SOURCE_ROOTS` value of `check-doc-sync.sh`;
- entries in the old `PATTERNS` and `SKIP_PATTERNS` arrays that the template lacks;
- logic the project added that no project-init template had, such as a check on a path the template never mentions.

Leave out old template code, which is not a customization even where the new script lacks it:

- `PATTERNS`: the AWS secret pattern that starts `(?<=aws_secret_access_key` (python3 `re` rejects its variable-width lookbehind), `sk-ant-[A-Za-z0-9-]{90,}`, and the case-sensitive assignment patterns that start `password\s*[:=]`, `secret\s*[:=]`, and `api[_-]?key\s*[:=]`; the template has its own forms of these.
- `SKIP_PATTERNS`: `secret-scan.sh`, `.claude/hooks/secret-scan.sh`, `tests/fixtures/*`, `package-lock.json`, and `yarn.lock`, which the template's path-aware entries replace (`tests/fixtures/*` would skip every fixture file again).
- `check-doc-sync.sh`: the "No ADRs found" and "No runbooks found" blocks (dropped on purpose), the `# Default: src/, app/, lib/ | Plugin projects: plugins/` comment, and the `MESSAGES` and `printf` output code.
- `notify.sh`: the heredoc `PAYLOAD` and the `curl` call.
- `secret-scan.sh`: the `BLOCKED` echo lines, the staged-file loop, and the `grep -P` matching.
- the old header comments of every script.

When you are unsure whether a difference is a customization, keep it and list it in the report.

```bash
diff .claude/backup-<stamp>/hooks/<name>.sh .claude/hooks/<name>.sh
chmod +x .claude/hooks/*.sh
bash -n .claude/hooks/<name>.sh
```

Run `diff` and `bash -n` for each regenerated script. Every line the diff removes should be input or exit code the template replaces (arguments, environment variables, `exit 1`), old template code from the list above, or a value you carried over in a new form; anything else is a customization you dropped.

## Step 4: Rewrite settings.json Registrations

In `.claude/settings.json`, set the `command` of each registered project-init hook to its string below. Find the entry by script name, whatever its current form: a relative or absolute path, `"$TOOL_INPUT_PATH"`, `"$EVENT"`, or `"$MESSAGE"` arguments, or `2>/dev/null || true` on a gate. Leave permissions, matchers, and every other hook untouched, and add no hook that is not registered.

```text
PreToolUse (matcher Bash)         "command": "bash \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/secret-scan.sh"
PostToolUse (matcher Write|Edit)  "command": "bash \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/check-doc-sync.sh 2>/dev/null || true"
SessionStart                      "command": "bash \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/session-context.sh 2>/dev/null || true"
Notification                      "command": "bash \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/notify.sh 2>/dev/null || true"
Stop                              "command": "bash \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/verify-on-stop.sh"
```

These are the shapes in `settings-json-template.md`.

```bash
python3 -m json.tool .claude/settings.json > /dev/null
```

## Step 5: Convert Agents to Markdown

For each `.claude/agents/<name>.yml` or `.yaml`:

1. If `agents-templates.md` has a template for `<name>`, write that template to `.claude/agents/<name>.md`.
2. Otherwise, build `<name>.md` by hand: the non-comment YAML keys `name`, `description`, `tools`, and `color` become the frontmatter, with `tools` as plain tool names (`Bash(git diff:*)` becomes `Bash`), and the `# Output Schema` comment block, with the leading `# ` stripped, becomes the body. Leave `model` out so the agent follows `CLAUDE_CODE_SUBAGENT_MODEL` or the session model, and list the dropped value in the report in case the pin was deliberate.
3. Run `rm .claude/agents/<name>.yml` (or `.yaml`); the backup keeps a copy.

## Step 6: Verify

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/harness-check.sh --contract-only
bash ${CLAUDE_PLUGIN_ROOT}/scripts/harness-check.sh
echo '{"tool_input":{"command":"ls"}}' | bash .claude/hooks/secret-scan.sh; echo "exit=$?"
echo '{"tool_input":{"file_path":"src/__probe__/file.ts"}}' | bash .claude/hooks/check-doc-sync.sh
```

Expected:

- The first exits 0 with no FAIL or WARN line.
- In the second, no `hook-reg-*` line says "not anchored" or "absolute path"; such a line is a registration Step 4 missed.
- The third prints only `exit=0`.
- Run the fourth with the first `SOURCE_ROOTS` entry in place of `src`. It prints a JSON line whose `additionalContext` names `<root>/__probe__/CLAUDE.md`, or nothing when `<root>/CLAUDE.md` exists, since that file covers every module below it.

Then check that the gate blocks a commit holding a secret, in a scratch repository so the project's own index is untouched:

```bash
d=$(mktemp -d) && git init -q "$d" && printf 'token = "%s%s"\n' ghp_ "$(printf '%036d' 0)" > "$d/probe.py" && git -C "$d" add probe.py && echo "$d"
```

```bash
(cd <printed dir> && CLAUDE_PROJECT_DIR=<printed dir> bash <project root>/.claude/hooks/secret-scan.sh 'git commit -m probe'); echo "exit=$?"
```

Expected: a stderr line naming `probe.py`, then `exit=2`. `exit=0` with a python3 warning means python3 is missing and the gate lets every commit through: report it. Leave the scratch directory in place; it is in the system temp directory.

If `tests/run-all.sh` exists, run `bash tests/run-all.sh` too. If `tests/hooks/test-hooks.sh` has no assertion that `secret-scan.sh` exits 2 on a commit with a secret, the old hook tests do not check the current contract: say so in the report and suggest regenerating `tests/hooks/` from `tests-templates.md`, but do not overwrite them, because they are the user's files.

If a check fails, fix the regenerated file and run the checks again. If you cannot make it pass, copy the affected file back from `.claude/backup-<stamp>/` and report what failed.

## Step 7: Report

One row per file changed. The values below are illustrative.

```
## Hook Migration Report

Backup: .claude/backup-20260923-101500/ (git-ignored; delete it once the migration is verified)

| Item | Action |
|------|--------|
| .claude/hooks/secret-scan.sh | regenerated (commit-scope scan, exit 2); kept custom PATTERNS: 'INTERNAL-[0-9]{8}' |
| .claude/hooks/check-doc-sync.sh | regenerated (first-level module coverage, stdin JSON, additionalContext); kept SOURCE_ROOTS="services lib" |
| .claude/settings.json | 3 hook commands rewritten to "$CLAUDE_PROJECT_DIR" paths; gate suffix removed |
| .claude/agents/code-reviewer.yml | converted to code-reviewer.md; dropped model: sonnet |
| Kept, possibly customized | none |
| Old hook tests | tests/hooks/test-hooks.sh does not check the exit-2 gate; regenerate it from tests-templates.md |

Verification: harness-check --contract-only exit 0; registrations anchored; secret-scan blocked the probe commit (exit 2); tests/run-all.sh passed

Restart the Claude Code session so the new hook registrations take effect.
Run /project-init:health-check to confirm.
```
