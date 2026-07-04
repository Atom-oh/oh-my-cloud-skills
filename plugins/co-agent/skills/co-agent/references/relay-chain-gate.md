# Relay-Chain Gate (co-agent:harness)

> **Scope:** the review gate used **inside `/co-agent:harness`** (H2 plan gate, H4 final
> gate) when `harness.review_mode == "relay"` (the default). It replaces the **independent
> parallel** fan-out of `references/consensus-mode.md` with a **sequential relay chain**:
> peers review one at a time, each building on the prior peers' findings, and the host
> (chair) synthesizes one high-confidence verdict at the end. Set `review_mode == "parallel"`
> to fall back to the `consensus-mode.md` gate. **Only harness reads this file** —
> `/co-agent:consensus` and the review/decide/ADR modes keep the parallel gate.

## Why relay instead of parallel

- **Parallel** (consensus-mode.md) = N *independent* opinions, then vote-with-verification.
  Good for breadth and for a quorum. Each peer sees only the artifact, never the others.
- **Relay** = one *cumulative* pass. Peer *k* sees the artifact **plus every prior peer's
  findings** and is asked to confirm/refute each and add what was missed. The chain deepens
  instead of duplicating, so the panel converges on **one thoroughly-vetted result in a
  single pass** — the harness goal ("완주해서 신뢰도 높은 결과를 한 번에 도출").
- Trade-off: relay is **sequential** (slower wall-clock, no `&`/`wait`) and later peers are
  primed by earlier ones (less independence). That priming is the point here — the chair
  still verifies every surviving finding against the actual code, so a wrong early claim is
  caught, not amplified.

## Ordering

Process the gate-eligible `(ai, model)` pairs from `co_agent_config.py pairs` **in order**,
but put the **strongest reasoner last** so it reviews with the most accumulated context.
The counterpart peer (Codex when Claude hosts; Claude when Codex hosts) is usually the
strongest — leave it at the tail of the chain. Reorder by toggling `enabled` / trimming
`models` in `/co-agent:configure`; there is no separate relay-order key. A single
gate-eligible pair degenerates to one review (still valid — see Quorum).

## The gate (one relay round)

Let `SK="${CLAUDE_PLUGIN_ROOT}/skills/co-agent/scripts"` and `CFG="$SK/co_agent_config.py"`.

