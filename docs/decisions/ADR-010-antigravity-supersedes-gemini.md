# ADR-010: Antigravity (`agy`) Supersedes the Gemini CLI (with `gemini` fallback)

## Status

Accepted (2026-06-17) — no prior ADR established the Gemini-family slot, so none is marked
`Superseded`. "Supersedes" here means **preferred-over-with-fallback**, not full removal
(`gemini` still runs when `agy` is absent; see Decision).

## Context

The co-agent panel has used a Gemini-family CLI as one slot. Now that the `gemini` CLI is
deprecated and **Antigravity (`agy`)** has emerged as the Gemini family's successor, fanning
out to both `agy` and `gemini` would create **duplication within the same family**. A
consistent rule is needed for which one is used as the panel member.

## Options Considered

1. **Always run both** — runs the same model family twice — cost/duplication, distorts the consensus signal.
2. **Prefer `agy`, fall back to `gemini`** — use `agy` if installed, otherwise `gemini`, and skip the slot if neither is installed. (Adopted)

## Decision

Fix the Gemini-family slot's priority order as **`agy` → `gemini` → skip**:

- If both `agy` and `gemini` are present, fan-out uses only `agy` and **skips** `gemini` (to prevent duplication within the same family).
- If `agy` is absent and only `gemini` is present, use `gemini` (**backward compatibility**).
- If neither is present, skip that slot (graceful degradation).
- Scope of application: co-agent fan-out (`ai-cli-adapters.md`), the `decision-reconcile` panel, and the panel notation in user-facing documentation (README/architecture).
- Invocation: `agy -p "<P>" --model "Gemini 3.1 Pro (High)" --sandbox` (read-only). `--dangerously-skip-permissions` is forbidden.

## Consequences

- Eliminates duplication within the same family; environments with only `gemini` continue to work.
- The panel notation in user-facing documentation defaults to "Kiro/Codex/Antigravity" while **explicitly noting the Gemini fallback** (not a full replacement).
- **The `GEMINI.md` filename is kept as-is** — it is the Gemini-family context file that both Antigravity and Gemini read, independent of which CLI is selected.
- Not applied to the pr-review CI panel — `agy` is OAuth-interactive-only and cannot authenticate in headless CI (only Codex + Kiro run there).

## References

- `plugins/co-agent/CLAUDE.md`, `plugins/co-agent/skills/co-agent/references/ai-cli-adapters.md`
- `plugins/co-agent/skills/decision-reconcile/SKILL.md` (probe/invoke priority)
- README.md / README.ko.md / `docs/architecture.md` panel notation
- PR #69 (introduced the antigravity panel), #83 (corrected the agy→gemini precedence documentation)
