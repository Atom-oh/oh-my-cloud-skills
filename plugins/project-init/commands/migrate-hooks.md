---
description: Migrate hooks, settings.json, and agents generated before v2.3 to the current Claude Code hook contract (stdin JSON, exit 2, Markdown subagents)
allowed-tools: Read, Write, Edit, Bash(mkdir:*), Bash(cp:*), Bash(mv:*), Bash(ls:*), Bash(chmod:*), Bash(diff:*), Bash(grep:*), Bash(date:*), Bash(bash -n:*), Bash(python3 -m json.tool:*), Glob, Grep
argument-hint: Optional --dry-run to report what would change without writing
---

# Migrate Hooks to the v2.3 Contract

Projects initialized with project-init before v2.3 carry hooks and agents that Claude Code never runs:

- `check-doc-sync.sh` and `notify.sh` read `$TOOL_INPUT_PATH`, `$EVENT`, `$MESSAGE`; Claude Code passes hook events as JSON on stdin and sets none of those variables
- `secret-scan.sh` exits 1 inside `|| true`; only exit 2 blocks, so the gate never blocked a commit
- `.claude/agents/*.yml` files are ignored; subagents must be Markdown with YAML frontmatter

This command replaces them with the current templates while keeping a backup. Everything it changes lives in the consuming project, so plugin updates alone cannot fix it.

Mode: $ARGUMENTS (`--dry-run` reports only; default applies changes)

## Step 1: Detect What Needs Migration

```bash
grep -l 'TOOL_INPUT_PATH\|\$EVENT\|\$MESSAGE' .claude/settings.json .claude/hooks/*.sh 2>/dev/null
grep -n 'secret-scan.sh.*|| true' .claude/settings.json 2>/dev/null
grep -L 'tool_input' .claude/hooks/check-doc-sync.sh .claude/hooks/secret-scan.sh 2>/dev/null
grep -n 'exit 1' .claude/hooks/secret-scan.sh 2>/dev/null
ls .claude/agents/*.yml .claude/agents/*.yaml 2>/dev/null
```

Build the migration list from the results:

| Finding | Action |
|---------|--------|
| `settings.json` passes `$TOOL_INPUT_PATH` / `$EVENT` / `$MESSAGE` | Rewrite the hook command strings |
| `secret-scan.sh` registered with `\|\| true` | Drop `2>/dev/null \|\| true` from that registration only |
| A hook script does not contain `tool_input` | Regenerate that script from the template |
| `secret-scan.sh` uses `exit 1` | Regenerate that script from the template |
| `.claude/agents/*.yml` exists | Convert to `.md` |

If the list is empty, report "Already on the v2.3 hook contract" and stop. With `--dry-run`, print the list and stop.

## Step 2: Back Up

```bash
BACKUP=".claude/backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP"
cp -r .claude/hooks "$BACKUP/" 2>/dev/null
cp .claude/settings.json "$BACKUP/" 2>/dev/null
[ -d .claude/agents ] && cp -r .claude/agents "$BACKUP/"
```

Tell the user the backup path. Do not delete it; the user decides when it goes.

## Step 3: Regenerate Hook Scripts

Read [references/hook-scripts.md](../skills/project-scaffolder/references/hook-scripts.md). For each hook on the migration list, extract the fenced `bash` block for that script and write it to `.claude/hooks/<name>.sh`.

Before overwriting, compare the old script with the original v2.2 template shape:

- If the old script only differs from the template in the parts this migration replaces (stdin reading, exit code, echo vs. `additionalContext`), overwrite silently.
- If it contains project-specific edits (different `SOURCE_ROOTS`, extra patterns in `PATTERNS`, extra `SKIP_PATTERNS`), carry those values into the regenerated script and list them in the report.

```bash
chmod +x .claude/hooks/*.sh
bash -n .claude/hooks/check-doc-sync.sh && bash -n .claude/hooks/secret-scan.sh
```

## Step 4: Rewrite settings.json Registrations

Edit only the `command` strings; leave permissions and any custom hooks untouched.

```diff
- "command": "bash .claude/hooks/secret-scan.sh 2>/dev/null || true"
+ "command": "bash .claude/hooks/secret-scan.sh"
- "command": "bash .claude/hooks/check-doc-sync.sh \"$TOOL_INPUT_PATH\" 2>/dev/null || true"
+ "command": "bash .claude/hooks/check-doc-sync.sh 2>/dev/null || true"
- "command": "bash .claude/hooks/notify.sh \"$EVENT\" \"$MESSAGE\" 2>/dev/null || true"
+ "command": "bash .claude/hooks/notify.sh 2>/dev/null || true"
```

```bash
python3 -m json.tool .claude/settings.json > /dev/null
```

## Step 5: Convert Agents to Markdown

For each `.claude/agents/<name>.yml`:

1. If [references/agents-templates.md](../skills/project-scaffolder/references/agents-templates.md) has a template for `<name>`, write that template to `.claude/agents/<name>.md`.
2. Otherwise, build `<name>.md` by hand: the non-comment YAML lines become the frontmatter (`name`, `description`, `tools`, `model`, `color`), and the `# Output Schema` comment block, with the leading `# ` stripped, becomes the Markdown body.
3. Remove the `.yml` file (the backup keeps a copy).

## Step 6: Verify

```bash
echo '{"tool_input":{"file_path":"src/newmodule/file.ts"}}' | bash .claude/hooks/check-doc-sync.sh
echo '{"tool_input":{"command":"ls"}}' | bash .claude/hooks/secret-scan.sh; echo "exit=$?"
```

Expected: the first prints a JSON line with `additionalContext` when `src/newmodule/CLAUDE.md` is missing (or nothing when it exists); the second prints nothing and `exit=0`. Adjust the sample path to the project's actual source root if `src/` does not apply.

## Step 7: Report

```
## Hook Migration Report

Backup: .claude/backup-YYYYMMDD-HHMMSS/

| Item | Action |
|------|--------|
| .claude/hooks/check-doc-sync.sh | regenerated (stdin JSON, additionalContext) |
| .claude/hooks/secret-scan.sh | regenerated (git commit gate, exit 2); kept custom PATTERNS: <n> |
| .claude/settings.json | 3 hook commands rewritten |
| .claude/agents/code-reviewer.yml | converted to code-reviewer.md |

Restart the Claude Code session so the new hook registrations take effect.
Run /health-check to confirm no pre-v2.3 findings remain.
```

If `--dry-run` was given, title the report "Hook Migration Plan (dry run)" and list the same rows with the action that would be taken.
