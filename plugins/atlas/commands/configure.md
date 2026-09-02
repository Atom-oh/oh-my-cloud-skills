---
description: Show or change atlas settings — wiki root, push-time sync toggle, fixer model, timeout, parallelism — via the layered config
allowed-tools: Read, Bash
argument-hint: show | set root <path> | set sync <on_push|model|timeout|parallel> <value>
---

# atlas: configure

Read or change this repo's atlas settings through `atlas_config.py`, so the user ends
up with a validated effective config and understands any consent implications of what
they changed. Never edit the config files by hand when the script can do it — the
script validates values and refuses symlink-tricked write paths.

Resolve paths first:

```bash
SK="${CLAUDE_PLUGIN_ROOT}/skills/atlas/scripts"
ROOT="$(git rev-parse --show-toplevel)"
```

`--root` takes the REPOSITORY root, never the wiki directory. Pass `--root "$ROOT"`
on every call; it may appear anywhere in the argv.

## Layering

Two files, merged in order (`atlas.defaults.json` <- `.claude/atlas.local.json`):

| Layer | File | Role |
|---|---|---|
| base | `atlas.defaults.json` (ships inside `skills/atlas/`, alongside `SKILL.md`) | shipped defaults |
| override | `<repo>/.claude/atlas.local.json` | personal, per-repo, gitignored |

`set` writes only the override file. A malformed override is reported and ignored,
never a crash.

## Commands

Map `$ARGUMENTS` onto one of these (bare `/atlas:configure` means `show`):

```bash
python3 "$SK/atlas_config.py" show --root "$ROOT"                          # effective merged config
python3 "$SK/atlas_config.py" set root <path> --root "$ROOT"               # wiki directory, repo-relative
python3 "$SK/atlas_config.py" set sync on_push <on|off> --root "$ROOT"     # push-time auto-sync gate
python3 "$SK/atlas_config.py" set sync model <m|default> --root "$ROOT"    # fixer model (default/null clears)
python3 "$SK/atlas_config.py" set sync timeout <seconds> --root "$ROOT"    # per-doc headless-call timeout
python3 "$SK/atlas_config.py" set sync parallel <n> --root "$ROOT"         # concurrent headless calls
python3 "$SK/atlas_config.py" sync-on-push --root "$ROOT"                  # exit 0 if on, 1 if off
python3 "$SK/atlas_config.py" atlas-root --root "$ROOT"                    # effective wiki dir, repo-relative
python3 "$SK/atlas_config.py" sync-model --root "$ROOT"                    # effective model (empty = default)
python3 "$SK/atlas_config.py" sync-timeout --root "$ROOT"                  # effective timeout in seconds
python3 "$SK/atlas_config.py" sync-parallel --root "$ROOT"                 # effective parallelism
```

## Keys

| Key | Default | Meaning / validation |
|---|---|---|
| `root` | `docs/atlas` | Wiki directory, repo-relative. Also the fixer's write-and-commit scope, so absolute paths and `..` segments are refused. |
| `sync.on_push` | `false` | Auto-fix drifted docs just before `git push`. **Consent gate — see below.** Accepts on/off/true/false/1/0/yes/no. |
| `sync.model` | `null` | Model for the headless fixer call; `default` or `null` clears it. Letters, digits, spaces and `. _ : / ( ) -` only — no shell metacharacters. |
| `sync.timeout` | `300` | Seconds per headless call. Positive integer. |
| `sync.parallel` | `3` | Concurrent headless calls. Positive integer. |

## The consent key: `sync.on_push`

Turning `sync.on_push` on IS the consent to send covered-file diff content to
Anthropic on every push — there is no per-push prompt afterwards. State that plainly
before running the `set` for a user who asked to enable it.

**A git-tracked `.claude/atlas.local.json` cannot enable `sync.on_push`.** That one
key is stripped when the override file is tracked (or reached through a symlink
alias), because the pre-push hook is registered at plugin-load time: a repo that
committed `"on_push": true` would otherwise silently opt every installing user's
every push into that data egress, a consent none of them gave. The strip is scoped:
every OTHER key (`root`, `sync.model`, `sync.timeout`, `sync.parallel`) still applies
from a tracked file — those are configuration, not a consent bypass. If `show` prints
a tracked-override warning, tell the user to untrack the file
(`git rm --cached .claude/atlas.local.json`) and gitignore it, then set the toggle
locally.

## Bypass without reconfiguring

For one push with the toggle left on, prefix the push command instead of flipping
config back and forth:

```bash
ATLAS_SYNC=off git push origin main
```

## Report

After any `set`, run `show` and echo the effective config back to the user, including
any warnings the script printed on stderr (tracked override, coerced values) — those
warnings are the interesting part of the output.
