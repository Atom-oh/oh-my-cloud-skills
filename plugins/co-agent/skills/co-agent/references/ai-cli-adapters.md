# AI CLI Adapters

Uniform, **read-only/advisory** invocation of external AI agents for co-agent. Claude
fans a prompt out to whichever of these are installed, then synthesizes. Commands
below are verified against the installed CLIs and the existing `arch-review` /
`multi-agent-ops` skills.

## Detection

```bash
# Detect by binary presence only. kiro-cli is usable headless via an interactive
# login session OR $KIRO_API_KEY — do NOT require the env key. An unauthenticated
# CLI simply errors at call time and is skipped (graceful fallback).
command -v kiro-cli >/dev/null 2>&1 && echo "kiro ok"
command -v codex    >/dev/null 2>&1 && echo "codex ok"
command -v gemini   >/dev/null 2>&1 && echo "gemini ok"
```

## Adapter commands (read-only advisory)

| AI | Command | Notes |
|----|---------|-------|
| **Kiro** | `kiro-cli chat "<PROMPT>" --no-interactive --trust-tools=read,grep --wrap never` | Auth via interactive login **or** `KIRO_API_KEY` (Pro/Pro+/Power) — either works headless. `--wrap never` = clean output. Pipe ctx: `echo "$CTX" \| kiro-cli chat … --no-interactive`. |
| **Codex** | `codex exec -s read-only "<PROMPT>"` | `-s read-only` = read-only sandbox (no writes). Pipe ctx: `cat ctx \| codex exec -s read-only "<PROMPT>"`. Free tier has model limits. |
| **Gemini** | `gemini -p "<PROMPT>" -o text` | `-o text` plain output; optional `-m gemini-2.5-pro`. Pipe ctx: `cat ctx \| gemini -p "<PROMPT>" -o text`. |

> These are **advisory** calls — no AI writes to the repo. Claude alone writes the
> final report/decision/ADR.

## Fan-out pattern (parallel, capture, synthesize)

```bash
mkdir -p /tmp/co-agent
PROMPT="<the same prompt for every AI>"
CTX_FILE=/tmp/co-agent/context.txt   # e.g. the git diff or decision brief

# Launch available panel members in parallel, each to its own file.
[ -n "$KIRO_API_KEY" ] && command -v kiro-cli >/dev/null 2>&1 && \
  ( cat "$CTX_FILE" | kiro-cli chat "$PROMPT" --no-interactive --trust-tools=read,grep --wrap never \
    > /tmp/co-agent/kiro.md 2>/tmp/co-agent/kiro.err || echo "[skip] kiro" ) &
command -v codex >/dev/null 2>&1 && \
  ( cat "$CTX_FILE" | codex exec -s read-only "$PROMPT" \
    > /tmp/co-agent/codex.md 2>/tmp/co-agent/codex.err || echo "[skip] codex" ) &
command -v gemini >/dev/null 2>&1 && \
  ( cat "$CTX_FILE" | gemini -p "$PROMPT" -o text \
    > /tmp/co-agent/gemini.md 2>/tmp/co-agent/gemini.err || echo "[skip] gemini" ) &
wait
# Then read the non-empty *.md files and synthesize. An empty/errored file = that AI
# is unavailable this run → note it and proceed with the rest.
```

- Run them **in parallel** (`&` + `wait`) — three sequential CLI calls are slow.
- Treat an empty output or non-zero exit as "this AI skipped"; never abort the others.
- Capacity/rate errors are common on free tiers (esp. Gemini/Codex) — they degrade to
  a smaller panel, which is fine.

## Synthesis rules (Claude as chair)

1. **Consensus first**: points raised by ≥2 AIs are highest-confidence.
2. **Attribute dissent**: "Codex flagged X (others didn't)" — divergence is signal.
3. **Claude owns the verdict/decision/ADR** — the panel never decides alone.
4. Keep each AI's prompt **identical** so their answers are comparable.

## ADR hand-off (project-init `/add-adr`)

`/add-adr` (project-init) creates `docs/decisions/ADR-NNN.md` with auto-numbering.
co-agent's ADR mode provides the **collaboration layer** that enriches the
"Considered Alternatives" and "Consequences" sections with panel input. Flow:

1. `/co-agent` ADR mode gathers panel alternatives/trade-offs/risks.
2. Claude drafts the ADR body (Nygard format) merging them.
3. Write to `docs/decisions/ADR-NNN.md` following the `/add-adr` numbering convention
   (or paste into the file `/add-adr` created). co-agent does **not** modify the
   upstream `/add-adr` command itself.

## Notes

- ACP (Agent Client Protocol) exists for Kiro but `session/prompt` isn't supported for
  external clients yet — subprocess (`kiro-cli chat --no-interactive`) is the stable path.
- The optional `kiro-cli-plugin` (Claude Code) exposes interactive slash commands
  (`/kiro-cli:review`, `/kiro-cli:adversarial-review`); those are for interactive use,
  not this skill's automated fan-out.