```bash
RUN=$(mktemp -d "${TMPDIR:-/tmp}/co-agent-relay.XXXXXX"); trap 'rm -rf "$RUN"' EXIT
HOST="${CO_AGENT_HOST:-claude}"
T=$(python3 "$CFG" timeout --host "$HOST" 2>/dev/null || echo 240)

# The artifact under review (plan doc for H2, cumulative diff for H4). Secret-scan it and
# obtain consent BEFORE the first peer — same data boundary as the parallel fan-out.
ARTIFACT="$RUN/artifact.txt"      # write the plan / cumulative diff here first
CHAIN="$RUN/chain.md"; : > "$CHAIN"   # accumulated prior findings (empty for peer #1)

# Fixed per-peer instruction — NEVER built from repo content.
BASE_PROMPT='You are one reviewer in a RELAY CHAIN. Review the ARTIFACT below for
correctness, scope, completeness, and AWS security mandate violations (no 0.0.0.0/0, no
IAM Principal "*", no secrets in env). If PRIOR FINDINGS are present, first CONFIRM or
REFUTE each against the actual content (cite the line/section), then ADD anything missed.
Do not repeat a prior finding you agree with — just mark it CONFIRMED. Output a single
consolidated findings list; label each CRITICAL / MAJOR / MINOR / NIT with evidence.'

i=0
while IFS=$'\t' read -r ai model; do
  i=$((i+1)); slot="$RUN/${i}-${ai}"
  # Per-peer context = the artifact + everything the chain has accumulated so far.
  CTX="$RUN/${i}-ctx.txt"
  { echo "=== ARTIFACT ==="; cat "$ARTIFACT"; echo;
    if [ -s "$CHAIN" ]; then echo "=== PRIOR FINDINGS (relay so far) ==="; cat "$CHAIN"; fi
  } > "$CTX"
  mapfile -t MFLAGS < <(python3 "$CFG" flags "$ai" --model "$model" --host "$HOST" 2>/dev/null || true)
  TOK=$(( ( $(wc -c < "$CTX") + 3 ) / 4 ))
  if ! python3 "$CFG" fits "$ai" "$TOK" --host "$HOST" 2>/dev/null; then
    echo "[skip] $ai/$model — ctx ~${TOK} tok > window"; continue
  fi
  # SEQUENTIAL — no `&`, no `wait`. Each peer must finish before the next starts so its
  # findings enter the chain. Same adapters as ai-cli-adapters.md (stdin for codex/claude/
  # agy/gemini; kiro reads the ctx file via fs_read since it ignores stdin).
  case "$ai" in
    kiro-cli) command -v kiro-cli >/dev/null 2>&1 && timeout "$T" \
                kiro-cli chat "$BASE_PROMPT"$'\n\n'"Read the review context with fs_read from: $CTX" \
                "${MFLAGS[@]}" --v3 --mode default --no-interactive --trust-tools=fs_read --wrap never \
                > "$slot.md" 2>"$slot.err" || echo "[skip] kiro-cli/$model" ;;
    claude)   command -v claude >/dev/null 2>&1 && cat "$CTX" | timeout "$T" \
                claude -p "$BASE_PROMPT" "${MFLAGS[@]}" --permission-mode plan \
                --tools Read,Grep,Glob --output-format text > "$slot.md" 2>"$slot.err" || echo "[skip] claude/$model" ;;
    codex)    command -v codex >/dev/null 2>&1 && cat "$CTX" | timeout "$T" \
                codex exec -s read-only "${MFLAGS[@]}" "$BASE_PROMPT" > "$slot.md" 2>"$slot.err" || echo "[skip] codex/$model" ;;
    agy)      if command -v agy >/dev/null 2>&1; then cat "$CTX" | timeout "$T" \
                agy -p "$BASE_PROMPT" "${MFLAGS[@]}" --sandbox > "$slot.md" 2>"$slot.err" || echo "[skip] agy/$model";
              elif command -v gemini >/dev/null 2>&1; then cat "$CTX" | timeout "$T" \
                gemini -p "$BASE_PROMPT" -o text > "$slot.md" 2>"$slot.err" || echo "[skip] gemini-fallback/$model"; fi ;;
    gemini)   command -v gemini >/dev/null 2>&1 && cat "$CTX" | timeout "$T" \
                gemini "${MFLAGS[@]}" -p "$BASE_PROMPT" -o text > "$slot.md" 2>"$slot.err" || echo "[skip] gemini/$model" ;;
  esac
  # Fold this peer's output into the chain for the NEXT peer. Skip empty/errored output.
  if [ -s "$slot.md" ]; then
    { echo; echo "## Reviewer $i — $ai/$model"; cat "$slot.md"; } >> "$CHAIN"
  fi
done < <(python3 "$CFG" pairs --host "$HOST" 2>/dev/null)
# The final $CHAIN holds the full relay. The host (chair) synthesizes from it — see below.
```

## Chair synthesis (host) — unchanged verification, cumulative input

The chain is **advisory input**, not the verdict. The host:

1. Runs `check_citations.py` over the accumulated findings → drop `unsupported`, flag
   `needs-review`. A finding a later peer marked CONFIRMED still needs a real citation.
2. Verifies each surviving finding **against the actual plan/diff** — a relay can propagate
   an early peer's mistake down the chain, so confirm, don't trust the "CONFIRMED" label.
3. Attributes dissent: "Reviewer 2 refuted Reviewer 1's X" is signal, keep it in the report.
4. Emits the verdict (PASS / REVIEW / FAIL) and, on CRITICAL/MAJOR, the fix list.

## Quorum (relay differs from parallel)

Relay is **cumulative**, not independent votes, so parallel's "≤1 usable pair → single-
opinion, not consensus" rule does **not** apply — one relayed pass with **≥1 peer** that
produced output is a valid gate result (the chair still verifies every finding). But harness
is **non-degraded**: if **zero** gate-eligible peers produced any output, do **not** solo —
`consensus_state.py set . status needs-human` (H2) / block and tell the user to run
`/co-agent:setup`, exactly as the parallel gate does.

## Loop-until-done

Same as the parallel gate: repeat the relay round up to `consensus.max_rounds` (default 2)
until no CRITICAL/MAJOR finding survives the chair's verification (also stop on no-progress /
oscillation). Between rounds, reset `$CHAIN` and re-run the chain on the *updated* artifact —
each round is a fresh relay over the current plan/diff, not an append to the prior round.
Record the outcome via `consensus_state.py stage-result` (`…/plan-gate/result.json` for H2,
`…/code-gate/result.json` for H4), then advance the harness phase.

## Security

Identical trust boundary to `ai-cli-adapters.md` — the artifact is secret-scanned and
consented before the first peer; context goes via stdin (kiro via a temp file + `fs_read`);
peers run read-only/sandboxed with a sanitized env. The **added** exposure is that each
peer's context now includes prior peers' text (`$CHAIN`), which is peer-generated, not repo
content — so it carries no new secret, but a compromised peer could try prompt-injection on
the next. Mitigation is the same: the chair treats all peer output as advisory and verifies
against the code; no peer's verdict is authoritative.
