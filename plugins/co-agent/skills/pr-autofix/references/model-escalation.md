# §5a Model Escalation — Rung Table & Application Mechanics

Read from SKILL.md §5a when `$ITERATION -gt 5` (post-commit value). One rung per
escalated pass: pass 6 = rung 1, pass 7 = rung 2, …; past the last rung, stay on it.

## Rung table

| Peer | Rung 1 | Rung 2 | Rung 3 |
|------|--------|--------|--------|
| kiro-cli | `claude-opus-5` | `claude-fable-5` (only if `kiro-cli chat --list-models` lists it — it's `[Internal]`) | `gpt-5.6-sol` |
| codex | `openai.gpt-5.6-sol`, effort `xhigh` | — | — |
| agy | stays on its configured/default model (no escalation rung defined for it) | — | — |
| chair | spawn `co-agent:gate-chair` (`opus`+`xhigh`) for triage instead of judging inline | — | — |

- Check `kiro-cli chat --list-models` for `claude-fable-5` before using rung 2 — never
  assume it's available; skip straight to `gpt-5.6-sol` if it's not listed.
- A rung's model can still return `INVALID_MODEL_ID` even when listed — treat that
  invocation as a skipped peer for this call, never a loop abort (same fail-open
  contract §5b's gate already has).

## Applying the override

Via the env vars `consensus_hooks.py` reads for exactly this purpose
(`_model_override`/`_codex_effort_override`) — set them right before §5b's call, unset
right after:

```bash
if [ "$ITERATION" -gt 5 ]; then
  export CO_AGENT_GATE_MODEL_OVERRIDE_KIRO_CLI="claude-opus-5"   # or the resolved rung
  export CO_AGENT_GATE_MODEL_OVERRIDE_CODEX="openai.gpt-5.6-sol"  # rung 1 — set explicitly,
  # never rely on it happening to match the configured panel default; a future config
  # change must not silently disable this escalation.
  export CO_AGENT_GATE_CODEX_EFFORT_OVERRIDE="xhigh"
fi
```

Unset all three
(`unset CO_AGENT_GATE_MODEL_OVERRIDE_KIRO_CLI CO_AGENT_GATE_MODEL_OVERRIDE_CODEX CO_AGENT_GATE_CODEX_EFFORT_OVERRIDE`)
immediately after §5b's call — these must not leak into a later, non-escalated pass.
