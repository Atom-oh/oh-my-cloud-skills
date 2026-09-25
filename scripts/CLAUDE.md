# scripts/

Evaluation, host-adapter generation and repository utilities. This is an existing
plugin marketplace, not an application scaffold. Maintain English prose and derive
commands from the scripts here; do not create dummy application/configuration files.

## Files

| Script | Purpose |
|--------|---------|
| `eval-skills.py` | Evaluate skill quality (structure, token usage, scoring) |
| `eval-skill-behavior.py` | E2E behavioral testing via `claude --print` |
| `test-plugins.py` | Validate Claude manifests and file references |
| `test-codex-plugins.py` | Validate every Codex manifest, source inventory and component path |
| `sync-codex-plugins.py` | Generate all Codex adapters; `--check` rejects missing or stale outputs |
| `test-codex-runtime.py` | Check actual disposable Codex installation and discovery |
| `test-codex-native-hooks.py` | Execute native hook fixtures; `--project-init` includes project templates |
| `sync-plugin-cache.sh` | Sync plugin cache for marketplace |
| `setup.sh` | One-command project setup for new developers |
| `install-hooks.sh` | Install Git commit-msg hook |
| `pr-review/` | Trusted-base CI prechecks, panel orchestration and review publication |

## Validator scope

Source-mirror discovery does not authorize a Codex publication exception or source fork:

| Constant | Script | Means |
|----------|--------|-------|
| `MIRRORED_PLUGINS` | `test-plugins.py` | plugin.json preserves upstream fields except the shared release version, so `agents`/`skills` may be absent — they're discovered from `agents/*.md` and `skills/*/SKILL.md` instead, and a mirror with neither the field nor any file on disk is an error |

`MIRRORED_PLUGINS` contains `project-init` and remains applicable after Codex
publication. The Codex validator requires every plugin's manifest and marketplace
entry; the temporary `CLAUDE_ONLY` staging exception has been removed.

All registered plugins provide Codex overlays. Keep adaptation tooling outside upstream-owned
files and regenerate after source updates. L1 executes trusted-base structural validators
against the archived PR tree as data; it never executes PR-supplied scripts. Generation
freshness runs separately in GitHub-hosted `pull_request` CI using that PR's generator and
outputs. The job has a read-only repository token, does not persist checkout credentials,
and receives no provider secrets. It does not run on the privileged cloud review runner.

A generator logic change and its regenerated outputs belong in the same PR. Both the
local full-checkout gate and the separate CI check always cover all plugins, including
missing or downgraded manifests. No generator-change exception skips freshness. Structural
success does not substitute for installed runtime and native hook verification.

**Agent `tools:` scopes.** `Bash(git log:*)` is accepted (upstream's mirrored
`doc-sync-checker` uses it) but **warns** — the scope syntax is documented for a command's
`allowed-tools`, not verified for a subagent's `tools:`, so it's treated as a full `Bash`
grant. A scope item that grants everything (`*`, `*:*`, `:*` — the last has an empty
prefix) is an **error**: it reads as narrowed while granting everything.

Mandatory CI review validates final Issues for the latest HEAD; the chair, informed
of any degraded coverage before it decides, is the judgment on whether that gap
still permits PASS (ADR-026), not a separate mechanical coverage check. The
semantic acceptance helper is
`plugins/co-agent/skills/pr-autofix/scripts/review_gate.py`; a lexical PASS or an
optional local hook skip cannot replace that result or separate Codex package CI.

## Running

```bash
python3 scripts/eval-skills.py
python3 scripts/eval-skills.py --skill reactive-presentation   # selects by SKILL name only (no --plugin flag)
python3 scripts/test-plugins.py
python3 scripts/test-codex-plugins.py
python3 scripts/sync-codex-plugins.py --check
```
