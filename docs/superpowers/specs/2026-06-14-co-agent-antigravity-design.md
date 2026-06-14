# Design — Add Antigravity (`agy`) to the co-agent panel

**Date:** 2026-06-14
**Status:** Approved (brainstorming)
**Scope:** Add Google Antigravity (CLI binary `agy`) to the co-agent multi-AI panel as the
**successor to the Gemini CLI** — `agy` is the Gemini-family member going forward; the
standalone `gemini` CLI is deprecated and being migrated to `agy`.

## Goal

co-agent fans the same prompt to whichever installed AI CLIs exist, then Claude (chair)
synthesizes. Today the panel is Kiro / Codex / Gemini. Add **Antigravity (`agy`)** as the
Gemini-family panel member. Because `gemini` is deprecated in favor of `agy` (both are
Gemini-family — running both is same-family redundancy), **when both `agy` and `gemini` are
installed, the panel uses `agy` and drops `gemini`** (see D4). When only `gemini` is present,
it still runs (backward compatible); when neither is present, the panel degrades gracefully.

## Ground truth — the `agy` CLI (verified via `agy --help` / `agy models`)

Binary: **`agy`** (NOT `agv`), at `~/.local/bin/agy`.

```
-p / --print / --prompt          Run a single prompt non-interactively and print the response
--model                          Model for the current CLI session
--sandbox                        Run in a sandbox with terminal restrictions enabled
--dangerously-skip-permissions   Auto-approve all tool permissions (DO NOT USE)
-c / --continue, --conversation  (session continuation — unused here)
subcommands: models, plugin, update, install, changelog
```

`agy models` (exact tokens — **note the spaces and parentheses**):
`Gemini 3.5 Flash (Medium|High|Low)`, `Gemini 3.1 Pro (Low|High)`,
`Claude Sonnet 4.6 (Thinking)`, `Claude Opus 4.6 (Thinking)`, `GPT-OSS 120B (Medium)`.

- Default model for the panel: **`Gemini 3.1 Pro (High)`** (user-chosen; exact valid token).
- No standalone reasoning/effort flag — "(High)" is baked into the model token. So, like
  Gemini/Kiro, `agy` has no headless `effort` lever (effort stays Codex-only).
- `-p` already prints non-interactively (no TUI); there is **no `-o text` flag**.
- Context files: `agy` auto-loads BOTH `AGENTS.md` and `GEMINI.md` from the repo root. The
  two files co-agent generates are byte-identical except the line-1 role header, so `agy`
  reusing them needs **no new context file**.

> Reminder applied: gemini's *researched* guess (`-m`, `-o text`) was wrong; only the
> `agy --help` ground truth is authoritative. The plugin's "adapters verified against the
> installed CLI" rule holds.

## Adapter

Read-only / advisory invocation (mirrors the Kiro/Codex/Gemini shape):

```bash
cat "$CTX_FILE" | timeout "$T" agy -p "$PROMPT" --model "$model" --sandbox \
  > "$slot.md" 2>"$slot.err" || echo "[skip] antigravity/$model"
```

- `--sandbox` enforces terminal restrictions (no writes) — required because panel output is
  advisory and no AI may mutate the repo. `--dangerously-skip-permissions` is never used.
- `-p "$PROMPT"` = fixed instruction; context piped via **stdin** (consistent with the
  other adapters; keeps untrusted repo content off the command line).
- **Verification step (implementation):** confirm `agy -p` actually consumes stdin with one
  minimal live call. If it does not, fall back to inlining the (size-bounded) context into
  the prompt — same approach used for the small PR #68 review.

## Decisions

### D1 — Model-name validation (security-relevant)
`agy` model tokens contain spaces and parentheses (`Gemini 3.1 Pro (High)`), which the
current `MODEL_RE = ^[A-Za-z0-9._:/-]+$` rejects. Relax it to also allow **space and
parentheses**, still blocking every shell metacharacter:

```
MODEL_RE = ^[A-Za-z0-9 ._:/()-]+$
```

Safe because the fan-out always passes the model as a single quoted argv element
(`--model "$model"` / `"${MFLAGS[@]}"`), so spaces/parens are never word-split or
interpreted. The regex still rejects `; | & $ \` " ' < > \ { }` etc. — the actual injection
vectors. This is a shared-validator change (applies to all AIs) — acceptable: it only widens
the allowed set by space + `()`, both inert inside a quoted argv.

### D2 — Context files: no change
co-agent integration does not touch context-file generation. `agy` reuses the existing
`AGENTS.md`/`GEMINI.md` (Codex + Gemini already require them). The fact that `agy` loads both
identical files is an `agy`-side rule-config preference, out of scope here. (Optional, separate:
the user may configure `agy` to load just one to avoid duplicate guidelines.)

