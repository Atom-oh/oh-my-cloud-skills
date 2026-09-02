---
description: Configure the co-agent panel — host-aware peer AI model, effort, enable/disable, and timeout
allowed-tools: Bash(python3:*), Read
argument-hint: "show | set <ai> <key> <value> | set timeout <seconds>  (host: claude|codex; ai: kiro-cli|claude|codex|agy)"
---

# co-agent: configure

Inspect and change what the multi-AI panel actually runs with — models, effort, panel
membership, timeouts, and the harness / pr-autofix / push-gate knobs. Every write lands in
a layered config that the fan-out (`references/ai-cli-adapters.md`) reads live via
`co_agent_config.py`, so a change here changes the very next panel call (e.g.
`enabled false` drops that AI from the panel). Excellent means the user leaves seeing the
effective merged config and never believes a dead setting took effect.

Settings are **layered** like Claude Code's own settings — precedence low→high:

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
   python3 "$H" set codex model openai.gpt-5.6-sol --scope user   # write to ~/.claude (all your repos)
   python3 "$H" set agy model "Gemini 3.1 Pro (High)"  # Agy tokens have spaces + parens
   python3 "$H" set kiro-cli models claude-opus-4.8,minimax-m2.5  # multi-model list
   python3 "$H" set profile deep                # activate each AI's `models` list
   python3 "$H" set harness implementer agy     # harness implementer (codex|agy)
   python3 "$H" set harness review_mode relay    # harness gate: hybrid (default) | relay | parallel
   python3 "$H" set harness parallel_tasks 3     # harness implement wave size (1 = sequential)
   python3 "$H" set harness max_fix_rounds 2     # harness per-task peer fix-loop bound
   python3 "$H" set harness implementer_model gpt-5.3-codex-mini  # write-path model (stored per implementer — set implementer first)
   python3 "$H" set harness implementer_effort low                # write-path effort (only when implementer is codex)
   python3 "$H" set pr_autofix max_iterations 5  # cap on the /co-agent:pr-autofix review-fix-push loop
   python3 "$H" set push_gate enabled on         # 3-lens pre-push gate (correctness/security/scope) — enabling = consent to external transmission
   python3 "$H" set push_gate block off          # advisory-only (does not block, just prints findings)
   python3 "$H" set push_gate timeout 180        # shared per-round timeout (seconds)
   ```
   Key semantics:
   - `context_limit` — the fan-out **skips** an AI whose model window can't hold the
     context (the cause of "prompt tokens exceed model maximum") instead of hard-failing:
     e.g. Codex (~272K) is skipped on a huge diff while Kiro/Agy (~1M) still run.
   - `model` values are charset-validated (letters/digits/`. _ : / - ( )` + spaces — agy
     tokens like `Gemini 3.1 Pro (High)`; shell metacharacters stay rejected) to block
     fan-out injection.
   - `profile deep` (the committed default) makes every model in an AI's `models` list its
     own `(ai, model)` fan-out/relay link — one gate pass verifies from each configured
     model's direction, capped by `consensus.max_calls`. All overrides ride the CLIs' real
     headless flags, so this works fully non-interactively; gate usage:
     `references/hybrid-gate.md` (default gate) and `references/relay-chain-gate.md` → "Multi-model relay".
   - `pr_autofix max_iterations` bounds the `/co-agent:pr-autofix` review→fix→push loop
     (positive int, default 5). It's a config knob rather than a skill constant because the
     right bound tracks how noisy the repo's review CI is; the skill reads it via
     `co_agent_config.py pr-autofix-iterations`.
   - `push_gate enabled on` turns on the `git push` PreToolUse gate
     (`consensus_hooks.py pre-push-gate`). Unlike `pr_gate` (hand-edited in the JSON file
     directly, no `set` path), `push_gate` is `set`-able because this is where the user is
     meant to opt in — **enabling is consent to external fan-out**, same as `pr_gate`. If
     kiro's own `review.on_push` is ALSO on for this repo, warn that both gates firing
     means every push runs two independent review rounds (not recommended, not blocked).
     Gate mechanics (3 lenses, verdict thresholds) are canonical in the plugin `CLAUDE.md`
     → "Pre-push Lens Gate".
   - `autosync on` makes the `CLAUDE.md` PostToolUse hook tell Claude to re-run
     `/co-agent:sync-context` when `AGENTS.md` drifts stale (default off = reminder only;
     first-time generation is still done by running the command once).
3. If the user asks for a setting that isn't headless-settable (e.g. Agy effort), explain
   why it's not offered and point at the closest real lever (model, or run that AI
   interactively).
4. For Kiro model values, you may enumerate valid models with
   `kiro-cli chat --list-models --format json` and show the user the choices.

## Role-based model tiering

Instead of using the same model for every role, assign a cost-efficient model per role —
the same principle as Opusplan splitting plan (Opus) from execution (Sonnet). There are 4
placement points:

| Role | Character | Lever | Recommendation |
|------|------|------|------|
| **Chair** (triage/synthesis/final verdict) | narrow and strong | Host model: `/model opusplan` (plan=Opus·execute=Sonnet), or spawn the `gate-chair` subagent (`agents/gate-chair.md`, `model: opus`) | Keep a strong judgment model here — economizing here weakens the entire gate |
| **Find panel** (hybrid gate F phase) | wide and cheap | `profile deep` + a low-cost model in each AI's `models` list (e.g. kiro `minimax-m2.5`) | Discovery is driven by diversity of perspective — model count matters more than per-model cost |
| **Verify panel** (V phase) | narrow and strong | The gate automatically uses `pairs --profile default` — each AI's single `model` becomes the verify model | Set `model` to each AI's strongest tier |
| **Implementer** (harness write path) | generation-focused | `set harness implementer <ai>` + `implementer_model <m>` / `implementer_effort <e>` (falls back to the panel's `model`/`effort` if unset) | For a subscription (flat-rate) CLI (the default assumption), use **that CLI's strongest generation model** — fewer fix rounds directly saves wall-clock time. Only lower to a cheaper model when metered billing applies, and use the review gate as a backstop |

- **`effort` is not phase-split** (easy to trip on silently): the panel `effort` (codex)
  applies identically to review calls in **both** find and verify — `--profile` only
  splits the model pairing. So `set codex effort low` to cheapen find also drops verify to
  low, breaking the "verify = strongest tier" placement. Keep the panel `effort` at the
  verify-appropriate level and lower only the write path via `implementer_effort`.
- `implementer_model`/`implementer_effort` apply **only to impl-flags (the write path)**
  and are **stored per implementer** (`harness.implementer_models.<ai>` /
  `implementer_efforts.<ai>`), keyed by the explicit `harness.implementer` at set time —
  so `implementer` must be set first (exits with code 2 if unset). After switching with
  `set harness implementer <other>`, the previous AI's entry stays dormant and never leaks
  into another CLI's `--model` (reused when you switch back; `show` marks active/dormant;
  re-validated at emit time). `implementer_effort` is codex-only — refused outright when
  the implementer is agy (agy's headless CLI has no effort flag). The review/gate path
  (`flags`) keeps the panel settings, so the same AI (codex) can review on a strong model
  and implement on a cheap one.
- `pairs`/`matrix`'s `--profile default|deep` is a per-call override the hybrid gate uses
  to split find (deep) from verify (default) — it never touches the config file. Detailed
  flow: "Role tiering" in `references/hybrid-gate.md`.
- **Billing is a per-peer property, not global**: under a flat-rate subscription (the
  usual case for the Claude Code host's kiro/codex/agy panel), marginal token cost ≈ 0, so
  tiering buys **(1) wall-clock** (strong generation model = fewer fix rounds), **(2)
  rate-limit quota** (the real scarce resource — the usage window), and **(3) chair triage
  noise** — not dollars. This flips per peer: under a Codex host, the Claude peer
  (`claude -p`, see adapters) may be API-key metered — for that peer the cheap-model-for-
  find, down-tiering reading is restored (and the hybrid gate's find+verify structure
  bills twice per round). There is no per-peer `billing flat|metered` key yet — the lever
  is that peer's `model`/`models` list.

Finish by echoing the effective config (`python3 "$H" show --host "$HOST"`) so the user
sees exactly what the panel will use.
