---
description: Configure the co-agent panel — host-aware peer AI model, effort, enable/disable, and timeout
allowed-tools: Bash(python3:*), Read
argument-hint: "show | set <ai> <key> <value> | set timeout <seconds>  (host: claude|codex; ai: kiro-cli|claude|codex|agy)"
---

# co-agent: configure

Configure the host-aware multi-AI panel. Settings are **layered** like Claude Code's own
settings — precedence low→high:

- `co-agent.defaults.json` (committed, in the skill) — base/shared
- `~/.claude/co-agent.user.json` (**user scope** — applies across all your repos) — written with `--scope user`
- `<repo>/.claude/co-agent.local.json` (gitignored, this repo only) — default write target

`set` writes to the **repo-local** scope by default; add `--scope user` to write the
user-global file instead (repo-local still overrides user, user overrides defaults).
(Override the user-file path with `$CO_AGENT_USER_CONFIG`.)

Only options the CLIs **actually accept headlessly** are exposed (no dead settings):

| Setting | kiro-cli | claude | codex | agy |
|---------|------|--------|-------|-----|
| `model` | `--model` | `--model` | `-m` | `--model` |
| `effort` | — | `--effort` (`low\|medium\|high\|xhigh\|max`) | `-c model_reasoning_effort` (`minimal\|low\|medium\|high`) | — |
| `enabled` (panel membership) | yes | yes | yes | yes |
| `timeout` (global, seconds) | yes | yes | yes | yes |
| `context_limit` (per-AI, tokens) | model context window — fan-out **skips** an AI whose window can't hold the context (default: Kiro/Claude/Agy 1,000,000 · Codex 272,000) |
| `autosync` (global, on/off) | run `/co-agent:sync-context` automatically when `CLAUDE.md` changes (opt-in; default off) |

Host controls panel membership:

- `--host claude` (default): Claude chairs; panel = Kiro, Codex, Agy.
- `--host codex`: Codex chairs; panel = Kiro, Claude, Agy.
- The third reviewer is always Agy — Gemini support was removed (Agy superseded it; ADR-010).

The fan-out in `references/ai-cli-adapters.md` reads these via the helper, so a change
here changes what actually runs (e.g. `enabled false` drops that AI from the panel).

## Helper

All operations go through `skills/co-agent/scripts/co_agent_config.py` (run with the
plugin path; `--root` defaults to the cwd / repo root):

```bash
H="${CLAUDE_PLUGIN_ROOT}/skills/co-agent/scripts/co_agent_config.py"
HOST="${CO_AGENT_HOST:-claude}"
```

## Behaviour

Argument: `$ARGUMENTS`

1. **No args or `show`** → print the effective merged config:
   ```bash
   python3 "$H" show --host "$HOST"
   ```
2. **`set <ai> <key> <value>`** → validate + write to `.claude/co-agent.local.json`,
   then show the result. Examples:
   ```bash
   python3 "$H" set codex model gpt-5-codex     # Codex model
   python3 "$H" set codex effort high           # Codex reasoning effort
   python3 "$H" set claude model sonnet --host codex
   python3 "$H" set claude effort max --host codex
   python3 "$H" set agy model default
   python3 "$H" set kiro-cli  model claude-opus-4.8 # Kiro model (see `kiro-cli chat --list-models`)
   python3 "$H" set agy enabled false           # drop Agy from the panel
   python3 "$H" set timeout 300                 # global per-CLI timeout (s)
   python3 "$H" set codex context_limit 400000  # raise/lower a model's context window
   python3 "$H" set autosync on                 # auto-sync AI context on CLAUDE.md change
   python3 "$H" set codex model gpt-5.5 --scope user   # write to ~/.claude (all your repos)
   python3 "$H" set agy model "Gemini 3.1 Pro (High)"  # Agy tokens have spaces + parens
   python3 "$H" set kiro-cli models claude-opus-4.8,kimi-k2.5,glm-5  # multi-model list
   python3 "$H" set profile deep                # activate each AI's `models` list
   python3 "$H" set harness implementer agy     # harness implementer (codex|agy)
   python3 "$H" set harness review_mode relay    # harness gate: hybrid (default) | relay | parallel
   python3 "$H" set harness parallel_tasks 3     # harness implement wave size (1 = sequential)
   ```
   `context_limit` lets the fan-out **skip** an AI when the context is too large for its
   model window (the cause of "prompt tokens exceed model maximum"), instead of hard-failing
   — e.g. Codex (~272K) is skipped on a huge diff while Kiro/Agy (~1M) still run. `model`
   values are charset-validated (letters/digits/`. _ : / - ( )` + spaces — agy tokens like
   `Gemini 3.1 Pro (High)`; shell metacharacters stay rejected) to keep the fan-out safe.
   **Multi-model = 다방향 검증**: with `profile deep` (the committed default), every model
   in an AI's `models` list becomes its own `(ai, model)` fan-out/relay link — one gate pass
   verifies from each configured model's direction, capped by `consensus.max_calls`. All
   overrides ride the CLIs' real headless flags (kiro/claude/agy `--model`, codex `-m`), so
   this works fully non-interactively; see `references/hybrid-gate.md` (default gate) and
   `references/relay-chain-gate.md` → "Multi-model relay" for how the gates use them.
   `autosync on` makes the `CLAUDE.md` PostToolUse hook tell Claude to run
   `/co-agent:sync-context` whenever `AGENTS.md` drifts stale (opt-in; default
   off = reminder only). It refreshes `AGENTS.md` and the Kiro steering bridge;
   first-time generation is still done by running the command once.
3. If the user asks for a setting that isn't headless-settable (e.g. Agy effort),
   explain why it's not offered and suggest the closest real lever (model, or run
   that AI interactively). Do **not** invent a setting that the CLI ignores.
4. For Kiro model values, you may enumerate valid models with
   `kiro-cli chat --list-models --format json` and show the user the choices.

Always finish by echoing the effective config (`python3 "$H" show --host "$HOST"`) so the user sees
exactly what the panel will use.