### D3 — Panel key + defaults
- Key: **`antigravity`** (binary `agy`) — descriptive, consistent with product naming.
- Defaults in `co-agent.defaults.json`:
  `"antigravity": { "enabled": true, "model": "Gemini 3.1 Pro (High)", "models": [], "context_limit": 1000000 }`
- `enabled: true` — the Gemini-family member going forward.
- `context_limit: 1_000_000` — conservative (Gemini 3.1 Pro is large-context; exact window
  unconfirmed, 1M matches the Kiro/Gemini default and is safe).
- `models: []` — single default model; no deep-profile expansion (avoid same-family
  redundancy / extra cost). Can be widened later via `/co-agent:configure`.
- **Cap check:** with D4 supersession, when `agy` is present the panel is
  kiro×3 + codex + antigravity = **5 pairs** (`gemini` dropped) — same as today's 5, so
  `per-round cap 6` is not exceeded and no `max_calls` change is needed.

### D4 — `agy` supersedes `gemini` (install-aware)
`gemini` is deprecated in favor of `agy`; both are Gemini-family, so running both is
redundant. **When both binaries are installed, the fan-out drops `gemini` and runs `agy`.**
This is *install-aware* (depends on `command -v`), so it lives in the **fan-out detection**,
not in static config:

- In the fan-out, compute `HAS_AGY=$(command -v agy)`. When iterating `(ai, model)` pairs,
  **skip every `gemini` pair if `HAS_AGY`**. `agy` pairs run normally; if `agy` is absent,
  `gemini` runs unchanged (backward compatible).
- Config keeps both `gemini` and `antigravity` `enabled: true` — the supersession is a
  runtime install fact, not a config preference. `matrix` (a config-time cost preview) notes
  that `gemini` is superseded by `agy` when `agy` is installed.
- Rationale for fan-out (not config): `co_agent_config.py` is pure config and cannot know
  what is installed; the fan-out already does `command -v` per AI and skips absent ones, so
  the one-line "skip gemini if agy present" rule belongs in the same place.

## Components changed (units, each with one purpose)

| File | Change |
|------|--------|
| `co_agent_config.py` | `AIS += ("antigravity",)`; `cmd_flags` antigravity branch → `--model "<model>"`; relax `MODEL_RE` (D1); ensure `models`/`enabled`/`context_limit` paths cover it (generic). |
| `co-agent.defaults.json` | Add `panel.antigravity` entry (D3). |
| `references/ai-cli-adapters.md` | Detection `command -v agy`; adapter-command table row; fan-out `case` branch `antigravity)`; **D4 supersession rule** (`skip gemini if agy present`); note `--sandbox`, stdin, no-skip-permissions. |
| `commands/configure.md` | Settings table + `context_limit`/matrix mention for antigravity; D4 note (gemini superseded by agy when installed); note no headless effort (model token carries "(High)"). |
| `plugins/co-agent/CLAUDE.md` + root `CLAUDE.md` | Mention the panel AIs (Kiro/Codex/Antigravity, with Gemini as the deprecated predecessor of Antigravity). |
| tests | Update any test asserting the 3-AI panel / `AIS` membership; add cases for the antigravity flags, the relaxed `MODEL_RE` (accepts `Gemini 3.1 Pro (High)`, still rejects `a;b`, `$(x)`, `a|b`), and the D4 supersession (gemini skipped when agy present). |

## Testing

- `co_agent_config.py`: `pairs`/`matrix`/`panel`/`flags antigravity`/`fits` include antigravity;
  `set antigravity model "Gemini 3.1 Pro (High)"` accepted; `MODEL_RE` rejects shell metachars.
- Fan-out dry check: `agy` present → appears in the panel; absent → gracefully skipped.
- **D4 supersession:** with `agy` present, the fan-out skips `gemini`; with `agy` absent,
  `gemini` runs. (Assert the detection rule; can be a shell-level unit on the documented
  fan-out snippet / a `command -v` stub.)
- `tests/run-all.sh` green.

## Risks / open items

- **stdin consumption by `agy -p`** — verified during implementation (fallback: inline context).
- **`--sandbox` scope** — assumed to still allow the model to answer over the piped context
  (it restricts the terminal/tools, not the prompt). Confirm in the live check.
- **`context_limit` exact value** — 1M is a safe default; adjust if `agy` documents otherwise.
- MODEL_RE relaxation is intentionally minimal (space + `()` only).

## Out of scope

- De-duplicating `AGENTS.md`/`GEMINI.md` generation.
- Adding `agy`'s Claude/GPT-OSS models to the panel (single Gemini 3.1 Pro (High) default only).
- Any `/sync-docs` change (covered separately; co-agent hook is already doc-sync-aware).
