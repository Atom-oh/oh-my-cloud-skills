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
   python3 "$H" set codex model openai.gpt-5.6-sol --scope user   # write to ~/.claude (all your repos)
   python3 "$H" set agy model "Gemini 3.1 Pro (High)"  # Agy tokens have spaces + parens
   python3 "$H" set kiro-cli models claude-opus-4.8,minimax-m2.5,glm-5  # multi-model list
   python3 "$H" set profile deep                # activate each AI's `models` list
   python3 "$H" set harness implementer agy     # harness implementer (codex|agy)
   python3 "$H" set harness review_mode relay    # harness gate: hybrid (default) | relay | parallel
   python3 "$H" set harness parallel_tasks 3     # harness implement wave size (1 = sequential)
   python3 "$H" set harness max_fix_rounds 2     # harness per-task peer fix-loop bound
   python3 "$H" set harness implementer_model gpt-5.3-codex-mini  # write-path model (stored per implementer — set implementer first)
   python3 "$H" set harness implementer_effort low                # write-path effort (only when implementer is codex)
   python3 "$H" set pr_autofix max_iterations 5  # /co-agent:pr-autofix review-fix-push loop bound
   python3 "$H" set push_gate enabled on         # 3-lens pre-push gate (correctness/security/scope) — enabling = consent to external egress
   python3 "$H" set push_gate block off          # advisory-only (prints findings without blocking)
   python3 "$H" set push_gate timeout 180        # shared per-round timeout (seconds)
   ```
   `context_limit` lets the fan-out **skip** an AI when the context is too large for its
   model window (the cause of "prompt tokens exceed model maximum"), instead of hard-failing
   — e.g. Codex (~272K) is skipped on a huge diff while Kiro/Agy (~1M) still run. `model`
   values are charset-validated (letters/digits/`. _ : / - ( )` + spaces — agy tokens like
   `Gemini 3.1 Pro (High)`; shell metacharacters stay rejected) to keep the fan-out safe.
   **Multi-model = multi-directional verification**: with `profile deep` (the committed default), every model
   in an AI's `models` list becomes its own `(ai, model)` fan-out/relay link — one gate pass
   verifies from each configured model's direction, capped by `consensus.max_calls`. All
   overrides ride the CLIs' real headless flags (kiro/claude/agy `--model`, codex `-m`), so
   this works fully non-interactively; see `references/hybrid-gate.md` (default gate) and
   `references/relay-chain-gate.md` → "Multi-model relay" for how the gates use them.
   `pr_autofix max_iterations` bounds the `/co-agent:pr-autofix` review→fix→push loop
   (positive int, default 5). It is a config knob rather than a skill constant because the
   right number depends on how noisy the repo's review CI is — a slow reviewer wants fewer
   rounds, a chatty linter more. The skill reads it once at start via
   `co_agent_config.py pr-autofix-iterations`.
   `push_gate enabled on` turns on the `git push` PreToolUse gate
   (`consensus_hooks.py pre-push-gate`) — unlike `pr_gate` (hand-edited in the JSON
   file directly, no `set` path), `push_gate` is `set`-able because this is where the
   user is meant to opt in. It round-robins THREE LENSES (correctness/security/scope,
   not the panel's usual identical-prompt diversity) across gate-eligible peers, so
   the call count stays fixed at 3 regardless of panel size. 2+ lenses flagging an
   issue is a hard BLOCK; exactly 1 is framed as "CHAIR JUDGMENT REQUIRED" (a hook
   can't call Claude directly — this is how the verdict reaches whoever's chairing).
   Enabling is consent to external fan-out, same as `pr_gate` — and if kiro's own
   `review.on_push` is ALSO on for this repo, `set push_gate enabled on` warns that
   both gates firing means every push runs two independent review rounds (not
   recommended, not blocked). Detail: `CLAUDE.md` "Pre-push Lens Gate".
   `autosync on` makes the `CLAUDE.md` PostToolUse hook tell Claude to run
   `/co-agent:sync-context` whenever `AGENTS.md` drifts stale (opt-in; default
   off = reminder only). It refreshes `AGENTS.md` and the Kiro steering bridge;
   first-time generation is still done by running the command once.
3. If the user asks for a setting that isn't headless-settable (e.g. Agy effort),
   explain why it's not offered and suggest the closest real lever (model, or run
   that AI interactively). Do **not** invent a setting that the CLI ignores.
4. For Kiro model values, you may enumerate valid models with
   `kiro-cli chat --list-models --format json` and show the user the choices.

## Model tiering (role-based model tiering)

Rather than using the same model for every role, place a cost-efficient model per role —
the same principle as Opusplan splitting plan (Opus) from execution (Sonnet). There are
four placement points:

| Role | Character | Lever | Recommendation |
|------|------|------|------|
| **Chair** (triage/synthesis/final judgment) | narrow and strong | host model: `/model opusplan` (plan=Opus, execute=Sonnet) or spawn the `gate-chair` subagent (`agents/gate-chair.md`, `model: opus`) | keep a strong judgment model — skimping here weakens the whole gate |
| **Find panel** (hybrid gate Phase F) | wide and cheap | `profile deep` + a low-cost model in each AI's `models` list (e.g. kiro `minimax-m2.5,glm-5`) | for finding, diversity of perspective is the performance driver — more models beats a cheaper per-model rate |
| **Verify panel** (Phase V) | narrow and strong | the gate automatically uses `pairs --profile default` — each AI's single `model` becomes the verify model | set `model` to each AI's strongest tier |
| **Implementer** (harness write path) | generation-focused | `set harness implementer <ai>` + `implementer_model <m>` / `implementer_effort <e>` (falls back to the panel's `model`/`effort` if unset) | for a subscription (flat-rate) CLI (the default assumption), use **that CLI's strongest generation model** — fewer fix rounds is pure wall-clock savings. Only drop to a cheaper model under metered billing, and let the review gate act as a backstop |

- **Caution — `effort` is not phase-split**: the panel's `effort` (codex) applies equally to
  **both** the find and verify review calls (`--profile` only splits the model pair). So
  setting `set codex effort low` to cheapen find also drops verify to low, breaking the
  "verify = strongest tier" placement — keep the panel's `effort` at a level suited to
  **verify**, and lower only the write path via `implementer_effort`.
- `implementer_model`/`implementer_effort` apply **only to impl-flags (the write path)** and
  are **stored per implementer** (`harness.implementer_models.<ai>` /
  `implementer_efforts.<ai>`) — keyed by the explicit `harness.implementer` at set time, so
  **`implementer` must be set first** (exit 2 if unset), and switching later with
  `set harness implementer <other>` leaves the previous AI's entry **dormant, never leaking
  into another CLI's `--model`** (reused when switching back; `show` marks active/dormant).
  Since model names don't encode a provider, only per-AI keying is safe for both the fallback
  and an explicit switch. The review/gate path (`flags`) keeps using the panel settings, so
  the same AI (codex) can use a strong model for review and a cheap one for implementation.
  `implementer_effort` is codex-only — storing it while the implementer is agy is refused
  outright (agy's headless CLI has no effort flag).
- `pairs`/`matrix`'s `--profile default|deep` is a per-call override the hybrid gate uses to
  split find (deep) from verify (default) — it never touches the config file.
- Rationale: for finding, perspective diversity drives performance; for verifying and for
  chair judgment, the strength of a single model drives performance. See
  `references/hybrid-gate.md` "Role tiering" for the detailed flow.
- **Cost-model assumption — a per-peer attribute, not global**: flat-rate subscription CLIs
  have marginal token cost ≈ 0, so tiering's purpose isn't dollar savings but **(1)
  wall-clock** (a strong generation model = fewer fix rounds), **(2) rate-limit quota** (the
  actually scarce resource under a subscription — the usage window), and **(3) chair-triage
  noise** (widening the finder needs more digest-quality management). The flat-rate
  assumption mostly holds for the Claude Code host's default panel (kiro/codex/agy), but
  **it flips when the host changes**: on a Codex host, Claude joins as a peer (`claude -p`,
  see adapters), and if that headless call is billed per API key, that peer is **metered** —
  for that peer alone, the cost-saving reading of the table above (cheap find model,
  down-tiering) is restored, and note in particular that the hybrid gate's 2-phase
  (find+verify) structure bills twice per round for that peer. There is not yet a per-peer
  `billing flat|metered` setting key (a candidate improvement) — for now, the lever is to
  manually tune each peer's `model`/`models` list to match that peer's billing model.

Always finish by echoing the effective config (`python3 "$H" show --host "$HOST"`) so the user sees
exactly what the panel will use.
