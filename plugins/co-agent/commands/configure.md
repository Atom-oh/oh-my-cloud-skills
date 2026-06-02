---
description: Configure the co-agent panel — per-AI model, Codex reasoning effort, enable/disable, and timeout
allowed-tools: Bash(python3:*), Read
argument-hint: "show | set <ai> <key> <value> | set timeout <seconds>  (ai: kiro|codex|gemini)"
---

# co-agent: configure

Configure the multi-AI panel. Settings are **layered** like Claude Code's own settings:

- `co-agent.defaults.json` (committed, in the skill) — base
- `<repo>/.claude/co-agent.local.json` (gitignored) — personal/per-repo override written here

Only options the CLIs **actually accept headlessly** are exposed (no dead settings):

| Setting | kiro | codex | gemini |
|---------|------|-------|--------|
| `model` | `--model` | `-m` | `-m` |
| `effort` (`minimal\|low\|medium\|high`) | — | `-c model_reasoning_effort` | — |
| `enabled` (panel membership) | ✅ | ✅ | ✅ |
| `timeout` (global, seconds) | ✅ | ✅ | ✅ |
| `autosync` (global, on/off) | run `/co-agent:sync-context` automatically when `CLAUDE.md` changes (opt-in; default off) |

> `effort` is **Codex-only** — Gemini and Kiro have no headless reasoning-effort flag
> (`/effort` is interactive-only), so it isn't offered for them.

The fan-out in `references/ai-cli-adapters.md` reads these via the helper, so a change
here changes what actually runs (e.g. `enabled false` drops that AI from the panel).

## Helper

All operations go through `skills/co-agent/scripts/co_agent_config.py` (run with the
plugin path; `--root` defaults to the cwd / repo root):

```bash
H="${CLAUDE_PLUGIN_ROOT}/skills/co-agent/scripts/co_agent_config.py"
```

## Behaviour

Argument: `$ARGUMENTS`

1. **No args or `show`** → print the effective merged config:
   ```bash
   python3 "$H" show
   ```
2. **`set <ai> <key> <value>`** → validate + write to `.claude/co-agent.local.json`,
   then show the result. Examples:
   ```bash
   python3 "$H" set codex model gpt-5-codex     # Codex model
   python3 "$H" set codex effort high           # Codex reasoning effort
   python3 "$H" set kiro  model claude-opus-4.8 # Kiro model (see `kiro-cli chat --list-models`)
   python3 "$H" set gemini enabled false        # drop Gemini from the panel
   python3 "$H" set timeout 300                 # global per-CLI timeout (s)
   python3 "$H" set autosync on                 # auto-sync AI context on CLAUDE.md change
   ```
   `autosync on` makes the `CLAUDE.md` PostToolUse hook tell Claude to run
   `/co-agent:sync-context` whenever the generated files drift stale (opt-in; default
   off = reminder only). It refreshes existing `AGENTS.md`/`GEMINI.md`; first-time
   generation is still done by running the command once.
3. If the user asks for a setting that isn't headless-settable (e.g. Gemini effort),
   explain why it's not offered and suggest the closest real lever (model, or run
   that AI interactively). Do **not** invent a setting that the CLI ignores.
4. For Kiro model values, you may enumerate valid models with
   `kiro-cli chat --list-models --format json` and show the user the choices.

Always finish by echoing the effective config (`python3 "$H" show`) so the user sees
exactly what the panel will use.
