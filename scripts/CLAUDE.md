# scripts/

Evaluation and utility scripts for the plugin marketplace.

## Files

| Script | Purpose |
|--------|---------|
| `eval-skills.py` | Evaluate skill quality (structure, token usage, scoring) |
| `eval-skill-behavior.py` | E2E behavioral testing via `claude --print` |
| `test-plugins.py` | Validate plugin manifests and file references |
| `sync-plugin-cache.sh` | Sync plugin cache for marketplace |
| `setup.sh` | One-command project setup for new developers |
| `install-hooks.sh` | Install Git commit-msg hook |

## Validator exceptions (independent source and publication scopes)

These exceptions govern different surfaces; neither authorizes weaker validation
or a source fork:

| Constant | Script | Means |
|----------|--------|-------|
| `MIRRORED_PLUGINS` | `test-plugins.py` | plugin.json is an upstream mirror kept verbatim, so `agents`/`skills` may be absent — they're discovered from `agents/*.md` and `skills/*/SKILL.md` instead, and a mirror with neither the field nor any file on disk is an error |
| `CLAUDE_ONLY` | `test-codex-plugins.py` | temporarily permits an unpublished adapter's absence. A present Codex manifest is validated normally; a marketplace entry without its manifest is still an error |

Both currently name `project-init`, but their membership need not stay coupled.
`MIRRORED_PLUGINS` concerns upstream source conventions and remains applicable after
Codex publication. `CLAUDE_ONLY` is a staging exception, not a permanent platform
policy: once the generated overlay and entry ship, it must not excuse missing Codex
delivery. Historical "keep in sync" comments do not extend its scope.

All eight plugins are approved for Codex support. Keep adaptation tooling outside
upstream-owned files, and generate project-init's separate `.codex-plugin/` overlay
when the factory is available. Current validator success does not establish that
every adapter or host workflow has been published and verified.

**Agent `tools:` scopes.** `Bash(git log:*)` is accepted (upstream's mirrored
`doc-sync-checker` uses it) but **warns** — the scope syntax is documented for a command's
`allowed-tools`, not verified for a subagent's `tools:`, so it's treated as a full `Bash`
grant. A scope item that grants everything (`*`, `*:*`, `:*` — the last has an empty
prefix) is an **error**: it reads as narrowed while granting everything.

## Running

```bash
python3 scripts/eval-skills.py
python3 scripts/eval-skills.py --skill reactive-presentation   # selects by SKILL name only (no --plugin flag)
python3 scripts/test-plugins.py
```
