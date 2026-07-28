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

## Validator allowlists (two, kept in sync)

Both validators carry one named exception, and neither is a blanket relaxation — anything
not listed still fails:

| Constant | Script | Means |
|----------|--------|-------|
| `MIRRORED_PLUGINS` | `test-plugins.py` | plugin.json is an upstream mirror kept verbatim, so `agents`/`skills` may be absent — they're discovered from `agents/*.md` and `skills/*/SKILL.md` instead, and a mirror with neither the field nor any file on disk is an error |
| `CLAUDE_ONLY` | `test-codex-plugins.py` | deliberately off the Codex surface: no `.codex-plugin/plugin.json` and no Codex marketplace entry. Any other plugin missing that manifest is an error, and a leftover marketplace entry for a listed plugin is an error once its manifest is gone |

Both currently hold `project-init` only. Add a plugin to one and you almost always want the
other too.

**Agent `tools:` scopes.** `Bash(git log:*)` is accepted (upstream's mirrored
`doc-sync-checker` uses it) but **warns** — the scope syntax is documented for a command's
`allowed-tools`, not verified for a subagent's `tools:`, so it's treated as a full `Bash`
grant. A scope item that grants everything (`*`, `*:*`, `:*` — the last has an empty
prefix) is an **error**: it reads as narrowed while granting everything.

## Running

```bash
python3 scripts/eval-skills.py
python3 scripts/eval-skills.py --plugin aws-content-plugin --skill reactive-presentation
python3 scripts/test-plugins.py
```
